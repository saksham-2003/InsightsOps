from src.data_loader import load_data
from src.data_cleaner import clean_data

from src.agents.tools import (
    get_period_drilldown,
    get_region_drilldown
)


file_path = "data/raw/data.csv"


df = load_data(file_path)

cleaned_df, report = clean_data(df)


print("\n===== NOVEMBER DRILLDOWN =====")


november = get_period_drilldown(
    cleaned_df,
    month=11
)


print("\nTotal November Revenue:")
print(
    f"${november['total_revenue']:,.2f}"
)


print("\nNovember Categories:")

for category in november["categories"]:

    print(
        category["Category"],
        f"${category['Revenue']:,.2f}"
    )


print("\nTop November Products:")

for product in november["top_products"][:5]:

    print(
        product["Product_Name"],
        f"${product['Revenue']:,.2f}"
    )


print("\n===== EAST REGION DRILLDOWN =====")


east = get_region_drilldown(
    cleaned_df,
    region="East"
)


print("\nEast Revenue:")
print(
    f"${east['total_revenue']:,.2f}"
)


print("\nEast Categories:")

for category in east["categories"]:

    print(
        category["Category"],
        f"${category['Revenue']:,.2f}"
    )


print("\nTop East Products:")

for product in east["top_products"][:5]:

    print(
        product["Product_Name"],
        f"${product['Revenue']:,.2f}"
    )