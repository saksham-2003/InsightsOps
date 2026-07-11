import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)


def prepare_daily_revenue(df):
    """
    Aggregate transaction data into daily revenue.
    """

    daily_data = (
        df.groupby("Order_Date")["Revenue"]
        .sum()
        .reset_index()
        .sort_values("Order_Date")
    )

    return daily_data


def create_forecasting_features(daily_data):
    """
    Create time-series and lag features.
    """

    data = daily_data.copy()

    # Calendar features
    data["DayOfWeek"] = data["Order_Date"].dt.dayofweek
    data["Month"] = data["Order_Date"].dt.month
    data["DayOfMonth"] = data["Order_Date"].dt.day
    data["Quarter"] = data["Order_Date"].dt.quarter

    # Lag features
    data["Lag_1"] = data["Revenue"].shift(1)
    data["Lag_7"] = data["Revenue"].shift(7)
    data["Lag_14"] = data["Revenue"].shift(14)
    data["Lag_30"] = data["Revenue"].shift(30)

    # Rolling averages
    data["Rolling_Mean_7"] = (
        data["Revenue"]
        .shift(1)
        .rolling(window=7)
        .mean()
    )

    data["Rolling_Mean_30"] = (
        data["Revenue"]
        .shift(1)
        .rolling(window=30)
        .mean()
    )

    # Remove rows containing NaN values
    data = data.dropna().reset_index(drop=True)

    return data


def train_revenue_forecaster(df):
    """
    Train and evaluate a revenue forecasting model.
    """

    daily_data = prepare_daily_revenue(df)

    feature_data = create_forecasting_features(
        daily_data
    )

    features = [
        "DayOfWeek",
        "Month",
        "DayOfMonth",
        "Quarter",
        "Lag_1",
        "Lag_7",
        "Lag_14",
        "Lag_30",
        "Rolling_Mean_7",
        "Rolling_Mean_30"
    ]

    X = feature_data[features]
    y = feature_data["Revenue"]


    # Time-based split: first 80% train, final 20% test
    split_index = int(len(feature_data) * 0.8)

    X_train = X.iloc[:split_index]
    X_test = X.iloc[split_index:]

    y_train = y.iloc[:split_index]
    y_test = y.iloc[split_index:]


    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)


    results = feature_data.iloc[
        split_index:
    ][["Order_Date", "Revenue"]].copy()

    results["Predicted_Revenue"] = predictions


    metrics = {
        "MAE": mean_absolute_error(
            y_test,
            predictions
        ),

        "RMSE": mean_squared_error(
            y_test,
            predictions
        ) ** 0.5,

        "R2": r2_score(
            y_test,
            predictions
        ),

        "train_days": len(X_train),

        "test_days": len(X_test)
    }


    return model, results, metrics

def evaluate_forecast_baselines(results):
    """
    Compare ML predictions against simple forecasting baselines.
    """

    evaluation_df = results.copy()

    # Baseline 1:
    # Predict today's revenue using yesterday's actual revenue
    evaluation_df["Naive_Prediction"] = (
        evaluation_df["Revenue"].shift(1)
    )

    # Baseline 2:
    # Predict using previous 7-day average
    evaluation_df["Rolling_7_Baseline"] = (
        evaluation_df["Revenue"]
        .shift(1)
        .rolling(window=7)
        .mean()
    )

    # Remove rows where baseline values are unavailable
    evaluation_df = evaluation_df.dropna()


    actual = evaluation_df["Revenue"]

    ml_prediction = evaluation_df["Predicted_Revenue"]

    naive_prediction = evaluation_df["Naive_Prediction"]

    rolling_prediction = evaluation_df["Rolling_7_Baseline"]


    comparison = {

        "Random_Forest_MAE":
            mean_absolute_error(
                actual,
                ml_prediction
            ),

        "Naive_MAE":
            mean_absolute_error(
                actual,
                naive_prediction
            ),

        "Rolling_7_MAE":
            mean_absolute_error(
                actual,
                rolling_prediction
            )
    }


    return comparison