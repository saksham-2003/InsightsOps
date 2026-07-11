from src.agents.planner import create_ai_plan


queries = [

    "Give me an overview of the business",

    "Which categories are making the most money?",

    "Why is the East region performing better than others?",

    "Why was November revenue unusually high?",

    "Are there any suspicious or unusual transactions?",

    "How well does our revenue forecasting model perform?"
]


print("\n===== AI PLANNER TEST =====")


for query in queries:

    print("\n" + "=" * 70)

    print(f"\nUSER: {query}")


    try:

        plan = create_ai_plan(query)

        print(
            f"\nINTENT: {plan['intent']}"
        )

        print(
            f"SELECTED TOOLS: "
            f"{plan['selected_tools']}"
        )

        print(
            f"REASON: {plan['reason']}"
        )


    except Exception as error:

        print(f"\nERROR: {error}")