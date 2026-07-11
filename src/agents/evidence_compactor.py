def compact_tool_evidence(execution):
    """
    Convert large raw tool outputs into a compact evidence
    package suitable for the LLM Evidence Analyst.

    Raw execution results remain available elsewhere.
    """

    compact = {}

    tool_results = execution.get(
        "tool_results",
        {}
    )


    for result_key, tool_data in tool_results.items():

        tool_name = tool_data.get("tool")

        arguments = tool_data.get(
            "arguments",
            {}
        )

        result = tool_data.get(
            "result",
            {}
        )


        # ====================================================
        # KPI SUMMARY
        # ====================================================

        if tool_name == "kpi_summary":

            compact[result_key] = {
                "tool": tool_name,
                "scope": "overall_dataset",
                "result": result
            }


        # ====================================================
        # MONTHLY TREND
        # Keep all monthly aggregated rows.
        # This is already small compared with transaction data.
        # ====================================================

        elif tool_name == "monthly_trend":

            compact[result_key] = {
                "tool": tool_name,
                "scope": "monthly_aggregated_dataset",
                "result": result
            }


        # ====================================================
        # CATEGORY PERFORMANCE
        # ====================================================

        elif tool_name == "category_performance":

            compact[result_key] = {
                "tool": tool_name,
                "scope": "overall_dataset",
                "result": result[:10]
            }


        # ====================================================
        # REGIONAL PERFORMANCE
        # ====================================================

        elif tool_name == "regional_performance":

            compact[result_key] = {
                "tool": tool_name,
                "scope": "overall_dataset",
                "result": result
            }


        # ====================================================
        # TOP PRODUCTS
        # ====================================================

        elif tool_name == "top_products":

            compact[result_key] = {
                "tool": tool_name,
                "scope": "overall_dataset",
                "result": result[:5]
            }


        # ====================================================
        # ANOMALY DETECTION
        # Do not send all anomaly records.
        # ====================================================

        elif tool_name == "anomaly_detection":

            compact[result_key] = {
                "tool": tool_name,
                "scope": "overall_dataset",
                "summary": result.get(
                    "summary",
                    {}
                ),
                "sample_top_anomalies": result.get(
                    "top_anomalies",
                    []
                )[:3]
            }


        # ====================================================
        # FORECAST EVALUATION
        # ====================================================

        elif tool_name == "forecast_evaluation":

            compact[result_key] = {
                "tool": tool_name,
                "scope": "forecast_evaluation",
                "metrics": result.get(
                    "metrics",
                    {}
                ),
                "recent_predictions": result.get(
                    "predictions",
                    []
                )[-5:]
            }


        # ====================================================
        # PERIOD DRILLDOWN
        # ====================================================

        elif tool_name == "period_drilldown":

            compact[result_key] = {
                "tool": tool_name,
                "scope": {
                    "type": "period",
                    "filters": result.get(
                        "filters",
                        arguments
                    )
                },
                "total_revenue": result.get(
                    "total_revenue"
                ),
                "total_profit": result.get(
                    "total_profit"
                ),
                "categories": result.get(
                    "categories",
                    []
                ),
                "regions": result.get(
                    "regions",
                    []
                ),
                "top_products": result.get(
                    "top_products",
                    []
                )[:5]
            }


        # ====================================================
        # REGION DRILLDOWN
        # ====================================================

        elif tool_name == "region_drilldown":

            compact[result_key] = {
                "tool": tool_name,
                "scope": {
                    "type": "region",
                    "region": result.get(
                        "region"
                    )
                },
                "total_revenue": result.get(
                    "total_revenue"
                ),
                "total_profit": result.get(
                    "total_profit"
                ),
                "categories": result.get(
                    "categories",
                    []
                ),
                "top_products": result.get(
                    "top_products",
                    []
                )[:5]
            }


        # ====================================================
        # CONTEXT DRILLDOWN
        # Keep totals + categories + only top 3 products.
        # ====================================================

        elif tool_name == "context_drilldown":

            compact[result_key] = {
                "tool": tool_name,
                "scope": {
                    "type": "filtered_context",
                    "filters": result.get(
                        "filters",
                        arguments
                    )
                },
                "transaction_count": result.get(
                    "transaction_count"
                ),
                "total_revenue": result.get(
                    "total_revenue"
                ),
                "total_profit": result.get(
                    "total_profit"
                ),
                "total_units": result.get(
                    "total_units"
                ),
                "categories": result.get(
                    "categories",
                    []
                ),
                "top_products": result.get(
                    "top_products",
                    []
                )[:3]
            }


    return compact