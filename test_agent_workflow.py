from src.data_loader import load_data
from src.data_cleaner import clean_data

from src.agents.workflow import (
    run_agent_workflow
)


file_path = "data/raw/data.csv"


df = load_data(file_path)

cleaned_df, report = clean_data(df)


queries = [

    "Give me a business summary",

    "Compare category performance",

    "Compare category and regional performance",

    "Show unusual transactions"

]


print("\n===== INSIGHTSOPS AGENT WORKFLOW =====")


for query in queries:

    print("\n" + "=" * 70)

    print(f"\nUSER: {query}")


    state = run_agent_workflow(
        query,
        cleaned_df
    )


    print(
        f"\nINTENT: {state['intent']}"
    )


    print(
        f"TOOLS USED: "
        f"{state['selected_tools']}"
    )


    print("\nINSIGHTS:")


    for insight in state["insights"]:

        print(f"- {insight}")


    if state["errors"]:

        print("\nERRORS:")

        for error in state["errors"]:

            print(f"- {error}")