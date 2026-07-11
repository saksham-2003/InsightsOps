from src.agents.tools import TOOL_REGISTRY


def execute_structured_tools(
    tool_calls,
    df
):

    results = {}

    errors = []


    for index, call in enumerate(tool_calls):

        tool_name = call.get("tool")

        arguments = call.get(
            "arguments",
            {}
        )


        if tool_name not in TOOL_REGISTRY:

            errors.append(
                f"Unknown tool: {tool_name}"
            )

            continue


        try:

            tool_function = (
                TOOL_REGISTRY[tool_name]
            )


            result = tool_function(
                df,
                **arguments
            )


            # Unique key prevents overwriting
            # repeated calls to the same tool

            result_key = (
                f"{tool_name}_{index}"
            )


            results[result_key] = {

                "tool": tool_name,

                "arguments": arguments,

                "result": result
            }


        except Exception as error:

            errors.append(
                f"{tool_name}: {str(error)}"
            )


    return {

        "tool_results": results,

        "errors": errors
    }