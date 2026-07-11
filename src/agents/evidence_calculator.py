def calculate_derived_evidence(execution):
    """
    Calculate reliable derived metrics from tool results.

    Arithmetic is performed in Python so the LLM
    does not need to calculate percentages itself.
    """

    derived = {}

    tool_results = execution.get(
        "tool_results",
        {}
    )


    for _, tool_data in tool_results.items():

        tool_name = tool_data.get("tool")

        result = tool_data.get("result", {})


        # Period drilldown calculations
        if tool_name == "period_drilldown":

            total_revenue = result.get(
                "total_revenue",
                0
            )

            categories = result.get(
                "categories",
                []
            )

            products = result.get(
                "top_products",
                []
            )


            # Category revenue shares
            category_shares = []

            for category in categories:

                share = (
                    category["Revenue"]
                    / total_revenue
                    * 100
                    if total_revenue > 0
                    else 0
                )

                category_shares.append({

                    "category":
                        category["Category"],

                    "revenue":
                        float(category["Revenue"]),

                    "revenue_share_percent":
                        round(float(share), 2)
                })


            # Product revenue shares
            product_shares = []

            for product in products:

                share = (
                    product["Revenue"]
                    / total_revenue
                    * 100
                    if total_revenue > 0
                    else 0
                )

                product_shares.append({

                    "product":
                        product["Product_Name"],

                    "revenue":
                        float(product["Revenue"]),

                    "revenue_share_percent":
                        round(float(share), 2)
                })


            # Top 3 combined share
            top_3_revenue = sum(
                product["Revenue"]
                for product in products[:3]
            )

            top_3_share = (
                top_3_revenue
                / total_revenue
                * 100
                if total_revenue > 0
                else 0
            )


            derived["period_analysis"] = {
                "filters": result.get(
                    "filters",
                    {}
                ),

                "total_revenue":
                    float(total_revenue),

                "category_revenue_shares":
                    category_shares,

                "product_revenue_shares":
                    product_shares,

                "top_3_product_revenue":
                    float(top_3_revenue),

                "top_3_product_share_percent":
                    round(float(top_3_share), 2),
            }


        # Regional calculations
        if tool_name == "regional_performance":

            regions = result

            regional_metrics = []

            for region in regions:

                revenue = region["Revenue"]

                profit = region["Profit"]

                orders = region["Orders"]


                regional_metrics.append({

                    "region":
                        region["Region"],

                    "revenue":
                        float(revenue),

                    "profit":
                        float(profit),

                    "revenue_per_order":
                        round(
                            float(
                                revenue / orders
                            ),
                            2
                        ),

                    "profit_margin_percent":
                        round(
                            float(
                                profit / revenue * 100
                            ),
                            2
                        )
                })


            derived["regional_metrics"] = (
                regional_metrics
            )


    return derived