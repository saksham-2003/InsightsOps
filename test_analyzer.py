from src.data_loader import load_data
from src.analyzer import analyze_data_quality


file_path = "data/raw/data.csv"

df = load_data(file_path)

report = analyze_data_quality(df)


print("\n===== DATA QUALITY REPORT =====")

print("\nDataset Shape:")
print(f"Rows: {report['rows']}")
print(f"Columns: {report['columns']}")

print("\nMissing Values:")
for column, missing in report["missing_values"].items():
    print(f"{column}: {missing}")

print("\nDuplicate Rows:")
print(report["duplicate_rows"])

print("\nData Types:")
for column, dtype in report["data_types"].items():
    print(f"{column}: {dtype}")

print("\nUnique Values:")
for column, unique in report["unique_values"].items():
    print(f"{column}: {unique}")

print("\nColumn Name Issues:")
print(report["column_name_issues"])