from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.dependencies import (
    get_cleaned_dataframe
)

from src.agents.agent_workflow import (
    run_insightsops_agent
)


router = APIRouter(
    prefix="/api/agent",
    tags=["AI Business Analyst"]
)


class AgentQueryRequest(BaseModel):
    """
    Request body for the AI Business Analyst.
    """

    question: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Business question to investigate"
    )


@router.post("/query")
def query_agent(
    request: AgentQueryRequest,
    df=Depends(get_cleaned_dataframe)
):
    """
    Run a natural-language business question through
    the complete InsightsOps agent workflow.
    """

    result = run_insightsops_agent(
        request.question,
        df
    )


    if not result.get("success"):

        raise HTTPException(
            status_code=500,
            detail={
                "message": (
                    "The InsightsOps agent could not "
                    "complete the analysis."
                ),
                "errors": result.get(
                    "errors",
                    []
                )
            }
        )


    plan = result.get(
        "plan",
        {}
    )

    analysis = result.get(
        "analysis",
        {}
    )

    recommendations = result.get(
        "recommendations",
        {}
    )


    tool_trace = []

    for call in plan.get(
        "tool_calls",
        []
    ):

        tool_trace.append({
            "tool": call.get("tool"),
            "arguments": call.get(
                "arguments",
                {}
            )
        })


    return {
        "success": True,

        "question": request.question,

        "intent": plan.get(
            "intent"
        ),

        "plan_reason": plan.get(
            "reason"
        ),

        "tools_used": tool_trace,

        "executive_summary": analysis.get(
            "executive_summary"
        ),

        "key_findings": analysis.get(
            "key_findings",
            []
        ),

        "risks_or_cautions": analysis.get(
            "risks_or_cautions",
            []
        ),

        "confidence": analysis.get(
            "confidence"
        ),

        "confidence_reason": analysis.get(
            "confidence_reason"
        ),

        "priority_actions": recommendations.get(
            "priority_actions",
            []
        ),

        "experiments": recommendations.get(
            "experiments",
            []
        ),

        "monitoring_metrics": recommendations.get(
            "monitoring_metrics",
            []
        )
    }