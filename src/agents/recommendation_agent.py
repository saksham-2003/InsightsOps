import json
import logging
from typing import Dict, Any, List

from src.agents.llm_client import (
    get_llm_client,
    create_chat_completion_with_retry,
    extract_response_text
)

class BusinessRecommendationEngine:
    """
    Intelligent Recommendation Engine for InsightsOps.

    Transforms structured analytical evidence into actionable, high-value 
    business action plans. Designed to act as an experienced Business Consultant.

    Architected for Future Agentic Extensions:
    - Industry-specific rules mapping
    - External Business Rule Engines
    - Enterprise Knowledge Graphs
    - Company Policies Integration
    - Multi-agent Reflection & Self-Critique
    """

    def __init__(self, user_query: str, plan: Dict[str, Any], execution: Dict[str, Any], analysis: Dict[str, Any], derived_evidence: Dict[str, Any]):
        self.user_query = user_query
        self.plan = plan
        self.execution = execution
        self.analysis = analysis
        self.derived_evidence = derived_evidence
        
        self.client = get_llm_client()
        self.model = "reasoning"
        self.temperature = 0.0

    # =========================================================================
    # EXTENSIBILITY HOOKS (Task 10: Future Compatibility)
    # =========================================================================

    def _apply_industry_rules(self) -> Dict[str, Any]:
        """Hook: Inject industry-specific operating standards."""
        return {}

    def _apply_business_rule_engine(self) -> Dict[str, Any]:
        """Hook: Interface with external deterministic rule engines."""
        return {}

    def _retrieve_knowledge_graph(self) -> Dict[str, Any]:
        """Hook: Retrieve contextual mapping from an enterprise knowledge graph."""
        return {}

    def _apply_company_policies(self) -> Dict[str, Any]:
        """Hook: Inject internal company policies to constrain recommendations."""
        return {}

    def _reflection_critique(self, recommendations: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hook: Multi-agent reflection to audit recommendation feasibility, 
        merge duplicates, and rank by importance.
        """
        # Base validation to ensure backwards compatibility with UI
        if "priority_actions" not in recommendations:
            recommendations["priority_actions"] = []
            
        # Guarantee frontend compatibility fields
        for action in recommendations.get("priority_actions", []):
            if "title" in action and "action" not in action:
                action["action"] = action["title"]
            elif "action" in action and "title" not in action:
                action["title"] = action["action"]
                
        return recommendations

    # =========================================================================
    # CORE ENGINE PROMPT & GENERATION
    # =========================================================================

    def _build_context(self) -> Dict[str, Any]:
        """Consolidates relevant business context for the LLM."""
        return {
            "user_query": self.user_query,
            "intent": self.plan.get("intent"),
            "analysis": self.analysis,
            "verified_derived_evidence": self.derived_evidence,
            "future_hooks": {
                "industry_rules": self._apply_industry_rules(),
                "business_rules": self._apply_business_rule_engine(),
                "company_policies": self._apply_company_policies()
            }
        }

    def _build_system_prompt(self) -> str:
        """Constructs the strict, persona-driven system prompt."""
        return """
You are the Principal Business Consultant and Recommendation Agent for InsightsOps.

Your objective is to generate highly strategic, actionable, and evidence-backed business recommendations based ONLY on the supplied evidence and analysis.

STRICT GROUNDING RULES (Task 1 & 9):
1. Recommendations MUST be derived directly from the provided evidence. Never hallucinate scenarios, metrics, or causes.
2. If evidence is lacking, recommend investigation or data auditing rather than assuming a cause.

SITUATIONAL LOGIC (Task 2):
Base your recommendations on the detected business situations:
- If Revenue decreasing -> Investigate customer demand, optimize pricing, review seasonal trends.
- If Profit decreasing -> Review operational costs, reduce discounting, audit supplier contracts.
- If Anomalies increasing -> Investigate suspicious transactions, review pricing inconsistencies, audit data quality.
- If Forecast declining -> Increase promotional campaigns, review inventory planning, optimize resource allocation.
- If Category underperforming -> Analyze customer behavior, review product assortment, evaluate marketing effectiveness.

EVALUATION METRICS (Task 3, 4, 5 & 8):
- Priority: Assign strictly as Critical, High, Medium, or Low.
- Business Impact: Categorize exactly as Revenue Growth, Profit Improvement, Cost Reduction, Risk Reduction, Customer Retention, or Operational Efficiency.
- Implementation Effort: Estimate exactly as Low, Medium, or High.
- Timeframe: Classify exactly as Short-term, Medium-term, or Long-term.

ACTION PLAN STRUCTURING (Task 6 & 7):
- Merge similar actions to avoid duplicates.
- Rank recommendations strictly by business importance (Critical first, then High, etc.).
- Ensure each action plan is comprehensive and executable.

REQUIRED JSON FORMAT:
You MUST return ONLY valid JSON matching this exact structure to maintain frontend compatibility:

{
    "priority_actions": [
        {
            "title": "Clear, professional title of the recommendation",
            "action": "Duplicate of the title (required for UI compatibility)",
            "reason": "Evidence-based justification for this action",
            "business_impact": "Revenue Growth | Profit Improvement | Cost Reduction | Risk Reduction | Customer Retention | Operational Efficiency",
            "priority": "Critical | High | Medium | Low",
            "implementation_effort": "Low | Medium | High",
            "suggested_actions": [
                "Specific tactical step 1",
                "Specific tactical step 2"
            ],
            "expected_outcome": "Quantifiable or strategic expected result",
            "timeframe": "Short-term | Medium-term | Long-term"
        }
    ],
    "experiments": [
        {
            "experiment": "Proposed business test or investigation",
            "success_metric": "Specific metric to monitor for success"
        }
    ],
    "monitoring_metrics": [
        "Metric 1 to monitor closely",
        "Metric 2 to monitor closely"
    ]
}
"""

    def generate(self) -> Dict[str, Any]:
        """Executes the LLM call and returns validated recommendations."""
        system_prompt = self._build_system_prompt()
        context_payload = json.dumps(self._build_context(), default=str)

        try:
            response = create_chat_completion_with_retry(
                self.client,
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context_payload}
                ],
                temperature=0.0,
                max_completion_tokens=2000,
                response_format={"type": "json_object"}
            )

            content = extract_response_text(response)
            raw_recommendations = json.loads(content)

            # Apply Reflection & formatting hook
            return self._reflection_critique(raw_recommendations)

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
            # Safe fallback compatible with UI
            return {
                "priority_actions": [
                    {
                        "title": "System Alert: Review Analysis Logs",
                        "action": "System Alert: Review Analysis Logs",
                        "reason": "The recommendation engine encountered an error while processing the evidence.",
                        "business_impact": "Operational Efficiency",
                        "priority": "Medium",
                        "implementation_effort": "Low",
                        "suggested_actions": ["Review system logs for API or context constraints."],
                        "expected_outcome": "Restored recommendation capabilities.",
                        "timeframe": "Short-term"
                    }
                ],
                "experiments": [],
                "monitoring_metrics": []
            }


# =========================================================================
# PUBLIC API (Maintains Existing Signature)
# =========================================================================

def generate_recommendations(
    user_query: str,
    plan: Dict[str, Any],
    execution: Dict[str, Any],
    analysis: Dict[str, Any],
    derived_evidence: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate business recommendations grounded in analytical evidence 
    and analyst findings using the BusinessRecommendationEngine.
    """
    engine = BusinessRecommendationEngine(
        user_query=user_query,
        plan=plan,
        execution=execution,
        analysis=analysis,
        derived_evidence=derived_evidence
    )
    
    return engine.generate()