import json
import logging
from typing import Dict, Any, List

from src.agents.llm_client import (
    get_llm_client,
    create_chat_completion_with_retry,
    extract_response_text
)

class BusinessInsightGenerator:
    """
    Professional Business Insight Generator for InsightsOps.

    Acts as the final reasoning layer, transforming structured evidence, 
    recommendations, and raw tool outputs into clear, connected, and 
    insightful business reports.

    Architected for Future Agentic Extensions:
    - Conversation Memory
    - Multi-turn Reasoning
    - Persona-based Responses
    - Reflection & Self-Review
    """

    def __init__(self, state: Dict[str, Any]):
        self.state = state
        self.client = get_llm_client()
        self.model = "insight_generator"
        self.temperature = 0.0

    def _build_business_briefing(self) -> str:
        """
        Convert the current context into a human-readable business briefing
        for the LLM.
        """

        context = self._build_context()

        briefing = f"""
    USER QUESTION
    -------------
    {context.get("user_query")}

    TOOL RESULTS
    ------------
    {json.dumps(context.get("tool_results"), indent=2, default=str)}

    STRUCTURED EVIDENCE
    -------------------
    {json.dumps(context.get("structured_evidence"), indent=2, default=str)}

    RECOMMENDATIONS
    ---------------
    {json.dumps(context.get("recommendations"), indent=2, default=str)}
    """

        return briefing

    # =========================================================================
    # TASK 10: EXTENSIBILITY HOOKS
    # =========================================================================

    def _apply_conversation_memory(self) -> Dict[str, Any]:
        """Hook: Inject historical context for multi-turn reasoning."""
        return {}

    def _apply_persona_configuration(self) -> str:
        """Hook: Dynamically alter the persona (e.g., Financial vs. Marketing focus)."""
        return "Principal Business Intelligence Consultant"

    def _reflection_and_self_review(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Hook: Multi-agent self-critique loop to verify insight quality before returning."""
        return report

    # =========================================================================
    # CONTEXT PREPARATION (TASK 1)
    # =========================================================================

    def _build_context(self) -> Dict[str, Any]:
        """
        Safely extracts all available layers of intelligence from the state.
        Maintains compatibility with both legacy flat states and new multi-stage pipelines.
        """
        return {
            "user_query": self.state.get("user_query", self.state.get("query", "General business analysis")),
            "tool_results": self.state.get("tool_results", self.state.get("execution", {}).get("results", {})),
            "structured_evidence": self.state.get("analysis", self.state.get("evidence", {})),
            "recommendations": self.state.get("recommendations", {}),
            "metadata": self.state.get("metadata", {}),
            "memory_context": self._apply_conversation_memory()
        }

    # =========================================================================
    # PROMPT ENGINEERING (TASKS 2, 3, 4, 5, 6, 7, 8, 9)
    # =========================================================================

    def _build_system_prompt(self, persona: str) -> str:
        return f"""
You are a {persona} for InsightsOps, an enterprise Business Intelligence application.
Your objective is to synthesize raw data, structured evidence, and recommendations into a dynamic, highly professional business report.

CRITICAL RULES:
1. Grounding (No Hallucinations): NEVER invent metrics, trends, anomalies, or recommendations. Use ONLY the provided context.
2. Dynamic Styling: Select the most appropriate response style based on the user's question (e.g., Executive Summary, Analytical Report, Decision Support, Risk Analysis, Comparison Report).
3. Relevant Sections Only: Do NOT output empty sections. If no anomaly data exists, omit the Risk Assessment section.
4. Metric Relationships: Connect the dots. Explain WHY things are happening. (e.g., "Revenue increased by 10%, but profit declined by 2%, indicating margin compression.")
5. Prioritization: Always list critical findings and highest-impact insights first.
6. Language: Use concise, impactful, executive-level business language. Avoid robotic phrasing or generic filler.

REQUIRED JSON OUTPUT FORMAT:
You must return a valid JSON object strictly matching this schema.

{{
    "response_style": "Name of the chosen style (e.g., 'Risk Analysis')",
    "executive_summary": "Concise overview covering the most important findings.",
    "dynamic_sections": [
        {{
            "section_title": "Choose from: Key Findings, Trend Analysis, Business Insights, Risk Assessment, Opportunities, Recommendations, Next Steps",
            "connected_insights": [
                "Insight explaining relationships between facts (e.g., Sales up BUT margins down).",
                "Insight 2"
            ]
        }}
    ],
    "prioritized_insights": [
        "A flat list of all insights ranked from most critical to least critical. (Used for UI rendering)"
    ],
    "follow_up_questions": [
        "Strategic business question 1 to guide the user?",
        "Strategic business question 2?"
    ]
}}
"""

    # =========================================================================
    # CORE GENERATION & FALLBACK
    # =========================================================================

    def _fallback_insights(self) -> List[str]:
        """
        Legacy rule-based generation to guarantee the application never crashes 
        if the LLM service is temporarily unavailable.
        """
        insights = []
        results = self.state.get("tool_results", self.state.get("execution", {}).get("results", {}))

        if "kpi_summary" in results and isinstance(results["kpi_summary"], dict):
            kpis = results["kpi_summary"]
            insights.append(f"Total revenue stands at ${kpis.get('total_revenue', 0):,.2f} with a profit margin of {kpis.get('profit_margin', 0):.2f}%.")
            
        if "category_performance" in results and isinstance(results["category_performance"], list):
            cats = results["category_performance"]
            if cats:
                top_rev = max(cats, key=lambda x: x.get("Revenue", 0))
                insights.append(f"{top_rev.get('Category', 'A category')} leads revenue at ${top_rev.get('Revenue', 0):,.2f}.")

        if not insights:
            insights.append("Data processed successfully, but deep insights could not be generated at this moment.")
            
        return insights

    def generate(self) -> Dict[str, Any]:
        """
        Executes the LLM insight generation and updates the state.
        """
        persona = self._apply_persona_configuration()
        system_prompt = self._build_system_prompt(persona)
        context_payload = self._build_business_briefing()

        try:
            response = create_chat_completion_with_retry(
                self.client,
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context_payload}
                ],
                temperature=0.0,
                max_completion_tokens=2500,
                response_format={"type": "json_object"}
            )

            raw_content = extract_response_text(response)
            report = json.loads(raw_content)

            # Apply multi-agent reflection hook
            verified_report = self._reflection_and_self_review(report)

            # Update State (Maintains backward compatibility with legacy lists while adding rich objects)
            self.state["insights"] = verified_report.get("prioritized_insights", self._fallback_insights())
            self.state["insight_report"] = verified_report
            self.state["follow_up_questions"] = verified_report.get("follow_up_questions", [])

        except Exception as e:
            import traceback

            print("\n================ LLM ERROR ================\n")

            traceback.print_exc()

            print("\n==========================================\n")

            logging.exception("LLM Response Generation Failed")

            return {
                "executive_summary": "An error occurred while generating the business analysis.",
                "key_findings": [],
                "evidence": [],
                "business_insights": [],
                "recommendations": [],
                "potential_risks": [],
                "suggested_follow_up_questions": [],
                "reflection_passed": False
            }
            # Graceful Fallback
            self.state["insights"] = self._fallback_insights()
            self.state["insight_report"] = {"error": "LLM generation failed. Showing legacy insights."}

        return self.state


# =========================================================================
# PUBLIC API (Maintains Existing Signature)
# =========================================================================

def generate_insights(state: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """
    Generate evidence-based insights from tool results and analytical findings.

    Transforms structured evidence and recommendations into clear, connected, 
    business-oriented responses via the BusinessInsightGenerator.
    
    Args:
        state (dict): The orchestration state containing tool outputs, analysis, and metadata.
        
    Returns:
        dict: The updated state containing the newly generated insights.
    """
    # Safety fallback if state is passed differently via kwargs
    if state is None:
        state = kwargs

    generator = BusinessInsightGenerator(state)
    return generator.generate()