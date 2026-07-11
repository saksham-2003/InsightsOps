import pandas as pd


def analyze_data_quality(df):
    """
    Analyze the quality of a Pandas DataFrame.

    Returns:
        dict: Data quality information
    """

    report = {}

    # Dataset size
    report["rows"] = df.shape[0]
    report["columns"] = df.shape[1]

    # Missing values
    report["missing_values"] = df.isnull().sum().to_dict()

    # Duplicate rows
    report["duplicate_rows"] = int(df.duplicated().sum())

    # Data types
    report["data_types"] = df.dtypes.astype(str).to_dict()

    # Number of unique values
    report["unique_values"] = df.nunique().to_dict()

    # Column names with leading/trailing spaces
    report["column_name_issues"] = [
        column
        for column in df.columns
        if column != column.strip()
    ]

    return report

def generate_business_analysis(df):
    """
    Generate analytical summaries from business data.

    Returns:
        dict: Different analytical DataFrames
    """

    analysis = {}


    # 1. Monthly performance
    monthly_performance = (
        df.groupby(
            df["Order_Date"].dt.to_period("M")
        )
        .agg(
            Revenue=("Revenue", "sum"),
            Profit=("Profit", "sum"),
            Orders=("Order_ID", "nunique"),
            Units_Sold=("Quantity", "sum")
        )
        .reset_index()
    )

    monthly_performance["Order_Date"] = (
        monthly_performance["Order_Date"].astype(str)
    )

    analysis["monthly_performance"] = monthly_performance


    # 2. Category performance
    category_performance = (
        df.groupby("Category")
        .agg(
            Revenue=("Revenue", "sum"),
            Profit=("Profit", "sum"),
            Orders=("Order_ID", "nunique"),
            Units_Sold=("Quantity", "sum")
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )

    analysis["category_performance"] = category_performance


    # 3. Sub-category performance
    subcategory_performance = (
        df.groupby(
            ["Category", "Sub_Category"]
        )
        .agg(
            Revenue=("Revenue", "sum"),
            Profit=("Profit", "sum"),
            Orders=("Order_ID", "nunique")
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )

    analysis["subcategory_performance"] = (
        subcategory_performance
    )


    # 4. Regional performance
    regional_performance = (
        df.groupby("Region")
        .agg(
            Revenue=("Revenue", "sum"),
            Profit=("Profit", "sum"),
            Orders=("Order_ID", "nunique"),
            Units_Sold=("Quantity", "sum")
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )

    analysis["regional_performance"] = regional_performance


    # 5. Top products
    top_products = (
        df.groupby("Product_Name")
        .agg(
            Revenue=("Revenue", "sum"),
            Profit=("Profit", "sum"),
            Units_Sold=("Quantity", "sum")
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
        .head(10)
    )

    analysis["top_products"] = top_products


    # 6. State performance
    state_performance = (
        df.groupby("State")
        .agg(
            Revenue=("Revenue", "sum"),
            Profit=("Profit", "sum"),
            Orders=("Order_ID", "nunique")
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )

    analysis["state_performance"] = state_performance


    # 7. City performance
    city_performance = (
        df.groupby("City")
        .agg(
            Revenue=("Revenue", "sum"),
            Profit=("Profit", "sum"),
            Orders=("Order_ID", "nunique")
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )

    analysis["city_performance"] = city_performance


    # 8. Product profitability
    product_profitability = (
        df.groupby("Product_Name")
        .agg(
            Revenue=("Revenue", "sum"),
            Profit=("Profit", "sum")
        )
        .reset_index()
    )

    product_profitability["Profit_Margin"] = (
        product_profitability["Profit"]
        / product_profitability["Revenue"]
        * 100
    )

    product_profitability = (
        product_profitability.sort_values(
            "Profit_Margin",
            ascending=False
        )
    )

    analysis["product_profitability"] = (
        product_profitability
    )


    return analysis