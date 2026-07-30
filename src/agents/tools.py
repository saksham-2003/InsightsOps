# src/agents/tools.py
import pandas as pd
import numpy as np
from src.kpi_engine import calculate_kpis
from src.analyzer import generate_business_analysis
from api.services.analytics_engine import (
    filter_dataframe,
    calculate_top_products,
    calculate_bottom_products
)
from src.ml.anomaly_detector import (
    detect_transaction_anomalies
)

from src.ml.forecaster import (
    train_revenue_forecaster,
    forecast_future_revenue
)

# Global cache to prevent retraining IsolationForest on the same dataset across requests
_ANOMALY_CACHE = {"df_id": None, "result": None}

def get_anomaly_summary(
    df, 
    region=None, 
    category=None, 
    start_date=None, 
    end_date=None, 
    severity=None, 
    search=None,
    sub_category=None,
    country=None,
    state=None,
    city=None,
    product=None,
    customer=None,
    year=None,
    month=None
):
    """
    Tool: Detect unusual transactions and return highly structured BI data.
    Implements caching, dynamic filtering, rule-based explanation, and severity grading.
    """
    global _ANOMALY_CACHE
    
    # Do NOT retrain if the underlying dataset hasn't changed in memory
    if _ANOMALY_CACHE["df_id"] == id(df):
        result_df, global_summary = _ANOMALY_CACHE["result"]
    else:
        result_df, global_summary = detect_transaction_anomalies(df)
        _ANOMALY_CACHE["df_id"] = id(df)
        _ANOMALY_CACHE["result"] = (result_df, global_summary)

    # 1. Base Filters (using filter_dataframe for consistency)
    filtered_df = filter_dataframe(
        result_df, 
        year=year,
        month=month,
        region=region,
        category=category,
        sub_category=sub_category,
        country=country,
        state=state,
        city=city,
        product=product,
        customer=customer,
        start_date=start_date,
        end_date=end_date
    )

    # 2. Search Filter (Product Name)
    if search:
        filtered_df = filtered_df[filtered_df["Product_Name"].str.contains(search, case=False, na=False)]

    # 3. Severity Scoring
    # In IsolationForest, lower decision function scores indicate stronger anomalies.
    # We map this globally so 100 = most anomalous, 0 = least anomalous.
    anomalies_global = result_df[result_df["Is_Anomaly"]].copy()
    if not anomalies_global.empty:
        min_score = anomalies_global["Anomaly_Score"].min()
        max_score = anomalies_global["Anomaly_Score"].max()
        
        def calc_severity(s):
            if max_score == min_score: return 100.0
            return ((max_score - s) / (max_score - min_score)) * 100.0
    else:
        def calc_severity(s): return 0.0

    filtered_anomalies = filtered_df[filtered_df["Is_Anomaly"]].copy()
    filtered_normals = filtered_df[~filtered_df["Is_Anomaly"]].copy()

    if not filtered_anomalies.empty:
        filtered_anomalies["Severity_Score"] = filtered_anomalies["Anomaly_Score"].apply(calc_severity)
        
        def get_severity_label(s):
            if s >= 75: return "Critical"
            if s >= 50: return "High"
            if s >= 25: return "Medium"
            return "Low"
            
        filtered_anomalies["Severity"] = filtered_anomalies["Severity_Score"].apply(get_severity_label)
    else:
        filtered_anomalies["Severity_Score"] = []
        filtered_anomalies["Severity"] = []

    # 4. Severity Filter
    if severity and severity.lower() != "all":
        filtered_anomalies = filtered_anomalies[filtered_anomalies["Severity"].str.lower() == severity.lower()]

    # 5. Rule-Based AI Explanations
    med_rev = df["Revenue"].median() if "Revenue" in df else 0
    med_prof = df["Profit"].median() if "Profit" in df else 0
    med_qty = df["Quantity"].median() if "Quantity" in df else 0

    reasons = []
    for _, row in filtered_anomalies.iterrows():
        r = []
        if "Revenue" in row and row["Revenue"] > med_rev * 3:
            r.append("Revenue unusually high compared to historical trend.")
        elif "Revenue" in row and row["Revenue"] < med_rev * 0.1:
            r.append("Revenue suspiciously low.")
            
        if "Profit" in row and row["Profit"] < 0:
            r.append("Transaction resulted in a significant loss.")
        elif "Profit" in row and row["Profit"] < med_prof * 0.2 and row["Revenue"] > med_rev:
            r.append("Profit margin remarkably lower than expected for revenue volume.")
            
        if "Quantity" in row and row["Quantity"] > med_qty * 4:
            r.append("Quantity unusually large (potential bulk anomaly).")
            
        if not r:
            r.append("Statistical outlier detected across multiple structural dimensions.")
            
        reasons.append(" ".join(r))
        
    filtered_anomalies["Reason"] = reasons

    # 6. Aggregations & Metrics
    total_tx = len(filtered_df)
    total_anom = len(filtered_anomalies)
    total_norm = len(filtered_normals)
    anom_pct = (total_anom / total_tx * 100) if total_tx > 0 else 0

    avg_rev = float(filtered_df["Revenue"].mean()) if "Revenue" in filtered_df and not filtered_df.empty else 0.0
    avg_prof = float(filtered_df["Profit"].mean()) if "Profit" in filtered_df and not filtered_df.empty else 0.0

    # Executive Summary Data
    highest_score = float(filtered_anomalies["Severity_Score"].max()) if not filtered_anomalies.empty else 0.0
    most_affected_region = filtered_anomalies["Region"].mode()[0] if "Region" in filtered_anomalies and not filtered_anomalies.empty else "N/A"
    most_affected_category = filtered_anomalies["Category"].mode()[0] if "Category" in filtered_anomalies and not filtered_anomalies.empty else "N/A"
    avg_anom_val = float(filtered_anomalies["Revenue"].mean()) if "Revenue" in filtered_anomalies and not filtered_anomalies.empty else 0.0

    bus_risk = "Critical" if anom_pct > 5 else "High" if anom_pct > 2 else "Medium" if anom_pct > 0.5 else "Low"

    executive_summary = {
        "total_anomalies": total_anom,
        "anomaly_percentage": anom_pct,
        "highest_score": highest_score,
        "most_affected_region": most_affected_region,
        "most_affected_category": most_affected_category,
        "avg_anomaly_value": avg_anom_val,
        "business_risk": bus_risk
    }

    kpis = {
        "total_transactions": total_tx,
        "normal_records": total_norm,
        "anomalies": total_anom,
        "anomaly_percentage": anom_pct,
        "average_revenue": avg_rev,
        "average_profit": avg_prof
    }

    # 7. Charts
    monthly_trend = []
    if not filtered_anomalies.empty and "Order_Date" in filtered_anomalies:
        monthly = filtered_anomalies.copy()
        monthly["Month"] = monthly["Order_Date"].dt.strftime("%Y-%m")
        m_trend = monthly.groupby("Month").size().reset_index(name="Count")
        monthly_trend = m_trend.to_dict(orient="records")

    region_dist = []
    if not filtered_anomalies.empty and "Region" in filtered_anomalies:
        r_dist = filtered_anomalies.groupby("Region").size().reset_index(name="Count")
        region_dist = r_dist.to_dict(orient="records")

    category_dist = []
    if not filtered_anomalies.empty and "Category" in filtered_anomalies:
        c_dist = filtered_anomalies.groupby("Category").size().reset_index(name="Count")
        category_dist = c_dist.to_dict(orient="records")

    severity_dist = []
    if not filtered_anomalies.empty:
        s_dist = filtered_anomalies.groupby("Severity").size().reset_index(name="Count")
        severity_dist = s_dist.to_dict(orient="records")

    top_products = []
    if not filtered_anomalies.empty and "Product_Name" in filtered_anomalies:
        p_dist = filtered_anomalies.groupby("Product_Name").size().reset_index(name="Count").sort_values("Count", ascending=False).head(10)
        top_products = p_dist.to_dict(orient="records")

    charts = {
        "monthly_trend": monthly_trend,
        "region_distribution": region_dist,
        "category_distribution": category_dist,
        "severity_distribution": severity_dist,
        "top_products": top_products
    }

    # 8. Business Recommendations
    recs = []
    if total_anom > 0:
        recs.append("Audit the flagged suspicious transactions in the detailed table immediately.")
        if highest_score > 80:
            recs.append("Critical severity anomalies detected. Isolate these transactions for manual fraud/error review.")
        if most_affected_category != "N/A":
            recs.append(f"Investigate pricing mechanisms and inventory strategy for the '{most_affected_category}' category.")
        if most_affected_region != "N/A":
            recs.append(f"Review supplier costs, shipping anomalies, and local operations in the '{most_affected_region}' region.")
        loss_anoms = len(filtered_anomalies[filtered_anomalies.get("Profit", 0) < 0])
        if loss_anoms > 0:
            recs.append(f"{loss_anoms} structural anomalies resulted in an overall profit loss. Verify discount rules and cost reporting.")

    # 9. Table Data Formatting
    table_data = []
    if not filtered_anomalies.empty:
        df_to_export = filtered_anomalies.sort_values("Severity_Score", ascending=False).copy()
        df_to_export["Order_Date"] = df_to_export["Order_Date"].dt.strftime("%Y-%m-%d")
        df_to_export = df_to_export.fillna("")
        cols_needed = ["Order_Date", "Region", "Category", "Product_Name", "Revenue", "Profit", "Severity_Score", "Severity", "Reason", "Order_ID"]
        cols_available = [c for c in cols_needed if c in df_to_export.columns]
        table_data = df_to_export[cols_available].to_dict(orient="records")

    unique_regions = df["Region"].dropna().unique().tolist() if "Region" in df else []
    unique_categories = df["Category"].dropna().unique().tolist() if "Category" in df else []

    return {
        "success": True,
        "data": {
            "executive_summary": executive_summary,
            "kpis": kpis,
            "charts": charts,
            "table_data": table_data,
            "recommendations": recs,
            "filter_options": {
                "regions": unique_regions,
                "categories": unique_categories
            }
        }
    }


