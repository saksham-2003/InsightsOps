import json

from src.agents.llm_client import (
    get_groq_client,
    create_chat_completion_with_retry
)

def generate_recommendations(
    user_query,
    plan,
    execution,
    analysis,
    derived_evidence
):
    """
    Generate business recommendations grounded
    in analytical evidence and analyst findings.
    """

    client = get_groq_client()


    # Prepare complete context for the Recommendation Agent

    context = {
        "user_query": user_query,

        "intent": plan.get("intent"),

        "analysis": analysis,

        "verified_derived_evidence":
            derived_evidence

    }


    system_prompt = """
You are the Recommendation Agent for InsightsOps.

Your job is to propose practical business actions based
only on the supplied evidence and analysis.

STRICT RULES:

1. Recommendations must be directly connected to evidence.

2. Do not invent causes that were not established.

3. Do not guarantee business outcomes.

4. Distinguish immediate actions from experiments.

5. When causality is uncertain, recommend testing or
   further investigation rather than asserting a cause.

6. Recommendations should be specific and measurable
   when the evidence allows it.

7. Do not recommend treating anomaly flags as fraud.
   Recommend investigation or review.

8. Keep recommendations concise and actionable.

9. Do not combine separate analytical dimensions into
   one claim unless intersection evidence is available.

10. A global anomaly rate applies to the full dataset.
    Do not describe it as a period-specific or
    region-specific anomaly rate.

11. Do not recommend a product-region strategy unless
    evidence explicitly shows product performance
    inside that region.

12. Prefer recommendations phrased as tests when
    cross-dimensional evidence is unavailable.

13. Use VERIFIED DERIVED EVIDENCE for numerical claims,
    percentages, ratios, shares, and margins.

14. Never describe products as high-margin unless explicit
    product margin evidence exists.

15. Do not assume marketing campaigns, discounts,
    promotions, or pricing changes caused performance
    unless such evidence is supplied.

16. If a possible cause is not represented in the dataset,
    recommend investigating it rather than stating that
    it occurred.

17. Do not say a global anomaly rate explains or rules out
    performance in a specific month or region.

18. Never recalculate a percentage when a verified value
    is already available in VERIFIED DERIVED EVIDENCE.

19. Revenue contribution does not prove that a product
    caused overall growth.

20. Use cautious business language when evidence shows
    association but not causation.

21. If top_3_product_share_percent is provided, it refers
    only to the top three products.

22. Do not use overall regional performance as evidence
    for a month-specific regional recommendation.

23. High revenue share alone does not justify maintaining,
    increasing, or decreasing prices.

24. Pricing recommendations should be experiments unless
    explicit pricing elasticity evidence is available.

25. Do not recommend combining unrelated products into a
    bundle solely because both appear in a top-product list.


Return only valid JSON.

Required format:

{
    "priority_actions": [
        {
            "action": "specific action",
            "reason": "evidence-based reason",
            "priority": "high, medium, or low"
        }
    ],

    "experiments": [
        {
            "experiment": "test or investigation",
            "success_metric": "metric to monitor"
        }
    ],

    "monitoring_metrics": [
        "metric 1",
        "metric 2"
    ]
}
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
                "content": json.dumps(
                    context,
                    default=str
                )
            }
        ],

        temperature=0,
        max_completion_tokens=1000,
        response_format={
            "type": "json_object"
        }
    )


    content = (
        response
        .choices[0]
        .message.content
    )


    recommendations = json.loads(content)


    return recommendations