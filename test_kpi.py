from src.data_loader import load_data
from src.data_cleaner import clean_data
from src.kpi_engine import calculate_kpis


file_path = "data/raw/data.csv"


# Load data
df = load_data(file_path)


# Clean data
cleaned_df, cleaning_report = clean_data(df)


# Calculate KPIs
kpis = calculate_kpis(cleaned_df)


print("\n===== BUSINESS KPI REPORT =====")


print(f"\nTotal Revenue: ${kpis['total_revenue']:,.2f}")

print(f"Total Profit: ${kpis['total_profit']:,.2f}")

print(f"Total Orders: {kpis['total_orders']:,}")

print(f"Total Units Sold: {kpis['total_units_sold']:,}")

print(
    f"Average Order Value: "
    f"${kpis['average_order_value']:,.2f}"
)

print(
    f"Profit Margin: "
    f"{kpis['profit_margin']:.2f}%"
)

print(f"Top Category: {kpis['top_category']}")

print(f"Top Region: {kpis['top_region']}")