def get_kpi_summary(
    df,
    year=None,
    month=None,
    region=None,
    category=None,
    sub_category=None,
    country=None,
    state=None,
    city=None,
    product=None,
    customer=None,
    start_date=None,
    end_date=None
):
    """
    Tool: Return overall business KPIs.
    """
    filtered_df = filter_dataframe(
        df,
        year=year,
        month=month,
        region=region,
        category=category,
        sub_category=sub_category,
        country=country,
        state=state,
        city=city,
        product=product,
        customer=customer,
        start_date=start_date,
        end_date=end_date
    )

    if filtered_df.empty:
        return {
            "success": False,
            "message": "No matching records were found for the specified filters."
        }

    return calculate_kpis(filtered_df)


def get_monthly_trend(
    df,
    year=None,
    month=None,
    region=None,
    category=None,
    sub_category=None,
    country=None,
    state=None,
    city=None,
    product=None,
    customer=None,
    start_date=None,
    end_date=None
):
    """
    Tool: Return monthly business performance.
    """
    filtered_df = filter_dataframe(
        df,
        year=year,
        month=month,
        region=region,
        category=category,
        sub_category=sub_category,
        country=country,
        state=state,
        city=city,
        product=product,
        customer=customer,
        start_date=start_date,
        end_date=end_date
    )

    if filtered_df.empty:
        return {
            "success": False,
            "message": "No matching records were found for the specified filters."
        }

    analysis = generate_business_analysis(filtered_df)
    return analysis["monthly_performance"].to_dict(orient="records")


