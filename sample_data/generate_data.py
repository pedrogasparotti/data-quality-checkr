"""
Generate all sample test data for data-quality-checker.

Run once:  python sample_data/generate_data.py
Produces CSV, Parquet, and YAML files inside sample_data/.
"""

import polars as pl
import yaml
from pathlib import Path

OUT = Path(__file__).parent

# ─────────────────────────────────────────────────────────────
# Canonical enum values (from the real checks.yml)
# ─────────────────────────────────────────────────────────────
OCCURRENCE_TYPES = [
    "Monitoração de Drenagem Profunda",
    "Monitoração de OAE",
    "Monitoração de Sinalização Horizontal - Longitudinal e Tachas",
    "Monitoração de Sinalização Horizontal - Marcas Viárias",
    "Monitoração de Sinalização Horizontal - Zebrados",
    "Monitoração de Sinalização Vertical",
    "Monitoração de Terraplenos e Estruturas de Contenção",
]

PREDICTIONS = ["stable", "degrading", "improving", "critical"]


# ═════════════════════════════════════════════════════════════
# 1. GOLDEN DATASET — all checks pass
# ═════════════════════════════════════════════════════════════
golden = pl.DataFrame({
    "uuid_inventario": [f"INV-{i:04d}" for i in range(1, 21)],
    "occurrence_type": [
        OCCURRENCE_TYPES[i % len(OCCURRENCE_TYPES)] for i in range(20)
    ],
    "target_name": [
        "Bridge Alpha", "Bridge Beta", "Tunnel Gamma", "Dam Delta",
        "Road Epsilon", "Sign Zeta", "Wall Eta", "Bridge Theta",
        "Tunnel Iota", "Dam Kappa", "Road Lambda", "Sign Mu",
        "Wall Nu", "Bridge Xi", "Tunnel Omicron", "Dam Pi",
        "Road Rho", "Sign Sigma", "Wall Tau", "Bridge Upsilon",
    ],
    "next_state_prediction": [
        PREDICTIONS[i % len(PREDICTIONS)] for i in range(20)
    ],
})
golden.write_csv(OUT / "01_golden.csv")
golden.write_parquet(OUT / "01_golden.parquet")


# ═════════════════════════════════════════════════════════════
# 2. NULLS — scattered nulls across checked columns
# ═════════════════════════════════════════════════════════════
nulls = pl.DataFrame({
    "uuid_inventario": [
        "INV-0001", None, "INV-0003", "INV-0004", "INV-0005",
        "INV-0006", "INV-0007", None, "INV-0009", "INV-0010",
    ],
    "occurrence_type": [
        OCCURRENCE_TYPES[0], OCCURRENCE_TYPES[1], None, OCCURRENCE_TYPES[3],
        OCCURRENCE_TYPES[4], None, OCCURRENCE_TYPES[6], OCCURRENCE_TYPES[0],
        OCCURRENCE_TYPES[1], None,
    ],
    "target_name": [
        "Bridge A", "Bridge B", "Tunnel C", None, "Road E",
        "Sign F", None, "Bridge H", "Tunnel I", "Dam J",
    ],
    "next_state_prediction": [
        "stable", None, "degrading", "improving", None,
        "stable", "critical", "degrading", None, "stable",
    ],
})
nulls.write_csv(OUT / "02_nulls.csv")


# ═════════════════════════════════════════════════════════════
# 3. DUPLICATES — uuid_inventario has repeated values
# ═════════════════════════════════════════════════════════════
duplicates = pl.DataFrame({
    "uuid_inventario": [
        "INV-0001", "INV-0002", "INV-0001",  # dup at row 3
        "INV-0004", "INV-0005", "INV-0002",  # dup at row 6
        "INV-0007", "INV-0007", "INV-0009",  # dup at row 8
        "INV-0010",
    ],
    "occurrence_type": [OCCURRENCE_TYPES[i % len(OCCURRENCE_TYPES)] for i in range(10)],
    "target_name": [f"Target_{i}" for i in range(1, 11)],
    "next_state_prediction": [PREDICTIONS[i % len(PREDICTIONS)] for i in range(10)],
})
duplicates.write_csv(OUT / "03_duplicates.csv")


