from src.data_loader import load_data
from src.data_cleaner import clean_data

from src.agents.agent_workflow import (
    run_insightsops_agent
)


file_path = "data/raw/data.csv"


df = load_data(file_path)

cleaned_df, report = clean_data(df)


query = "Why was November revenue unusually high?"


print(
    "\n===== INSIGHTSOPS COMPLETE AGENT ====="
)


result = run_insightsops_agent(
    query,
    cleaned_df
)


print("\nSUCCESS:")

print(result["success"])


print("\nUSER QUESTION:")

print(result["user_query"])


print("\nTOOLS SELECTED:")


for call in result.get(
    "plan",
    {}
).get(
    "tool_calls",
    []
):

    print(
        f"- {call['tool']} "
        f"{call.get('arguments', {})}"
    )


if result["success"]:

    analysis = result["analysis"]

    recommendations = result[
        "recommendations"
    ]


    print("\nEXECUTIVE SUMMARY:")

    print(
        analysis.get(
            "executive_summary",
            ""
        )
    )


    print("\nKEY FINDINGS:")

    for finding in analysis.get(
        "key_findings",
        []
    ):

        print(f"- {finding}")


    print("\nPRIORITY ACTIONS:")

    for action in recommendations.get(
        "priority_actions",
        []
    ):

        print(
            f"- [{action.get('priority', '').upper()}] "
            f"{action.get('action', '')}"
        )

        print(
            f"  Reason: "
            f"{action.get('reason', '')}"
        )


    print("\nEXPERIMENTS:")

    for experiment in recommendations.get(
        "experiments",
        []
    ):

        print(
            f"- {experiment.get('experiment', '')}"
        )


else:

    print("\nAGENT ERRORS:")

    for error in result["errors"]:

        print(f"- {error}")


print(
    "\n===== COMPLETE WORKFLOW TEST FINISHED ====="
)