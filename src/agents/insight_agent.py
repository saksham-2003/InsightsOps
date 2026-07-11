def generate_insights(state):
    """
    Generate evidence-based insights from tool results.

    This is the deterministic version.
    It will later be upgraded with LLM reasoning.
    """

    insights = []

    results = state.get(
        "tool_results",
        {}
    )


    # KPI insights
    if "kpi_summary" in results:

        kpis = results["kpi_summary"]

        insights.append(
            f"Total revenue is "
            f"${kpis['total_revenue']:,.2f} "
            f"with a profit margin of "
            f"{kpis['profit_margin']:.2f}%."
        )

        insights.append(
            f"The strongest category by revenue "
            f"is {kpis['top_category']}, while "
            f"{kpis['top_region']} is the "
            f"top-performing region."
        )


    # Category insights
    if "category_performance" in results:

        categories = results[
            "category_performance"
        ]

        if categories:

            top_revenue = max(
                categories,
                key=lambda x: x["Revenue"]
            )

            top_profit = max(
                categories,
                key=lambda x: x["Profit"]
            )

            insights.append(
                f"{top_revenue['Category']} leads "
                f"category revenue at "
                f"${top_revenue['Revenue']:,.2f}."
            )

            if (
                top_revenue["Category"]
                != top_profit["Category"]
            ):

                insights.append(
                    f"However, "
                    f"{top_profit['Category']} "
                    f"generates the highest profit at "
                    f"${top_profit['Profit']:,.2f}."
                )


    # Regional insights
    if "regional_performance" in results:

        regions = results[
            "regional_performance"
        ]

        if regions:

            strongest_region = max(
                regions,
                key=lambda x: x["Revenue"]
            )

            weakest_region = min(
                regions,
                key=lambda x: x["Revenue"]
            )

            insights.append(
                f"{strongest_region['Region']} is "
                f"the strongest region with "
                f"${strongest_region['Revenue']:,.2f} "
                f"in revenue."
            )

            insights.append(
                f"{weakest_region['Region']} has "
                f"the lowest regional revenue at "
                f"${weakest_region['Revenue']:,.2f}."
            )


    # Anomaly insights
    if "anomaly_detection" in results:

        anomaly_data = results[
            "anomaly_detection"
        ]

        summary = anomaly_data["summary"]

        insights.append(
            f"The anomaly detector flagged "
            f"{summary['anomaly_count']:,} "
            f"transactions "
            f"({summary['anomaly_percentage']:.2f}% "
            f"of all transactions) for review."
        )


    # Forecast insights
    if "forecast_evaluation" in results:

        forecast = results[
            "forecast_evaluation"
        ]

        metrics = forecast["metrics"]

        insights.append(
            f"The forecasting model achieved "
            f"an R² score of "
            f"{metrics['R2']:.4f} with an MAE of "
            f"${metrics['MAE']:,.2f}."
        )


    state["insights"] = insights

    return state