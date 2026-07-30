import pandas as pd


def clean_data(df):
    """
    Automatically clean common data quality issues.

    Returns:
        cleaned_df: Cleaned DataFrame
        cleaning_report: Dictionary containing cleaning actions
    """

    # Create copy so original data is not modified
    cleaned_df = df.copy()

    cleaning_report = {
        "original_rows": len(cleaned_df),
        "duplicates_removed": 0,
        "columns_renamed": [],
        "date_columns_converted": [],
        "final_rows": 0
    }


    # 1. Clean column names
    original_columns = cleaned_df.columns.tolist()

    cleaned_df.columns = [
        column.strip().replace(" ", "_")
        for column in cleaned_df.columns
    ]

    for old, new in zip(original_columns, cleaned_df.columns):
        if old != new:
            cleaning_report["columns_renamed"].append(
                {
                    "old": old,
                    "new": new
                }
            )


    # 2. Remove duplicate rows
    duplicate_count = cleaned_df.duplicated().sum()

    cleaned_df = cleaned_df.drop_duplicates()

    cleaning_report["duplicates_removed"] = int(duplicate_count)


    # 3. Automatically detect and convert date columns
    for column in cleaned_df.columns:

        if "date" in column.lower():

            try:
                cleaned_df[column] = pd.to_datetime(
                    cleaned_df[column],
                    format="%m-%d-%y",
                    errors="coerce"
                )

                # Shift dates for demo dataset
                cleaned_df[column] = cleaned_df[column] + pd.DateOffset(years=3)

                cleaning_report["date_columns_converted"].append(column)

            except Exception:
                pass


    # 4. Reset index
    cleaned_df = cleaned_df.reset_index(drop=True)


    cleaning_report["final_rows"] = len(cleaned_df)


    return cleaned_df, cleaning_report

    for column in cleaned_df.columns:
        if "date" in column.lower():
            print(f"{column} Range:")
            print(cleaned_df[column].min())
            print(cleaned_df[column].max())