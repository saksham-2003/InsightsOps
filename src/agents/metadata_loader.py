"""
Metadata Loader Module for InsightsOps BI Platform.

This module provides functionality to extract, cache, and structure unique 
business entities from a pandas DataFrame to support metadata-driven operations.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import pandas as pd


@dataclass
class BusinessMetadata:
    """Structured container holding unique, sorted business metadata entities."""
    regions: List[str] = field(default_factory=list)
    countries: List[str] = field(default_factory=list)
    states: List[str] = field(default_factory=list)
    cities: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    sub_categories: List[str] = field(default_factory=list)
    products: List[str] = field(default_factory=list)
    customers: List[str] = field(default_factory=list)


class MetadataLoader:
    """
    Loader responsible for extracting unique business entities from a pandas DataFrame 
    with built-in caching and robust error handling.
    """

    def __init__(self, df: Optional[pd.DataFrame] = None) -> None:
        """
        Initializes the MetadataLoader with a source DataFrame.

        Args:
            df (Optional[pd.DataFrame]): The source pandas DataFrame containing business data.
        """
        self.df = df
        self._cached_metadata: Optional[BusinessMetadata] = None

    def load(self) -> BusinessMetadata:
        """
        Extracts unique business entities from the DataFrame. 
        Caches the result after the first successful computation.

        Returns:
            BusinessMetadata: A populated dataclass containing sorted unique lists for each entity type.
        """
        # Return cached metadata if already computed
        if self._cached_metadata is not None:
            return self._cached_metadata

        # Initialize with empty metadata in case df is invalid or missing
        metadata = BusinessMetadata()

        if self.df is None or not isinstance(self.df, pd.DataFrame) or self.df.empty:
            self._cached_metadata = metadata
            return metadata

        try:
            # Column mapping configuration: (DataFrame Column Name -> BusinessMetadata attribute)
            column_mapping = {
                "Region": "regions",
                "Country": "countries",
                "State": "states",
                "City": "cities",
                "Category": "categories",
                "Sub_Category": "sub_categories",
                "Product_Name": "products",
                "Customer_Name": "customers"
            }

            extracted_data = {}

            for col, attr in column_mapping.items():
                if col in self.df.columns:
                    # Drop nulls, convert to string, strip whitespace, drop duplicates, and sort alphabetically
                    unique_values = (
                        self.df[col]
                        .dropna()
                        .astype(str)
                        .str.strip()
                    )
                    # Filter out empty strings after strip if any
                    unique_values = unique_values[unique_values != ""]
                    
                    sorted_unique_list = sorted(unique_values.unique().tolist())
                    extracted_data[attr] = sorted_unique_list
                else:
                    extracted_data[attr] = []

            metadata = BusinessMetadata(**extracted_data)

        except Exception:
            # Never raise exceptions as per requirements; fallback to empty metadata
            pass

        # Cache the result
        self._cached_metadata = metadata
        return metadata