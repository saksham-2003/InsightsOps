"""
Chart Generator Module for InsightsOps BI Platform.

Automatically converts executed tool outputs into structured visualization specifications
based on tool type and visualization rules.

Visualization selection uses a two-pass strategy:
  1. Intent-first:  INTENT_PREFERRED_TOOL maps each planner intent to an ordered
                    list of preferred tools — the first one that was executed and
                    produces a valid chart wins.
  2. Priority fallback: CHART_PRIORITY is used only when no intent-matched tool
                    produced a chart (e.g. kpi-only query or unsupported intent).
"""

from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# INTENT-FIRST CHART SELECTION MAP
# Keys match SUPPORTED_INTENTS in planner.py exactly.
# Values are ordered lists of preferred tool names — first match that ran wins.
# ---------------------------------------------------------------------------
INTENT_PREFERRED_TOOL: Dict[str, List[str]] = {
    "Revenue":          ["monthly_trend"],                          # Line chart
    "Trend":            ["monthly_trend"],                          # Line chart
    "Profit":           ["monthly_trend"],                          # Line chart (profit series)
    "Forecast":         ["forecast_evaluation"],                    # Actual vs Predicted multi-line
    "Region":           ["regional_performance"],                   # Vertical bar
    "Comparison":       ["regional_performance", "category_performance"],  # Bar or pie
    "Category":         ["category_performance"],                   # Pie / donut
    "Product":          ["top_products", "bottom_products"],        # Horizontal bar
    "Anomaly":          ["anomaly_detection"],                      # Scatter plot
    "Risk":             ["anomaly_detection", "monthly_trend"],     # Scatter preferred, trend fallback
    "Executive Summary":["monthly_trend", "regional_performance"],  # Trend preferred
    "Recommendation":   ["monthly_trend", "regional_performance"],  # Trend preferred
    "General Business Question": ["monthly_trend", "regional_performance", "category_performance"],
}

# ---------------------------------------------------------------------------
# PRIORITY FALLBACK TABLE
# Used only when the intent-first pass finds no matching chart.
# Higher number = higher priority. kpi_summary = 0 (renders as cards, not chart).
# ---------------------------------------------------------------------------
CHART_PRIORITY: Dict[str, int] = {
    "forecast_evaluation":  10,  # Always show forecast when present
    "anomaly_detection":     9,  # Scatter is high-signal for anomaly/risk queries
    "monthly_trend":         8,  # Trend line for temporal/revenue queries
    "regional_performance":  7,  # Bar chart for regional comparisons
    "category_performance":  6,  # Pie for category share questions
    "top_products":          5,  # Horizontal bar for product queries
    "bottom_products":       4,  # Horizontal bar for worst-product queries
    "kpi_summary":           0,  # KPIs shown as dashboard cards — never as a chart
}

def _resolve_primary_intent(plan_intents: Optional[List[str]] = None) -> Optional[str]:
    if not plan_intents:
        return None

    intent_priority = [
        "Forecast",
        "Anomaly",
        "Risk",
        "Trend",
        "Revenue",
        "Category",
        "Region",
        "Product",
        "Comparison",
        "Profit",
        "Executive Summary",
        "Recommendation",
        "General Business Question"
    ]

    for intent in intent_priority:
        if intent in plan_intents:
            return intent
    return None


