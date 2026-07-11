def route_query(user_query):
    """
    Analyze a user query and select appropriate tools.

    This is the initial rule-based router.
    Later it will be upgraded to an LLM planner.
    """

    query = user_query.lower()

    selected_tools = []

    intent = "general_business_analysis"


    # KPI questions
    if any(word in query for word in [
        "kpi",
        "summary",
        "overview",
        "total revenue",
        "total profit",
        "profit margin"
    ]):
        selected_tools.append("kpi_summary")

        intent = "business_summary"


    # Time trend questions
    if any(word in query for word in [
        "monthly",
        "month",
        "trend",
        "growth",
        "decline",
        "spike",
        "time"
    ]):
        selected_tools.append("monthly_trend")

        intent = "trend_analysis"


    # Category questions
    if any(word in query for word in [
        "category",
        "categories"
    ]):
        selected_tools.append(
            "category_performance"
        )

        intent = "category_analysis"


    # Region questions
    if any(word in query for word in [
        "region",
        "regional",
        "east",
        "west",
        "south",
        "centre"
    ]):
        selected_tools.append(
            "regional_performance"
        )

        intent = "regional_analysis"


    # Product questions
    if any(word in query for word in [
        "product",
        "products",
        "best selling",
        "top selling"
    ]):
        selected_tools.append(
            "top_products"
        )

        intent = "product_analysis"


    # Anomaly questions
    if any(word in query for word in [
        "anomaly",
        "anomalies",
        "unusual",
        "outlier",
        "suspicious"
    ]):
        selected_tools.append(
            "anomaly_detection"
        )

        intent = "anomaly_analysis"


    # Forecast questions
    if any(word in query for word in [
        "forecast",
        "prediction",
        "predict",
        "future"
    ]):
        selected_tools.append(
            "forecast_evaluation"
        )

        intent = "forecast_analysis"


    # Default tool
    if not selected_tools:
        selected_tools = [
            "kpi_summary"
        ]


    # Remove duplicate tools
    selected_tools = list(
        dict.fromkeys(selected_tools)
    )


    return {
        "intent": intent,
        "selected_tools": selected_tools
    }