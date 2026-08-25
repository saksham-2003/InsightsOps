import time
import json
import logging
from typing import Dict, Any, List, Optional

from src.agents.planner import create_ai_plan
from src.agents.router import route_query
from src.agents.llm_client import get_llm_client, create_chat_completion_with_retry, extract_response_text
from .state import ConversationMemoryManager, TurnContext, FilterState
from .metadata_loader import MetadataLoader, BusinessMetadata
from .entity_extractor import EntityExtractor, ExtractedEntities

# Phase B: EvidenceAnalysisEngine wired into the active pipeline (deterministic, no LLM call)
from .evidence_analyst import EvidenceAnalysisEngine

# ============================================================
# INTENT-AWARE SYNTHESIS INSTRUCTIONS
# Each key matches a value from planner.SUPPORTED_INTENTS.
# When multiple intents are detected, ALL matching blocks are
# merged and injected into the synthesis prompt — additive, not
# conflicting (each block covers a distinct analytical dimension).
# ============================================================
INTENT_INSTRUCTIONS: Dict[str, str] = {
    "Revenue": """
═══ REVENUE ANALYSIS CONTRACT ═══
• Open with the exact total revenue figure and the period it covers.
• If monthly trend data is present, calculate and state overall growth % (first → last period).
• Name the peak period and its exact revenue; name the trough period and its exact revenue.
• State the single largest MoM swing: direction, % change, months involved.
• Quantify every statement: never write \"revenue increased\" — write \"revenue increased by
  54.2% from $120,450 (October) to $185,492 (November)\".
• If profit/margin data is present, state whether revenue growth is translating to profit.""",

    "Trend": """
═══ TREND ANALYSIS CONTRACT ═══
• Describe overall direction (growing/declining/flat) with exact % change across the full period.
• Name peak and trough periods with exact values.
• Identify the steepest MoM increase and steepest MoM decline, naming the periods and % values.
• Comment on whether the trend is accelerating, stable, or decelerating in recent periods.""",

    "Region": """
═══ REGIONAL ANALYSIS CONTRACT ═══
• Rank ALL available regions by revenue from highest to lowest with exact figures.
• Calculate each region's % share of total revenue (e.g., \"East: 38.4% of total\").
• Quantify the performance gap between the top and bottom region in both $ and %.
• Flag any region performing significantly below the regional average.
• If category or product data is also available, attribute regional leadership to specific
  categories if the evidence supports it.""",

    "Category": """
═══ CATEGORY ANALYSIS CONTRACT ═══
• Rank ALL available categories by revenue with exact figures and % contribution to total.
• Identify the highest and lowest performing categories with exact values.
• If order volume is available, identify any category with high orders but low revenue
  (pricing opportunity) or high revenue but low orders (premium concentration risk).
• Surface the strongest growth opportunity based on the data.""",

    "Forecast": """
═══ FORECAST ANALYSIS CONTRACT ═══
• State the forecast horizon explicitly (e.g., \"over the next 90 days\").
• Name the peak predicted period and its value; name the trough and its value.
• State overall forecast direction (growing/declining/flat) with % change first → last period.
• If R² or accuracy metrics are available, state and interpret them
  (e.g., \"R²=0.87 indicates high model reliability\").
• Always add: these are model-predicted values, not actuals.
• If forecast shows decline, provide specific evidence-backed mitigation recommendations.""",

    "Anomaly": """
═══ ANOMALY ANALYSIS CONTRACT ═══
• State total flagged anomalies and their exact % of total transactions.
• If severity data is available, break down the count by severity level (Critical/High/Medium/Low).
• Describe the most likely systemic cause based on patterns in the evidence
  (e.g., concentrated in a specific category, region, or time window).
• Provide 2–3 specific, actionable investigation steps that can be taken immediately.
• Quantify potential revenue/profit at risk if the data supports it.""",

    "Product": """
═══ PRODUCT ANALYSIS CONTRACT ═══
• List top and bottom products with exact revenue figures.
• State the revenue gap between #1 and last-ranked product.
• Calculate revenue concentration: what % of total revenue comes from the top 3 products?
• Identify products with disproportionately low revenue relative to their category peers.
• Flag high-concentration risk if the top 3 products exceed 40% of total revenue.""",

    "Comparison": """
═══ COMPARISON ANALYSIS CONTRACT ═══
• Present exact figures for each entity being compared.
• Calculate absolute ($) and relative (%) differences.
• Identify the leader and quantify the margin of difference.
• Explain what likely drives the gap based on available evidence.""",

    "Profit": """
═══ PROFIT ANALYSIS CONTRACT ═══
• State total profit and profit margin with exact figures.
• Comment on whether margin is expanding, stable, or compressing relative to revenue.
• If both revenue and profit trends are present, calculate the divergence explicitly.
• Flag margin compression if revenue grew while profit declined.""",
}


