"""
Analytics calculation engine for InsightsOps.

This module is the single source of truth for all Analytics-related
filtering and aggregation. Every endpoint in api/routes/analytics.py
filters the raw dataframe ONCE via `filter_dataframe()`, then derives
every downstream result (KPIs, monthly trend, category/region summaries,
top products, business insights) from that SAME filtered dataframe.

Nothing in this module ever filters an already-aggregated result — that
was the architectural problem being replaced.

ASSUMED SCHEMA (post data_cleaner.clean_data underscore-normalization):

    Order_Date   : datetime64  (converted by data_cleaner.clean_data)
    Region       : str
    Category     : str
    Product_Name : str
    Order_ID     : str / int
    Quantity     : numeric
    Unit_Price   : numeric
    Revenue      : numeric
    Profit       : numeric
    Customer_ID  : str / int   (OPTIONAL — customer_count degrades to
                   None automatically if this column is absent, rather
                   than crashing or fabricating a count)

I inferred this schema from the fields already flowing through the
existing frontend (Order_ID/Product_Name/Quantity/Unit_Price/Revenue/
Profit appear in the Anomalies response; Region/Category/Revenue appear
in the existing regions/categories responses). If your actual column
names differ, update the COL_* constants below — every function reads
through those constants rather than hardcoding column names inline, so
a schema change only has to happen in one place.
"""

from datetime import datetime, timezone

import pandas as pd

# ---------------------------------------------------------------------------
# Column name constants — the ONE place to edit if your schema differs.
# ---------------------------------------------------------------------------
COL_DATE = "Order_Date"
COL_REGION = "Region"
COL_CATEGORY = "Category"
COL_PRODUCT = "Product_Name"
COL_ORDER_ID = "Order_ID"
COL_QUANTITY = "Quantity"
COL_UNIT_PRICE = "Unit_Price"
COL_REVENUE = "Revenue"
COL_PROFIT = "Profit"
COL_CUSTOMER = "Customer_ID"  # optional


def _has(df, col):
    return col in df.columns


def _is_empty_filter(value):
    """A filter is "not applied" if it's None, empty, or the literal 'all'."""
    return value is None or (isinstance(value, str) and value.strip().lower() in ("", "all"))


# ---------------------------------------------------------------------------
# STEP 1 — Reusable filtering engine
# ---------------------------------------------------------------------------
def filter_dataframe(df, year=None, month=None, region=None, category=None):
    """
    Filter the dataframe by any combination of optional filters.

    - Filters that are None / "" / "all" (case-insensitive) are ignored.
    - Invalid or unparseable values (e.g. year="banana") are treated as
      "this filter matches zero rows" rather than raising — the request
      never crashes, it just returns an empty result for that filter.
    - Always returns a NEW DataFrame; the input is never mutated, which
      matters because get_cleaned_dataframe() is an lru_cache singleton
      shared across every request.
    """
    filtered = df.copy()

    if not _is_empty_filter(year) and _has(filtered, COL_DATE):
        try:
            year_int = int(year)
            filtered = filtered[filtered[COL_DATE].dt.year == year_int]
        except (ValueError, TypeError, AttributeError):
            filtered = filtered.iloc[0:0]

    if not _is_empty_filter(month) and _has(filtered, COL_DATE):
        try:
            month_str = str(month).strip()
            month_num = int(month_str) if month_str.isdigit() else datetime.strptime(month_str[:3], "%b").month
            filtered = filtered[filtered[COL_DATE].dt.month == month_num]
        except (ValueError, TypeError, AttributeError):
            filtered = filtered.iloc[0:0]

    if not _is_empty_filter(region) and _has(filtered, COL_REGION):
        filtered = filtered[
            filtered[COL_REGION].astype(str).str.strip().str.lower() == str(region).strip().lower()
        ]

    if not _is_empty_filter(category) and _has(filtered, COL_CATEGORY):
        filtered = filtered[
            filtered[COL_CATEGORY].astype(str).str.strip().str.lower() == str(category).strip().lower()
        ]

    return filtered


