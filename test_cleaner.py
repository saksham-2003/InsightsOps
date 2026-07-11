from src.data_loader import load_data
from src.data_cleaner import clean_data


file_path = "data/raw/data.csv"


# Load raw data
df = load_data(file_path)


# Clean data
cleaned_df, report = clean_data(df)


print("\n===== CLEANING REPORT =====")


print("\nOriginal Rows:")
print(report["original_rows"])


print("\nDuplicates Removed:")
print(report["duplicates_removed"])


print("\nColumns Renamed:")

for change in report["columns_renamed"]:
    print(
        f"{repr(change['old'])} -> {repr(change['new'])}"
    )


print("\nDate Columns Converted:")
print(report["date_columns_converted"])


print("\nFinal Rows:")
print(report["final_rows"])


print("\nCleaned Column Names:")
print(cleaned_df.columns.tolist())


print("\nCleaned Data Types:")
print(cleaned_df.dtypes)