# ═════════════════════════════════════════════════════════════
# 4. BAD ENUM VALUES — occurrence_type has invalid entries
# ═════════════════════════════════════════════════════════════
bad_enum = pl.DataFrame({
    "uuid_inventario": [f"INV-{i:04d}" for i in range(1, 13)],
    "occurrence_type": [
        OCCURRENCE_TYPES[0],
        OCCURRENCE_TYPES[1],
        "Inspeção Visual",               # invalid
        OCCURRENCE_TYPES[3 % len(OCCURRENCE_TYPES)],
        "Manutenção Corretiva",           # invalid
        OCCURRENCE_TYPES[5 % len(OCCURRENCE_TYPES)],
        OCCURRENCE_TYPES[6 % len(OCCURRENCE_TYPES)],
        "Reparo Emergencial",             # invalid
        OCCURRENCE_TYPES[0],
        OCCURRENCE_TYPES[1],
        "",                               # empty string (not null — subtle!)
        OCCURRENCE_TYPES[2],
    ],
    "target_name": [f"Target_{i}" for i in range(1, 13)],
    "next_state_prediction": [PREDICTIONS[i % len(PREDICTIONS)] for i in range(12)],
})
bad_enum.write_csv(OUT / "04_bad_enum.csv")


# ═════════════════════════════════════════════════════════════
# 5. MIXED FAILURES — every check type fails simultaneously
# ═════════════════════════════════════════════════════════════
mixed = pl.DataFrame({
    "uuid_inventario": [
        "INV-0001", "INV-0002", "INV-0001",  # dup
        None, "INV-0005", "INV-0006",         # null uuid
        "INV-0007", "INV-0008",
    ],
    "occurrence_type": [
        OCCURRENCE_TYPES[0], None,             # null
        OCCURRENCE_TYPES[2], OCCURRENCE_TYPES[3],
        "Tipo Desconhecido",                   # invalid enum
        OCCURRENCE_TYPES[5], OCCURRENCE_TYPES[6],
        OCCURRENCE_TYPES[0],
    ],
    "target_name": [
        "Bridge A", "Bridge B", None, "Dam D",  # null
        "Road E", "Sign F", "Wall G", "Bridge H",
    ],
    "next_state_prediction": [
        "stable", "degrading", "improving", None,  # null
        "stable", "critical", None, "degrading",   # null
    ],
})
mixed.write_csv(OUT / "05_mixed_failures.csv")


# ═════════════════════════════════════════════════════════════
# 6. EMPTY DATASET — zero rows, only headers
# ═════════════════════════════════════════════════════════════
empty = pl.DataFrame({
    "uuid_inventario": pl.Series([], dtype=pl.Utf8),
    "occurrence_type": pl.Series([], dtype=pl.Utf8),
    "target_name": pl.Series([], dtype=pl.Utf8),
    "next_state_prediction": pl.Series([], dtype=pl.Utf8),
})
empty.write_csv(OUT / "06_empty.csv")


# ═════════════════════════════════════════════════════════════
# 7. SINGLE ROW — boundary test
# ═════════════════════════════════════════════════════════════
single = pl.DataFrame({
    "uuid_inventario": ["INV-SOLO"],
    "occurrence_type": [OCCURRENCE_TYPES[0]],
    "target_name": ["Solo Target"],
    "next_state_prediction": ["stable"],
})
single.write_csv(OUT / "07_single_row.csv")


# ═════════════════════════════════════════════════════════════
# 8. LARGE DATASET — 10k rows for performance/stress testing
# ═════════════════════════════════════════════════════════════
import random
random.seed(42)

n = 10_000
large_uuids = [f"INV-{i:06d}" for i in range(n)]
# inject 50 random duplicates
for _ in range(50):
    src = random.randint(0, n - 1)
    dst = random.randint(0, n - 1)
    large_uuids[dst] = large_uuids[src]

