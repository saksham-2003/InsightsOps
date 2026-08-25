# api/routes/ml.py
import logging
from fastapi import APIRouter, Depends, Query
from typing import Optional
from pydantic import BaseModel
from src.agents.agent_workflow import run_insightsops_agent
from api.dependencies import (
    get_cleaned_dataframe
)

from src.agents.tools import (
    TOOL_REGISTRY
)

from src.agents.state import ConversationMemoryManager

logger = logging.getLogger(__name__)

memory_manager = ConversationMemoryManager()

router = APIRouter(
    prefix="/api/ml",
    tags=["Machine Learning"]
)

class AnalystQuery(BaseModel):
    question: str

@router.post("/ai-analyst")
def ai_analyst(query: AnalystQuery, df=Depends(get_cleaned_dataframe)):
    print("===== ENTERED /api/ml/ai-analyst =====")
    
    """
    AI Business Analyst Endpoint
    Classifies intent, executes tools from the registry, and returns structured 
    Markdown responses with evidence data for frontend charting.
    """

    q = query.question.lower()
    # TEMPORARY TEST
    print("\n========================")
    print("STARTING AGENT")
    print("========================")

    workflow_result = run_insightsops_agent(
        user_query=query.question,
        df=df,
        memory_manager=memory_manager
    )

    print("\n========================")
    print("AGENT FINISHED")
    print("========================")
    print(workflow_result)
    if workflow_result.get("success"):
        return workflow_result

    print("⚠️ AGENT WORKFLOW FAILED — ENTERING FALLBACK")
    print("Fallback query:", query.question)

    logger.warning("=" * 80)
    logger.warning("WORKFLOW RESULT")
    logger.warning(workflow_result)
    logger.warning("=" * 80)
    
    tools_used = []
    evidence_data = []
    chart_type = None
    content = ""
    
    try:
        # INTENT: Forecast / Predictive
        if any(w in q for w in ["forecast", "predict", "next", "future"]):
            res = TOOL_REGISTRY["forecast_evaluation"](df, horizon=30)
            tools_used.append("forecast_evaluation")
            
            if "error" in res or res.get("success") is False:
                content = f"### Executive Summary\n{res.get('message', res.get('error', 'Unable to generate forecast at this time.'))}"
            else:
                metrics = res["metrics"]
                preds = res["predictions"]
                content = "### Executive Summary\nBased on historical data patterns, the forecasting model has generated revenue projections for the upcoming 30-day period.\n\n"
                content += "### Key Findings\n"
                content += f"- **Model Reliability**: R² Score of {metrics['R2']:.2f} (values closer to 1.0 indicate higher predictive accuracy).\n"
                content += f"- **Error Margin (RMSE)**: ${metrics['RMSE']:,.2f} average deviation per day.\n\n"
                content += "### Recommendations\n- **Inventory Planning**: Utilize the 30-day projected trend to proactively adjust stock levels.\n- **Risk Mitigation**: Monitor dates with historically high prediction variance closely."
                
                # Send the last 45 days (mix of historical and future) for context
                evidence_data = preds[-45:]
                chart_type = "forecast"
                
        # INTENT: Anomaly / Outliers
        elif any(w in q for w in ["anomal", "unusual", "suspicious", "outlier", "risk"]):
            res = TOOL_REGISTRY["anomaly_detection"](df)
            tools_used.append("anomaly_detection")
            
            if not res.get("success"):
                content = "### Executive Summary\nUnable to run anomaly detection at this time."
            else:
                data = res["data"]
                summ = data["executive_summary"]
                content = f"### Executive Summary\nThe isolation forest model detected **{summ['total_anomalies']} anomalies** across the dataset, representing **{summ['anomaly_percentage']:.2f}%** of all evaluated transactions.\n\n"
                content += "### Key Findings\n"
                content += f"- **Most Affected Region**: {summ['most_affected_region']}\n"
                content += f"- **Most Affected Category**: {summ['most_affected_category']}\n"
                content += f"- **Highest Severity Score**: {summ['highest_score']:.1f}/100\n\n"
                content += "### Recommendations\n"
                for rec in data["recommendations"]:
                    content += f"- {rec}\n"
                    
                evidence_data = data["table_data"]
                chart_type = "anomaly_scatter"
                
        # INTENT: Region / Comparison
        elif any(w in q for w in ["region", "east", "west", "north", "south", "compare", "territory"]):
            res = TOOL_REGISTRY["regional_performance"](df)
            tools_used.append("regional_performance")
            
            content = "### Executive Summary\nRegional performance analysis indicates significant variations in revenue generation and overall profitability across territories.\n\n"
            content += "### Key Findings\n"
            for r in res[:4]:
                content += f"- **{r['Region']}**: Generated **${r['Revenue']:,.2f}** in revenue with a profit of **${r.get('Profit', 0):,.2f}**.\n"
            content += "\n### Recommendations\n- **Resource Allocation**: Investigate the top-performing regions to replicate best practices.\n- **Growth Strategy**: Consider targeted marketing or operational audits in underperforming areas."
            
            evidence_data = res
            chart_type = "bar_region"
            
        # INTENT: Category / Segments
        elif any(w in q for w in ["category", "categories", "type", "segment"]):
            res = TOOL_REGISTRY["category_performance"](df)
            tools_used.append("category_performance")
            
            content = "### Executive Summary\nCategory performance highlights the primary product segments driving business revenue.\n\n"
            content += "### Key Findings\n"
            for c in res[:4]:
                content += f"- **{c['Category']}**: Contributed **${c['Revenue']:,.2f}** to overall revenue.\n"
            content += "\n### Recommendations\n- **Inventory Expansion**: Expand product lines within high-growth categories.\n- **Margin Review**: Analyze profit margins for bottom-tier categories to determine long-term viability."
            
            evidence_data = res
            chart_type = "bar_category"
            
        # INTENT: Product Performance
        elif any(w in q for w in ["product", "worst", "top", "item", "sku"]):
            res = TOOL_REGISTRY["top_products"](df)
            tools_used.append("top_products")
            
            content = "### Executive Summary\nProduct-level analysis reveals the top revenue-generating items currently in the portfolio.\n\n"
            content += "### Key Findings\n"
            for p in res[:5]:
                name = p.get('Product_Name', p.get('Product', 'Unknown'))
                content += f"- **{name}**: Generated **${p['Revenue']:,.2f}**.\n"
            content += "\n### Recommendations\n- **Stock Protection**: Ensure high availability and priority fulfillment for top-ranking products.\n- **Rationalization**: Assess the operational cost of maintaining chronically low-performing SKUs."
            
            evidence_data = res[:10]
            chart_type = "table_product"
            
        # INTENT: Trend / KPI Summary (Default Fallback)
        else: 
            res = TOOL_REGISTRY["monthly_trend"](df)
            kpi = TOOL_REGISTRY["kpi_summary"](df)
            tools_used.extend(["kpi_summary", "monthly_trend"])
            
            content = f"### Executive Summary\nThe business has generated a total revenue of **${kpi.get('total_revenue', 0):,.2f}** with an overall profit margin of **{kpi.get('profit_margin', 0):.1f}%**.\n\n"
            content += "### Key Findings\n"
            content += f"- **Total Orders Processed**: {kpi.get('total_orders', 0):,}\n"
            content += f"- **Average Order Value (AOV)**: ${kpi.get('average_order_value', 0):,.2f}\n"
            content += f"- **Leading Region**: {kpi.get('top_region', 'N/A')}\n"
            content += f"- **Leading Category**: {kpi.get('top_category', 'N/A')}\n\n"
            content += "### Recommendations\n- **Efficiency**: Maintain current operational efficiencies driving the baseline margin.\n- **Seasonality**: Leverage the monthly historical trend data to anticipate upcoming shifts in demand."
            
            evidence_data = res
            chart_type = "trend_area"
            
    except Exception as e:
        import traceback

        traceback.print_exc()

        raise

    return {
        "success": True,
        "role": "ai",
        "content": content,
        "tools_used": tools_used,
        "evidence_data": evidence_data,
        "chart_type": chart_type
    }


@router.get("/anomalies")
def get_anomalies(
    region: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    df=Depends(get_cleaned_dataframe)
):
    """
    Return anomaly detection summary, KPIs, filtered table, 
    and the top unusual transactions.
    """
    result = TOOL_REGISTRY[
        "anomaly_detection"
    ](
        df,
        region=region,
        category=category,
        start_date=startDate,
        end_date=endDate,
        severity=severity,
        search=search
    )
    return result


@router.get("/forecast-evaluation")
def get_forecast_evaluation(
    region: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    horizon: int = Query(30),
    customDate: Optional[str] = Query(None),
    df=Depends(get_cleaned_dataframe)
):
    """
    Return revenue forecasting model
    evaluation metrics and predictions.
    """
    result = TOOL_REGISTRY[
        "forecast_evaluation"
    ](
        df,
        region=region,
        category=category,
        horizon=horizon,
        custom_date=customDate
    )
    return {
        "success": True,
        "data": result
    }