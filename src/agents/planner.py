import json

from src.agents.llm_client import get_groq_client


AVAILABLE_TOOLS = [
    "kpi_summary",
    "monthly_trend",
    "category_performance",
    "regional_performance",
    "top_products",
    "anomaly_detection",
    "forecast_evaluation"
]


def create_ai_plan(user_query):
    """
    Use an LLM to understand the user's business question
    and select the analytical tools needed.
    """

    client = get_groq_client()


    system_prompt = f"""
You are the planning agent for InsightsOps,
an AI-powered business analytics platform.

Your task is to understand the user's business question
and select the analytical tools needed to investigate it.

Available tools:

1. kpi_summary
   Use for overall revenue, profit, orders,
   profit margin, top category, and top region.

2. monthly_trend
   Use for monthly patterns, growth, decline,
   seasonality, spikes, and time-based comparisons.

3. category_performance
   Use for category-level revenue, profit,
   orders, and units sold.

4. regional_performance
   Use for regional revenue, profit,
   orders, and units sold.

5. top_products
   Use for top products by revenue,
   profit, and units sold.

6. anomaly_detection
   Use for unusual or suspicious transactions
   and transaction-level outliers.

7. forecast_evaluation
   Use when the user asks about forecasting,
   prediction, or model performance.

Important rules:

- Select only tools that help answer the question.
- You may select multiple tools.
- For "why" questions, select enough tools to investigate
  possible contributors.
- Never invent a tool name.
- Return only valid JSON.

Required JSON format:

{{
    "intent": "short description of the analytical intent",
    "selected_tools": ["tool_name"],
    "reason": "brief explanation of why these tools are needed"
}}
"""


    response = client.chat.completions.create(

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


    content = response.choices[0].message.content

    plan = json.loads(content)


    # Safety validation:
    # reject hallucinated tool names

    valid_tools = [
        tool
        for tool in plan.get("selected_tools", [])
        if tool in AVAILABLE_TOOLS
    ]


    if not valid_tools:
        valid_tools = ["kpi_summary"]


    plan["selected_tools"] = valid_tools


    return plan