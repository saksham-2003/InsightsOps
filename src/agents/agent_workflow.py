from src.agents.structured_planner import (
    create_structured_plan
)

from src.agents.structured_executor import (
    execute_structured_tools
)

from src.agents.evidence_calculator import (
    calculate_derived_evidence
)

from src.agents.evidence_compactor import (
    compact_tool_evidence
)

from src.agents.evidence_analyst import (
    analyze_evidence
)

from src.agents.recommendation_agent import (
    generate_recommendations
)


def run_insightsops_agent(
    user_query,
    df
):
    """
    Run the complete InsightsOps agent pipeline.

    Pipeline:
    1. AI planning
    2. Structured tool execution
    3. Deterministic evidence calculation
    4. Evidence compaction
    5. LLM evidence analysis
    6. LLM recommendation generation
    """

    response = {
        "success": False,
        "user_query": user_query,
        "plan": {},
        "execution": {},
        "derived_evidence": {},
        "compact_evidence": {},
        "analysis": {},
        "recommendations": {},
        "errors": []
    }


    # ========================================================
    # STEP 1: AI PLANNING
    # ========================================================

    try:

        plan = create_structured_plan(
            user_query
        )

        response["plan"] = plan

    except Exception as error:

        response["errors"].append(
            f"Planning error: {str(error)}"
        )

        return response


    # ========================================================
    # STEP 2: TOOL EXECUTION
    # ========================================================

    try:

        execution = execute_structured_tools(
            plan["tool_calls"],
            df
        )

        response["execution"] = execution


        if execution.get("errors"):

            response["errors"].extend(
                execution["errors"]
            )

    except Exception as error:

        response["errors"].append(
            f"Tool execution error: {str(error)}"
        )

        return response


    # ========================================================
    # STEP 3: VERIFIED EVIDENCE CALCULATION
    # ========================================================

    try:

        derived_evidence = (
            calculate_derived_evidence(
                execution
            )
        )

        response["derived_evidence"] = (
            derived_evidence
        )

    except Exception as error:

        response["errors"].append(
            f"Evidence calculation error: {str(error)}"
        )

        return response


    # ========================================================
    # STEP 4: COMPACT RAW TOOL EVIDENCE
    # ========================================================

    try:

        compact_evidence = (
            compact_tool_evidence(
                execution
            )
        )

        response["compact_evidence"] = (
            compact_evidence
        )

    except Exception as error:

        response["errors"].append(
            f"Evidence compaction error: {str(error)}"
        )

        return response


    # ========================================================
    # STEP 5: EVIDENCE ANALYSIS
    # ========================================================

    try:

        analysis = analyze_evidence(
            user_query,
            plan,
            compact_evidence,
            derived_evidence
        )

        response["analysis"] = analysis

    except Exception as error:

        response["errors"].append(
            f"Evidence analysis error: {str(error)}"
        )

        return response


    # ========================================================
    # STEP 6: RECOMMENDATION GENERATION
    # ========================================================

    try:

        recommendations = (
            generate_recommendations(
                user_query,
                plan,
                execution,
                analysis,
                derived_evidence
            )
        )

        response["recommendations"] = (
            recommendations
        )

    except Exception as error:

        response["errors"].append(
            f"Recommendation error: {str(error)}"
        )

        return response


    # ========================================================
    # WORKFLOW COMPLETE
    # ========================================================

    response["success"] = True

    return response