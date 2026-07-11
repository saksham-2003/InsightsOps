from src.data_loader import load_data
from src.data_cleaner import clean_data

from src.agents.structured_planner import (
    create_structured_plan
)

from src.agents.structured_executor import (
    execute_structured_tools
)

from src.agents.evidence_calculator import (
    calculate_derived_evidence
)

from src.agents.evidence_analyst import (
    analyze_evidence
)

from src.agents.recommendation_agent import (
    generate_recommendations
)
from src.agents.evidence_compactor import (
    compact_tool_evidence
)

# ============================================================
# LOAD AND CLEAN DATA
# ============================================================

file_path = "data/raw/data.csv"


df = load_data(file_path)


cleaned_df, report = clean_data(df)


# ============================================================
# USER QUERY
# ============================================================

query = "Why was November revenue unusually high?"


print(
    "\n===== COMPLETE AGENT REASONING TEST ====="
)


# ============================================================
# STEP 1: CREATE STRUCTURED AI PLAN
# ============================================================

plan = create_structured_plan(
    query
)


# ============================================================
# STEP 2: EXECUTE SELECTED ANALYTICAL TOOLS
# ============================================================

execution = execute_structured_tools(
    plan["tool_calls"],
    cleaned_df
)


# ============================================================
# STEP 3: CALCULATE VERIFIED DERIVED EVIDENCE
# ============================================================

derived_evidence = calculate_derived_evidence(
    execution
)


# ============================================================
# STEP 4: ANALYZE EVIDENCE
# ============================================================

analysis = analyze_evidence(
    query,
    plan,
    execution,
    derived_evidence
)


# ============================================================
# STEP 5: GENERATE RECOMMENDATIONS
# ============================================================

recommendations = generate_recommendations(
    query,
    plan,
    execution,
    analysis,
    derived_evidence
)


# ============================================================
# DISPLAY USER QUESTION
# ============================================================

print("\nUSER QUESTION:")

print(query)


# ============================================================
# DISPLAY AI PLAN
# ============================================================

print("\nINTENT:")

print(
    plan.get(
        "intent",
        "No intent returned"
    )
)


print("\nTOOLS USED:")


for call in plan["tool_calls"]:

    print(
        f"- {call['tool']} "
        f"{call.get('arguments', {})}"
    )


print("\nPLAN REASON:")

print(
    plan.get(
        "reason",
        "No reason returned"
    )
)


# ============================================================
# DISPLAY EXECUTION ERRORS
# ============================================================

if execution["errors"]:

    print("\nEXECUTION ERRORS:")

    for error in execution["errors"]:

        print(f"- {error}")


# ============================================================
# DISPLAY EXECUTIVE SUMMARY
# ============================================================

print("\nEXECUTIVE SUMMARY:")

print(
    analysis.get(
        "executive_summary",
        "No executive summary generated."
    )
)


# ============================================================
# DISPLAY KEY FINDINGS
# ============================================================

print("\nKEY FINDINGS:")


for finding in analysis.get(
    "key_findings",
    []
):

    print(f"- {finding}")


# ============================================================
# DISPLAY RISKS AND CAUTIONS
# ============================================================

print("\nRISKS / CAUTIONS:")


for caution in analysis.get(
    "risks_or_cautions",
    []
):

    print(f"- {caution}")


# ============================================================
# DISPLAY ANALYSIS CONFIDENCE
# ============================================================

print("\nCONFIDENCE:")

print(
    analysis.get(
        "confidence",
        "Not provided"
    )
)


print("\nCONFIDENCE REASON:")

print(
    analysis.get(
        "confidence_reason",
        "Not provided"
    )
)


# ============================================================
# DISPLAY PRIORITY ACTIONS
# ============================================================

print("\nPRIORITY ACTIONS:")


for item in recommendations.get(
    "priority_actions",
    []
):

    priority = item.get(
        "priority",
        "unknown"
    ).upper()


    action = item.get(
        "action",
        "No action provided"
    )


    reason = item.get(
        "reason",
        "No reason provided"
    )


    print(
        f"- [{priority}] {action}"
    )


    print(
        f"  Reason: {reason}"
    )


# ============================================================
# DISPLAY EXPERIMENTS
# ============================================================

print("\nEXPERIMENTS:")


for item in recommendations.get(
    "experiments",
    []
):

    print(
        f"- {item.get('experiment', 'No experiment provided')}"
    )


    print(
        "  Success Metric: "
        f"{item.get('success_metric', 'Not provided')}"
    )


# ============================================================
# DISPLAY MONITORING METRICS
# ============================================================

print("\nMONITORING METRICS:")


for metric in recommendations.get(
    "monitoring_metrics",
    []
):

    print(f"- {metric}")


# ============================================================
# DISPLAY VERIFIED DERIVED EVIDENCE
# ============================================================

print(
    "\n===== VERIFIED DERIVED EVIDENCE ====="
)


print(derived_evidence)


# ============================================================
# TEST COMPLETE
# ============================================================

print(
    "\n===== AGENT REASONING TEST COMPLETED ====="
)