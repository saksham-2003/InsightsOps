from src.agents.router import route_query
from src.agents.executor import execute_tools
from src.agents.insight_agent import generate_insights

def initialize_state(user_query):
    """
    Create the initial shared agent state.
    """

    return {
        "user_query": user_query,
        "intent": "",
        "selected_tools": [],
        "tool_results": {},
        "insights": [],
        "recommendations": [],
        "final_response": "",
        "errors": []
    }


def routing_node(state):
    """
    Decide which tools should be used.
    """

    route = route_query(
        state["user_query"]
    )

    state["intent"] = route["intent"]

    state["selected_tools"] = (
        route["selected_tools"]
    )

    return state


def tool_execution_node(state, df):
    """
    Execute selected analytical tools.
    """

    execution = execute_tools(
        state["selected_tools"],
        df
    )

    state["tool_results"] = (
        execution["tool_results"]
    )

    state["errors"].extend(
        execution["errors"]
    )

    return state


def run_agent_workflow(user_query, df):
    """
    Run the current InsightsOps agent workflow.
    """

    # Step 1: Initialize state
    state = initialize_state(user_query)


    # Step 2: Route query
    state = routing_node(state)


        # Step 3: Execute tools
    state = tool_execution_node(
        state,
        df
    )


    # Step 4: Generate insights
    state = generate_insights(state)


    return state