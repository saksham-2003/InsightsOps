# src/ml/forecaster.py
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

    # ----------------------------------------------------------------
    # Walk-forward (recursive) evaluation — Fix #2
    #
    # The one-step metrics above are computed with all test-set lag and
    # rolling features sourced from REAL historical revenue, which is
    # how the model was trained.  In production, however, forecasting is
    # recursive: each predicted value feeds the next step as a lag.
    # This block replicates that exact behaviour on the held-out test
    # period so that Recursive_* metrics reflect operational accuracy.
    #
    # Ground truth (y_test) is used ONLY for final comparison — it is
    # never read back as an input during the recursive loop.
    # ----------------------------------------------------------------
    train_end_date       = feature_data.iloc[split_index - 1]["Order_Date"]
    train_daily          = daily_data[daily_data["Order_Date"] <= train_end_date].copy()

    # Anchor rolling means to last actual values (mirrors Fix #1 in production).
    _actual_rev          = train_daily["Revenue"].values
    _rec_anchor_7        = float(np.mean(_actual_rev[-7:]))
    _rec_anchor_30       = float(np.mean(_actual_rev[-30:]))

    _rec_working_df      = train_daily.copy()
    _recursive_preds     = []

    for _i in range(len(X_test)):
        _next_date        = train_end_date + pd.Timedelta(days=_i + 1)
        _new_row          = pd.DataFrame([{"Order_Date": _next_date, "Revenue": 0.0}])
        _rec_working_df   = pd.concat([_rec_working_df, _new_row], ignore_index=True)

        _feat_df          = create_forecasting_features(_rec_working_df)
        _X_rec            = _feat_df.iloc[-1:][features].copy()
        _X_rec["Rolling_Mean_7"]  = _rec_anchor_7
        _X_rec["Rolling_Mean_30"] = _rec_anchor_30

        _pred_val         = model.predict(_X_rec)[0]
        _rec_working_df.loc[_rec_working_df.index[-1], "Revenue"] = _pred_val
        _recursive_preds.append(_pred_val)

    _recursive_preds = np.array(_recursive_preds)
    _y_test_arr      = y_test.values

    metrics["Recursive_MAE"]  = float(mean_absolute_error(_y_test_arr, _recursive_preds))
    metrics["Recursive_RMSE"] = float(mean_squared_error(_y_test_arr, _recursive_preds) ** 0.5)
    metrics["Recursive_R2"]   = float(r2_score(_y_test_arr, _recursive_preds))

    return model, results, metrics


def forecast_future_revenue(model, df, horizon=30, custom_date=None):
    """
    Generate future predictions recursively using the trained model.
    Dynamically bounds forecasts up to 365 days beyond the last dataset date.
    """
    daily_data = prepare_daily_revenue(df)
    
    if daily_data.empty:
        return {"error": "No historical data available to forecast from."}
        
    last_date = daily_data["Order_Date"].max()

    horizon_int = 30
    try:
        if horizon and str(horizon).isdigit():
            horizon_int = int(horizon)
    except Exception:
        pass

    print("=" * 60)
    print("LAST DATE IN DATASET:", last_date)
    print("FORECAST HORIZON:", horizon_int)
    print("=" * 60)
        
    if custom_date:
        try:
            target_date = pd.to_datetime(custom_date)

            days_diff = (target_date - last_date).days

            # Meaningful Validation Rejections
            if days_diff <= 0:
                return {
                    "error": (
                        f"Forecast date must be after the last available "
                        f"dataset date ({last_date.strftime('%d %b %Y')})."
                    )
                }

            if days_diff > 365:
                max_date = (
                    last_date + pd.Timedelta(days=365)
                ).strftime('%d %b %Y')

                return {
                    "error": (
                        "Forecast horizon exceeds the maximum limit of "
                        f"365 days (max date allowed: {max_date})."
                    )
                }

            # We still need to forecast recursively from the end
            # of the dataset up to the requested target date.
            horizon_int = days_diff

        except Exception:
            return {"error": "Invalid custom date format provided."}
    else:
        if horizon_int > 365:
            horizon_int = 365

    working_df = daily_data.copy()
    future_predictions = []

    # ----------------------------------------------------------------
    # Rolling-mean anchoring — Fix #1
    #
    # Without anchoring, Rolling_Mean_7 fills with predicted values
    # after 7 recursive steps and Rolling_Mean_30 after 30 steps.
    # Because predictions start lower than the preceding December peak,
    # this creates a self-reinforcing feedback loop that suppresses
    # weeks 6-8 of a 90-day forecast to unrealistically low levels.
    #
    # Fix: compute fixed anchors from the LAST ACTUAL historical values
    # before the loop begins, then override those two columns in the
    # feature vector at each step.  All lag features (Lag_1, Lag_7,
    # Lag_14, Lag_30) are left unchanged — they still propagate the
    # recursive prediction chain exactly as before.
    # ----------------------------------------------------------------
    _actual_rev       = daily_data["Revenue"].values
    rolling_anchor_7  = float(np.mean(_actual_rev[-7:]))
    rolling_anchor_30 = float(np.mean(_actual_rev[-30:]))

    X_cols = [
        "DayOfWeek", "Month", "DayOfMonth", "Quarter",
        "Lag_1", "Lag_7", "Lag_14", "Lag_30",
        "Rolling_Mean_7", "Rolling_Mean_30"
    ]

    for i in range(horizon_int):
        next_date = last_date + pd.Timedelta(days=i+1)

        # We append a dummy Revenue of 0.0 to prevent dropna() from stripping
        # the new row during feature generation. Because all lag and rolling
        # features use .shift(1), this row's own dummy value won't corrupt its features.
        new_row = pd.DataFrame([{"Order_Date": next_date, "Revenue": 0.0}])
        working_df = pd.concat([working_df, new_row], ignore_index=True)

        # Re-calculate features on the extended dataset
        feat_df = create_forecasting_features(working_df)

        # Extract the feature row for the new step and override the two rolling
        # means with the pre-computed historical anchors.  Lag features are taken
        # as-is from the recursive working dataframe.
        X_pred = feat_df.iloc[-1:][X_cols].copy()
        X_pred["Rolling_Mean_7"]  = rolling_anchor_7
        X_pred["Rolling_Mean_30"] = rolling_anchor_30

        # Predict the next step
        pred_val = model.predict(X_pred)[0]

        # Inject prediction back into working dataframe for next recursive step
        working_df.loc[working_df.index[-1], "Revenue"] = pred_val

        future_predictions.append({
            "Order_Date": next_date.strftime("%Y-%m-%d"),
            "Revenue": None,  # Explicitly null since this is future forecasting
            "Predicted_Revenue": float(pred_val)
        })
        
    # ---------------------------------------------------------
    # If a custom date was requested, return only the forecast
    # period represented by that requested date.
    #
    # Example:
    #   custom_date = 2027-02-28
    #
    # The model internally forecasts:
    #   2027-01-01 → 2027-02-28
    #
    # But the user asked for February 2027, so only return:
    #   2027-02-01 → 2027-02-28
    # ---------------------------------------------------------

    if custom_date:
        target_date = pd.to_datetime(custom_date)

        target_month_start = target_date.replace(day=1)

        future_predictions = [
            item
            for item in future_predictions
            if target_month_start
            <= pd.to_datetime(item["Order_Date"])
            <= target_date
        ]

    return future_predictions


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