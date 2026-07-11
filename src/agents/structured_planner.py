import json

from src.agents.llm_client import (
    get_groq_client,
    create_chat_completion_with_retry
)

AVAILABLE_TOOLS = [
    "kpi_summary",
    "monthly_trend",
    "category_performance",
    "regional_performance",
    "top_products",
    "anomaly_detection",
    "forecast_evaluation",
    "period_drilldown",
    "region_drilldown",
    "context_drilldown"
]


def create_structured_plan(user_query):

    client = get_groq_client()


    system_prompt = """
You are the planning agent of InsightsOps,
an AI-powered business analytics system.

Your job is to analyze a business question and create
a structured analytical investigation plan.

AVAILABLE TOOLS

1. kpi_summary
Arguments: {}

Use for:
overall business overview, revenue, profit,
orders, profit margin and general KPIs.


2. monthly_trend
Arguments: {}

Use for:
monthly trends, seasonality, spikes,
growth and decline over time.


3. category_performance
Arguments: {}

Use for:
overall category comparison across the entire dataset.


4. regional_performance
Arguments: {}

Use for:
overall regional comparison across the entire dataset.


5. top_products
Arguments: {}

Use for:
overall top product analysis.


6. anomaly_detection
Arguments: {}

Use for:
unusual transactions and transaction outliers.


7. forecast_evaluation
Arguments: {}

Use for:
forecasting model evaluation and prediction questions.


8. period_drilldown
Arguments:
{
    "month": integer from 1 to 12 or null,
    "year": integer or null
}

Use when the question refers to a specific month
or year.

Examples:

November:
{"month": 11}

March 2024:
{"month": 3, "year": 2024}

Year 2023:
{"year": 2023}


9. region_drilldown
Arguments:
{
    "region": string
}

Valid regions:
East
West
South
Centre

Use when investigating why or how a specific
region performs.


PLANNING RULES

- Select only useful tools.
- For investigation questions, use multiple tools when needed.
- Prefer scoped drilldown tools when the user refers to
  a specific month, year or region.
- Do not use whole-dataset category or product results
  as evidence for a specific period when period_drilldown
  can provide scoped evidence.
- Never invent tool names.
- Return only valid JSON.


REQUIRED FORMAT

{
    "intent": "description of analytical objective",

    "tool_calls": [
        {
            "tool": "tool_name",
            "arguments": {}
        }
    ],

    "reason": "brief explanation of the investigation plan"
}
10. context_drilldown

Arguments:
{
    "month": integer from 1 to 12 or null,
    "year": integer or null,
    "region": string or null
}

Use when analysis requires combined filters.

Examples:

November in East:
{
    "month": 11,
    "region": "East"
}

November 2024 in East:
{
    "month": 11,
    "year": 2024,
    "region": "East"
}

Prefer this tool when the question requires evidence
at the intersection of time and geography.
"""


    response = create_chat_completion_with_retry(
        client,

        model="openai/gpt-oss-20b",

        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_query
            }
        ],

        temperature=0,

        response_format={
            "type": "json_object"
        }
    )


    content = (
        response
        .choices[0]
        .message.content
    )


    plan = json.loads(content)


    # Validate tool calls

    validated_calls = []


    for call in plan.get("tool_calls", []):

        tool_name = call.get("tool")

        if tool_name in AVAILABLE_TOOLS:

            validated_calls.append({

                "tool": tool_name,

                "arguments":
                    call.get("arguments", {})
            })


    if not validated_calls:

        validated_calls = [
            {
                "tool": "kpi_summary",
                "arguments": {}
            }
        ]


    plan["tool_calls"] = validated_calls


    return plan