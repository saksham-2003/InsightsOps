from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


def detect_transaction_anomalies(
    df,
    contamination=0.01
):
    """
    Detect unusual transactions using Isolation Forest.

    Returns:
        result_df: DataFrame with anomaly columns
        summary: Dictionary containing anomaly statistics
    """

    result_df = df.copy()

    features = [
        "Quantity",
        "Unit_Price",
        "Revenue",
        "Profit"
    ]

    # Select ML features
    X = result_df[features].copy()

    # Scale numerical values
    scaler = StandardScaler()

    X_scaled = scaler.fit_transform(X)


    # Build Isolation Forest model
    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=42,
        n_jobs=-1
    )


    # Train and predict
    predictions = model.fit_predict(X_scaled)

    anomaly_scores = model.decision_function(X_scaled)


    # Isolation Forest returns:
    #  1 = normal
    # -1 = anomaly

    result_df["Anomaly"] = predictions

    result_df["Anomaly_Score"] = anomaly_scores

    result_df["Is_Anomaly"] = (
        result_df["Anomaly"] == -1
    )


    anomaly_count = int(
        result_df["Is_Anomaly"].sum()
    )

    total_transactions = len(result_df)


    summary = {
        "total_transactions": total_transactions,

        "anomaly_count": anomaly_count,

        "anomaly_percentage": (
            anomaly_count / total_transactions
        ) * 100,

        "features_used": features
    }


    return result_df, summary