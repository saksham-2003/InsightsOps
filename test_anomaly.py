from src.data_loader import load_data
from src.data_cleaner import clean_data

from src.ml.anomaly_detector import (
    detect_transaction_anomalies
)


file_path = "data/raw/data.csv"


# Load data
df = load_data(file_path)


# Clean data
cleaned_df, cleaning_report = clean_data(df)


# Run anomaly detection
result_df, summary = detect_transaction_anomalies(
    cleaned_df
)


print("\n===== ANOMALY DETECTION REPORT =====")


print(
    f"\nTotal Transactions: "
    f"{summary['total_transactions']:,}"
)


print(
    f"Anomalies Detected: "
    f"{summary['anomaly_count']:,}"
)


print(
    f"Anomaly Percentage: "
    f"{summary['anomaly_percentage']:.2f}%"
)


print(
    "\nFeatures Used:",
    summary["features_used"]
)


print("\n===== TOP DETECTED ANOMALIES =====")


anomalies = result_df[
    result_df["Is_Anomaly"]
].sort_values(
    "Anomaly_Score"
)


columns_to_show = [
    "Order_ID",
    "Product_Name",
    "Quantity",
    "Unit_Price",
    "Revenue",
    "Profit",
    "Anomaly_Score"
]


print(
    anomalies[columns_to_show].head(10)
)
