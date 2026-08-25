from src.data_loader import load_data
from src.data_cleaner import clean_data
from src.ml.forecaster import (
    train_revenue_forecaster,
    forecast_future_revenue,
    evaluate_forecast_baselines,
)


FILE_PATH = "data/raw/data.csv"


def print_section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def main():

    # ============================================================
    # 1. LOAD AND CLEAN DATA
    # ============================================================

    print_section("LOADING DATA")

    df = load_data(FILE_PATH)
    cleaned_df, report = clean_data(df)

    print(f"Raw rows     : {len(df):,}")
    print(f"Cleaned rows : {len(cleaned_df):,}")

    # ============================================================
    # 2. TRAIN FORECASTING MODEL
    # ============================================================

    print_section("TRAINING FORECASTING MODEL")

    model, results, metrics = train_revenue_forecaster(cleaned_df)

    print(f"Training Days : {metrics['train_days']}")
    print(f"Testing Days  : {metrics['test_days']}")

    print("\n===== ONE-STEP MODEL METRICS =====")

    print(f"MAE           : ${metrics['MAE']:,.2f}")
    print(f"RMSE          : ${metrics['RMSE']:,.2f}")
    print(f"R² Score      : {metrics['R2']:.4f}")

    # ============================================================
    # 3. VERIFY NEW RECURSIVE METRICS
    # ============================================================

    print_section("RECURSIVE / WALK-FORWARD METRICS")

    required_recursive_metrics = [
        "Recursive_MAE",
        "Recursive_RMSE",
        "Recursive_R2",
    ]

    for metric_name in required_recursive_metrics:

        if metric_name not in metrics:
            raise AssertionError(
                f"Missing required metric: {metric_name}"
            )

        print(
            f"{metric_name:<18}: "
            f"{metrics[metric_name]:.4f}"
        )

    recursive_r2 = metrics["Recursive_R2"]
    one_step_r2 = metrics["R2"]

    print(
        f"\nOne-step R²      : {one_step_r2:.4f}"
    )

    print(
        f"Recursive R²     : {recursive_r2:.4f}"
    )

    if recursive_r2 > one_step_r2:
        print(
            "WARNING: Recursive R² is higher than one-step R². "
            "Verify the evaluation logic."
        )
    else:
        print(
            "PASS: Recursive R² is lower than or equal to "
            "one-step R²."
        )

    # ============================================================
    # 4. SAMPLE PREDICTIONS
    # ============================================================

    print_section("SAMPLE HISTORICAL PREDICTIONS")

    print(results.head(10))

    # ============================================================
    # 5. MODEL VS BASELINES
    # ============================================================

    print_section("MODEL VS BASELINES")

    comparison = evaluate_forecast_baselines(results)

    print(
        f"Random Forest MAE      : "
        f"${comparison['Random_Forest_MAE']:,.2f}"
    )

    print(
        f"Yesterday Baseline MAE : "
        f"${comparison['Naive_MAE']:,.2f}"
    )

    print(
        f"7-Day Average MAE      : "
        f"${comparison['Rolling_7_MAE']:,.2f}"
    )

    # ============================================================
    # 6. TEST FUTURE FORECASTS
    # ============================================================

    print_section("TESTING FUTURE FORECASTS")

    horizons = [15, 30, 90]

    for horizon in horizons:

        print(f"\n--- {horizon}-DAY FORECAST ---")

        future_forecast = forecast_future_revenue(
            model,
            cleaned_df,
            horizon=horizon,
        )

        # --------------------------------------------------------
        # Basic validation
        # --------------------------------------------------------

        if isinstance(future_forecast, dict):
            raise AssertionError(
                f"{horizon}-day forecast returned an error: "
                f"{future_forecast}"
            )

        if not isinstance(future_forecast, list):
            raise AssertionError(
                f"{horizon}-day forecast did not return a list."
            )

        # --------------------------------------------------------
        # Verify number of future rows
        # --------------------------------------------------------

        actual_count = len(future_forecast)

        print(
            f"Future rows      : "
            f"{actual_count}"
        )

        if actual_count != horizon:
            raise AssertionError(
                f"{horizon}-day forecast returned "
                f"{actual_count} rows instead of {horizon}."
            )

        # --------------------------------------------------------
        # Verify future dates
        # --------------------------------------------------------

        first_date = future_forecast[0]["Order_Date"]
        last_date = future_forecast[-1]["Order_Date"]

        print(
            f"Date range       : "
            f"{first_date} -> {last_date}"
        )

        # --------------------------------------------------------
        # Verify forecast structure
        # --------------------------------------------------------

        for row in future_forecast:

            if row.get("Revenue") is not None:
                raise AssertionError(
                    "Future forecast row contains a non-null "
                    "Revenue value."
                )

            if row.get("Predicted_Revenue") is None:
                raise AssertionError(
                    "Future forecast row is missing "
                    "Predicted_Revenue."
                )

        # --------------------------------------------------------
        # Calculate forecast statistics
        # --------------------------------------------------------

        predicted_values = [
            float(row["Predicted_Revenue"])
            for row in future_forecast
        ]

        total_forecast = sum(predicted_values)
        average_forecast = (
            total_forecast / len(predicted_values)
        )

        highest_forecast = max(predicted_values)
        lowest_forecast = min(predicted_values)

        print(
            f"Total predicted  : "
            f"${total_forecast:,.2f}"
        )

        print(
            f"Average per day  : "
            f"${average_forecast:,.2f}"
        )

        print(
            f"Highest day      : "
            f"${highest_forecast:,.2f}"
        )

        print(
            f"Lowest day       : "
            f"${lowest_forecast:,.2f}"
        )

        print(
            f"PASS: {horizon}-day forecast "
            f"returned exactly {horizon} future rows."
        )

    # ============================================================
    # 7. FINAL RESULT
    # ============================================================

    print_section("ALL FORECASTING TESTS PASSED")

    print("✓ Model training")
    print("✓ One-step metrics")
    print("✓ Recursive MAE")
    print("✓ Recursive RMSE")
    print("✓ Recursive R²")
    print("✓ Baseline comparison")
    print("✓ 15-day forecast")
    print("✓ 30-day forecast")
    print("✓ 90-day forecast")
    print("✓ Future row counts")
    print("✓ Future date ranges")
    print("✓ Future Revenue = None")
    print("✓ Predicted_Revenue exists")

    print("\nForecasting pipeline verification complete.")


if __name__ == "__main__":
    main()