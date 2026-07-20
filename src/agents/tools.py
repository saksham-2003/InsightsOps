# src/agents/tools.py
from src.kpi_engine import calculate_kpis
from src.analyzer import generate_business_analysis
from api.services.analytics_engine import filter_dataframe
from src.ml.anomaly_detector import (
    detect_transaction_anomalies
)

from src.ml.forecaster import (
    train_revenue_forecaster,
    forecast_future_revenue
)


def get_kpi_summary(df):
    """
    Tool: Return overall business KPIs.
    """

    return calculate_kpis(df)


def get_monthly_trend(df):
    """
    Tool: Return monthly business performance.
    """

    analysis = generate_business_analysis(df)

    return analysis[
        "monthly_performance"
    ].to_dict(orient="records")


def get_category_performance(df):
    """
    Tool: Analyze category performance.
    """

    analysis = generate_business_analysis(df)

    return analysis[
        "category_performance"
    ].to_dict(orient="records")


def get_regional_performance(df):
    """
    Tool: Analyze regional performance.
    """

    analysis = generate_business_analysis(df)

    return analysis[
        "regional_performance"
    ].to_dict(orient="records")


def get_top_products(df):
    """
    Tool: Return top products by revenue.
    """

    analysis = generate_business_analysis(df)

    return analysis[
        "top_products"
    ].to_dict(orient="records")


def get_anomaly_summary(df):
    """
    Tool: Detect unusual transactions.
    """

    result_df, summary = (
        detect_transaction_anomalies(df)
    )

    top_anomalies = (
        result_df[
            result_df["Is_Anomaly"]
        ]
        .sort_values("Anomaly_Score")
        .head(10)
    )

    return {
        "summary": summary,

        "top_anomalies": top_anomalies[
            [
                "Order_ID",
                "Product_Name",
                "Quantity",
                "Unit_Price",
                "Revenue",
                "Profit",
                "Anomaly_Score"
            ]
        ].to_dict(orient="records")
    }


def get_forecast_evaluation(
    df,
    region=None,
    category=None,
    horizon=30,
    custom_date=None,
):
    """
    Tool: Train forecasting model and return evaluation + future forecast.
    """
    filtered_df = filter_dataframe(
        df,
        region=region,
        category=category
    )
    
    if filtered_df.empty:
        return {
            "success": False,
            "message": "No data available for the selected filters."
        }
        
    model, results, metrics = (
        train_revenue_forecaster(filtered_df)
    )
    
    future_forecast = forecast_future_revenue(
        model, 
        filtered_df, 
        horizon=horizon, 
        custom_date=custom_date
    )
    
    # Append the future forecast to the historical evaluation tail
    historical = results.tail(30).copy()
    historical["Order_Date"] = historical["Order_Date"].dt.strftime("%Y-%m-%d")
    historical_records = historical.to_dict(orient="records")

    return {
        "metrics": metrics,
        "predictions": historical_records + future_forecast
    }


