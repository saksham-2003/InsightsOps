import json
import logging
from typing import List, Dict, Any, Optional

from src.agents.llm_client import get_llm_client, create_chat_completion_with_retry, extract_response_text

# =====================================================================
# CONSTANTS & CONFIGURATION
# =====================================================================

AVAILABLE_TOOLS = [
    "kpi_summary",
    "monthly_trend",
    "category_performance",
    "regional_performance",
    "top_products",
    "bottom_products",
    "anomaly_detection",
    "forecast_evaluation"
]

SUPPORTED_INTENTS = [
    "Revenue",
    "Profit",
    "Forecast",
    "Anomaly",
    "Trend",
    "Comparison",
    "Region",
    "Category",
    "Product",
    "Executive Summary",
    "Recommendation",
    "Risk",
    "General Business Question",
    "east",
    "west",
    "north",
    "south",
    "central",
    "india",
    "usa",
    "country",
    "state",
    "city",
    "electronics",
    "furniture",
    "office supplies",
    "segment",
    "sub category",
    "subcategory",
    "product category"
]

# Tool-specific allowed filters
TOOL_ALLOWED_FILTERS = {
    "regional_performance": {"region", "country", "state", "city", "year", "month", "category"},
    "category_performance": {"category", "sub_category", "year", "month", "region"},
    "top_products": {"category", "sub_category", "region", "year", "month"},
    "bottom_products": {"category", "sub_category", "region", "year", "month"},
    "forecast_evaluation": {"year", "month", "custom_date", "horizon"},
    "monthly_trend": {"year", "month", "region", "category"},
    "anomaly_detection": {"year", "month", "region", "category"},
    "kpi_summary": {
        "region", "country", "state", "city", "category", 
        "sub_category", "product", "customer", "year", "month", 
        "quarter", "metric", "comparison", "aggregation", "date_range"
    }
}

# =====================================================================
# AGENTIC PLANNER CLASS (Designed for Extensibility)
# =====================================================================

