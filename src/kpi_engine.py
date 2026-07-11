def calculate_kpis(df):
    """
    Calculate important business KPIs.

    Returns:
        dict: Calculated KPI values
    """

    total_revenue = df["Revenue"].sum()

    total_profit = df["Profit"].sum()

    total_orders = df["Order_ID"].nunique()

    total_units_sold = df["Quantity"].sum()

    average_order_value = (
        total_revenue / total_orders
        if total_orders > 0
        else 0
    )

    profit_margin = (
        (total_profit / total_revenue) * 100
        if total_revenue > 0
        else 0
    )

    top_category = (
        df.groupby("Category")["Revenue"]
        .sum()
        .idxmax()
    )

    top_region = (
        df.groupby("Region")["Revenue"]
        .sum()
        .idxmax()
    )

    kpis = {
        "total_revenue": float(total_revenue),
        "total_profit": float(total_profit),
        "total_orders": int(total_orders),
        "total_units_sold": int(total_units_sold),
        "average_order_value": float(average_order_value),
        "profit_margin": float(profit_margin),
        "top_category": str(top_category),
        "top_region": str(top_region)
    }

    return kpis