from src.data_loader import load_data
from src.data_cleaner import clean_data

from src.agents.structured_planner import (
    create_structured_plan
)

from src.agents.structured_executor import (
    execute_structured_tools
)


file_path = "data/raw/data.csv"


df = load_data(file_path)

cleaned_df, report = clean_data(df)


queries = [

    "Why was November revenue unusually high?",

    "Why is the East region performing better than others?",

    "Give me an overview of the business",

    "Show revenue trends and investigate November",

    "Are there unusual transactions?"
]


print(
    "\n===== STRUCTURED AGENT TEST ====="
)


for query in queries:

    print("\n" + "=" * 70)

    print(f"\nUSER: {query}")


    plan = create_structured_plan(
        query
    )


    print(
        f"\nINTENT: "
        f"{plan['intent']}"
    )


    print("\nTOOL CALLS:")


    for call in plan["tool_calls"]:

        print(
            f"- {call['tool']} "
            f"{call['arguments']}"
        )


    print(
        f"\nPLAN REASON: "
        f"{plan['reason']}"
    )


    execution = execute_structured_tools(

        plan["tool_calls"],

        cleaned_df
    )


    print("\nEXECUTED:")


    for result_key, data in (
        execution["tool_results"].items()
    ):

        print(
            f"- {data['tool']} "
            f"{data['arguments']}"
        )


    print(
        f"\nERRORS: "
        f"{execution['errors']}"
    )