from typing import Optional

from fastapi import APIRouter, Depends, Query

from api.dependencies import get_cleaned_dataframe

from api.services.analytics_engine import (
    filter_dataframe,
    calculate_kpis,
    calculate_monthly_trend,
    calculate_category_summary,
    calculate_region_summary,
    calculate_top_products,
    generate_business_insights,
    get_filter_metadata,
    build_metadata,
)


router = APIRouter(
    prefix="/api/analytics",
    tags=["Analytics"]
)


def _filter_or_empty(df, year, month, region, category):
    """
    Shared filtering step for every endpoint in this router (STEP 1 + 12).

    Returns (filtered_df, empty_response). If a filter was actually
    supplied but matched zero rows, empty_response is a ready-to-return
    dict (success=True, empty=True, "No records found.") and the caller
    should return it immediately. If empty_response is None, the caller
    should proceed using filtered_df as normal — this covers both "no
    filters were passed" and "filters were passed and matched rows".
    """
    filtered_df = filter_dataframe(df, year=year, month=month, region=region, category=category)

    any_filter_applied = any(
        v is not None and str(v).strip().lower() not in ("", "all")
        for v in (year, month, region, category)
    )

    if any_filter_applied and filtered_df.empty:
        return filtered_df, {
            "success": True,
            "empty": True,
            "message": "No records found.",
            "data": None,
            "metadata": build_metadata(df, filtered_df, year, month, region, category),
        }

    return filtered_df, None


@router.get("/summary")
def get_business_summary(
    year: Optional[str] = Query(None),
    month: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    df=Depends(get_cleaned_dataframe),
):
    """Return overall business KPIs, optionally filtered."""
    filtered_df, empty_response = _filter_or_empty(df, year, month, region, category)
    if empty_response:
        return empty_response

    return {"success": True, "data": calculate_kpis(filtered_df)}


@router.get("/monthly-trend")
def get_monthly_trend(
    year: Optional[str] = Query(None),
    month: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    df=Depends(get_cleaned_dataframe),
):
    """Return monthly Revenue AND Profit trend, optionally filtered."""
    filtered_df, empty_response = _filter_or_empty(df, year, month, region, category)
    if empty_response:
        return empty_response

    return {"success": True, "data": calculate_monthly_trend(filtered_df)}


@router.get("/categories")
def get_category_performance(
    year: Optional[str] = Query(None),
    month: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    df=Depends(get_cleaned_dataframe),
):
    """Return category performance: Revenue, Profit, Units, Contribution %, Growth %."""
    filtered_df, empty_response = _filter_or_empty(df, year, month, region, category)
    if empty_response:
        return empty_response

    return {"success": True, "data": calculate_category_summary(filtered_df)}


@router.get("/regions")
def get_regional_performance(
    year: Optional[str] = Query(None),
    month: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    df=Depends(get_cleaned_dataframe),
):
    """Return regional performance: Revenue, Profit, Orders, Contribution %, Growth %."""
    filtered_df, empty_response = _filter_or_empty(df, year, month, region, category)
    if empty_response:
        return empty_response

    return {"success": True, "data": calculate_region_summary(filtered_df)}


@router.get("/top-products")
def get_top_products(
    year: Optional[str] = Query(None),
    month: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    df=Depends(get_cleaned_dataframe),
):
    """Return top products by revenue: Revenue, Profit, Units, Growth %, Ranking."""
    filtered_df, empty_response = _filter_or_empty(df, year, month, region, category)
    if empty_response:
        return empty_response

    return {"success": True, "data": calculate_top_products(filtered_df, limit=limit)}


@router.get("/dashboard-overview")
def get_dashboard_overview(
    year: Optional[str] = Query(None, description="e.g. 2024"),
    month: Optional[str] = Query(None, description="e.g. November"),
    region: Optional[str] = Query(None, description="e.g. East"),
    category: Optional[str] = Query(None, description="e.g. Electronics"),
    df=Depends(get_cleaned_dataframe),
):
    """
    Single source of truth for the Analytics workspace.

    Filters are applied ONCE, here, against the raw cleaned dataframe.
    Every downstream calculation — KPIs, monthly trend, category summary,
    region summary, top products, business insights — is derived from
    that SAME filtered dataframe. Nothing downstream re-filters an
    already-aggregated result, which is what made Region/Category filters
    unable to affect the monthly trend and Revenue/Profit toggle in the
    old architecture.
    """
    filtered_df, empty_response = _filter_or_empty(df, year, month, region, category)
    if empty_response:
        return empty_response

    kpis = calculate_kpis(filtered_df)
    monthly_trend = calculate_monthly_trend(filtered_df)
    categories_summary = calculate_category_summary(filtered_df)
    regions_summary = calculate_region_summary(filtered_df)
    top_products = calculate_top_products(filtered_df, limit=10)
    insights = generate_business_insights(monthly_trend, categories_summary, regions_summary, kpis)

    return {
        "success": True,
        "data": {
            "kpis": kpis,
            "monthly_trend": monthly_trend,
            "categories": categories_summary,
            "regions": regions_summary,
            "top_products": top_products,
            "insights": insights,
        },
        "filters_available": get_filter_metadata(df),
        "metadata": build_metadata(df, filtered_df, year, month, region, category),
    }