def get_period_drilldown(df, month=None, year=None):
    """
    Tool: Analyze business performance for a specific
    month and/or year.
    """

    filtered_df = df.copy()

    if month is not None:
        filtered_df = filtered_df[
            filtered_df["Order_Date"].dt.month == month
        ]

    if year is not None:
        filtered_df = filtered_df[
            filtered_df["Order_Date"].dt.year == year
        ]

    if filtered_df.empty:
        return {
            "error": "No data found for the selected period."
        }


    category_analysis = (
        filtered_df.groupby("Category")
        .agg(
            Revenue=("Revenue", "sum"),
            Profit=("Profit", "sum"),
            Orders=("Order_ID", "nunique")
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )


    regional_analysis = (
        filtered_df.groupby("Region")
        .agg(
            Revenue=("Revenue", "sum"),
            Profit=("Profit", "sum"),
            Orders=("Order_ID", "nunique")
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )


    product_analysis = (
        filtered_df.groupby("Product_Name")
        .agg(
            Revenue=("Revenue", "sum"),
            Profit=("Profit", "sum"),
            Units_Sold=("Quantity", "sum")
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
        .head(10)
    )


    return {
        "filters": {
            "month": month,
            "year": year
        },

        "total_revenue": float(
            filtered_df["Revenue"].sum()
        ),

        "total_profit": float(
            filtered_df["Profit"].sum()
        ),

        "categories":
            category_analysis.to_dict(
                orient="records"
            ),

        "regions":
            regional_analysis.to_dict(
                orient="records"
            ),

        "top_products":
            product_analysis.to_dict(
                orient="records"
            )
    }

def get_region_drilldown(df, region):
    """
    Tool: Analyze categories and products
    inside a specific region.
    """

    filtered_df = df[
        df["Region"].str.lower()
        == region.lower()
    ].copy()


    if filtered_df.empty:

        return {
            "error": f"No data found for region: {region}"
        }


    category_analysis = (
        filtered_df.groupby("Category")
        .agg(
            Revenue=("Revenue", "sum"),
            Profit=("Profit", "sum"),
            Orders=("Order_ID", "nunique")
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )


    product_analysis = (
        filtered_df.groupby("Product_Name")
        .agg(
            Revenue=("Revenue", "sum"),
            Profit=("Profit", "sum"),
            Units_Sold=("Quantity", "sum")
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
        .head(10)
    )


    return {
        "region": region,

        "total_revenue": float(
            filtered_df["Revenue"].sum()
        ),

        "total_profit": float(
            filtered_df["Profit"].sum()
        ),

        "categories":
            category_analysis.to_dict(
                orient="records"
            ),

        "top_products":
            product_analysis.to_dict(
                orient="records"
            )
    }

def get_context_drilldown(
    df,
    month=None,
    year=None,
    region=None
):
    """
    Analyze a filtered business context using optional
    month, year, and region filters.
    """

    filtered_df = df.copy()

    if month is not None:
        filtered_df = filtered_df[
            filtered_df["Order_Date"].dt.month == month
        ]

    if year is not None:
        filtered_df = filtered_df[
            filtered_df["Order_Date"].dt.year == year
        ]

    if region is not None:
        filtered_df = filtered_df[
            filtered_df["Region"].str.lower()
            == region.lower()
        ]

    if filtered_df.empty:
        return {
            "error": "No data found for the selected context."
        }


    category_analysis = (
        filtered_df.groupby("Category")
        .agg(
            Revenue=("Revenue", "sum"),
            Profit=("Profit", "sum"),
            Orders=("Order_ID", "nunique"),
            Units_Sold=("Quantity", "sum")
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )


    regional_analysis = (
        filtered_df.groupby("Region")
        .agg(
            Revenue=("Revenue", "sum"),
            Profit=("Profit", "sum"),
            Orders=("Order_ID", "nunique"),
            Units_Sold=("Quantity", "sum")
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )


    product_analysis = (
        filtered_df.groupby("Product_Name")
        .agg(
            Revenue=("Revenue", "sum"),
            Profit=("Profit", "sum"),
            Units_Sold=("Quantity", "sum")
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
        .head(10)
    )


    return {

        "filters": {
            "month": month,
            "year": year,
            "region": region
        },

        "transaction_count": int(len(filtered_df)),

        "total_revenue": float(
            filtered_df["Revenue"].sum()
        ),

        "total_profit": float(
            filtered_df["Profit"].sum()
        ),

        "total_units": int(
            filtered_df["Quantity"].sum()
        ),

        "categories":
            category_analysis.to_dict(
                orient="records"
            ),

        "regions":
            regional_analysis.to_dict(
                orient="records"
            ),

        "top_products":
            product_analysis.to_dict(
                orient="records"
            )
    }

TOOL_REGISTRY = {

    "kpi_summary": get_kpi_summary,

    "monthly_trend": get_monthly_trend,

    "category_performance":
        get_category_performance,

    "regional_performance":
        get_regional_performance,

    "top_products": get_top_products,

    "anomaly_detection":
        get_anomaly_summary,

    "forecast_evaluation":
        get_forecast_evaluation,

    "period_drilldown":
        get_period_drilldown,

    "region_drilldown":
        get_region_drilldown,

    "context_drilldown": 
        get_context_drilldown
}