def select_visualization(plan_intents: Optional[List[str]], executed_tools: Optional[List[str]], raw_results: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Select the visualization based on the primary user intent rather than the execution order.
    """
    if not raw_results:
        return None

    primary_intent = _resolve_primary_intent(plan_intents)
    if primary_intent:
        intent_tool_map = {
            "Forecast": ["forecast_evaluation"],
            "Anomaly": ["anomaly_detection"],
            "Risk": ["anomaly_detection"],
            "Trend": ["monthly_trend"],
            "Revenue": ["monthly_trend"],
            "Profit": ["monthly_trend"],
            "Category": ["category_performance"],
            "Region": ["regional_performance"],
            "Product": ["top_products", "bottom_products"],
            "Comparison": ["regional_performance", "category_performance"],
            "Executive Summary": ["monthly_trend", "regional_performance"],
            "Recommendation": ["monthly_trend", "regional_performance"],
            "General Business Question": ["monthly_trend", "regional_performance", "category_performance"],
        }

        for tool_name in intent_tool_map.get(primary_intent, []):
            if tool_name in executed_tools and tool_name in raw_results:
                viz = generate_visualization(tool_name, raw_results[tool_name])
                if viz:
                    return viz

    best_priority = -1
    for t_name in executed_tools or []:
        if t_name in raw_results:
            priority = CHART_PRIORITY.get(t_name, 0)
            if priority > best_priority:
                viz = generate_visualization(t_name, raw_results[t_name])
                if viz:
                    best_priority = priority
                    selected_viz = viz
    return selected_viz if 'selected_viz' in locals() else None


def generate_visualization(tool_name: str, tool_result: Any) -> Optional[Dict[str, Any]]:
    """
    Generates a visualization specification object based on the executed tool name 
    and its output data.
    """
    if not tool_result:
        return None

    # Handle wrapped response formats (e.g. dictionaries containing 'data' or lists)
    data = tool_result
    if isinstance(tool_result, dict):
        if "data" in tool_result and isinstance(tool_result["data"], (list, dict)):
            data = tool_result["data"]
        elif "table_data" in tool_result and isinstance(tool_result["table_data"], list):
            data = tool_result["table_data"]
        elif "predictions" in tool_result and isinstance(tool_result["predictions"], list):
            data = tool_result["predictions"]

    # 1. bottom_products -> Horizontal Bar Chart
    if tool_name == "bottom_products":
        items = data if isinstance(data, list) else data.get("table_data", [])
        if not items:
            return None

        visualization = {
            "type": "horizontal_bar",
            "title": "Bottom 10 Products by Revenue",
            "x": [item.get("Product", item.get("Product_Name", "Unknown")) for item in items],
            "y": [float(item.get("Revenue", 0)) for item in items],

            "focus": {
                "mode": "lowest",
                "value": "Tote Bag"
            }
        }

        

        return visualization

    # 2. top_products -> Horizontal Bar Chart
    if tool_name == "top_products":
        items = data if isinstance(data, list) else data.get("table_data", [])

        if not items:
            return None

        return {
            "type": "horizontal_bar",
            "title": "Top 10 Products by Revenue",
            "x": [
                item.get("Product", item.get("Product_Name", "Unknown"))
                for item in items
            ],
            "y": [
                float(item.get("Revenue", 0))
                for item in items
            ],
            "focus": {
                "mode": "highest",
                "value": None
            }
        }

        

        return visualization

    # 3. monthly_trend -> Line Chart
    if tool_name == "monthly_trend":
        items = data if isinstance(data, list) else []
        if not items:
            return None
        return {
            "type": "line",
            "title": "Monthly Revenue Trend",
            "x": [str(item.get("Order_Date", "")) for item in items],
            "y": [float(item.get("Revenue", 0)) for item in items]
        }

    # 4. regional_performance -> Bar Chart
    if tool_name == "regional_performance":
        items = data if isinstance(data, list) else []

        if not items:
            return None

        visualization = {
            "type": "bar",
            "title": "Regional Performance",
            "x": [item["Region"] for item in items],
            "y": [item["Revenue"] for item in items],

            "focus": {
                "mode": None,
                "value": None
            }
        }
        
        return visualization
    # 5. category_performance -> Pie Chart
    if tool_name == "category_performance":
        items = data if isinstance(data, list) else []
        if not items:
            return None
        return {
            "type": "pie",
            "title": "Category Performance",
            "labels": [str(item.get("Category", "")) for item in items],
            "values": [float(item.get("Revenue", 0)) for item in items]
        }

    # 6. forecast / forecast_evaluation -> Multi-Line Chart (Actual vs Predicted)
    if tool_name in ["forecast", "forecast_evaluation"]:
        preds = data.get("predictions", []) if isinstance(data, dict) else data
        if not preds:
            return None
        return {
            "type": "multi_line",
            "title": "Revenue Forecast: Actual vs Predicted",
            "x": [str(item.get("Order_Date", "")) for item in preds],
            "actual": [float(item.get("Revenue", 0)) if item.get("Revenue") is not None else None for item in preds],
            "predicted": [float(item.get("Predicted_Revenue", 0)) if item.get("Predicted_Revenue") is not None else None for item in preds]
        }

    # 7. anomaly_detection -> Scatter Plot
    if tool_name == "anomaly_detection":
        table_data = data.get("table_data", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        if not table_data:
            return None
        return {
            "type": "scatter",
            "title": "Transaction Anomaly Detection",
            "points": [
                {
                    "x": float(item.get("Revenue", 0)),
                    "y": float(item.get("Profit", 0)),
                    "label": str(item.get("Product_Name", ""))
                }
                for item in table_data
            ]
        }

    return None