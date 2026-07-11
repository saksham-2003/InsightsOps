from typing import TypedDict, Any


class AgentState(TypedDict, total=False):
    """
    Shared state passed between agents.
    """

    user_query: str

    intent: str

    selected_tools: list[str]

    tool_results: dict[str, Any]

    insights: list[str]

    recommendations: list[str]

    final_response: str

    errors: list[str]