large_occ = [random.choice(OCCURRENCE_TYPES) for _ in range(n)]
# inject 20 invalid values
for _ in range(20):
    large_occ[random.randint(0, n - 1)] = "INVALID_TYPE"

large_targets = [f"Target_{i}" for i in range(n)]

large_preds = [random.choice(PREDICTIONS) for _ in range(n)]
# inject 100 nulls across columns
large_nulls_uuid = random.sample(range(n), 30)
large_nulls_occ = random.sample(range(n), 40)
large_nulls_pred = random.sample(range(n), 30)

large_uuids_final = [None if i in large_nulls_uuid else large_uuids[i] for i in range(n)]
large_occ_final = [None if i in large_nulls_occ else large_occ[i] for i in range(n)]
large_preds_final = [None if i in large_nulls_pred else large_preds[i] for i in range(n)]

large = pl.DataFrame({
    "uuid_inventario": large_uuids_final,
    "occurrence_type": large_occ_final,
    "target_name": large_targets,
    "next_state_prediction": large_preds_final,
})
large.write_csv(OUT / "08_large_10k.csv")
large.write_parquet(OUT / "08_large_10k.parquet")


# ═════════════════════════════════════════════════════════════
# 9. REFERENTIAL INTEGRITY — parent + child tables
# ═════════════════════════════════════════════════════════════
parent = pl.DataFrame({
    "department_id": ["D001", "D002", "D003", "D004", "D005"],
    "department_name": ["Engineering", "Marketing", "Finance", "Operations", "HR"],
})
parent.write_csv(OUT / "09_parent_departments.csv")

# child with valid refs
child_clean = pl.DataFrame({
    "employee_id": [f"E{i:03d}" for i in range(1, 11)],
    "name": [
        "Alice", "Bob", "Charlie", "Diana", "Eve",
        "Frank", "Grace", "Hank", "Ivy", "Jack",
    ],
    "department_id": [
        "D001", "D002", "D003", "D001", "D004",
        "D005", "D002", "D003", "D001", "D005",
    ],
})
child_clean.write_csv(OUT / "09_child_employees_clean.csv")

# child with orphan foreign keys
child_orphans = pl.DataFrame({
    "employee_id": [f"E{i:03d}" for i in range(1, 11)],
    "name": [
        "Alice", "Bob", "Charlie", "Diana", "Eve",
        "Frank", "Grace", "Hank", "Ivy", "Jack",
    ],
    "department_id": [
        "D001", "D002", "D999",  # orphan
        "D001", "D004",
        "D005", "D888",          # orphan
        "D003", "D777",          # orphan
        "D005",
    ],
})
child_orphans.write_csv(OUT / "09_child_employees_orphans.csv")


# ═════════════════════════════════════════════════════════════
# 10. UNICODE / ENCODING STRESS — accents, special chars
# ═════════════════════════════════════════════════════════════
unicode_stress = pl.DataFrame({
    "uuid_inventario": [f"INV-{i:04d}" for i in range(1, 9)],
    "occurrence_type": [
        "Monitoração de OAE",                # valid, has ã
        "Monitoração de Sinalização Vertical",  # valid, has ç, ã
        "Monitoração de Drenagem Profunda",   # valid
        "Monitoração de Terraplenos e Estruturas de Contenção",  # valid, has ç, ã
        "Monitoraçao de OAE",                # TYPO: ç instead of çã
        "Monitoração  de OAE",               # DOUBLE SPACE
        "monitoração de oae",                # LOWERCASE
        " Monitoração de OAE",               # LEADING SPACE
    ],
    "target_name": [
        "Ponte São João", "Túnel Ipê-Amarelo", "Barragem Itaúna",
        "Rodovia BR-101", "Sinalização km 42,5", "Muro Nº 7",
        "Contenção — Setor B", "Drenagem (Trecho 3/A)",
    ],
    "next_state_prediction": [PREDICTIONS[i % len(PREDICTIONS)] for i in range(8)],
})
unicode_stress.write_csv(OUT / "10_unicode_stress.csv")


