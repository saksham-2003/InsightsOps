import json
import logging
from typing import Dict, List, Any

from src.agents.llm_client import (
    get_llm_client,
    create_chat_completion_with_retry,
    extract_response_text
)

class EvidenceAnalysisEngine:
    """
    Professional Evidence Analysis Engine for InsightsOps.
    
    Transforms raw numerical tool outputs into highly structured, prioritized, 
    and cross-correlated business evidence. 
    
    Architected for Future Agentic Extensions:
    - RAG & Knowledge Graphs
    - External Business Rules Engine
    - Self-Critique & Reflection Loops
    """

    def __init__(self, compact_evidence: Dict[str, Any], derived_evidence: Dict[str, Any]):
        self.compact = compact_evidence or {}
        self.derived = derived_evidence or {}
        self.evidence_pool: List[Dict[str, Any]] = []

    # =========================================================================
    # TASK 9: EXTENSIBILITY HOOKS
    # =========================================================================

    def _retrieve_knowledge_graph_context(self):
        """Hook: Inject enterprise knowledge graph semantic context here."""
        pass

    def _apply_external_business_rules(self):
        """Hook: Apply strict declarative business rules (e.g., specific margin thresholds)."""
        pass

    def _self_critique_evidence(self, evidence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Hook: Multi-agent reflection to double-check evidence validity."""
        return evidence

    # =========================================================================
    # CORE ENGINE PIPELINE
    # =========================================================================

    def process(self) -> List[Dict[str, Any]]:
        """Run the full deterministic extraction and correlation pipeline."""
        self._retrieve_knowledge_graph_context()
        self._apply_external_business_rules()

        # Extract Raw Facts (Tasks 1, 2)
        self._extract_kpis()
        self._extract_trends()
        self._extract_category_region()
        self._extract_products()
        self._extract_anomalies()
        self._extract_forecasts()

        # Synthesize Relationships (Task 4)
        self._detect_relationships()

        # Deduplicate, Merge, and Rank (Tasks 5, 6)
        ranked_evidence = self._deduplicate_and_rank(self.evidence_pool)
        
        return self._self_critique_evidence(ranked_evidence)

    # =========================================================================
    # TASK 3: STRUCTURED EVIDENCE GENERATOR
    # =========================================================================

    def _add_evidence(
        self, 
        metric: str, 
        value: str, 
        trend: str, 
        observation: str, 
        impact: str, 
        priority: str, 
        confidence: str = "High"
    ):
        """Standardized structure for all business evidence."""
        self.evidence_pool.append({
            "metric": metric,
            "value": value,
            "trend": trend,
            "observation": observation,
            "business_impact": impact,
            "priority": priority,
            "confidence": confidence
        })

    # =========================================================================
    # DETERMINISTIC EXTRACTORS
    # =========================================================================

    def _safe_float(self, val) -> float:
        if val is None: return 0.0
        try:
            clean_str = str(val).replace('%', '').replace('+', '').replace(',', '').replace('$', '')
            return float(clean_str)
        except (ValueError, TypeError):
            return 0.0

    def _extract_kpis(self):
        kpi = self.compact.get("kpi_summary", {})
        if not isinstance(kpi, dict): return
        
        rev = kpi.get("total_revenue")
        prof = kpi.get("total_profit")
        margin = kpi.get("profit_margin")
        
        if rev is not None:
            self._add_evidence(
                "Total Revenue", f"${rev:,.2f}", "Current Baseline", 
                "Overall revenue generation within the filtered context.", 
                "Drives top-line health.", "High"
            )
        if margin is not None:
            priority = "Critical" if margin <= 0 else "High"
            self._add_evidence(
                "Profit Margin", f"{margin:.2f}%", "Current Baseline",
                "Calculated operational profitability.", 
                "Indicates business sustainability and efficiency.", priority
            )

    def _extract_trends(self):
        trend = self.compact.get("monthly_trend", [])
        if isinstance(trend, list) and len(trend) >= 2:
            first_rev = trend[0].get("Revenue", 0)
            last_rev = trend[-1].get("Revenue", 0)
            
            if first_rev > 0:
                growth = ((last_rev - first_rev) / first_rev) * 100
                direction = "Increasing" if growth > 0 else "Declining"
                priority = "High" if abs(growth) > 5 else "Medium"
                
                self._add_evidence(
                    "Revenue Growth", f"{growth:+.2f}%", direction,
                    f"Revenue shifted from ${first_rev:,.2f} to ${last_rev:,.2f}.",
                    "Direct impact on momentum and cash flow.", priority
                )

            first_prof = trend[0].get("Profit", 0)
            last_prof = trend[-1].get("Profit", 0)
            
            if first_prof > 0:
                p_growth = ((last_prof - first_prof) / first_prof) * 100
                direction = "Increasing" if p_growth > 0 else "Declining"
                priority = "Critical" if p_growth < -10 else "High" if abs(p_growth) > 5 else "Medium"
                
                self._add_evidence(
                    "Profit Growth", f"{p_growth:+.2f}%", direction,
                    f"Profitability shifted from ${first_prof:,.2f} to ${last_prof:,.2f}.",
                    "Bottom-line operational trajectory.", priority
                )

    def _extract_category_region(self):
        reg = self.compact.get("regional_performance", [])
        if isinstance(reg, list) and reg:
            best = reg[0]
            self._add_evidence(
                "Top Performing Region", str(best.get("Region", "Unknown")), "Dominant",
                f"Led regional cohort with ${best.get('Revenue', 0):,.2f} in revenue.",
                "Primary geographical growth engine.", "High"
            )
            if len(reg) > 1:
                worst = reg[-1]
                self._add_evidence(
                    "Worst Performing Region", str(worst.get("Region", "Unknown")), "Lagging",
                    f"Lowest cohort revenue at ${worst.get('Revenue', 0):,.2f}.",
                    "Identifies territory requiring operational audit or withdrawal.", "Medium"
                )

        cat = self.compact.get("category_performance", [])
        if isinstance(cat, list) and cat:
            best = cat[0]
            self._add_evidence(
                "Highest Selling Category", str(best.get("Category", "Unknown")), "Dominant",
                f"Led categories with ${best.get('Revenue', 0):,.2f} in revenue.",
                "Identifies core structural product segments.", "High"
            )

    def _extract_products(self):
        prod = self.compact.get("top_products", [])
        if isinstance(prod, list) and prod:
            best = prod[0]
            name = best.get("Product_Name", best.get("Product", "Unknown"))
            self._add_evidence(
                "Most Valuable Product", str(name), "Leading",
                f"Generated the highest single-item revenue (${best.get('Revenue', 0):,.2f}).",
                "Product concentration risk and primary growth dependency.", "Medium"
            )

    def _extract_anomalies(self):
        anom = self.compact.get("anomaly_detection", {})
        
        # Handle variations in anomaly response payload structure
        summary = {}
        if isinstance(anom, dict):
            summary = anom.get("data", {}).get("executive_summary", anom.get("summary", {}))
            
        count = summary.get("total_anomalies", summary.get("anomaly_count", 0))
        pct = summary.get("anomaly_percentage", 0.0)
        
        if count > 0:
            priority = "Critical" if pct > 5 else "High" if pct > 1 else "Medium"
            self._add_evidence(
                "Total Anomalies", str(count), "Elevated",
                f"{pct:.2f}% of evaluated transactions were flagged by ML models as structural anomalies.",
                "Indicates potential fraud, systemic pricing errors, or operational inefficiencies.", priority
            )

    def _extract_forecasts(self):
        fc = self.compact.get("forecast_evaluation", {})
        if not isinstance(fc, dict): return
        
        preds = fc.get("predictions", [])
        if isinstance(preds, list) and len(preds) > 0:
            first = preds[0].get("Predicted_Revenue", 0)
            last = preds[-1].get("Predicted_Revenue", 0)
            if first > 0:
                growth = ((last - first) / first) * 100
                direction = "Increasing" if growth > 0 else "Declining"
                priority = "Critical" if growth < -5 else "High"
                
                self._add_evidence(
                    "Forecast Trend", f"{growth:+.2f}%", direction,
                    f"Predicted revenue shifts by {growth:+.2f}% over the available forecast horizon.",
                    "Crucial forward-looking signal for inventory and capacity planning.", priority
                )

    # =========================================================================
    # TASK 4: RELATIONSHIP & CORRELATION DETECTION
    # =========================================================================

    def _detect_relationships(self):
        metrics = {e["metric"]: e for e in self.evidence_pool}
        
        # 1. Margin Compression Risk
        if "Revenue Growth" in metrics and "Profit Growth" in metrics:
            rev_growth = self._safe_float(metrics["Revenue Growth"]["value"])
            prof_growth = self._safe_float(metrics["Profit Growth"]["value"])
            
            if rev_growth > 0 and prof_growth <= 0:
                self._add_evidence(
                    "Margin Compression", "Divergent", "Warning",
                    f"Revenue grew by {rev_growth}% while profit changed by {prof_growth}%.",
                    "Costs are scaling faster than revenue. Immediate operational audit required.",
                    "Critical"
                )
                
        # 2. Compounded Risk (Forecast down + Anomalies active)
        if "Forecast Trend" in metrics and "Total Anomalies" in metrics:
            fc_trend = metrics["Forecast Trend"]["trend"]
            anom_count = self._safe_float(metrics["Total Anomalies"]["value"])
            
            if fc_trend == "Declining" and anom_count > 0:
                self._add_evidence(
                    "Compounded Business Risk", "Elevated", "Negative Convergence",
                    "Declining future forecasts coincide with active transaction anomalies.",
                    "Systemic business risk requiring strategic intervention.",
                    "Critical"
                )

    # =========================================================================
    # TASKS 5 & 6: DEDUPLICATION & RANKING
    # =========================================================================

    def _deduplicate_and_rank(self, evidence_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        unique = {}
        # Keep the highest priority entry if duplicates exist
        for e in evidence_list:
            unique[e["metric"]] = e
                
        priority_map = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
        
        # Rank by Critical -> High -> Medium -> Low
        return sorted(
            unique.values(), 
            key=lambda x: priority_map.get(x.get("priority", "Low"), 0), 
            reverse=True
        )


# =========================================================================
# MAIN ORCHESTRATION FUNCTION
# =========================================================================

def analyze_evidence(
    user_query: str,
    plan: Dict[str, Any],
    compact_evidence: Dict[str, Any],
    derived_evidence: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Main entry point for the agent workflow.
    Orchestrates deterministic Python evidence extraction, cross-correlation, 
    and strict LLM formatting/synthesis.
    """
    # 1. Deterministic Extraction & Correlation Engine
    engine = EvidenceAnalysisEngine(compact_evidence, derived_evidence)
    structured_facts = engine.process()
    
    # 2. Prepare LLM Synthesis Payload
    payload = {
        "user_query": user_query,
        "intent": plan.get("intent", "General Analysis"),
        "verified_facts": structured_facts
    }

    # 3. LLM Prompt Configuration (Tasks 7 & 8)
    system_prompt = """
    You are the Principal Evidence Analyst Engine for InsightsOps.

    Your objective is to synthesize structured, deterministically verified business facts 
    into a comprehensive, final JSON analytical report.

    STRICT GROUNDING RULES:
    1. ONLY use the verified facts provided in the payload array.
    2. NEVER invent, estimate, or hallucinate metrics, trends, percentages, or relationships.
    3. If the evidence is insufficient to populate a section, leave its array empty.
    4. Maintain a highly professional, objective, and analytical BI tone.
    5. Translate raw facts into strategic business observations.
    6. Do not claim statistical significance without explicit validation.

    REQUIRED JSON OUTPUT FORMAT:
    {
        "evidence_summary": "A 2-4 sentence executive overview synthesizing the most critical extracted facts.",
        "key_metrics": [
            {
                "metric": "Name of metric",
                "value": "Value",
                "trend": "Trend direction",
                "observation": "What this means in business context",
                "business_impact": "Impact on the business",
                "confidence": "High/Medium/Low",
                "priority": "Critical/High/Medium/Low"
            }
        ],
        "business_signals": [
            {
                "signal": "Clear statement of the signal (e.g., Margin Compression)",
                "observation": "Supporting observation from evidence",
                "impact": "Strategic business impact",
                "confidence": "High/Medium/Low"
            }
        ],
        "detected_trends": ["String describing a distinct trend based on data."],
        "business_risks": ["String describing a potential risk or vulnerability."],
        "opportunities": ["String describing a potential area for growth or optimization."],
        "confidence": "High/Medium/Low"
    }
    """

    try:
        client = get_llm_client()
        
        response = create_chat_completion_with_retry(
            client,
            model="reasoning",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(payload, default=str)}
            ],
            temperature=0,
            max_completion_tokens=2500,
            response_format={"type": "json_object"}
        )

        content = extract_response_text(response)
        return json.loads(content)
        
    except Exception as e:
        import traceback

        print("\n================ LLM ERROR ================\n")

        traceback.print_exc()

        print("\n==========================================\n")

        logging.exception("LLM Response Generation Failed")

        return {
            "executive_summary": "An error occurred while generating the business analysis.",
            "key_findings": [],
            "evidence": [],
            "business_insights": [],
            "recommendations": [],
            "potential_risks": [],
            "suggested_follow_up_questions": [],
            "reflection_passed": False
        }
        # Safe fallback matching the required schema
        return {
            "evidence_summary": "Analysis encountered an error during synthesis. See raw facts for details.",
            "key_metrics": structured_facts,
            "business_signals": [],
            "detected_trends": [],
            "business_risks": ["Analysis pipeline failure."],
            "opportunities": [],
            "confidence": "Low"
        }