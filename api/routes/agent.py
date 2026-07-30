from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.dependencies import (
    get_cleaned_dataframe
)

from src.agents.agent_workflow import (
    run_insightsops_agent
)
from src.agents.state import ConversationMemoryManager

router = APIRouter(
    prefix="/api/agent",
    tags=["AI Business Analyst"]
)

# Shared ConversationMemoryManager instance at module level for development persistence.
# Future Ready: This shared instance can later be replaced by Redis, a Session Manager,
# or a Database without changing the endpoint logic.
shared_memory_manager = ConversationMemoryManager()


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
        df,
        memory_manager=shared_memory_manager
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

    if not tool_trace:
        for tool_name in result.get("metadata", {}).get("tools_used", []):
            tool_trace.append({
                "tool": tool_name,
                "arguments": {}
            })


    return {
        "success": True,

        "question": request.question,

        "intent": plan.get(
            "intent", plan.get("intents", ["General Analysis"])[0] if isinstance(plan.get("intents"), list) else None
        ),

        "plan_reason": plan.get(
            "reason", ""
        ),

        "tools_used": tool_trace,

        "analysis": result.get("final_response", {}),

        "evidence": result.get("evidence", {}),

        "metadata": result.get("metadata", {}),

        "errors": result.get("errors", [])
    }