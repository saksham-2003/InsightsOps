from src.data_loader import load_data
from src.data_cleaner import clean_data

from src.agents.structured_planner import (
    create_structured_plan
)

from src.agents.structured_executor import (
    execute_structured_tools
)

from src.agents.evidence_analyst import (
    analyze_evidence
)


file_path = "data/raw/data.csv"


df = load_data(file_path)

cleaned_df, report = clean_data(df)


queries = [

    "Why was November revenue unusually high?",

    "Why is the East region performing better than others?",

    "Give me an overview of the business"
]


print(
    "\n===== AI EVIDENCE ANALYST TEST ====="
)


for query in queries:

    print("\n" + "=" * 70)

    print(f"\nUSER: {query}")


    # Step 1: AI planning

    plan = create_structured_plan(
        query
    )


    print("\nPLAN:")

    for call in plan["tool_calls"]:

        print(
            f"- {call['tool']} "
            f"{call['arguments']}"
        )


    # Step 2: Tool execution

    execution = execute_structured_tools(

        plan["tool_calls"],

        cleaned_df
    )


    # Step 3: Evidence analysis

    analysis = analyze_evidence(

        query,

        plan,

        execution
    )


    print("\nEXECUTIVE SUMMARY:")

    print(
        analysis["executive_summary"]
    )


    print("\nKEY FINDINGS:")

    for finding in analysis[
        "key_findings"
    ]:

        print(f"- {finding}")


    print("\nRISKS / CAUTIONS:")

    for caution in analysis[
        "risks_or_cautions"
    ]:

        print(f"- {caution}")


    print(
        f"\nCONFIDENCE: "
        f"{analysis['confidence']}"
    )


    print(
        f"REASON: "
        f"{analysis['confidence_reason']}"
    )