def get_category_performance(
    df,
    year=None,
    month=None,
    region=None,
    category=None,
    sub_category=None,
    country=None,
    state=None,
    city=None,
    product=None,
    customer=None,
    start_date=None,
    end_date=None
):
    """
    Tool: Analyze category performance.
    """
    filtered_df = filter_dataframe(
        df,
        year=year,
        month=month,
        region=region,
        category=category,
        sub_category=sub_category,
        country=country,
        state=state,
        city=city,
        product=product,
        customer=customer,
        start_date=start_date,
        end_date=end_date
    )

    if filtered_df.empty:
        return {
            "success": False,
            "message": "No matching records were found for the specified filters."
        }

    analysis = generate_business_analysis(filtered_df)
    return analysis["category_performance"].to_dict(orient="records")


def get_regional_performance(
    df,
    year=None,
    month=None,
    region=None,
    category=None,
    sub_category=None,
    country=None,
    state=None,
    city=None,
    product=None,
    customer=None,
    start_date=None,
    end_date=None
):
    """
    Tool: Analyze regional performance.
    """
    filtered_df = filter_dataframe(
        df,
        year=year,
        month=month,
        region=region,
        category=category,
        sub_category=sub_category,
        country=country,
        state=state,
        city=city,
        product=product,
        customer=customer,
        start_date=start_date,
        end_date=end_date
    )

    if filtered_df.empty:
        return {
            "success": False,
            "message": "No matching records were found for the specified filters."
        }

    analysis = generate_business_analysis(filtered_df)
    return analysis["regional_performance"].to_dict(orient="records")


