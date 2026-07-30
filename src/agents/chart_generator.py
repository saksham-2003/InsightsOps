"""
Chart Generator Module for InsightsOps BI Platform.

Automatically converts executed tool outputs into structured visualization specifications
based on tool type and visualization rules.
"""

from typing import Any, Dict, List, Optional

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