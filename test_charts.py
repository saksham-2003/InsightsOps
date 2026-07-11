from src.data_loader import load_data
from src.data_cleaner import clean_data
from src.analyzer import generate_business_analysis

from src.chart_generator import (
    create_monthly_revenue_chart,
    create_category_revenue_chart,
    create_category_profit_chart,
    create_regional_chart,
    create_top_products_chart,
    create_profitability_chart
)


file_path = "data/raw/data.csv"


# Load data
df = load_data(file_path)


# Clean data
cleaned_df, report = clean_data(df)


# Generate analysis
analysis = generate_business_analysis(cleaned_df)


# Create charts
monthly_chart = create_monthly_revenue_chart(
    analysis["monthly_performance"]
)

category_revenue_chart = create_category_revenue_chart(
    analysis["category_performance"]
)

category_profit_chart = create_category_profit_chart(
    analysis["category_performance"]
)

regional_chart = create_regional_chart(
    analysis["regional_performance"]
)

product_chart = create_top_products_chart(
    analysis["top_products"]
)

profitability_chart = create_profitability_chart(
    analysis["product_profitability"]
)


print("\nCharts generated successfully!")

print("\nOpening Monthly Revenue Chart...")

monthly_chart.show()