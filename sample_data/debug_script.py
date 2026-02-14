"""
Debug script — exercises every check type against sample data.
Use with the "DQC: Programmatic API" VS Code launch configuration.
"""

import polars as pl
from data_quality_checker import DataQualityChecker, DBConnector

db = DBConnector("sample_data/debug_validation.db")
checker = DataQualityChecker(db)

# ── Load the "mixed failures" dataset ──
df = pl.read_csv("sample_data/05_mixed_failures.csv")
print(f"Loaded {df.shape[0]} rows, {df.shape[1]} columns")
print(df)
print()

# ── not_null checks ──
for col in ["uuid_inventario", "occurrence_type", "target_name", "next_state_prediction"]:
    result = checker.is_column_not_null(df, col)
    print(f"not_null({col}): {result}")

# ── unique check ──
result = checker.is_column_unique(df, "uuid_inventario")
print(f"unique(uuid_inventario): {result}")

# ── accepted_values check ──
accepted = [
    "Monitoração de Drenagem Profunda",
    "Monitoração de OAE",
    "Monitoração de Sinalização Horizontal - Longitudinal e Tachas",
    "Monitoração de Sinalização Horizontal - Marcas Viárias",
    "Monitoração de Sinalização Horizontal - Zebrados",
    "Monitoração de Sinalização Vertical",
    "Monitoração de Terraplenos e Estruturas de Contenção",
]
result = checker.is_column_enum(df, "occurrence_type", accepted)
print(f"accepted_values(occurrence_type): {result}")

# ── referential integrity check ──
parent_df = pl.read_csv("sample_data/09_parent_departments.csv")
child_df = pl.read_csv("sample_data/09_child_employees_orphans.csv")
result = checker.are_tables_referential_integral(
    parent_df, child_df, "department_id", "department_id"
)
print(f"referential_integrity(department_id): {result}")

# ── Print all logs ──
print("\n--- Validation Log ---")
db.print_all_logs()
