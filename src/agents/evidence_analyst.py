import json

from src.agents.llm_client import (
    get_groq_client,
    create_chat_completion_with_retry
)

def analyze_evidence(
    user_query,
    plan,
    compact_evidence,
    derived_evidence
):
    """
    Analyze tool evidence and generate grounded
    business insights.
    """

    client = get_groq_client()


    evidence = {
        "user_query": user_query,

        "intent": plan.get("intent"),

        "compact_tool_evidence":
            compact_evidence,

        "verified_derived_evidence":
            derived_evidence
    }

    system_prompt = """
    You are the Evidence Analyst Agent for InsightsOps.

    Your job is to analyze business evidence produced by
    analytics and machine learning tools.

    STRICT GROUNDING RULES:

    1. Use only values and relationships directly supported
    by the supplied tool evidence.

    2. Never invent numbers, percentages, classifications,
    causes, trends, or relationships.

    3. Before stating a calculated percentage, calculate it
    accurately from the supplied evidence.

    4. Do not say that a category, region, or product caused
    an increase unless comparative evidence supports it.

    5. If only one period's breakdown is available, describe
    its composition, but do not claim that components
    caused growth versus another period.

    6. Clearly distinguish:
    - observed fact
    - likely contributor
    - hypothesis requiring more evidence

    7. Anomaly detection identifies unusual transactions.
    It does not prove fraud.

    8. Transaction anomalies cannot prove that an entire
    month is a time-series anomaly.

    9. R-squared is not an accuracy percentage.

    10. Do not call a product high-margin unless margin
        evidence is explicitly available.

    11. Do not claim statistical significance unless a
        statistical significance test is present in evidence.

    12. Keep insights concise and business-focused.

    Return only valid JSON.

    Required format:

    {
        "executive_summary": "2-4 sentence grounded summary",

        "key_findings": [
            "finding 1",
            "finding 2",
            "finding 3"
        ],

        "risks_or_cautions": [
            "caution 1"
        ],

        "confidence": "high, medium, or low",

        "confidence_reason": "brief explanation"
        13. VERIFIED DERIVED EVIDENCE contains metrics calculated
        deterministically in Python.

    14. When discussing percentages, shares, ratios, margins,
        or combined contributions, use values from
        VERIFIED DERIVED EVIDENCE whenever available.

    15. Do not recalculate a verified metric independently.

    16. Product revenue does not prove high margin.
        Never describe a product as high-margin unless explicit
        product margin evidence is provided.

    17. A global anomaly rate cannot prove that anomalies did
        or did not cause a specific month's revenue movement.

    18. Do not say marketing, promotions, pricing, or discounts
        caused a result unless those variables exist in evidence.
    19. Always respect the scope of each evidence source.

    20. If period filters contain a month but no year,
        the period drilldown may combine that month across
        multiple years in the dataset.

    21. Never attach a combined multi-year percentage or share
        to one specific year.

    22. When evidence scopes differ, clearly label them.
        Example:
        "Across all November records in the dataset..."
        versus
        "In November 2023..."

    23. Category or product composition within a period does
        not prove that those categories or products caused
        growth compared with another period.
    }
    24. The field top_3_product_share_percent refers only
    to the first three products. Never describe it as
    the contribution of the top 10 products.

    25. regional_performance contains overall dataset-level
        regional performance unless a scoped regional result
        is explicitly provided.

    26. Never describe overall regional shares as shares
        for a specific month or year.

    27. A category's high revenue share shows composition,
        not proof that the category caused the increase.

    28. Do not claim seasonality or a seasonal shopping peak
        unless repeated historical patterns across sufficient
        periods support that conclusion.

    29. Clearly preserve the scope of every metric:
        overall dataset, specific year, combined month across
        years, specific region, or combined filtered context.

    30. When referring to top-N combined metrics from VERIFIED
        DERIVED EVIDENCE, preserve the exact product names and
        ordering associated with that metric. Never substitute
        products from another scoped tool result.

    31. Never state that anomalies are unrelated to a specific
        period unless anomaly detection was explicitly scoped
        to that period.

    32. If anomaly evidence is dataset-wide, describe it only
        as dataset-wide evidence.

    33. Do not infer seasonal demand merely because the same
        calendar month appears across two years.

    34. Seasonality requires sufficient repeated time periods
        or explicit seasonality analysis.

    35. If evidence explains the composition of high revenue
        but not its causal origin, state:
        "The evidence describes where the revenue came from,
        but does not establish the underlying cause of the spike."
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
                    evidence,
                    default=str
                )
            }
        ],

        temperature=0,
        max_completion_tokens=2000,
        response_format={
            "type": "json_object"
        }
    )


    content = (
        response
        .choices[0]
        .message.content
    )


    return json.loads(content)