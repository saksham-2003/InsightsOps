from src.agents.tools import TOOL_REGISTRY


def execute_tools(
    selected_tools,
    df
):
    """
    Execute tools selected by the router.

    Returns:
        dict containing results from each tool
    """

    results = {}

    errors = []


    for tool_name in selected_tools:

        try:

            if tool_name not in TOOL_REGISTRY:

                errors.append(
                    f"Unknown tool: {tool_name}"
                )

                continue


            tool_function = TOOL_REGISTRY[
                tool_name
            ]


            result = tool_function(df)


            results[tool_name] = result


        except Exception as error:

            errors.append(
                f"{tool_name}: {str(error)}"
            )


    return {
        "tool_results": results,
        "errors": errors
    }