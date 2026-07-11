from src.data_loader import load_data
from src.data_cleaner import clean_data

from src.agents.tools import TOOL_REGISTRY


file_path = "data/raw/data.csv"


df = load_data(file_path)

cleaned_df, report = clean_data(df)


print("\n===== AGENT TOOL REGISTRY =====")


for tool_name in TOOL_REGISTRY:

    print(f"Available Tool: {tool_name}")


print("\n===== TESTING KPI TOOL =====")


kpi_tool = TOOL_REGISTRY["kpi_summary"]

result = kpi_tool(cleaned_df)

print(result)


print("\n===== TESTING CATEGORY TOOL =====")


category_tool = TOOL_REGISTRY[
    "category_performance"
]

category_result = category_tool(cleaned_df)

for category in category_result:

    print(category)