def get_top_products(
    df,
    year=None,
    month=None,
    region=None,
    category=None,
    sub_category=None,
    country=None,
    state=None,
    city=None,
    product=None,
    customer=None,
    start_date=None,
    end_date=None
):
    """
    Tool: Return top products by revenue.
    """
    filtered_df = filter_dataframe(
        df,
        year=year,
        month=month,
        region=region,
        category=category,
        sub_category=sub_category,
        country=country,
        state=state,
        city=city,
        product=product,
        customer=customer,
        start_date=start_date,
        end_date=end_date
    )

    if filtered_df.empty:
        return {
            "success": False,
            "message": "No matching records were found for the specified filters."
        }

    analysis = generate_business_analysis(filtered_df)
    return analysis["top_products"].to_dict(orient="records")

def get_bottom_products(
    df,
    year=None,
    month=None,
    region=None,
    category=None,
    sub_category=None,
    country=None,
    state=None,
    city=None,
    product=None,
    customer=None,
    start_date=None,
    end_date=None
):
    """
    Tool: Return bottom (worst-performing) products by revenue and profit.
    """
    filtered_df = filter_dataframe(
        df,
        year=year,
        month=month,
        region=region,
        category=category,
        sub_category=sub_category,
        country=country,
        state=state,
        city=city,
        product=product,
        customer=customer,
        start_date=start_date,
        end_date=end_date
    )

    if filtered_df.empty:
        return {
            "success": False,
            "message": "No matching records were found for the specified filters."
        }

    
    return calculate_bottom_products(filtered_df)


def get_forecast_evaluation(
    df,
    region=None,
    category=None,
    horizon=30,
    custom_date=None,
    sub_category=None,
    country=None,
    state=None,
    city=None,
    product=None,
    customer=None,
    year=None,
    month=None,
    start_date=None,
    end_date=None
):
    """
    Tool: Train forecasting model and return evaluation + future forecast.
    """
    filtered_df = filter_dataframe(
        df,
        year=year,
        month=month,
        region=region,
        category=category,
        sub_category=sub_category,
        country=country,
        state=state,
        city=city,
        product=product,
        customer=customer,
        start_date=start_date,
        end_date=end_date
    )
    
    if filtered_df.empty:
        return {
            "success": False,
            "message": "No data available for the selected filters."
        }
        
    model, results, metrics = train_revenue_forecaster(filtered_df)
    
    future_forecast = forecast_future_revenue(
        model, 
        filtered_df, 
        horizon=horizon, 
        custom_date=custom_date
    )
    
    if isinstance(future_forecast, dict) and "error" in future_forecast:
        return {
            "success": False,
            "message": future_forecast["error"]
        }
    
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
        filtered_df = filtered_df[filtered_df["Order_Date"].dt.month == month]

    if year is not None:
        filtered_df = filtered_df[filtered_df["Order_Date"].dt.year == year]

    if filtered_df.empty:
        return {"error": "No data found for the selected period."}

    category_analysis = (
        filtered_df.groupby("Category")
        .agg(Revenue=("Revenue", "sum"), Profit=("Profit", "sum"), Orders=("Order_ID", "nunique"))
        .reset_index().sort_values("Revenue", ascending=False)
    )

    regional_analysis = (
        filtered_df.groupby("Region")
        .agg(Revenue=("Revenue", "sum"), Profit=("Profit", "sum"), Orders=("Order_ID", "nunique"))
        .reset_index().sort_values("Revenue", ascending=False)
    )

    product_analysis = (
        filtered_df.groupby("Product_Name")
        .agg(Revenue=("Revenue", "sum"), Profit=("Profit", "sum"), Units_Sold=("Quantity", "sum"))
        .reset_index().sort_values("Revenue", ascending=False).head(10)
    )

    return {
        "filters": {"month": month, "year": year},
        "total_revenue": float(filtered_df["Revenue"].sum()),
        "total_profit": float(filtered_df["Profit"].sum()),
        "categories": category_analysis.to_dict(orient="records"),
        "regions": regional_analysis.to_dict(orient="records"),
        "top_products": product_analysis.to_dict(orient="records")
    }