# ---------------------------------------------------------------------------
# STEP 4 — KPIs
# ---------------------------------------------------------------------------
def calculate_kpis(df):
    """Revenue, Profit, Orders, Margin, AOV, Units, Top Category/Region, Customers."""
    if df.empty:
        return {
            "total_revenue": 0.0,
            "total_profit": 0.0,
            "total_orders": 0,
            "profit_margin": 0.0,
            "average_order_value": 0.0,
            "units_sold": 0.0 if _has(df, COL_QUANTITY) else None,
            "top_category": None,
            "top_region": None,
            "customer_count": None,
        }

    total_revenue = float(df[COL_REVENUE].sum()) if _has(df, COL_REVENUE) else 0.0
    total_profit = float(df[COL_PROFIT].sum()) if _has(df, COL_PROFIT) else 0.0
    total_orders = int(df[COL_ORDER_ID].nunique()) if _has(df, COL_ORDER_ID) else len(df)
    units_sold = float(df[COL_QUANTITY].sum()) if _has(df, COL_QUANTITY) else None

    profit_margin = (total_profit / total_revenue * 100) if total_revenue else 0.0
    average_order_value = (total_revenue / total_orders) if total_orders else 0.0

    top_category = None
    if _has(df, COL_CATEGORY) and _has(df, COL_REVENUE):
        totals = df.groupby(COL_CATEGORY)[COL_REVENUE].sum()
        if not totals.empty:
            top_category = totals.idxmax()

    top_region = None
    if _has(df, COL_REGION) and _has(df, COL_REVENUE):
        totals = df.groupby(COL_REGION)[COL_REVENUE].sum()
        if not totals.empty:
            top_region = totals.idxmax()

    customer_count = int(df[COL_CUSTOMER].nunique()) if _has(df, COL_CUSTOMER) else None

    return {
        "total_revenue": round(total_revenue, 2),
        "total_profit": round(total_profit, 2),
        "total_orders": total_orders,
        "profit_margin": round(profit_margin, 2),
        "average_order_value": round(average_order_value, 2),
        "units_sold": units_sold,
        "top_category": top_category,
        "top_region": top_region,
        "customer_count": customer_count,
    }


# ---------------------------------------------------------------------------
# Shared helper — month-over-month growth % per group (category / region /
# product), based on the two most recent months PRESENT IN THE FILTERED
# DATA. Returns {} if fewer than two distinct months exist, since growth
# genuinely cannot be computed from a single period — this returns None
# per-group in that case rather than fabricating a number.
# ---------------------------------------------------------------------------
def _growth_by_group(df, group_col):
    if not _has(df, COL_DATE) or not _has(df, group_col) or not _has(df, COL_REVENUE):
        return {}

    working = df.copy()
    working["_period"] = working[COL_DATE].dt.to_period("M")
    periods = sorted(working["_period"].dropna().unique())

    if len(periods) < 2:
        return {}

    latest, previous = periods[-1], periods[-2]
    latest_totals = working[working["_period"] == latest].groupby(group_col)[COL_REVENUE].sum()
    previous_totals = working[working["_period"] == previous].groupby(group_col)[COL_REVENUE].sum()

    growth = {}
    for key in set(latest_totals.index) | set(previous_totals.index):
        prev_val = previous_totals.get(key, 0)
        latest_val = latest_totals.get(key, 0)
        growth[key] = round(float((latest_val - prev_val) / prev_val * 100), 2) if prev_val else None

    return growth


# ---------------------------------------------------------------------------
# STEP 5 — Monthly Trend (Revenue AND Profit, powering the frontend toggle)
# ---------------------------------------------------------------------------
def calculate_monthly_trend(df):
    if df.empty or not _has(df, COL_DATE):
        return []

    working = df.copy()
    working["_period"] = working[COL_DATE].dt.to_period("M")

    agg_cols = {}
    if _has(working, COL_REVENUE):
        agg_cols[COL_REVENUE] = "sum"
    if _has(working, COL_PROFIT):
        agg_cols[COL_PROFIT] = "sum"

    if not agg_cols:
        return []

    grouped = working.groupby("_period").agg(agg_cols).reset_index().sort_values("_period")

    result = []
    for _, row in grouped.iterrows():
        entry = {"Order_Date": row["_period"].strftime("%b %Y")}
        if COL_REVENUE in agg_cols:
            entry["Revenue"] = round(float(row[COL_REVENUE]), 2)
        if COL_PROFIT in agg_cols:
            entry["Profit"] = round(float(row[COL_PROFIT]), 2)
        result.append(entry)

    return result


