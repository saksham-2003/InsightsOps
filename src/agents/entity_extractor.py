"""
Metadata-Driven Entity Extraction Module for InsightsOps BI Platform.

This module provides an advanced rule-based and metadata-driven EntityExtractor 
that maps natural language queries to structured business filters (ExtractedEntities) 
using dynamic values supplied by BusinessMetadata.
"""

from dataclasses import dataclass
import re
from typing import Optional, List, Dict, Any, Tuple
from src.agents.metadata_loader import BusinessMetadata

@dataclass
class ExtractedEntities:
    """Structured representation of extracted business entities and metadata context."""
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
    confidence: float = 0.0


class EntityExtractor:
    """
    Metadata-driven Entity Extractor that uses dynamic BusinessMetadata 
    to resolve business entities from natural language queries without hardcoded lists.
    """

    def __init__(self, metadata: BusinessMetadata) -> None:
        """
        Initializes the EntityExtractor with reference BusinessMetadata.

        Args:
            metadata (BusinessMetadata): The loaded business metadata container.
        """
        self.metadata = metadata or BusinessMetadata()
        
        # Static sets for operational tokens (metrics, temporal keywords, comparison keywords)
        self.static_metrics = {"revenue", "profit", "orders", "sales", "quantity"}
        self.static_aggregations = {"average", "maximum", "minimum", "top", "bottom", "growth"}
        self.comparison_keywords = {"compare", "vs", "versus", "against", "with"}
        self.months = {
            "january", "february", "march", "april", "may", "june",
            "july", "august", "september", "october", "november", "december"
        }

    def _match_metadata_entity(self, query_lower: str, values: List[str]) -> Optional[str]:
        """
        Helper method to perform case-insensitive and partial substring matching 
        against a list of metadata values, prioritizing longer/exact matches.
        """
        if not values or not query_lower:
            return None

        # Sort values by length descending to match more specific entities first (e.g., 'MacBook Air' before 'Air')
        sorted_values = sorted(values, key=len, reverse=True)
        
        for val in sorted_values:
            if not val:
                continue
            val_lower = val.lower()
            if val_lower in query_lower:
                return val
        return None

    def extract(self, query: str) -> ExtractedEntities:
        """
        Extracts business entities and computes confidence score from a natural language query.

        Args:
            query (str): The natural language query string.

        Returns:
            ExtractedEntities: Populated dataclass containing extracted filters and confidence.
        """
        if not query or not isinstance(query, str):
            return ExtractedEntities(confidence=0.0)

        try:
            cleaned_query = query.strip()
            query_lower = cleaned_query.lower()
            tokens = set(re.findall(r'\b\w+\b', query_lower))

            extracted_data: Dict[str, Any] = {}
            matched_entities_count = 0

            # 1. Metadata-Driven Entity Extractions
            # Region
            region = self._match_metadata_entity(query_lower, self.metadata.regions)
            if region:
                extracted_data["region"] = region
                matched_entities_count += 1

            # Country
            country = self._match_metadata_entity(query_lower, self.metadata.countries)
            if country:
                extracted_data["country"] = country
                matched_entities_count += 1

            # State
            state = self._match_metadata_entity(query_lower, self.metadata.states)
            if state:
                extracted_data["state"] = state
                matched_entities_count += 1

            # City
            city = self._match_metadata_entity(query_lower, self.metadata.cities)
            if city:
                extracted_data["city"] = city
                matched_entities_count += 1

            # Category
            category = self._match_metadata_entity(query_lower, self.metadata.categories)
            if category:
                extracted_data["category"] = category
                matched_entities_count += 1

            # Sub-Category
            sub_category = self._match_metadata_entity(query_lower, self.metadata.sub_categories)
            if sub_category:
                extracted_data["sub_category"] = sub_category
                matched_entities_count += 1

            # Product
            product = self._match_metadata_entity(query_lower, self.metadata.products)
            if product:
                extracted_data["product"] = product
                matched_entities_count += 1

            # Customer
            customer = self._match_metadata_entity(query_lower, self.metadata.customers)
            if customer:
                extracted_data["customer"] = customer
                matched_entities_count += 1

            # 2. Time Extraction (Years, Quarters, Months, Date Ranges)
            # Year (4-digit numbers starting with 19 or 20)
            year_match = re.search(r'\b(19\d{2}|20\d{2})\b', cleaned_query)
            if year_match:
                extracted_data["year"] = year_match.group(1)
                matched_entities_count += 1
            elif "last year" in query_lower:
                extracted_data["year"] = "Last Year"
                matched_entities_count += 1

            # Quarter (Q1, Q2, Q3, Q4)
            quarter_match = re.search(r'\b(q[1-4])\b', query_lower)
            if quarter_match:
                extracted_data["quarter"] = quarter_match.group(1).upper()
                matched_entities_count += 1

            # Month
            for month in self.months:
                if month in tokens or month in query_lower:
                    extracted_data["month"] = month.capitalize()
                    matched_entities_count += 1
                    break

            if "this month" in query_lower:
                extracted_data["month"] = "This Month"
                matched_entities_count += 1

            # Date Range (e.g., between X and Y)
            date_range_match = re.search(r'\bbetween\s+([a-zA-Z0-9\s]+)\s+and\s+([a-zA-Z0-9\s]+)', query_lower)
            if date_range_match:
                extracted_data["date_range"] = f"Between {date_range_match.group(1).strip().title()} and {date_range_match.group(2).strip().title()}"
                matched_entities_count += 1

            # 3. Metrics and Aggregations Extraction
            found_metrics = [m for m in self.static_metrics if m in tokens or m in query_lower]
            found_aggs = [a for a in self.static_aggregations if a in tokens or a in query_lower]

            if found_metrics and found_aggs:
                extracted_data["metric"] = f"{found_aggs[0].capitalize()} {found_metrics[0].capitalize()}"
                matched_entities_count += 1
            elif found_metrics:
                extracted_data["metric"] = found_metrics[0].capitalize()
                matched_entities_count += 1
            elif found_aggs:
                extracted_data["metric"] = found_aggs[0].capitalize()
                matched_entities_count += 1

            # 4. Comparison Detection
            if any(comp_kw in tokens for comp_kw in self.comparison_keywords) or any(comp_kw in query_lower for comp_kw in self.comparison_keywords):
                # Attempt to extract what follows the comparison keyword
                comp_pattern = re.compile(r'(?:compare|vs\.?|versus|against|with)\s+([a-zA-Z0-9\s]+?)(?:\s+and\s+([a-zA-Z0-9\s]+))?', re.IGNORECASE)
                comp_match = comp_pattern.search(query_lower)
                if comp_match:
                    candidates = [c.strip().title() for c in comp_match.groups() if c]
                    if candidates:
                        comp_val = candidates[0]
                        # Ensure comparison isn't duplicating primary category if another option exists
                        if extracted_data.get("category") and comp_val.lower() == extracted_data.get("category", "").lower():
                            if len(candidates) > 1:
                                comp_val = candidates[1]
                        extracted_data["comparison"] = comp_val
                        matched_entities_count += 1
                else:
                    extracted_data["comparison"] = "True"
                    matched_entities_count += 1

            # 5. Confidence Calculation (0.0 to 1.0 based on matched entities count)
            # Scales nicely: 1 entity = 0.35, 2 entities = 0.65, 3+ entities = 0.9 - 1.0 max
            if matched_entities_count == 0:
                confidence = 0.0
            else:
                confidence = min(1.0, 0.2 + (matched_entities_count * 0.25))

            extracted_data["confidence"] = round(confidence, 2)

            return ExtractedEntities(**extracted_data)

        except Exception:
            # Never raise exceptions as per requirements
            return ExtractedEntities(confidence=0.0)