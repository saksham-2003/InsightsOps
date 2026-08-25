from typing import TypedDict, Any, List, Dict, Optional
from dataclasses import dataclass, field
import time
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class FilterState:
    """
    Holds filter entities across conversation turns.
    """
    region: Optional[str] = None
    category: Optional[str] = None
    product: Optional[str] = None
    year: Optional[str] = None
    month: Optional[str] = None
    date_range: Optional[str] = None


@dataclass
class ExtractedEntitiesState:
    """
    Holds the complete set of structured business entities across conversation turns.
    """
    region: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    product: Optional[str] = None
    customer: Optional[str] = None
    year: Optional[str] = None
    month: Optional[str] = None
    quarter: Optional[str] = None
    metric: Optional[str] = None
    comparison: Optional[str] = None
    aggregation: Optional[str] = None
    date_range: Optional[str] = None


@dataclass
class TurnContext:
    """
    Represents the complete context and metadata captured for a single conversation turn.
    """
    user_query: str
    ai_response: str
    planner_output: Dict[str, Any] = field(default_factory=dict)
    selected_tools: List[str] = field(default_factory=list)
    extracted_entities: List[str] = field(default_factory=list)
    filters: FilterState = field(default_factory=FilterState)
    execution_metadata: Dict[str, Any] = field(default_factory=dict)
    evidence_summary: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


@dataclass
class ConversationSummary:
    """
    Maintains a lightweight high-level summary of the ongoing session.
    """
    current_topic: str = ""
    previous_topic: str = ""
    latest_recommendation: str = ""


