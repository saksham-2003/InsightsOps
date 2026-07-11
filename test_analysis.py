from src.data_loader import load_data
from src.data_cleaner import clean_data
from src.analyzer import generate_business_analysis


file_path = "data/raw/data.csv"


# Load data
df = load_data(file_path)


# Clean data
cleaned_df, cleaning_report = clean_data(df)


# Generate analysis
analysis = generate_business_analysis(cleaned_df)


print("\n===== BUSINESS ANALYSIS REPORT =====")


print("\n--- MONTHLY PERFORMANCE ---")
print(analysis["monthly_performance"].head())


print("\n--- CATEGORY PERFORMANCE ---")
print(analysis["category_performance"])


print("\n--- TOP 10 PRODUCTS ---")
print(analysis["top_products"])


print("\n--- REGIONAL PERFORMANCE ---")
print(analysis["regional_performance"])


print("\n--- TOP 10 STATES ---")
print(
    analysis["state_performance"].head(10)
)


print("\n--- TOP 10 CITIES ---")
print(
    analysis["city_performance"].head(10)
)


print("\n--- MOST PROFITABLE PRODUCTS ---")
print(
    analysis["product_profitability"].head(10)
)
