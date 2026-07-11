from src.data_loader import load_data
from src.data_cleaner import clean_data

from src.agents.router import route_query

from src.agents.executor import execute_tools


file_path = "data/raw/data.csv"


df = load_data(file_path)

cleaned_df, report = clean_data(df)


test_queries = [

    "Give me a business summary",

    "Show me monthly revenue trends",

    "Which categories perform best?",

    "Compare regional performance",

    "Show unusual transactions",

    "Evaluate the revenue forecast",

    "Show category and regional performance"
]


print("\n===== AGENT ROUTER TEST =====")


for query in test_queries:

    print("\n" + "=" * 60)

    print(f"USER QUERY: {query}")


    route = route_query(query)


    print(
        f"INTENT: {route['intent']}"
    )


    print(
        f"SELECTED TOOLS: "
        f"{route['selected_tools']}"
    )


    execution = execute_tools(
        route["selected_tools"],
        cleaned_df
    )


    print(
        f"TOOLS EXECUTED: "
        f"{list(execution['tool_results'].keys())}"
    )


    print(
        f"ERRORS: "
        f"{execution['errors']}"
    )