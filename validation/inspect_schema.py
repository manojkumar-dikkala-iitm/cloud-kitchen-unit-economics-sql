from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


TABLES = [
    "outlets",
    "platforms",
    "menu_items",
    "menu_item_prices",
    "customers",
    "orders",
    "order_items",
    "promotions",
    "item_availability",
    "wastage",
    "expenses",
    "daily_operations",
]


print("=" * 80)
print("E-TABLE FOODS — GENERATED DATA SCHEMA INSPECTION")
print("=" * 80)


for table in TABLES:

    filepath = DATA_DIR / f"{table}.csv"

    df = pd.read_csv(filepath)

    print("\n" + "-" * 80)
    print(f"{table.upper()}")
    print("-" * 80)

    print(f"Rows: {len(df):,}")

    print("\nColumns:")

    for i, column in enumerate(df.columns, start=1):

        dtype = df[column].dtype
        nulls = df[column].isna().sum()
        unique = df[column].nunique(dropna=True)

        print(
            f"  {i:2}. {column:<30} "
            f"dtype={str(dtype):<12} "
            f"nulls={nulls:<8,} "
            f"unique={unique:<8,}"
        )

    print("\nFirst 3 rows:")

    print(df.head(3).to_string(index=False))


# ============================================================
# EXPENSE OUTLET INVESTIGATION
# ============================================================

print("\n" + "=" * 80)
print("EXPENSE OUTLET INVESTIGATION")
print("=" * 80)

expenses = pd.read_csv(DATA_DIR / "expenses.csv")
outlets = pd.read_csv(DATA_DIR / "outlets.csv")


print("\nValid outlet IDs:")
print(sorted(outlets["outlet_id"].dropna().unique().tolist()))


if "outlet_id" in expenses.columns:

    print("\nExpense outlet IDs:")
    print(
        expenses["outlet_id"]
        .value_counts(dropna=False)
        .sort_index()
        .to_string()
    )

    valid_ids = set(outlets["outlet_id"].dropna())

    orphan_mask = (
        expenses["outlet_id"].notna()
        & ~expenses["outlet_id"].isin(valid_ids)
    )

    orphan_expenses = expenses[orphan_mask]

    print(
        f"\nOrphan expense records: "
        f"{len(orphan_expenses):,}"
    )

    if len(orphan_expenses) > 0:

        print("\nOrphan outlet IDs:")

        print(
            orphan_expenses["outlet_id"]
            .value_counts()
            .sort_index()
            .to_string()
        )

        print("\nSample orphan expense records:")

        print(
            orphan_expenses.head(20).to_string(index=False)
        )

else:

    print("\nexpenses.csv does not contain outlet_id.")


# ============================================================
# DAILY OPERATIONS INVESTIGATION
# ============================================================

print("\n" + "=" * 80)
print("DAILY OPERATIONS INVESTIGATION")
print("=" * 80)

daily = pd.read_csv(DATA_DIR / "daily_operations.csv")

print("\nRows:", f"{len(daily):,}")

print("\nColumns:")
print(list(daily.columns))


if "outlet_id" in daily.columns and "operation_date" in daily.columns:

    duplicate_pairs = daily.duplicated(
        subset=["outlet_id", "operation_date"]
    ).sum()

    print(
        "\nDuplicate outlet/date combinations:",
        duplicate_pairs
    )

    print("\nRows per outlet:")

    print(
        daily["outlet_id"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print("\nDate range:")

    dates = pd.to_datetime(
        daily["operation_date"],
        errors="coerce"
    )

    print("  Start:", dates.min())
    print("  End  :", dates.max())

    print("\nRows per outlet/date uniqueness check:")

    if duplicate_pairs == 0:
        print(
            "  ✅ (outlet_id, operation_date) is unique"
        )
    else:
        print(
            "  ❌ Duplicate outlet/date combinations found"
        )


print("\n" + "=" * 80)
print("INSPECTION COMPLETE")
print("=" * 80)