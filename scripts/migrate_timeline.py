from pathlib import Path
import pandas as pd

# ==========================================================
# InsightsOps Timeline Migration
#
# Converts:
#   2023 -> 2025
#   2024 -> 2026
#
# Original file is NEVER modified.
# A new dataset is created.
# ==========================================================

INPUT_FILE = Path("data/raw/data.csv")
OUTPUT_FILE = Path("data/raw/data_2025_2026.csv")


def main():

    print("=" * 60)
    print("InsightsOps Timeline Migration")
    print("=" * 60)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Could not find:\n{INPUT_FILE}")

    print("\nLoading dataset...")
    df = pd.read_csv(INPUT_FILE)

    print(f"Rows Loaded : {len(df):,}")

    # ------------------------------------------------------
    # Validate column
    # ------------------------------------------------------
    if "Order_Date" not in df.columns:
        raise Exception("Order_Date column not found.")

    # ------------------------------------------------------
    # Convert to datetime
    # ------------------------------------------------------
    df["Order_Date"] = pd.to_datetime(
        df["Order_Date"],
        format="%m-%d-%y",
        errors="raise"
    )

    original_start = df["Order_Date"].min()
    original_end = df["Order_Date"].max()

    print("\nOriginal Timeline")
    print("----------------------------")
    print("Start :", original_start.date())
    print("End   :", original_end.date())

    # ------------------------------------------------------
    # Shift every date by exactly 2 years
    # 2023 -> 2025
    # 2024 -> 2026
    # ------------------------------------------------------
    df["Order_Date"] = df["Order_Date"] + pd.DateOffset(years=2)

    new_start = df["Order_Date"].min()
    new_end = df["Order_Date"].max()

    print("\nNew Timeline")
    print("----------------------------")
    print("Start :", new_start.date())
    print("End   :", new_end.date())

    # ------------------------------------------------------
    # Convert back to original format
    # ------------------------------------------------------
    df["Order_Date"] = df["Order_Date"].dt.strftime("%m-%d-%y")

    # ------------------------------------------------------
    # Save
    # ------------------------------------------------------
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\nDataset successfully migrated.")
    print(f"\nSaved to:\n{OUTPUT_FILE}")

    print("\nVerification")
    print("----------------------------")
    print(f"Rows               : {len(df):,}")
    print(f"Historical Start   : {new_start.date()}")
    print(f"Historical End     : {new_end.date()}")

    print("\nMigration completed successfully.")
    print("=" * 60)


if __name__ == "__main__":
    main()