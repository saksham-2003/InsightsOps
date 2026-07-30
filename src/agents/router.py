import time
import logging
from typing import Any, Dict, List, Optional

from src.agents.tools import TOOL_REGISTRY

class DynamicToolRouter:
    """
    Production-grade Tool Router for Agentic AI.
    
    Responsible for intelligently mapping execution plans to backend tools,
    handling execution with structured arguments, deduplication, error isolation, 
    and metadata generation.
    
    Future Ready: 
    Designed to easily integrate Parallel Execution, Caching, Retry mechanisms, 
    and Agent Loops without altering the external API contract.
    """
    
    def __init__(self, registry: Dict[str, callable]):
        self.registry = registry
        # Future enhancement insertion points
        self.cache = {}
        self.max_retries = 3

    def _map_intents_to_tools(self, intents: List[str]) -> List[str]:
        """
        Task 2: Tool Mapping
        Maps identified intents to their corresponding backend analytical tools.
        """
        intent_map = {
            "revenue": ["monthly_trend"],
            "profit": ["kpi_summary"],
            "forecast": ["forecast_evaluation"],
            "region": ["regional_performance"],
            "category": ["category_performance"],
            "anomaly": ["anomaly_detection"],
            "executive summary": ["kpi_summary", "monthly_trend"],
            "recommendation": ["kpi_summary"]  # Base contextual tool for recommendations
        }
        
        mapped_tools = []
        for intent in intents:
            key = str(intent).strip().lower()
            if key in intent_map:
                mapped_tools.extend(intent_map[key])
                
        return mapped_tools

    def _execute_single_tool(self, tool_name: str, arguments: Dict[str, Any], df: Any) -> Any:
        """
        Reusable helper to execute a single tool with given arguments or fallback to df alone.
        """
        tool_func = self.registry[tool_name]
        if arguments:
            return tool_func(df, **arguments)
        else:
            return tool_func(df)
        
    def _is_tool_failed(self, result) -> bool:
        """
        Returns True if the tool execution did not produce usable output.
        """

        if result is None:
            return True

        if isinstance(result, list) and len(result) == 0:
            return True

        if isinstance(result, dict):

            if len(result) == 0:
                return True

            if result.get("success") is False:
                return True

            if result.get("error") is not None:
                return True

        return False

    def execute_plan(self, plan: Dict[str, Any], df: Any) -> Dict[str, Any]:
        """
        Core routing and execution logic supporting both legacy selected_tools 
        and structured tool_execution_plan with arguments.
        """
        start_time = time.time()
        
        # 1. Dynamic Routing: Extract intents and structured execution plan
        intents = plan.get("intents", [])
        if not intents and "intent" in plan:
            # Fallback for legacy planner string format
            intents = [i.strip() for i in plan.get("intent", "").split(",")]
            
        tool_execution_plan = plan.get("tool_execution_plan")
        planned_tools = plan.get("selected_tools", [])

        executed_tools = []
        failed_tools = []
        tool_arguments_used = {}
        results = {}
        skipped_tools = []

        # 2. Execution path based on tool_execution_plan availability (Backward Compatibility)
        if tool_execution_plan and isinstance(tool_execution_plan, list):
            # Process structured tool_execution_plan with arguments
            seen_tools = set()
            for entry in tool_execution_plan:
                if not isinstance(entry, dict):
                    continue
                tool_name = entry.get("tool")
                arguments = entry.get("arguments", {})
                
                if not tool_name or tool_name not in self.registry:
                    continue
                
                if tool_name in seen_tools:
                    continue
                seen_tools.add(tool_name)
                
                tool_arguments_used[tool_name] = arguments

                try:
                    res = self._execute_single_tool(tool_name, arguments, df)

                    results[tool_name] = res

                    if self._is_tool_failed(res):
                        failed_tools.append(tool_name)
                    else:
                        executed_tools.append(tool_name)
                except Exception as e:
                    logging.error(f"Tool execution failed for '{tool_name}': {str(e)}")
                    failed_tools.append(tool_name)
                    results[tool_name] = {
                        "success": False, 
                        "error": f"Execution failed: {str(e)}"
                    }
        else:
            # Legacy Fallback Path using selected_tools and intent mapping
            mapped_tools = self._map_intents_to_tools(intents)
            combined_tools = planned_tools + mapped_tools

            if not combined_tools:
                combined_tools = ["kpi_summary"]
                intents.append("fallback_general_summary")

            unique_tools = []
            for tool in combined_tools:
                if tool not in unique_tools and tool in self.registry:
                    unique_tools.append(tool)
                else:
                    if tool not in skipped_tools:
                        skipped_tools.append(tool)

            for tool_name in unique_tools:
                tool_arguments_used[tool_name] = {}
                try:
                    res = self._execute_single_tool(tool_name, {}, df)

                    results[tool_name] = res

                    if self._is_tool_failed(res):
                        failed_tools.append(tool_name)
                    else:
                        executed_tools.append(tool_name)
                except Exception as e:
                    logging.error(f"Tool execution failed for '{tool_name}': {str(e)}")
                    failed_tools.append(tool_name)
                    results[tool_name] = {
                        "success": False, 
                        "error": f"Execution failed: {str(e)}"
                    }

        end_time = time.time()
        if (
            len(failed_tools) > 0
            and len(executed_tools) > 0
        ):
            logging.info(
                "Some tools failed. Agent is requesting a new plan..."
            )

            # Replanning will happen here

        # 3. Execution Metadata
        return {
            "results": results,
            "metadata": {
                "executed_tools": executed_tools,
                "failed_tools": failed_tools,
                "tool_arguments_used": tool_arguments_used,
                "skipped_tools": skipped_tools,
                "execution_order": executed_tools + failed_tools,
                "execution_time_seconds": round(end_time - start_time, 4),
                "intents_processed": intents,
                "execution_status":
                    "success" if len(failed_tools) == 0 else "partial_success"
            }
        }


def route_query(plan_or_query: Any, df: Optional[Any] = None) -> Dict[str, Any]:
    """
    Analyze a user query or an execution plan, map to tools, and execute them.
    
    Maintains backward compatibility with older implementations while 
    enabling the new DynamicToolRouter pipeline.
    
    Args:
        plan_or_query: A string (legacy query) or a dictionary representing the AI plan.
        df: The pandas DataFrame required for tool execution.
    """
    router = DynamicToolRouter(TOOL_REGISTRY)
    
    # Normalize string inputs to a structured plan format
    if isinstance(plan_or_query, str):
        plan = {
            "intents": [plan_or_query.lower()], 
            "selected_tools": []
        }
    else:
        plan = plan_or_query

    # Backward Compatibility Mode: Return routing logic without execution if df is omitted
    if df is None:
        intents = plan.get("intents", [])
        if not intents and "intent" in plan:
            intents = [plan["intent"]]
            
        tool_execution_plan = plan.get("tool_execution_plan")
        if tool_execution_plan and isinstance(tool_execution_plan, list):
            unique = [item.get("tool") for item in tool_execution_plan if isinstance(item, dict) and "tool" in item]
        else:
            mapped = router._map_intents_to_tools(intents)
            planned = plan.get("selected_tools", [])
            unique = list(dict.fromkeys(planned + mapped)) or ["kpi_summary"]
        
        return {
            "intent": ", ".join(intents) if intents else "general_business_analysis",
            "selected_tools": unique
        }

    # Production Execution Mode
    return router.execute_plan(plan, df)