# ---------------------------------------------------------------------------
# STEP 6 — Category Summary
# ---------------------------------------------------------------------------
def calculate_category_summary(df):
    if df.empty or not _has(df, COL_CATEGORY) or not _has(df, COL_REVENUE):
        return []

    total_revenue = float(df[COL_REVENUE].sum())

    agg_cols = {COL_REVENUE: "sum"}
    if _has(df, COL_PROFIT):
        agg_cols[COL_PROFIT] = "sum"
    if _has(df, COL_QUANTITY):
        agg_cols[COL_QUANTITY] = "sum"

    grouped = df.groupby(COL_CATEGORY).agg(agg_cols).reset_index()
    growth_map = _growth_by_group(df, COL_CATEGORY)

    result = []
    for _, row in grouped.iterrows():
        cat = row[COL_CATEGORY]
        revenue = float(row[COL_REVENUE])
        entry = {
            "Category": cat,
            "Revenue": round(revenue, 2),
            "Contribution": round((revenue / total_revenue * 100) if total_revenue else 0, 2),
            "Growth": growth_map.get(cat),
        }
        if COL_PROFIT in agg_cols:
            entry["Profit"] = round(float(row[COL_PROFIT]), 2)
        if COL_QUANTITY in agg_cols:
            entry["Units"] = float(row[COL_QUANTITY])
        result.append(entry)

    result.sort(key=lambda r: r["Revenue"], reverse=True)
    return result


# ---------------------------------------------------------------------------
# STEP 7 — Region Summary
# ---------------------------------------------------------------------------
def calculate_region_summary(df):
    if df.empty or not _has(df, COL_REGION) or not _has(df, COL_REVENUE):
        return []

    total_revenue = float(df[COL_REVENUE].sum())

    agg_cols = {COL_REVENUE: "sum"}
    if _has(df, COL_PROFIT):
        agg_cols[COL_PROFIT] = "sum"

    grouped = df.groupby(COL_REGION).agg(agg_cols).reset_index()

    orders_map = {}
    if _has(df, COL_ORDER_ID):
        orders_map = df.groupby(COL_REGION)[COL_ORDER_ID].nunique().to_dict()

    growth_map = _growth_by_group(df, COL_REGION)

    result = []
    for _, row in grouped.iterrows():
        reg = row[COL_REGION]
        revenue = float(row[COL_REVENUE])
        entry = {
            "Region": reg,
            "Revenue": round(revenue, 2),
            "Contribution": round((revenue / total_revenue * 100) if total_revenue else 0, 2),
            "Growth": growth_map.get(reg),
        }
        if COL_PROFIT in agg_cols:
            entry["Profit"] = round(float(row[COL_PROFIT]), 2)
        if orders_map:
            entry["Orders"] = int(orders_map.get(reg, 0))
        result.append(entry)

    result.sort(key=lambda r: r["Revenue"], reverse=True)
    return result


# ---------------------------------------------------------------------------
# STEP 8 — Top Products
# ---------------------------------------------------------------------------
def calculate_top_products(df, limit=10):
    if df.empty or not _has(df, COL_PRODUCT) or not _has(df, COL_REVENUE):
        return []

    agg_cols = {COL_REVENUE: "sum"}
    if _has(df, COL_PROFIT):
        agg_cols[COL_PROFIT] = "sum"
    if _has(df, COL_QUANTITY):
        agg_cols[COL_QUANTITY] = "sum"

    grouped = df.groupby(COL_PRODUCT).agg(agg_cols).reset_index()
    grouped = grouped.sort_values(COL_REVENUE, ascending=False).head(limit)

    growth_map = _growth_by_group(df, COL_PRODUCT)

    result = []
    for rank, (_, row) in enumerate(grouped.iterrows(), start=1):
        product = row[COL_PRODUCT]
        entry = {
            "Rank": rank,
            "Product": product,
            "Revenue": round(float(row[COL_REVENUE]), 2),
            "Growth": growth_map.get(product),
        }
        if COL_PROFIT in agg_cols:
            entry["Profit"] = round(float(row[COL_PROFIT]), 2)
        if COL_QUANTITY in agg_cols:
            entry["Units"] = float(row[COL_QUANTITY])
        result.append(entry)

    return result


