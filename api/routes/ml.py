from fastapi import APIRouter, Depends

from api.dependencies import (
    get_cleaned_dataframe
)

from src.agents.tools import (
    TOOL_REGISTRY
)


router = APIRouter(
    prefix="/api/ml",
    tags=["Machine Learning"]
)


@router.get("/anomalies")
def get_anomalies(
    df=Depends(get_cleaned_dataframe)
):
    """
    Return anomaly detection summary
    and the top unusual transactions.
    """

    result = TOOL_REGISTRY[
        "anomaly_detection"
    ](df)

    return {
        "success": True,
        "data": result
    }


@router.get("/forecast-evaluation")
def get_forecast_evaluation(
    df=Depends(get_cleaned_dataframe)
):
    """
    Return revenue forecasting model
    evaluation metrics and predictions.
    """

    result = TOOL_REGISTRY[
        "forecast_evaluation"
    ](df)

    return {
        "success": True,
        "data": result
    }