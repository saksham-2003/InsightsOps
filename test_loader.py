from src.data_loader import load_data


file_path = "data/raw/data.csv"

df = load_data(file_path)


print("\nDataset loaded successfully!")

print("\nShape:")
print(df.shape)

print("\nColumns:")
print(df.columns.tolist())

print("\nFirst 5 rows:")
print(df.head())