class ConversationMemoryManager:
    """
    Modular conversation memory manager responsible for storing, retrieving,
    updating, clearing, summarizing, and context-resolving conversation turns.
    Designed for extensibility (session IDs, persistence, vector memory, reflection).
    """

    def __init__(self, session_id: Optional[str] = None):
        self.session_id: Optional[str] = session_id
        self.history: List[TurnContext] = []
        self.summary: ConversationSummary = ConversationSummary()
        self.current_filters: FilterState = FilterState()
        self.current_entities: ExtractedEntitiesState = ExtractedEntitiesState()

    def update_entities(self, extracted_entities: Any) -> None:
        """
        Update the current entities state with extracted entities from a new turn.
        If a new entity value is None, keep the previous value. If it has a value, replace it.
        """
        try:
            if not extracted_entities:
                return

            fields = [
                "region", "country", "state", "city", "category", "sub_category",
                "product", "customer", "year", "month", "quarter", "metric",
                "comparison", "aggregation", "date_range"
            ]

            for field_name in fields:
                val = getattr(extracted_entities, field_name, None)
                if val is not None:
                    setattr(self.current_entities, field_name, val)

            logger.info("Successfully updated current entities.")
        except Exception as e:
            logger.error(f"Error updating entities: {str(e)}")

    def get_current_entities(self) -> Dict[str, Any]:
        """
        Retrieve the current structured business entities as a dictionary.
        """
        return vars(self.current_entities)

    def clear_entities(self) -> None:
        """
        Clear all stored structured business entities, resetting them to None.
        """
        self.current_entities = ExtractedEntitiesState()
        logger.info("Cleared current entities.")

    def merge_entities(self, new_entities: Any) -> ExtractedEntitiesState:
        """
        Merge new entities into the current entity state following merge rules:
        If new entity is None, keep previous value; if new entity has a value, replace it.
        Returns the updated ExtractedEntitiesState.
        """
        try:
            if not new_entities:
                return self.current_entities

            fields = [
                "region", "country", "state", "city", "category", "sub_category",
                "product", "customer", "year", "month", "quarter", "metric",
                "comparison", "aggregation", "date_range"
            ]

            for field_name in fields:
                val = getattr(new_entities, field_name, None)
                if val is not None:
                    setattr(self.current_entities, field_name, val)

            return self.current_entities
        except Exception as e:
            logger.error(f"Error merging entities: {str(e)}")
            return self.current_entities

    def store_turn(self, turn: TurnContext) -> None:
        """
        Store a new conversation turn and update summary/filters.
        """
        try:
            if self.summary.current_topic:
                self.summary.previous_topic = self.summary.current_topic
            

            if turn.recommendations:
                self.summary.latest_recommendation = turn.recommendations[0]

            # Update persistent filter state if provided in the turn
            if turn.filters:
                if turn.filters.region:
                    self.current_filters.region = turn.filters.region
                if turn.filters.category:
                    self.current_filters.category = turn.filters.category
                if turn.filters.product:
                    self.current_filters.product = turn.filters.product
                if turn.filters.year:
                    self.current_filters.year = turn.filters.year
                if turn.filters.month:
                    self.current_filters.month = turn.filters.month
                if turn.filters.date_range:
                    self.current_filters.date_range = turn.filters.date_range

            # Ensure turn has the latest cumulative filters
            turn.filters = FilterState(
                region=self.current_filters.region,
                category=self.current_filters.category,
                product=self.current_filters.product,
                year=self.current_filters.year,
                month=self.current_filters.month,
                date_range=self.current_filters.date_range
            )

            self.history.append(turn)
            logger.info("Successfully stored conversation turn.")
        except Exception as e:
            logger.error(f"Error storing turn context: {str(e)}")

    def retrieve_context(self) -> Dict[str, Any]:
        """
        Retrieve all stored history, summaries, and current filter/entity states.
        """
        return {
            "session_id": self.session_id,
            "history": [vars(t) for t in self.history],
            "summary": vars(self.summary),
            "current_filters": vars(self.current_filters),
            "current_entities": vars(self.current_entities)
        }

    def update_memory(self, additional_data: Dict[str, Any]) -> None:
        """
        Update memory state dynamically (extensibility hook).
        """
        if "summary" in additional_data and isinstance(additional_data["summary"], dict):
            s = additional_data["summary"]
            if "current_topic" in s:
                self.summary.current_topic = s["current_topic"]
            if "previous_topic" in s:
                self.summary.previous_topic = s["previous_topic"]
            if "latest_recommendation" in s:
                self.summary.latest_recommendation = s["latest_recommendation"]

    def reset_context(self) -> None:
        """
        Clear all memory, history, and active filters/entities.
        """
        self.history.clear()
        self.summary = ConversationSummary()
        self.current_filters = FilterState()
        self.current_entities = ExtractedEntitiesState()
        logger.info("Conversation memory reset.")

    def summarize_context(self) -> str:
        """
        Return a lightweight string representation of the session summary.
        """
        return (
            f"Current Topic: {self.summary.current_topic} | "
            f"Previous Topic: {self.summary.previous_topic} | "
            f"Latest Recommendation: {self.summary.latest_recommendation}"
        )

    def is_follow_up(self, query: str) -> bool:
        """
        Automatically detect if a user query is a follow-up question.
        Returns True or False without modifying or rewriting the query.
        """
        if not self.history:
            return False

        follow_up_triggers = [
            "why",
            "how",
            "continue",
            "expand",
            "explain",
            "show details",
            "compare",
            "same analysis",
            "forecast",
            "drill down",
            "it",
            "which one",
            "which",
            "best",
            "worst",
            "highest",
            "lowest",
            "more",
            "that",
            "those",
            "this"
        ]
        q_lower = query.lower().strip()
        # Explicit forecast horizons are new standalone requests,
        # not conversational follow-ups.
        explicit_forecast_horizon = re.search(
            r'\b(?:15|30|60|90)\s*[-]?\s*days?\b',
            q_lower
        )

        if explicit_forecast_horizon and any(
            term in q_lower
            for term in ["forecast", "prediction", "predict", "revenue"]
        ):
            print("EXPLICIT FORECAST REQUEST:", query, "-> False")
            return False

        # Short queries are frequently follow-ups
        if len(q_lower.split()) <= 4:
            print("FOLLOW UP DETECTED:", query, "-> True")
            return True

        for trigger in follow_up_triggers:
            if q_lower.startswith(trigger) or trigger in q_lower:
                print("FOLLOW UP DETECTED:", query, "-> True")
                return True

        print("FOLLOW UP DETECTED:", query, "-> False")
        return False

    def resolve_context(self, current_query: str) -> str:
        """
        Combines the latest conversation context with the new query if it's a follow-up,
        while preserving previous functionality and improving ambiguous follow-up questions.
        """
        if not self.history or not self.is_follow_up(current_query):
            return current_query

        last_turn = self.history[-1]
        print("=" * 50)
        print("LAST TURN TOOLS:", last_turn.selected_tools)
        print("CURRENT QUERY:", current_query)
        print("=" * 50)
        last_query = last_turn.user_query
        q_lower = current_query.lower().strip()

        # Determine subject from last selected tool
        subject = "item"

        if last_turn.selected_tools:
            tool = last_turn.selected_tools[0]

            tool_subject_map = {
                "regional_performance": "region",
                "category_performance": "category",
                "top_products": "product",
                "bottom_products": "product",
                "monthly_trend": "month",
                "forecast_evaluation": "forecast",
                "anomaly_detection": "anomaly",
                "kpi_summary": "business metric"
            }

            subject = tool_subject_map.get(tool, "item")

        # ----------------------------
        # Improved follow-up handling
        # ----------------------------

        if "worst" in q_lower or "lowest" in q_lower:
            return f"Which {subject} is performing worst?"

        elif "best" in q_lower or "highest" in q_lower:
            return f"Which {subject} is performing best?"

        elif q_lower in ["which one", "which one?"]:
            return f"Which {subject} are you referring to?"

        elif q_lower in [
            "why",
            "why?",
            "how",
            "how?",
            "explain more",
            "continue",
            "expand",
            "show details"
        ]:
            return f"{current_query} regarding the previous analysis of: {last_query}"

        # ----------------------------
        # Preserve your existing logic
        # ----------------------------

        elif "compare" in q_lower and ("it" in q_lower or "previous" in q_lower or "last" in q_lower):
            return f"Compare the results of '{last_query}' with {current_query}"

        elif "same analysis" in q_lower or "for " in q_lower or "only " in q_lower:
            return f"{last_query} applied for {current_query}"

        elif "forecast" in q_lower:
            return f"Forecast performance based on previous request: {last_query}"

        elif "drill down" in q_lower or "go deeper" in q_lower:
            return f"Drill down and expand further on previous analysis: {last_query}"

        elif "only" in q_lower or "in " in q_lower:
            return f"{last_query} restricted to {current_query}"

        else:
            return f"{current_query} in the context of previous request: {last_query}"


class AgentState(TypedDict, total=False):
    """
    Shared state passed between agents.
    """
    user_query: str
    resolved_query: str
    intent: str
    selected_tools: list[str]
    tool_results: dict[str, Any]
    insights: list[str]
    recommendations: list[str]
    final_response: str
    errors: list[str]
    conversation_history: list[dict[str, Any]]
    memory_manager: Any