# ═════════════════════════════════════════════════════════════
# 11. TYPE COERCION TRAPS — numeric-looking strings, booleans
# ═════════════════════════════════════════════════════════════
type_traps = pl.DataFrame({
    "uuid_inventario": [
        "001", "002", "003", "004", "005",
        "006", "007", "008", "009", "010",
    ],
    "occurrence_type": [
        OCCURRENCE_TYPES[0], OCCURRENCE_TYPES[1], OCCURRENCE_TYPES[2],
        OCCURRENCE_TYPES[3], OCCURRENCE_TYPES[4], OCCURRENCE_TYPES[5],
        OCCURRENCE_TYPES[6], OCCURRENCE_TYPES[0], OCCURRENCE_TYPES[1],
        OCCURRENCE_TYPES[2],
    ],
    "target_name": [
        "0", "1", "true", "false", "None",
        "null", "NaN", "inf", "-1", "3.14",
    ],
    "next_state_prediction": [
        "stable", "degrading", "improving", "critical",
        "stable", "degrading", "improving", "critical",
        "stable", "degrading",
    ],
})
type_traps.write_csv(OUT / "11_type_coercion_traps.csv")


# ═════════════════════════════════════════════════════════════
# YAML CONFIGS — one per scenario
# ═════════════════════════════════════════════════════════════

# Full config matching checks.yml (not_null + accepted_values)
full_config = {
    "db": "sample_data/validation_results.db",
    "checks": [
        {"type": "not_null", "column": "uuid_inventario"},
        {"type": "not_null", "column": "occurrence_type"},
        {"type": "not_null", "column": "target_name"},
        {"type": "not_null", "column": "next_state_prediction"},
        {"type": "unique", "column": "uuid_inventario"},
        {
            "type": "accepted_values",
            "column": "occurrence_type",
            "values": OCCURRENCE_TYPES,
        },
    ],
}
with open(OUT / "checks_full.yml", "w") as f:
    yaml.dump(full_config, f, default_flow_style=False, allow_unicode=True)

# Nulls-only config
null_config = {
    "db": "sample_data/validation_results.db",
    "checks": [
        {"type": "not_null", "column": "uuid_inventario"},
        {"type": "not_null", "column": "occurrence_type"},
        {"type": "not_null", "column": "target_name"},
        {"type": "not_null", "column": "next_state_prediction"},
    ],
}
with open(OUT / "checks_nulls_only.yml", "w") as f:
    yaml.dump(null_config, f, default_flow_style=False, allow_unicode=True)

# Unique-only config
unique_config = {
    "db": "sample_data/validation_results.db",
    "checks": [
        {"type": "unique", "column": "uuid_inventario"},
    ],
}
with open(OUT / "checks_unique_only.yml", "w") as f:
    yaml.dump(unique_config, f, default_flow_style=False, allow_unicode=True)

# Enum-only config
enum_config = {
    "db": "sample_data/validation_results.db",
    "checks": [
        {
            "type": "accepted_values",
            "column": "occurrence_type",
            "values": OCCURRENCE_TYPES,
        },
    ],
}
with open(OUT / "checks_enum_only.yml", "w") as f:
    yaml.dump(enum_config, f, default_flow_style=False, allow_unicode=True)


# ═════════════════════════════════════════════════════════════
# DEBUG SCRIPT — exercises every check against the mixed file
# ═════════════════════════════════════════════════════════════
debug_script = '''\
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
print("\\n--- Validation Log ---")
db.print_all_logs()
'''

with open(OUT / "debug_script.py", "w") as f:
    f.write(debug_script)


# ═════════════════════════════════════════════════════════════
# Summary
# ═════════════════════════════════════════════════════════════
files = sorted(OUT.glob("*"))
print(f"\nGenerated {len(files)} files in {OUT}/:\n")
for f in files:
    if f.name == Path(__file__).name:
        continue
    size = f.stat().st_size
    unit = "KB" if size > 1024 else "B"
    val = size / 1024 if size > 1024 else size
    print(f"  {f.name:<45} {val:>7.1f} {unit}")
