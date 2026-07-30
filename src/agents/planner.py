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
    "General Business Question"
]

# Tool-specific allowed filters
TOOL_ALLOWED_FILTERS = {
    "regional_performance": {"region", "country", "state", "city", "year", "month", "category"},
    "category_performance": {"category", "sub_category", "year", "month", "region"},
    "top_products": {"category", "sub_category", "region", "year", "month"},
    "bottom_products": {"category", "sub_category", "region", "year", "month"},
    "forecast_evaluation": {"year", "month"},
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
        self.client = get_llm_client()
        self.model = "planner"
        self.temperature = 0.0

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
        system_prompt = self._build_system_prompt(context)

        try:
            response = create_chat_completion_with_retry(
                self.client,
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
            self.client,
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
    Use an LLM to understand the user's business question
    and select an ordered sequence of analytical tools needed along with filtered arguments.
    
    (Backwards compatible entry point).
    """
    planner = BusinessAnalysisPlanner()

    if failed_tools:
        if context is None:
            context = {}

        context["failed_tools"] = failed_tools

    return planner.generate_plan(user_query, context)