def get_region_drilldown(df, region):
    """
    Tool: Analyze categories and products
    inside a specific region.
    """
    filtered_df = df[df["Region"].str.lower() == region.lower()].copy()

    if filtered_df.empty:
        return {"error": f"No data found for region: {region}"}

    category_analysis = (
        filtered_df.groupby("Category")
        .agg(Revenue=("Revenue", "sum"), Profit=("Profit", "sum"), Orders=("Order_ID", "nunique"))
        .reset_index().sort_values("Revenue", ascending=False)
    )

    product_analysis = (
        filtered_df.groupby("Product_Name")
        .agg(Revenue=("Revenue", "sum"), Profit=("Profit", "sum"), Units_Sold=("Quantity", "sum"))
        .reset_index().sort_values("Revenue", ascending=False).head(10)
    )

    return {
        "region": region,
        "total_revenue": float(filtered_df["Revenue"].sum()),
        "total_profit": float(filtered_df["Profit"].sum()),
        "categories": category_analysis.to_dict(orient="records"),
        "top_products": product_analysis.to_dict(orient="records")
    }

def get_context_drilldown(df, month=None, year=None, region=None):
    """
    Analyze a filtered business context using optional
    month, year, and region filters.
    """
    filtered_df = df.copy()

    if month is not None:
        filtered_df = filtered_df[filtered_df["Order_Date"].dt.month == month]

    if year is not None:
        filtered_df = filtered_df[filtered_df["Order_Date"].dt.year == year]

    if region is not None:
        filtered_df = filtered_df[filtered_df["Region"].str.lower() == region.lower()]

    if filtered_df.empty:
        return {"error": "No data found for the selected context."}

    category_analysis = (
        filtered_df.groupby("Category")
        .agg(Revenue=("Revenue", "sum"), Profit=("Profit", "sum"), Orders=("Order_ID", "nunique"), Units_Sold=("Quantity", "sum"))
        .reset_index().sort_values("Revenue", ascending=False)
    )

    regional_analysis = (
        filtered_df.groupby("Region")
        .agg(Revenue=("Revenue", "sum"), Profit=("Profit", "sum"), Orders=("Order_ID", "nunique"), Units_Sold=("Quantity", "sum"))
        .reset_index().sort_values("Revenue", ascending=False)
    )

    product_analysis = (
        filtered_df.groupby("Product_Name")
        .agg(Revenue=("Revenue", "sum"), Profit=("Profit", "sum"), Units_Sold=("Quantity", "sum"))
        .reset_index().sort_values("Revenue", ascending=False).head(10)
    )

    return {
        "filters": {"month": month, "year": year, "region": region},
        "transaction_count": int(len(filtered_df)),
        "total_revenue": float(filtered_df["Revenue"].sum()),
        "total_profit": float(filtered_df["Profit"].sum()),
        "total_units": int(filtered_df["Quantity"].sum()),
        "categories": category_analysis.to_dict(orient="records"),
        "regions": regional_analysis.to_dict(orient="records"),
        "top_products": product_analysis.to_dict(orient="records")
    }

TOOL_REGISTRY = {
    "kpi_summary": get_kpi_summary,
    "monthly_trend": get_monthly_trend,
    "category_performance": get_category_performance,
    "regional_performance": get_regional_performance,
    "top_products": get_top_products,
    "bottom_products": get_bottom_products,
    "anomaly_detection": get_anomaly_summary,
    "forecast_evaluation": get_forecast_evaluation,
    "period_drilldown": get_period_drilldown,
    "region_drilldown": get_region_drilldown,
    "context_drilldown": get_context_drilldown
}