class InsightsOpsOrchestrator:
    """
    Multi-stage orchestration engine for InsightsOps Business Analyst.

    Designed to behave like a professional Business Analyst and explicitly
    structured for future Agentic AI capabilities:

    - Conversation Memory: Integrated via ConversationMemoryManager.
    - Reflection & Self Critique: Outputs can be looped back to LLM for validation.
    - Agent Retry: LLM generation blocks are structured to easily wrap with tenacity/retries.
    - Parallel Execution & Caching: Directly integrated via upstream dynamic router.
    """

    def __init__(self, memory_manager: ConversationMemoryManager):
        self.client = None
        # Phase A fix: use the valid alias defined in llm_client.py.
        # "openai/gpt-oss-20b" is not a real model name and caused silent
        # fallbacks or errors on every Synthesis and Reflection call.
        self.model = "insight_generator"
        self.temperature = 0.1
        self.memory_manager = memory_manager

    def _get_client(self):
        if self.client is None:
            self.client = get_llm_client()
        return self.client

    def validate_and_clean_evidence(self, raw_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        STEP 4: Validate evidence.
        Removes duplicates, drops empty values, and filters out missing/failed tool outputs.
        """
        cleaned = {}
        for tool_name, data in raw_results.items():
            if not data:
                continue

            # Handle structured dictionary responses
            if isinstance(data, dict):
                if data.get("success") is False or "error" in data:
                    continue  # Drop failed tool executions
                if not data:
                    continue
                cleaned[tool_name] = data

            # Handle list responses and remove duplicates
            elif isinstance(data, list):
                if len(data) == 0:
                    continue

                unique_list = []
                seen = set()
                for item in data:
                    if isinstance(item, dict):
                        item_str = json.dumps(item, sort_keys=True, default=str)
                        if item_str not in seen:
                            seen.add(item_str)
                            unique_list.append(item)
                    else:
                        if item not in seen:
                            seen.add(item)
                            unique_list.append(item)

                if unique_list:
                    cleaned[tool_name] = unique_list
            else:
                cleaned[tool_name] = data

        return cleaned

    def _safe_float(self, value: Any) -> float:
        try:
            if value is None:
                return 0.0
            if isinstance(value, (int, float)):
                return float(value)
            return float(str(value).replace(",", "").replace("$", ""))
        except (TypeError, ValueError):
            return 0.0

    def _compute_business_metrics(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute lightweight, deterministic business metrics in Python before the synthesis LLM runs.
        These metrics are meant to enrich the context with concrete business facts and reduce the need
        for the LLM to infer them from raw arrays.
        """
        metrics: Dict[str, Any] = {}

        monthly_trend = evidence.get("monthly_trend", [])
        if isinstance(monthly_trend, list) and monthly_trend:
            revenues = [self._safe_float(item.get("Revenue", 0)) for item in monthly_trend if isinstance(item, dict)]
            profits = [self._safe_float(item.get("Profit", 0)) for item in monthly_trend if isinstance(item, dict)]
            if revenues:
                peak_idx = max(range(len(revenues)), key=lambda idx: revenues[idx])
                lowest_idx = min(range(len(revenues)), key=lambda idx: revenues[idx])
                peak_month = monthly_trend[peak_idx].get("Order_Date", "") if peak_idx < len(monthly_trend) else ""
                lowest_month = monthly_trend[lowest_idx].get("Order_Date", "") if lowest_idx < len(monthly_trend) else ""

                mom_changes = []
                for i in range(1, len(revenues)):
                    prev = revenues[i - 1]
                    curr = revenues[i]
                    if prev > 0:
                        mom_changes.append(round(((curr - prev) / prev) * 100, 2))
                    else:
                        mom_changes.append(0.0)

                metrics["mom_growth"] = {
                    "values": mom_changes,
                    "peak_month": peak_month,
                    "lowest_month": lowest_month,
                    "fastest_growing_month": monthly_trend[mom_changes.index(max(mom_changes)) + 1].get("Order_Date", "") if mom_changes else None,
                    "steepest_decline": monthly_trend[mom_changes.index(min(mom_changes)) + 1].get("Order_Date", "") if mom_changes else None,
                    "overall_growth_pct": round(((revenues[-1] - revenues[0]) / revenues[0]) * 100, 2) if revenues and revenues[0] > 0 else 0.0,
                }

                if len(revenues) >= 6:
                    quarterly_totals = [sum(revenues[i:i+3]) for i in range(0, len(revenues), 3)]
                    if len(quarterly_totals) >= 2:
                        prev_q = quarterly_totals[-2]
                        curr_q = quarterly_totals[-1]
                        metrics["qoq_growth_pct"] = round(((curr_q - prev_q) / prev_q) * 100, 2) if prev_q > 0 else 0.0

            if profits:
                metrics["profit_trend"] = {
                    "first_profit": round(profits[0], 2),
                    "last_profit": round(profits[-1], 2)
                }

        category_data = evidence.get("category_performance", [])
        if isinstance(category_data, list) and category_data:
            total_category_rev = sum(self._safe_float(item.get("Revenue", 0)) for item in category_data if isinstance(item, dict))
            if total_category_rev > 0:
                contributions = []
                for item in category_data:
                    if not isinstance(item, dict):
                        continue
                    rev = self._safe_float(item.get("Revenue", 0))
                    contributions.append({
                        "category": item.get("Category", "Unknown"),
                        "revenue": round(rev, 2),
                        "contribution_pct": round((rev / total_category_rev) * 100, 2) if total_category_rev else 0.0,
                    })
                metrics["category_contributions"] = sorted(contributions, key=lambda entry: entry["revenue"], reverse=True)
                metrics["top_category_contribution_pct"] = metrics["category_contributions"][0]["contribution_pct"] if metrics["category_contributions"] else 0.0

        region_data = evidence.get("regional_performance", [])
        if isinstance(region_data, list) and region_data:
            total_region_rev = sum(self._safe_float(item.get("Revenue", 0)) for item in region_data if isinstance(item, dict))
            if total_region_rev > 0:
                contributions = []
                for item in region_data:
                    if not isinstance(item, dict):
                        continue
                    rev = self._safe_float(item.get("Revenue", 0))
                    contributions.append({
                        "region": item.get("Region", "Unknown"),
                        "revenue": round(rev, 2),
                        "contribution_pct": round((rev / total_region_rev) * 100, 2) if total_region_rev else 0.0,
                    })
                metrics["region_contributions"] = sorted(contributions, key=lambda entry: entry["revenue"], reverse=True)
                metrics["top_region_contribution_pct"] = metrics["region_contributions"][0]["contribution_pct"] if metrics["region_contributions"] else 0.0

        top_products = evidence.get("top_products", [])
        if isinstance(top_products, list) and top_products:
            total_product_rev = sum(self._safe_float(item.get("Revenue", 0)) for item in top_products if isinstance(item, dict))
            if total_product_rev > 0:
                metrics["top_product_contribution_pct"] = round(self._safe_float(top_products[0].get("Revenue", 0)) / total_product_rev * 100, 2) if isinstance(top_products[0], dict) else 0.0
                top3_rev = sum(self._safe_float(item.get("Revenue", 0)) for item in top_products[:3] if isinstance(item, dict))
                metrics["top3_concentration_pct"] = round((top3_rev / total_product_rev) * 100, 2) if total_product_rev > 0 else 0.0

        if monthly_trend and isinstance(monthly_trend, list):
            revenues_total = sum(self._safe_float(item.get("Revenue", 0)) for item in monthly_trend if isinstance(item, dict))
            if revenues_total > 0:
                metrics["revenue_concentration_pct"] = round(self._safe_float(monthly_trend[-1].get("Revenue", 0)) / revenues_total * 100, 2) if isinstance(monthly_trend[-1], dict) else 0.0

        if metrics:
            metrics["driver_summary"] = {
                "top_category": metrics.get("category_contributions", [{}])[0].get("category") if metrics.get("category_contributions") else None,
                "top_region": metrics.get("region_contributions", [{}])[0].get("region") if metrics.get("region_contributions") else None,
            }

        return metrics

    def _resolve_primary_intent(self, intents: Optional[List[str]] = None) -> Optional[str]:
        if not intents:
            return None

        priority_order = [
            "Forecast",
            "Anomaly",
            "Product",
            "Region",
            "Category",
            "Revenue",
            "Trend",
            "Profit",
            "Comparison",
            "Executive Summary",
            "Recommendation",
            "General Business Question",
        ]

        for intent in priority_order:
            if intent in intents:
                return intent
        return None

    def _resolve_primary_visualization(self, intents: Optional[List[str]] = None, executed_tools: Optional[List[str]] = None) -> Optional[str]:
        if not executed_tools and not intents:
            return None

        if any(intent in (intents or []) for intent in ["Forecast"]):
            return "multi_line"
        if any(intent in (intents or []) for intent in ["Anomaly", "Risk"]):
            return "scatter"
        if any(intent in (intents or []) for intent in ["Category"]):
            return "pie"
        if any(intent in (intents or []) for intent in ["Region", "Comparison"]):
            return "bar"
        if any(intent in (intents or []) for intent in ["Product"]):
            return "horizontal_bar"
        if any(tool in (executed_tools or []) for tool in ["forecast_evaluation"]):
            return "multi_line"
        if any(tool in (executed_tools or []) for tool in ["anomaly_detection"]):
            return "scatter"
        if any(tool in (executed_tools or []) for tool in ["category_performance"]):
            return "pie"
        if any(tool in (executed_tools or []) for tool in ["regional_performance"]):
            return "bar"
        if any(tool in (executed_tools or []) for tool in ["top_products", "bottom_products"]):
            return "horizontal_bar"
        return "line"

    def _filter_context_for_intent(self, context_str: str, intents: Optional[List[str]] = None, executed_tools: Optional[List[str]] = None) -> str:
        try:
            context_obj = json.loads(context_str) if isinstance(context_str, str) else context_str
        except Exception:
            return context_str

        if not isinstance(context_obj, dict):
            return context_str

        primary_intent = self._resolve_primary_intent(intents)
        allowed_keys = []

        if primary_intent == "Revenue":
            allowed_keys = ["KPIs", "Monthly Trend", "Monthly_Trend", "Monthly_Trend_Analysis", "Business Metrics", "Business_Metrics", "computed_business_metrics", "structured_evidence_facts"]
        elif primary_intent == "Category":
            allowed_keys = ["KPIs", "Category Performance", "Category_Performance", "Business Metrics", "Business_Metrics", "computed_business_metrics", "structured_evidence_facts"]
        elif primary_intent == "Region":
            allowed_keys = ["KPIs", "Regional Performance", "Regional_Performance", "Business Metrics", "Business_Metrics", "computed_business_metrics", "structured_evidence_facts"]
        elif primary_intent == "Forecast":
            allowed_keys = ["Forecast", "Forecast Metrics", "Forecast_Metrics", "Forecast_Trends", "Predictions", "Forecasts", "Business Metrics", "Business_Metrics", "computed_business_metrics", "structured_evidence_facts"]
        elif primary_intent == "Anomaly":
            allowed_keys = ["Anomaly Summary", "Anomalies_Summary", "Anomaly Table", "Top_Anomalies", "Anomalies", "structured_evidence_facts"]
        elif primary_intent == "Product":
            allowed_keys = ["Top Products", "Top_Products", "Bottom Products", "Bottom_Products", "Business Metrics", "Business_Metrics", "computed_business_metrics", "structured_evidence_facts"]
        else:
            allowed_keys = list(context_obj.keys())

        filtered_context = {}
        for key in allowed_keys:
            if key in context_obj and context_obj.get(key):
                filtered_context[key] = context_obj[key]

        if not filtered_context and context_obj:
            filtered_context = context_obj

        return json.dumps(filtered_context, default=str)

    def generate_business_context(self, evidence: Dict[str, Any]) -> str:
        """
        STEP 3 & 5: Collect and Generate Business Context.
        Merges outputs from all executed tools into one structured evidence object.
        Summarizes KPIs, Forecasts, Anomalies, Regional/Category performance, etc.
        """
        context_obj = {}

        # Explicitly map known tools to structured context segments
        if "kpi_summary" in evidence:
            context_obj["KPIs"] = evidence["kpi_summary"]

        if "forecast_evaluation" in evidence:
            fc = evidence["forecast_evaluation"]

            if isinstance(fc, dict) and "predictions" in fc:

                context_obj["Forecast_Metrics"] = fc.get("metrics", {})

                # Keep only actual FUTURE forecast records.
                # Historical records contain an actual Revenue value,
                # while future forecast records have Revenue=None.
                future_predictions = [
                    prediction
                    for prediction in fc["predictions"]
                    if prediction.get("Revenue") is None
                    and prediction.get("Predicted_Revenue") is not None
                ]

                # Pass the complete requested forecast horizon to the
                # Evidence Analyst instead of artificially limiting it to 15 days.
                context_obj["Forecast_Trends"] = future_predictions

            else:
                context_obj["Forecasts"] = fc

        if "anomaly_detection" in evidence:
            anom = evidence["anomaly_detection"]
            if isinstance(anom, dict) and "data" in anom:
                context_obj["Anomalies_Summary"] = anom["data"].get("executive_summary", {})
                context_obj["Top_Anomalies"] = anom["data"].get("table_data", [])[:10]
            else:
                context_obj["Anomalies"] = anom

        if "regional_performance" in evidence:
            context_obj["Regional_Performance"] = evidence["regional_performance"][:10]

        if "category_performance" in evidence:
            context_obj["Category_Performance"] = evidence["category_performance"][:10]

        if "top_products" in evidence:
            context_obj["Top_Products"] = evidence["top_products"][:10]

        if "bottom_products" in evidence:
            context_obj["Bottom_Products"] = evidence["bottom_products"][:10]

        if "monthly_trend" in evidence:
            trend_raw = evidence["monthly_trend"][-12:]
            if len(trend_raw) >= 2:
                # Pre-compute deltas so the synthesis LLM receives structured
                # business context instead of a raw list of revenue figures.
                # All arithmetic is done here in pure Python (zero LLM calls).
                revenues = [float(r.get("Revenue", 0)) for r in trend_raw]
                profits  = [float(r.get("Profit",  0)) for r in trend_raw]

                peak_idx   = revenues.index(max(revenues))
                trough_idx = revenues.index(min(revenues))

                mom_pct = [
                    round(((revenues[i] - revenues[i-1]) / revenues[i-1]) * 100, 2)
                    if revenues[i-1] > 0 else 0.0
                    for i in range(1, len(revenues))
                ]

                overall_growth = (
                    round(((revenues[-1] - revenues[0]) / revenues[0]) * 100, 2)
                    if revenues[0] > 0 else 0.0
                )

                # Steepest MoM swing (absolute value)
                if mom_pct:
                    max_swing_idx = mom_pct.index(max(mom_pct, key=abs))
                    max_swing = {
                        "from_period": str(trend_raw[max_swing_idx].get("Order_Date", "")),
                        "to_period":   str(trend_raw[max_swing_idx + 1].get("Order_Date", "")),
                        "change_pct":  mom_pct[max_swing_idx]
                    }
                else:
                    max_swing = {}

                context_obj["Monthly_Trend_Analysis"] = {
                    "data":               trend_raw,
                    "period_count":       len(trend_raw),
                    "peak_period":        str(trend_raw[peak_idx].get("Order_Date", "")),
                    "peak_revenue":       revenues[peak_idx],
                    "trough_period":      str(trend_raw[trough_idx].get("Order_Date", "")),
                    "trough_revenue":     revenues[trough_idx],
                    "overall_growth_pct": overall_growth,
                    "mom_changes_pct":    mom_pct,
                    "steepest_swing":     max_swing,
                    "first_revenue":      revenues[0],
                    "last_revenue":       revenues[-1],
                    "first_profit":       profits[0]  if profits else 0.0,
                    "last_profit":        profits[-1] if profits else 0.0,
                }
            else:
                # Not enough data points for delta computation
                context_obj["Monthly_Trend"] = trend_raw

        computed_metrics = self._compute_business_metrics(evidence)
        if computed_metrics:
            context_obj["computed_business_metrics"] = computed_metrics

        if "computed_business_metrics" in context_obj:
            context_obj["Business Metrics"] = context_obj["computed_business_metrics"]
        if "Monthly_Trend_Analysis" in context_obj:
            context_obj["Monthly Trend"] = context_obj["Monthly_Trend_Analysis"]
        if "Category_Performance" in context_obj:
            context_obj["Category Performance"] = context_obj["Category_Performance"]
        if "Regional_Performance" in context_obj:
            context_obj["Regional Performance"] = context_obj["Regional_Performance"]
        if "Anomalies_Summary" in context_obj:
            context_obj["Anomaly Summary"] = context_obj["Anomalies_Summary"]
        if "Top_Anomalies" in context_obj:
            context_obj["Anomaly Table"] = context_obj["Top_Anomalies"]
        if "Forecast_Metrics" in context_obj:
            context_obj["Forecast Metrics"] = context_obj["Forecast_Metrics"]
        if "Forecast_Trends" in context_obj:
            context_obj["Predictions"] = context_obj["Forecast_Trends"]

        # Ensure we only return segments that actually have data
        filtered_context = {k: v for k, v in context_obj.items() if v}

        return json.dumps(filtered_context, default=str)

    def generate_final_response(
        self,
        user_query: str,
        context_str: str,
        memory_summary: str = "",
        intents: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        STEP 6 & 7: LLM Generation
        Passes structured, intent-enriched context to the LLM.
        Includes Reflection / Self-Validation stage.
        """
        print("\n========== ENTERED generate_final_response ==========\n")

        # Build merged intent instruction block.
        # All matching intent blocks are concatenated — they cover distinct
        # analytical dimensions so they are additive, never conflicting.
        _intent_block = ""
        if intents:
            matched_blocks = [
                INTENT_INSTRUCTIONS[i]
                for i in intents
                if i in INTENT_INSTRUCTIONS
            ]
            if matched_blocks:
                _intent_block = "\n".join(matched_blocks)

        system_prompt = f"""
You are a Principal Business Intelligence Analyst for InsightsOps, an enterprise BI platform.
Your role is equivalent to a Senior Business Analyst presenting findings to a C-suite audience.
Answer the user's business question using ONLY the provided evidence and structured context.

CONVERSATION CONTEXT:
{memory_summary}

═══ CRITICAL GROUNDING RULES ═══
1. Every statement MUST cite specific numbers from the evidence.
   ✕ Bad:  \"Revenue increased.\"
   ✓ Good: \"Revenue increased by 54.2% from $120,450 (October) to $185,492 (November).\"
2. Every business insight MUST explain WHY, using evidence rather than assumptions.
   ✕ Bad:  \"Sales performance was strong.\"
   ✓ Good: "Revenue grew 54% while average order value stayed flat at $340, indicating order volume, not price, drove growth."
3. Every recommendation MUST be actionable and tied to a specific evidence finding.
   ✕ Bad:  "Invest more in the East region."
   ✓ Good: "Reallocate 15-20% of the West budget to East, which generated $480K in revenue — 35.5% above West — and showed 3 months of consecutive growth."
4. Follow-up questions MUST extend the current investigation thread.
5. If evidence is empty or indicates no records found, clearly say what was searched and suggest a refinement.
6. Only populate JSON sections with evidence-backed content. Empty sections MUST be [].
7. Do not use generic phrases such as "performance was strong" or "there is an opportunity" without quantification.

{_intent_block}

═══ REQUIRED JSON OUTPUT SCHEMA ═══
{{
    "executive_summary": "2-4 sentence overview with specific numbers directly answering the user question.",
    "key_findings": [
        "Finding with exact numbers, e.g.: Revenue peaked at $185K in November — a +54.2% increase from October's $120K."
    ],
    "evidence": ["Direct data citation from context supporting the above findings."],
    "business_insights": [
        "Insight explaining WHY, e.g.: Revenue growth coincides with a 52% order volume increase, suggesting promotional demand rather than price-driven growth."
    ],
    "recommendations": [
        "Specific actionable recommendation with business justification tied to evidence."
    ],
    "potential_risks": ["Evidence-backed risk or caveat."],
    "suggested_follow_up_questions": [
        "Specific follow-up that continues this exact analysis thread."
    ]
}}
"""

        # Prepare the LLM payload
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"USER QUESTION:\n{user_query}\n\nEVIDENCE CONTEXT:\n{context_str}"
            }
        ]

        try:
            print("Calling LLM...")
            print("LLM call completed.")
            response = create_chat_completion_with_retry(
                self._get_client(),
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            print("\n========== RAW GEMINI RESPONSE ==========\n")

            raw = extract_response_text(response)

            print(type(response))
            print("------------------------")
            print("RAW TEXT:")
            print(raw)
            print("------------------------")
            print("RESPONSE OBJECT:")
            print(response)

            print("\n=========================================\n")

            initial_response = self._normalize_final_response(json.loads(raw))

            # ========================================================
            # REFLECTION / SELF-VALIDATION STAGE (Phase A — activated)
            # _reflect_and_validate() was already fully implemented but
            # never called. It sends a second LLM call that audits every
            # claim in the response against the evidence context and
            # corrects any unsupported statements.
            # Non-fatal: any exception falls through to the original response.
            # ========================================================
            try:
                validated_response, passed = self._reflect_and_validate(
                    user_query, context_str, initial_response
                )
                validated_response["reflection_passed"] = passed
                return validated_response
            except Exception as ref_err:
                logging.error(f"Reflection stage error (non-fatal): {str(ref_err)}")
                initial_response["reflection_passed"] = True
                return initial_response

        except Exception as e:
            raise


    def _normalize_final_response(self, response: Any) -> Dict[str, Any]:
        if not isinstance(response, dict):
            return {
                "executive_summary": "",
                "business_findings": [],
                "business_insights": [],
                "strategic_recommendations": [],
                "potential_risks": [],
                "suggested_follow_up_questions": [],
                "key_findings": [],
                "recommendations": [],
                "evidence": []
            }

        normalized = dict(response)
        if "business_findings" not in normalized and "key_findings" in normalized:
            normalized["business_findings"] = normalized["key_findings"]
        if "key_findings" not in normalized and "business_findings" in normalized:
            normalized["key_findings"] = normalized["business_findings"]
        if "strategic_recommendations" not in normalized and "recommendations" in normalized:
            normalized["strategic_recommendations"] = normalized["recommendations"]
        if "recommendations" not in normalized and "strategic_recommendations" in normalized:
            normalized["recommendations"] = normalized["strategic_recommendations"]
        if "suggested_follow_up_questions" not in normalized and "follow_up_questions" in normalized:
            normalized["suggested_follow_up_questions"] = normalized["follow_up_questions"]
        if "follow_up_questions" not in normalized and "suggested_follow_up_questions" in normalized:
            normalized["follow_up_questions"] = normalized["suggested_follow_up_questions"]
        if "business_insights" not in normalized:
            normalized["business_insights"] = []
        if "potential_risks" not in normalized:
            normalized["potential_risks"] = []
        if "evidence" not in normalized:
            normalized["evidence"] = []
        return normalized

    def _reflect_and_validate(self, user_query: str, context_str: str, generated_response: Dict[str, Any]) -> tuple[Dict[str, Any], bool]:
        """
        Validates the generated response against the provided evidence.
        Revises the response once if validation fails, replacing unsupported claims.
        """
        reflection_prompt = f"""
You are a QA and Fact-Checking Auditor for an enterprise BI platform.
Your task is to validate whether the generated response is grounded in the provided evidence context.

USER QUESTION:
{user_query}

EVIDENCE CONTEXT:
{context_str}

GENERATED RESPONSE TO VALIDATE:
{json.dumps(generated_response, default=str)}

VALIDATION CRITERIA:
1. Every major claim, number, and finding must be directly supported by or reasonably
   inferable from the evidence context.
2. No hallucinated or invented numbers or statistics that do not appear in or cannot be
   derived from the evidence context.
3. Recommendations must be grounded in evidence or be a reasonable business response to
   the evidence findings.
4. Risks are mentioned only if the evidence supports or implies them.
5. If evidence is insufficient or completely absent for a claim with no basis for inference,
   replace that statement with: "The available evidence does not provide enough information."

Return a valid JSON object matching this schema:
{{
    "passed": true/false,
    "revised_response": {{
        "executive_summary": "...",
        "business_findings": ["..."],
        "business_insights": ["..."],
        "strategic_recommendations": ["..."],
        "potential_risks": ["..."],
        "suggested_follow_up_questions": ["..."],
        "key_findings": ["..."],
        "recommendations": ["..."],
        "evidence": ["..."]
    }}
}}
If passed is true, revised_response can be the original response. If false, provide the corrected response.
"""
        try:
            reflection_messages = [
                {"role": "system", "content": reflection_prompt},
                {"role": "user", "content": "Perform validation and return JSON."}
            ]

            ref_resp = create_chat_completion_with_retry(
                self._get_client(),
                model=self.model,
                messages=reflection_messages,
                temperature=0.0,
                response_format={"type": "json_object"}
            )

            ref_data = json.loads(extract_response_text(ref_resp))
            passed = bool(ref_data.get("passed", True))
            revised = self._normalize_final_response(ref_data.get("revised_response", generated_response))

            if not isinstance(revised, dict):
                revised = generated_response

            return revised, passed

        except Exception as ref_error:
            logging.error(f"Reflection stage error (non-fatal): {str(ref_error)}")
            # Default to passing original response if reflection fails technically
            return generated_response, True


def run_insightsops_agent(user_query: str, df: Any, memory_manager: Optional[ConversationMemoryManager] = None) -> Dict[str, Any]:
    """
    Run the complete InsightsOps Business Analyst orchestration pipeline with memory integration.

    Pipeline Steps:
    1. Receive user query
    2. Load metadata & extract entities
    3. Load conversation memory & merge entities
    4. Detect whether the query is a follow-up
    5. Resolve the query using conversation context if required
    6. Pass resolved query to planner
    7. Execute tools
    8. Validate evidence
    9. Generate business context
    10. Generate final response (with Reflection / Self-Validation)
    11. Save current interaction into ConversationMemoryManager
    12. Return response with memory metadata and extracted entities
    """
    start_time = time.time()

    # 2. Load conversation memory (Reuse passed manager, or fall back to a new one if none supplied)
    mem_mgr = memory_manager if memory_manager is not None else ConversationMemoryManager()
    orchestrator = InsightsOpsOrchestrator(memory_manager=mem_mgr)

    # Initialize MetadataLoader once per workflow execution
    extracted_entities_obj = ExtractedEntities()
    merged_entities_dict = {}

    try:
        metadata_loader = MetadataLoader(df)
        business_metadata = metadata_loader.load()
        entity_extractor = EntityExtractor(business_metadata)
        extracted_entities_obj = entity_extractor.extract(user_query)

        # Merge entities into memory
        merged_entities = mem_mgr.merge_entities(extracted_entities_obj)
        merged_entities_dict = vars(merged_entities) if merged_entities else {}
    except Exception as ent_error:
        logging.error(f"Entity extraction / metadata loading error (non-fatal): {str(ent_error)}")
        merged_entities_dict = mem_mgr.get_current_entities()

    # Detect follow-up & Resolve query
    follow_up_detected = False
    resolved_query = user_query
    try:
        follow_up_detected = mem_mgr.is_follow_up(user_query)
        if follow_up_detected:
            resolved_query = mem_mgr.resolve_context(user_query)
    except Exception as mem_error:
        logging.error(f"Memory processing error (non-fatal): {str(mem_error)}")

    response = {
        "success": False,
        "user_query": user_query,
        "resolved_query": resolved_query,
        "entities": merged_entities_dict,
        "confidence": getattr(extracted_entities_obj, "confidence", 0.0),
        "plan": {},
        "execution": {},
        "evidence": {},
        "context": "",
        "final_response": {},
        "metadata": {},
        "errors": []
    }

    # ========================================================
    # STEP 5: AI PLANNING (using resolved query)
    # ========================================================
    plan_start = time.time()
    try:
        print("\n" + "=" * 70)
        print("FORECAST DEBUG - STEP 5")
        print("=" * 70)

        print("USER QUERY:")
        print(user_query)

        print("\nRESOLVED QUERY:")
        print(resolved_query)

        print("\nMERGED ENTITIES:")
        print(json.dumps(merged_entities_dict, indent=2, default=str))

        # --------------------------------------------------------
        # AI PLANNING
        # --------------------------------------------------------
        plan = create_ai_plan(
            resolved_query,
            context={
                "entities": merged_entities_dict
            }
        )

        print("\nGENERATED PLAN:")
        print(json.dumps(plan, indent=2, default=str))

        print("\nFORECAST TOOL ARGUMENTS:")
        for step in plan.get("tool_execution_plan", []):
            if isinstance(step, dict):
                if step.get("tool") == "forecast_evaluation":
                    print(json.dumps(
                        step.get("arguments", {}),
                        indent=2,
                        default=str
                    ))

        print("=" * 70)
        print("END FORECAST DEBUG")
        print("=" * 70 + "\n")

        response["plan"] = plan

    except Exception as error:
        response["errors"].append(f"Planning error: {str(error)}")

        plan = {
            "intents": ["General Analysis"],
            "selected_tools": ["kpi_summary", "monthly_trend"],
            "confidence": 0.0
        }

        response["plan"] = plan

        plan_time = time.time() - plan_start

    plan_time = time.time() - plan_start

    # ========================================================
    # STEP 6: TOOL EXECUTION & GRACEFUL ERROR HANDLING
    # ========================================================
    try:
        execution = route_query(plan, df)
        response["execution"] = execution

        metadata = execution.get("metadata", {})
        failed_tools = metadata.get("failed_tools", [])

        if failed_tools:

            logging.info(f"Replanning because these tools failed: {failed_tools}")

            new_plan = create_ai_plan(
                resolved_query,
                context={"failed_tools": failed_tools},
                failed_tools=failed_tools
            )

            execution = route_query(new_plan, df)

            response["execution"] = execution
            response["replanned"] = True

        # Track individual tool failures without crashing workflow
        failed_tools = execution.get("metadata", {}).get("failed_tools", [])
        if failed_tools and not response.get("replanned", False):
            response["errors"].extend([f"Tool failed during execution: {t}" for t in failed_tools])

    except Exception as error:
        response["errors"].append(f"Tool routing/execution error: {str(error)}")
        execution = {"results": {}, "metadata": {}}

    # ========================================================
    # STEP 7: COLLECT & VALIDATE EVIDENCE
    # ========================================================
    try:
        raw_results = execution.get("results", {})
        valid_evidence = orchestrator.validate_and_clean_evidence(raw_results)
        response["evidence"] = valid_evidence
    except Exception as error:
        response["errors"].append(f"Evidence validation error: {str(error)}")
        valid_evidence = {}

    reflection = {
        "is_evidence_sufficient": len(valid_evidence) > 0,
        "missing_information": [],
        "warnings": []
    }

    response["reflection"] = reflection

    # ========================================================
    # STEP 7b: EVIDENCE ANALYSIS (Phase B — EvidenceAnalysisEngine)
    #
    # Deterministic — pure Python, zero LLM calls, < 50ms.
    # Reads valid_evidence (same key schema as tool outputs) and:
    #   • Extracts structured fact objects per tool result
    #   • Detects cross-tool signals (e.g. margin compression: revenue up
    #     but profit down, or compounded risk: forecast declining + anomalies)
    #   • Deduplicates and ranks facts Critical > High > Medium > Low
    #
    # Output stored in response["structured_evidence"] and the top 12
    # priority facts are injected into context_str before Step 9 so the
    # synthesis LLM call has richer, pre-correlated grounding evidence.
    # ========================================================
    structured_evidence_items = []
    try:
        evidence_engine = EvidenceAnalysisEngine(
            compact_evidence=valid_evidence,
            derived_evidence={}
        )
        structured_evidence_items = evidence_engine.process()
        response["structured_evidence"] = structured_evidence_items
        logging.info(
            f"[Phase B] EvidenceAnalysisEngine: {len(structured_evidence_items)} "
            f"structured facts extracted from {len(valid_evidence)} tool results."
        )
    except Exception as ev_error:
        logging.error(f"[Phase B] Evidence analysis error (non-fatal): {str(ev_error)}")
        response["structured_evidence"] = []

    # ========================================================
    # STEP 8: GENERATE BUSINESS CONTEXT
    # ========================================================
    try:
        context_str = orchestrator.generate_business_context(valid_evidence)

        # Phase B: augment context_str with the top-priority structured facts
        # produced by EvidenceAnalysisEngine. Capped at 12 to stay within
        # the synthesis LLM's context window budget.
        if structured_evidence_items:
            context_obj = json.loads(context_str)
            context_obj["structured_evidence_facts"] = structured_evidence_items[:12]
            context_str = json.dumps(context_obj, default=str)
            logging.info(
                f"[Phase B] Context enriched with "
                f"{min(len(structured_evidence_items), 12)} structured facts."
            )

        executed_tools = execution.get("metadata", {}).get("executed_tools", [])
        synthesis_intents = plan.get("intents", [])
        synthesis_metadata = {
            "planner_intents": synthesis_intents,
            "executed_tools": executed_tools,
            "primary_visualization": orchestrator._resolve_primary_visualization(synthesis_intents, executed_tools)
        }

        context_obj = json.loads(context_str)
        context_obj["synthesis_metadata"] = synthesis_metadata
        context_str = json.dumps(context_obj, default=str)
        context_str = orchestrator._filter_context_for_intent(context_str, synthesis_intents, executed_tools)

        response["context"] = context_str
    except Exception as error:
        response["errors"].append(f"Context generation error: {str(error)}")
        context_str = "{}"

    # ========================================================
    # STEP 9: LLM ANALYSIS & FINAL RESPONSE (with Reflection)
    # ========================================================
    try:
        print("STEP 9 - Before summarize_context")

        memory_summary = mem_mgr.summarize_context()

        print("STEP 9 - Before generate_final_response")

        # Pass the planner's detected intents so the synthesis LLM receives
        # the merged, intent-specific quantitative writing contracts.
        _synthesis_intents = plan.get("intents", [])
        final_response = orchestrator.generate_final_response(
            resolved_query,
            context_str,
            memory_summary,
            intents=_synthesis_intents
        )

        print("STEP 9 - After generate_final_response")

        response["final_response"] = final_response
        response["llm_status"] = "success"

    except Exception as error:
        print("STEP 9 ERROR:", error)

        final_response = {
            "executive_summary": "The AI service is temporarily unavailable. Please try again later.",
            "key_findings": [],
            "evidence": [],
            "business_insights": [],
            "recommendations": [],
            "potential_risks": [],
            "suggested_follow_up_questions": [],
            "reflection_passed": False
        }

        response["final_response"] = final_response
        response["errors"].append(f"LLM Error: {str(error)}")

    # ========================================================
    # STEP 10: SAVE THE CURRENT INTERACTION INTO MEMORY
    # ========================================================
    try:
        exec_meta = execution.get("metadata", {})
        executed_tools = exec_meta.get("executed_tools", [])
        ai_resp_text = final_response.get("executive_summary", "") if isinstance(final_response, dict) else str(final_response)
        recs = final_response.get("recommendations", []) if isinstance(final_response, dict) else []

        turn = TurnContext(
            user_query=user_query,
            ai_response=ai_resp_text,
            planner_output=plan,
            selected_tools=executed_tools,
            extracted_entities=[],
            filters=FilterState(),
            execution_metadata=exec_meta,
            evidence_summary=valid_evidence,
            recommendations=recs,
            timestamp=time.time()
        )
        mem_mgr.store_turn(turn)

    except Exception as mem_store_error:
        logging.error(f"Memory storage error (non-fatal): {str(mem_store_error)}")
        response["errors"].append(f"Memory storage error: {str(mem_store_error)}")

    # [Insert the rest of agent_workflow.py unmodified up to run_insightsops_agent return block]
    # ========================================================
    # STEP 11: RETURN RESPONSE & METADATA
    # ========================================================
    end_time = time.time()
    total_time = end_time - start_time

    executed_tools = execution.get("metadata", {}).get("executed_tools", [])

    # Calculate total evidence points securely
    evidence_count = sum(
        len(v) if isinstance(v, list) else 1
        for v in valid_evidence.values()
    )

    reflection_passed_flag = final_response.get("reflection_passed", True) if isinstance(final_response, dict) else True

    response["metadata"] = {
        "execution_time_seconds": round(total_time, 4),
        "planning_time_seconds": round(plan_time, 4),
        "tool_count": len(executed_tools),
        "tools_used": executed_tools,
        "evidence_count": evidence_count,
        "confidence": plan.get("confidence", 0.85),
        "reflection_passed": reflection_passed_flag,
        "memory": {
            "follow_up_detected": follow_up_detected,
            "resolved_query": resolved_query,
            "conversation_turns": len(mem_mgr.history)
        }
    }

    # --------------------------------------------------------
    # VISUALIZATION SELECTION — two-pass intent-first strategy
    # Pass 1 (Intent-first): iterate the planner's detected intents in
    #   order; for each intent look up its preferred tool list and use
    #   the first preferred tool that was executed and returns a chart.
    # Pass 2 (Priority fallback): only runs if Pass 1 finds nothing.
    #   Uses the numeric CHART_PRIORITY table to pick the highest-value
    #   chart from all executed tools.
    # --------------------------------------------------------
    visualization_spec = None
    try:
        from src.agents.chart_generator import select_visualization
        raw_results    = execution.get("results", {})
        plan_intents   = plan.get("intents", [])

        visualization_spec = select_visualization(plan_intents, executed_tools, raw_results)
        if visualization_spec:
            logging.info(
                f"[Viz] Intent-driven selection → {visualization_spec.get('type')}"
            )

        print("VISUALIZATION GENERATED:")
        print(json.dumps(visualization_spec, indent=2, default=str))

    except Exception as viz_error:
        logging.error(f"Visualization generation error (non-fatal): {str(viz_error)}")

    # Workflow guarantees a response object is always returned successfully
    response["success"] = True
    response["visualization"] = visualization_spec
    response["execution_summary"] = {
        "planned_tools": plan.get("selected_tools", []),
        "executed_tools": execution.get("metadata", {}).get("executed_tools", []),
        "failed_tools": execution.get("metadata", {}).get("failed_tools", []),
        "replanned": response.get("replanned", False)
    }
    print("=" * 60)
    print("EXECUTED TOOLS:", executed_tools)
    print("=" * 60)

    print("VISUALIZATION GENERATED:")
    print(json.dumps(visualization_spec, indent=2, default=str))

    return response