# ---------------------------------------------------------------------------
# STEP 9 — Business Insights (generated dynamically, never hardcoded)
# ---------------------------------------------------------------------------
def generate_business_insights(monthly_trend, category_summary, region_summary, kpis):
    insights = {}

    if monthly_trend:
        by_revenue = sorted(monthly_trend, key=lambda m: m.get("Revenue", 0))
        insights["highest_revenue_month"] = by_revenue[-1]["Order_Date"]
        insights["lowest_revenue_month"] = by_revenue[0]["Order_Date"]

        if all("Profit" in m for m in monthly_trend):
            by_profit = sorted(monthly_trend, key=lambda m: m.get("Profit", 0))
            insights["highest_profit_month"] = by_profit[-1]["Order_Date"]
            insights["lowest_profit_month"] = by_profit[0]["Order_Date"]
        else:
            insights["highest_profit_month"] = None
            insights["lowest_profit_month"] = None

        best_growth, worst_decline = None, None
        if len(monthly_trend) >= 2:
            for prev, curr in zip(monthly_trend, monthly_trend[1:]):
                prev_rev = prev.get("Revenue", 0)
                curr_rev = curr.get("Revenue", 0)
                if not prev_rev:
                    continue
                change_pct = round((curr_rev - prev_rev) / prev_rev * 100, 2)
                candidate = {"month": curr["Order_Date"], "change_pct": change_pct}
                if best_growth is None or change_pct > best_growth["change_pct"]:
                    best_growth = candidate
                if worst_decline is None or change_pct < worst_decline["change_pct"]:
                    worst_decline = candidate

        insights["fastest_growing_month"] = best_growth
        insights["largest_revenue_growth"] = best_growth
        insights["largest_revenue_decline"] = worst_decline
    else:
        insights.update(
            {
                "highest_revenue_month": None,
                "lowest_revenue_month": None,
                "highest_profit_month": None,
                "lowest_profit_month": None,
                "fastest_growing_month": None,
                "largest_revenue_growth": None,
                "largest_revenue_decline": None,
            }
        )

    if category_summary:
        by_rev = sorted(category_summary, key=lambda c: c.get("Revenue", 0))
        insights["best_category"] = by_rev[-1]["Category"]
        insights["worst_category"] = by_rev[0]["Category"]

        if all("Profit" in c for c in category_summary):
            by_profit = sorted(category_summary, key=lambda c: c.get("Profit", 0))
            insights["highest_profit_category"] = by_profit[-1]["Category"]
        else:
            insights["highest_profit_category"] = None
    else:
        insights["best_category"] = None
        insights["worst_category"] = None
        insights["highest_profit_category"] = None

    if region_summary:
        by_rev = sorted(region_summary, key=lambda r: r.get("Revenue", 0))
        insights["best_region"] = by_rev[-1]["Region"]
        insights["weakest_region"] = by_rev[0]["Region"]

        if all("Profit" in r for r in region_summary):
            by_profit = sorted(region_summary, key=lambda r: r.get("Profit", 0))
            insights["highest_profit_region"] = by_profit[-1]["Region"]
        else:
            insights["highest_profit_region"] = None
    else:
        insights["best_region"] = None
        insights["weakest_region"] = None
        insights["highest_profit_region"] = None

    insights["highest_average_order_value"] = kpis.get("average_order_value")

    return insights


# ---------------------------------------------------------------------------
# STEP 10 — Filters Metadata (always derived live from the data, never
# hardcoded, so new years/regions/categories show up automatically).
# ---------------------------------------------------------------------------
def get_filter_metadata(df):
    years, months, regions, categories = [], [], [], []

    if _has(df, COL_DATE):
        years = sorted(int(y) for y in df[COL_DATE].dt.year.dropna().unique())
        month_nums = sorted(int(m) for m in df[COL_DATE].dt.month.dropna().unique())
        months = [datetime(2000, m, 1).strftime("%B") for m in month_nums]

    if _has(df, COL_REGION):
        regions = sorted(df[COL_REGION].dropna().astype(str).unique().tolist())

    if _has(df, COL_CATEGORY):
        categories = sorted(df[COL_CATEGORY].dropna().astype(str).unique().tolist())

    return {
        "available_years": years,
        "available_months": months,
        "available_regions": regions,
        "available_categories": categories,
    }


# ---------------------------------------------------------------------------
# STEP 11 — Request Metadata
# ---------------------------------------------------------------------------
def build_metadata(original_df, filtered_df, year, month, region, category):
    date_range = {"start": None, "end": None}
    if _has(original_df, COL_DATE) and not original_df.empty:
        date_range = {
            "start": original_df[COL_DATE].min().strftime("%Y-%m-%d"),
            "end": original_df[COL_DATE].max().strftime("%Y-%m-%d"),
        }

    return {
        "records_returned": int(len(filtered_df)),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_range": date_range,
        "filters": {
            "year": year,
            "month": month,
            "region": region,
            "category": category,
        },
    }