class BusinessAnalysisPlanner:
    """
    Intelligent Business Analysis Planner.
    
    Designed to be extensible for future Agentic AI capabilities including:
    - Conversation Memory
    - Reflection & Self-Correction
    - Retry Mechanisms
    - Agent Loops
    """

    def __init__(self):
        self.client = None
        self.model = "planner"
        self.temperature = 0.0

    def _get_client(self):
        if self.client is None:
            self.client = get_llm_client()
        return self.client

    def _normalize_query(self, user_query: str) -> str:
        return " ".join(str(user_query or "").lower().split())

    def _build_deterministic_plan(self, user_query: str, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Create a deterministic, minimal plan before falling back to the LLM.
        Keeps the workflow fast, inexpensive, and aligned with the requested
        routing rules for trend, category, region, forecast, anomaly, and product questions.
        """
        query = self._normalize_query(user_query)
        if not query:
            return None

                # ---------------------------------------------------------
        # FORECAST
        # ---------------------------------------------------------
        if any(term in query for term in [
            "forecast",
            "prediction",
            "predict",
            "future revenue",
            "next month",
            "next quarter"
        ]):
            # Extract date/entity information passed from agent_workflow.py
            entities = {}

            if context:
                entities = (
                    context.get("extracted_entities")
                    or context.get("entities")
                    or {}
                )

            import re
            import calendar
            from datetime import datetime

            # ---------------------------------------------------------
            # Forecast entities
            # ---------------------------------------------------------
            requested_year = entities.get("year")
            requested_month = entities.get("month")

            # ---------------------------------------------------------
            # Forecast arguments
            # ---------------------------------------------------------
            forecast_arguments = {}

            # =========================================================
            # 1. EXPLICIT FORECAST HORIZON
            # =========================================================
            # Examples:
            # "Give me a 15-day revenue forecast"
            # "Give me a 30-day forecast"
            # "Forecast revenue for the next 90 days"
            # =========================================================

            horizon_match = re.search(
                r'\b(?:next\s+)?(\d+)\s*[-]?\s*days?\b',
                query.lower()
            )

            if horizon_match:
                try:
                    horizon_days = int(horizon_match.group(1))

                    if horizon_days > 0:
                        # Maximum horizon supported by planner
                        horizon_days = min(horizon_days, 365)

                        forecast_arguments["horizon"] = horizon_days

                except (ValueError, TypeError):
                    pass

            # =====================================================
            # 2. EXPLICIT "UNTIL" DATE
            # Examples:
            # "forecast until March 15, 2027"
            # "forecast until March 15"
            # =====================================================
            if "until" in query:
                month_names = (
                    "january|february|march|april|may|june|july|"
                    "august|september|october|november|december"
                )

                until_match = re.search(
                    rf'\buntil\s+({month_names})\s+(\d{{1,2}})'
                    rf'(?:st|nd|rd|th)?'
                    rf'(?:,?\s+(\d{{4}}))?\b',
                    query,
                    re.IGNORECASE
                )

                if until_match:
                    try:
                        month_name = until_match.group(1).lower()
                        day = int(until_match.group(2))

                        year = until_match.group(3)

                        # If year is not explicitly provided, use the
                        # extracted year from the entities if available.
                        if year:
                            year_int = int(year)
                        elif requested_year:
                            year_int = int(str(requested_year))
                        else:
                            year_int = None

                        month_numbers = {
                            "january": 1,
                            "february": 2,
                            "march": 3,
                            "april": 4,
                            "may": 5,
                            "june": 6,
                            "july": 7,
                            "august": 8,
                            "september": 9,
                            "october": 10,
                            "november": 11,
                            "december": 12
                        }

                        month_int = month_numbers[month_name]

                        if year_int:
                            target_date = datetime(
                                year_int,
                                month_int,
                                day
                            )

                            forecast_arguments["custom_date"] = (
                                target_date.strftime("%Y-%m-%d")
                            )

                            # Custom date takes priority over horizon.
                            forecast_arguments.pop("horizon", None)

                    except (ValueError, TypeError, KeyError):
                        pass

            # =====================================================
            # 3. SPECIFIC YEAR + MONTH
            # Example:
            # "Forecast revenue for February 2027"
            # =====================================================
            if (
                "custom_date" not in forecast_arguments
                and "horizon" not in forecast_arguments
                and requested_year
                and requested_month
            ):
                try:
                    year_int = int(str(requested_year))

                    month_name = str(requested_month).strip().lower()

                    month_numbers = {
                        "january": 1,
                        "february": 2,
                        "march": 3,
                        "april": 4,
                        "may": 5,
                        "june": 6,
                        "july": 7,
                        "august": 8,
                        "september": 9,
                        "october": 10,
                        "november": 11,
                        "december": 12
                    }

                    month_int = month_numbers.get(month_name)

                    if month_int:
                        last_day = calendar.monthrange(
                            year_int,
                            month_int
                        )[1]

                        forecast_arguments["custom_date"] = (
                            f"{year_int:04d}-{month_int:02d}-{last_day:02d}"
                        )

                except (ValueError, TypeError):
                    pass

            # =====================================================
            # 4. SPECIFIC YEAR ONLY
            # Example:
            # "Forecast revenue for 2027"
            # =====================================================
            elif (
                "custom_date" not in forecast_arguments
                and "horizon" not in forecast_arguments
                and requested_year
            ):
                try:
                    year_int = int(str(requested_year))

                    forecast_arguments["custom_date"] = (
                        f"{year_int:04d}-12-31"
                    )

                except (ValueError, TypeError):
                    pass

            # =====================================================
            # 5. DEFAULT FORECAST
            # If the user doesn't specify a date or horizon,
            # allow forecast_future_revenue() to use its default.
            # =====================================================

            return {
                "intents": ["Forecast"],
                "selected_tools": ["forecast_evaluation"],
                "tool_execution_plan": [
                    {
                        "tool": "forecast_evaluation",
                        "arguments": forecast_arguments
                    }
                ],
                "tool_reasoning": {
                    "forecast_evaluation": (
                        "Forecasting questions are routed to the forecast "
                        "tool. Explicit day horizons are passed as horizon, "
                        "specific endpoint dates are passed as custom_date, "
                        "and calendar-month requests use the last day of "
                        "the requested month."
                    )
                },
                "overall_reasoning": (
                    "Forecast questions are routed directly to the forecast "
                    "tool with the user's requested horizon or future endpoint."
                ),
                "confidence": 0.98,
                "tool_confidence": {
                    "forecast_evaluation": 0.98
                }
            }

        if any(term in query for term in [
            "anomaly",
            "anomalies",
            "outlier",
            "outliers",
            "abnormal",
            "unusual",
            "suspicious",
            "suspicious transaction",
            "suspicious transactions",
            "fraud",
            "fraudulent",
            "risk",
            "risks",
            "exception",
            "exceptions",
            "critical transaction",
            "critical transactions",
            "high risk",
            "high-risk",
            "flagged transaction",
            "flagged transactions",
            "show anomalies",
            "detect anomalies"
        ]):
            return {
                "intents": ["Anomaly"],
                "selected_tools": ["anomaly_detection"],
                "tool_execution_plan": [
                    {
                        "tool": "anomaly_detection",
                        "arguments": {}
                    }
                ],
                "tool_reasoning": {
                    "anomaly_detection": "Anomaly, fraud, suspicious or risk-related questions require anomaly detection."
                },
                "overall_reasoning": "The query is asking to identify unusual or suspicious transactions.",
                "confidence": 0.98,
                "tool_confidence": {
                    "anomaly_detection": 0.98
                }
            }

        if any(term in query for term in [
            "top product",
            "top products",
            "top 10 product",
            "top 10 products",
            "best selling",
            "best seller",
            "best sellers",
            "highest selling",
            "highest revenue product",
            "highest revenue products",
            "highest grossing",
            "highest grossing products",
            "most profitable product",
            "leading product",
            "top items",
            "best items"
        ]):
            return {
                "intents": ["Product"],
                "selected_tools": ["top_products"],
                "tool_execution_plan": [{"tool": "top_products", "arguments": {}}],
                "tool_reasoning": {"top_products": "Top-product questions require ranking the highest-revenue products."},
                "overall_reasoning": "Product questions are routed to the top-products tool.",
                "confidence": 0.96,
                "tool_confidence": {"top_products": 0.96}
            }

        if any(term in query for term in [
            "bottom product",
            "bottom products",
            "bottom 10 product",
            "bottom 10 products",
            "worst product",
            "worst products",
            "lowest selling",
            "least selling",
            "lowest revenue product",
            "lowest revenue products",
            "lowest grossing",
            "least profitable",
            "worst performing",
            "worst performing product",
            "bottom items",
            "least performing"
        ]):
            return {
                "intents": ["Product"],
                "selected_tools": ["bottom_products"],
                "tool_execution_plan": [{"tool": "bottom_products", "arguments": {}}],
                "tool_reasoning": {"bottom_products": "Lowest-product questions require the bottom-products tool."},
                "overall_reasoning": "Product questions are routed to the bottom-products tool.",
                "confidence": 0.96,
                "tool_confidence": {"bottom_products": 0.96}
            }

        if any(term in query for term in [
            "region",
            "regions",
            "regional",
            "territory",
            "territories",
            "geography",
            "geographical",
            "east",
            "west",
            "north",
            "south",
            "central",
            "by region",
            "revenue by region",
            "profit by region",
            "region performance",
            "regional performance",
            "compare region",
            "compare regions",
            "compare east",
            "compare west",
            "best region",
            "worst region",
            "top region",
            "highest region",
            "highest revenue region",
            "which region",
            "performing region"
        ]):
            return {
                "intents": ["Region"],
                "selected_tools": ["regional_performance", "kpi_summary"],
                "tool_execution_plan": [
                    {"tool": "regional_performance", "arguments": {}},
                    {"tool": "kpi_summary", "arguments": {}}
                ],
                "tool_reasoning": {
                    "regional_performance": "Regional questions require a regional performance breakdown.",
                    "kpi_summary": "KPI context is added to anchor the regional comparison in overall business size."
                },
                "overall_reasoning": "Regional questions are answered with regional performance plus KPI context.",
                "confidence": 0.97,
                "tool_confidence": {"regional_performance": 0.97, "kpi_summary": 0.9}
            }

        if any(term in query for term in [
            "category",
            "categories",
            "product category",
            "product categories",
            "by category",
            "across categories",
            "revenue by category",
            "profit by category",
            "category performance",
            "category comparison",
            "compare category",
            "compare categories",
            "highest category",
            "best category",
            "top category",
            "leading category",
            "highest revenue category",
            "highest grossing category",
            "best performing category",
            "which category"
        ]):
            return {
                "intents": ["Category"],
                "selected_tools": ["category_performance", "kpi_summary"],
                "tool_execution_plan": [
                    {"tool": "category_performance", "arguments": {}},
                    {"tool": "kpi_summary", "arguments": {}}
                ],
                "tool_reasoning": {
                    "category_performance": "Category questions require the category breakdown.",
                    "kpi_summary": "KPI context is added to compare category performance against overall business scale."
                },
                "overall_reasoning": "Category questions are answered with category performance plus KPI context.",
                "confidence": 0.97,
                "tool_confidence": {"category_performance": 0.97, "kpi_summary": 0.9}
            }

        if any(term in query for term in [
            "trend",
            "monthly",
            "month",
            "month over month",
            "mom",
            "growth",
            "decline",
            "increase",
            "decrease",
            "peak",
            "trough",
            "seasonality",
            "year over year",
            "yoy",
            "quarter",
            "q1",
            "q2",
            "q3",
            "q4",
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
            "better than",
            "worse than",
            "compared to",
            "compare october",
            "compare november",
            "vs",
            "versus"
        ]):
            return {
                "intents": ["Trend"],
                "selected_tools": ["monthly_trend", "kpi_summary"],
                "tool_execution_plan": [
                    {"tool": "monthly_trend", "arguments": {}},
                    {"tool": "kpi_summary", "arguments": {}}
                ],
                "tool_reasoning": {
                    "monthly_trend": "Trend and timing questions require the monthly performance trend.",
                    "kpi_summary": "KPI context is added to contextualize the trend against overall business scale."
                },
                "overall_reasoning": "Trend questions are answered with the monthly trend and KPI context.",
                "confidence": 0.96,
                "tool_confidence": {"monthly_trend": 0.96, "kpi_summary": 0.9}
            }

        if any(term in query for term in ["revenue", "profit", "summary", "overall", "business overview"]):
            return {
                "intents": ["Revenue"],
                "selected_tools": [
                    "kpi_summary"
                ],
                "tool_execution_plan": [
                    {
                        "tool":"kpi_summary",
                        "arguments":{}
                    }
                ],
                "tool_reasoning": {
                    "kpi_summary": "General revenue or profit questions need a baseline KPI view.",
                    "monthly_trend": "A trend view is added for context when the question is about performance over time."
                },
                "overall_reasoning": "General KPI questions are answered using KPI Summary only.",
                "confidence": 0.9,
                "tool_confidence": {"kpi_summary": 0.9, "monthly_trend": 0.8}
            }

        return None

    def _build_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Constructs the system prompt, incorporating context entities if available
        and instructing the LLM to generate an ordered sequence of tools in `tool_execution_plan`.
        """
        tools_description = """
1. bottom_products (DETERMINISTIC RULE: Must be selected for worst products, lowest revenue, least revenue, minimum revenue, or bottom products).
2. top_products (DETERMINISTIC RULE: Must be selected for top products, best-selling products, highest revenue products, or top 10 products).
3. category_performance (Use for category-level revenue, profit, orders, and units sold, e.g., revenue by category, profit by category).
4. regional_performance (DETERMINISTIC RULE: Must be selected for any regional questions, regional comparisons like "Compare East vs West", or highest/lowest revenue by region).
5. monthly_trend (Use for monthly revenue, revenue trend, monthly patterns, growth, decline, seasonality, and spikes over time).
6. forecast_evaluation (DETERMINISTIC RULE: Strictly restricted to future predictions, sales forecasts, or revenue predictions. NEVER select for historical questions or past data retrieval).
7. anomaly_detection (Use for outliers, abnormal sales, unusual transactions, risk, and transaction-level outliers).
8. kpi_summary (LOWEST PRIORITY FALLBACK: Use ONLY as a last resort for overall business overview or generic queries like "What is total revenue?" or "Revenue" when no specific dimension applies).
"""

        intents_list = ", ".join(SUPPORTED_INTENTS)
        
        context_str = json.dumps(context, indent=2) if context else "{}"
        failed_tools = []

        if context:
            failed_tools = context.get("failed_tools", [])

        return f"""
You are the Principal Planning Agent for InsightsOps, an enterprise AI-powered business analytics platform.
Your task is to analyze the user's business question as a senior Business Analyst, detect intent, and select the MOST SPECIFIC tool available using strict deterministic routing rules.

SUPPORTED INTENTS:
{intents_list}

AVAILABLE TOOLS (Strictly follow priority order from most specific to least specific fallback):
{tools_description}

CONTEXT ENTITIES:
{context_str}

FAILED TOOLS:
{failed_tools}

DETERMINISTIC PLANNING RULES & TOOL RANKING PRIORITY:
1. Always choose the MOST SPECIFIC tool available. If multiple tools match, choose the most granular one.
2. Priority Order (Strictly enforce from top to bottom):
   bottom_products > top_products > category_performance > regional_performance > monthly_trend > forecast_evaluation > anomaly_detection > kpi_summary
3. Regional Rule: Any question referencing regions, territories, or regional comparisons (e.g., "Which region generated highest revenue?", "Compare East vs West") MUST use `regional_performance`.
4. Worst Products Rule: Any question referencing "worst products", "lowest revenue products", or "least revenue" MUST use `bottom_products`.
5. Top Products Rule: Any question referencing "top products", "best-selling products", or "highest revenue products" MUST use `top_products`.
6. Forecast Restriction Rule: `forecast_evaluation` is strictly prohibited for historical questions, past performance, or current record summaries. It must only be used for future predictions.
7. KPI Summary Fallback Rule: General KPI Summary (`kpi_summary`) must always be the absolute last fallback. Never choose KPI Summary if a more specific tool directly answers the question.
8. Entity Extraction Integration: Ensure that arguments match extracted context entities precisely.
9. For every selected tool, explain why it was chosen based on the user's query and detected entities (1–2 sentences).
10. Provide overall reasoning in `overall_reasoning`, assign a confidence score between 0.0 and 1.0, and avoid duplicated tool entries.

REQUIRED JSON OUTPUT FORMAT:
{{
    "intents": ["List", "of", "detected", "intents"],
    "selected_tools": ["tool_1"],
    "tool_execution_plan": [
        {{
            "tool": "tool_1",
            "arguments": {{
                "region": "East",
                "category": "Electronics"
            }}
        }}
    ],
    "tool_reasoning": {{
        "tool_1": "Explanation of why tool_1 is needed."
    }},
    "overall_reasoning": "Brief explanation of the holistic multi-step strategy.",
    "confidence": 0.95,
    "tool_confidence": {{
        "tool_1": 0.96
    }}
}}

"""

    def _validate_and_format_plan(self, raw_plan: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validates tools, filters arguments according to tool scope, deduplicates tools 
        while preserving logical execution order, and ensures backward compatibility.
        """
        # Extract entities from context if provided
        context_entities = {}
        if context and isinstance(context, dict):
            context_entities = context.get("entities", {})
            if not isinstance(context_entities, dict):
                context_entities = {}

        # Process raw tool_execution_plan or fallback to selected_tools to build ordered sequence
        raw_exec_plan = raw_plan.get("tool_execution_plan", [])
        raw_selected_tools = raw_plan.get("selected_tools", [])

        candidate_steps = []
        if isinstance(raw_exec_plan, list) and len(raw_exec_plan) > 0:
            for item in raw_exec_plan:
                if isinstance(item, dict) and "tool" in item:
                    t_name = item.get("tool")
                    if t_name in AVAILABLE_TOOLS:
                        candidate_steps.append({
                            "tool": t_name,
                            "arguments": item.get("arguments", {})
                        })
        
        # If execution plan didn't provide valid steps, construct from selected_tools
        if not candidate_steps:
            for t_name in raw_selected_tools:
                if t_name in AVAILABLE_TOOLS:
                    candidate_steps.append({
                        "tool": t_name,
                        "arguments": {}
                    })

        # If still empty, use safe fallback
        if not candidate_steps:
            candidate_steps = [{"tool": "kpi_summary", "arguments": {}}]

        # Deduplicate tools while strictly preserving logical execution order
        validated_exec_plan = []
        seen_tools = set()
        valid_tools = []

        for step in candidate_steps:
            tool = step["tool"]
            if tool not in seen_tools:
                seen_tools.add(tool)
                valid_tools.append(tool)

                # Filter arguments according to tool scope rules
                allowed_keys = TOOL_ALLOWED_FILTERS.get(tool, set())
                tool_args = {}
                source_args = step.get("arguments", {})
                
                if not source_args and context_entities:
                    source_args = context_entities

                if isinstance(source_args, dict):
                    for k, v in source_args.items():
                        if k in allowed_keys and v is not None:
                            if v != "":
                                tool_args[k] = v

                validated_exec_plan.append({
                    "tool": tool,
                    "arguments": tool_args
                })

        intents = raw_plan.get("intents", ["General Business Question"])
        overall_reasoning = raw_plan.get("overall_reasoning", "Standard multi-step execution plan generated.")
        
        formatted_plan = {
            "intents": intents,
            "selected_tools": valid_tools,
            "tool_execution_plan": validated_exec_plan,
            "tool_reasoning": raw_plan.get("tool_reasoning", {}),
            "overall_reasoning": overall_reasoning,
            "confidence": raw_plan.get("confidence", 0.5),
            
            # Legacy compatible keys
            "intent": ", ".join(intents),
            "reason": overall_reasoning,
            "tool_confidence": raw_plan.get("tool_confidence", {})
        }

        return formatted_plan

    def generate_plan(self, user_query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Core planning execution loop.
        """
        deterministic_plan = self._build_deterministic_plan(user_query, context)
        if deterministic_plan:
            return self._validate_and_format_plan(deterministic_plan, context)

        system_prompt = self._build_system_prompt(context)

        try:
            response = create_chat_completion_with_retry(
                self._get_client(),
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            content = extract_response_text(response)
            raw_plan = json.loads(content)
            
            return self._validate_and_format_plan(raw_plan, context)

        except Exception as e:
            import traceback

            print("\n================ LLM ERROR ================\n")
            traceback.print_exc()
            print("\n==========================================\n")

            logging.exception("LLM Response Generation Failed")

            fallback_plan = {
                "intents": ["General Business Question"],
                "selected_tools": ["kpi_summary"],
                "tool_execution_plan": [
                    {
                        "tool": "kpi_summary",
                        "arguments": {}
                    }
                ],
                "tool_reasoning": {
                    "kpi_summary": "Fallback tool selected due to planning error."
                },
                "overall_reasoning": "Fallback execution plan due to an internal error.",
                "confidence": 0.0,
                "intent": "General Business Question",
                "reason": "Fallback execution plan due to an internal error."
            }

            return fallback_plan

    def replan(
        self,
        user_query: str,
        failed_tools: list[str],
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Generate an alternative execution plan by excluding failed tools.
        """
        replanning_instruction = f"""
    The following tools have already failed:
    {failed_tools}
    Do NOT select any of these tools again.
    Generate the best alternative execution plan.
    """

        system_prompt = (
            self._build_system_prompt(context)
            + replanning_instruction
        )

        response = create_chat_completion_with_retry(
            self._get_client(),
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            temperature=self.temperature,
            response_format={"type": "json_object"}
        )

        content = extract_response_text(response)
        raw_plan = json.loads(content)

        return self._validate_and_format_plan(raw_plan, context)

# =====================================================================
# PUBLIC API (Preserves Existing Signature)
# =====================================================================

def create_ai_plan(
    user_query: str,
    context: Optional[Dict[str, Any]] = None,
    failed_tools: Optional[list[str]] = None
) -> Dict[str, Any]:
    """
    Use the BusinessAnalysisPlanner to understand the user's business
    question and select an ordered sequence of analytical tools.

    The function preserves extracted entity/date information in the
    planner context so that filters such as year, month, region, category,
    etc. can be used when constructing tool arguments.

    Backwards compatible entry point.
    """

    planner = BusinessAnalysisPlanner()

    # Always work with a dictionary so we can safely enrich the context.
    if context is None:
        context = {}

    # Preserve extracted entities/date information if they were already
    # supplied by the workflow.
    if "entities" in context and context["entities"]:
        context["extracted_entities"] = context["entities"]

    # Preserve failed tools for retry/fallback planning.
    if failed_tools:
        context["failed_tools"] = failed_tools

    return planner.generate_plan(
        user_query,
        context
    )