from functools import lru_cache

from src.data_loader import load_data
from src.data_cleaner import clean_data


@lru_cache(maxsize=1)
def get_cleaned_dataframe():
    """
    Load and clean the default dataset once.

    The cleaned DataFrame is cached and reused
    across API requests.
    """

    file_path = "data/raw/data.csv"

    df = load_data(file_path)

    cleaned_df, _ = clean_data(df)

    return cleaned_df