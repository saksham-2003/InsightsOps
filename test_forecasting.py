from src.data_loader import load_data
from src.data_cleaner import clean_data

from src.ml.forecaster import (
    train_revenue_forecaster,
    evaluate_forecast_baselines
)


file_path = "data/raw/data.csv"


df = load_data(file_path)

cleaned_df, report = clean_data(df)


model, results, metrics = (
    train_revenue_forecaster(cleaned_df)
)


print("\n===== REVENUE FORECASTING REPORT =====")


print(
    f"\nTraining Days: "
    f"{metrics['train_days']}"
)

print(
    f"Testing Days: "
    f"{metrics['test_days']}"
)

print(
    f"\nMAE: "
    f"${metrics['MAE']:,.2f}"
)

print(
    f"RMSE: "
    f"${metrics['RMSE']:,.2f}"
)

print(
    f"R² Score: "
    f"{metrics['R2']:.4f}"
)


print("\n===== SAMPLE PREDICTIONS =====")

print(
    results.head(10)
)

comparison = evaluate_forecast_baselines(results)


print("\n===== MODEL VS BASELINES =====")


print(
    f"\nRandom Forest MAE: "
    f"${comparison['Random_Forest_MAE']:,.2f}"
)


print(
    f"Yesterday Baseline MAE: "
    f"${comparison['Naive_MAE']:,.2f}"
)


print(
    f"7-Day Average Baseline MAE: "
    f"${comparison['Rolling_7_MAE']:,.2f}"
)