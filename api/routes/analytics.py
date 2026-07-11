from fastapi import APIRouter, Depends

from api.dependencies import (
    get_cleaned_dataframe
)

from src.agents.tools import (
    TOOL_REGISTRY
)


router = APIRouter(
    prefix="/api/analytics",
    tags=["Analytics"]
)


@router.get("/summary")
def get_business_summary(
    df=Depends(get_cleaned_dataframe)
):
    """
    Return overall business KPIs.
    """

    result = TOOL_REGISTRY[
        "kpi_summary"
    ](df)

    return {
        "success": True,
        "data": result
    }


@router.get("/monthly-trend")
def get_monthly_trend(
    df=Depends(get_cleaned_dataframe)
):
    """
    Return monthly revenue, profit,
    orders, and units sold.
    """

    result = TOOL_REGISTRY[
        "monthly_trend"
    ](df)

    return {
        "success": True,
        "data": result
    }


@router.get("/categories")
def get_category_performance(
    df=Depends(get_cleaned_dataframe)
):
    """
    Return category performance.
    """

    result = TOOL_REGISTRY[
        "category_performance"
    ](df)

    return {
        "success": True,
        "data": result
    }


@router.get("/regions")
def get_regional_performance(
    df=Depends(get_cleaned_dataframe)
):
    """
    Return regional performance.
    """

    result = TOOL_REGISTRY[
        "regional_performance"
    ](df)

    return {
        "success": True,
        "data": result
    }


@router.get("/top-products")
def get_top_products(
    df=Depends(get_cleaned_dataframe)
):
    """
    Return top products by revenue.
    """

    result = TOOL_REGISTRY[
        "top_products"
    ](df)

    return {
        "success": True,
        "data": result
    }
@router.get("/dashboard-overview")
def get_dashboard_overview(
    df=Depends(get_cleaned_dataframe)
):
    """
    Return the main data needed for the
    initial dashboard view.
    """

    kpis = TOOL_REGISTRY[
        "kpi_summary"
    ](df)

    monthly_trend = TOOL_REGISTRY[
        "monthly_trend"
    ](df)

    categories = TOOL_REGISTRY[
        "category_performance"
    ](df)

    regions = TOOL_REGISTRY[
        "regional_performance"
    ](df)

    top_products = TOOL_REGISTRY[
        "top_products"
    ](df)


    return {
        "success": True,

        "data": {
            "kpis": kpis,

            "monthly_trend":
                monthly_trend,

            "categories":
                categories,

            "regions":
                regions,

            "top_products":
                top_products[:10]
        }
    }