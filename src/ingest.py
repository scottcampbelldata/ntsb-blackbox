# src/ingest.py  -  run locally, builds the structured DB and the document corpus
# Source CSV: Zenodo record 17096333, file final_reports_2016-23_cons_2024-12-24.csv
# NOTE: this file is SEMICOLON-delimited (European-style CSV), quoted, UTF-8.

import re
import sqlite3
from pathlib import Path

import pandas as pd

RAW = Path("data/raw/final_reports_2016-23_cons_2024-12-24.csv")
DB = Path("data/ntsb.db")
DOCS = Path("data/docs")
DOCS.mkdir(parents=True, exist_ok=True)
DB.parent.mkdir(parents=True, exist_ok=True)

# ----- 1. Load (semicolon separator, UTF-8) -----
df = pd.read_csv(RAW, sep=";", encoding="utf-8", low_memory=False)
print(f"Loaded {df.shape[0]} rows, {df.shape[1]} columns")
print("\nColumns as delivered:")
print(df.columns.tolist())

# ----- 2. Normalize column names to clean snake_case for predictable SQL -----
def to_snake(name):
    s = re.sub(r"(?<!^)(?=[A-Z])", "_", str(name))     # CamelCase -> Camel_Case
    s = re.sub(r"[^0-9a-zA-Z]+", "_", s).strip("_")
    return s.lower()

df.columns = [to_snake(c) for c in df.columns]
print("\nColumns after normalize:")
print(df.columns.tolist())

# The narrative column is the document side. Everything else is structured.
# Adjust these names if the printed columns differ.
TEXT_COL = "rep_text"
KEY_COL = "ntsb_no"

assert KEY_COL in df.columns, f"Expected key column {KEY_COL!r}, got {df.columns.tolist()}"
assert TEXT_COL in df.columns, f"Expected text column {TEXT_COL!r}, got {df.columns.tolist()}"

# ----- 3. Type coercion so SQL aggregates behave -----
for col in df.columns:
    if col.endswith("_count"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
if "event_date" in df.columns:
    df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce", utc=True)
    df["event_year"] = df["event_date"].dt.year

# ----- 4. Profile what is actually queryable (this output drives the eval design) -----
print("\n--- NULL RATE BY COLUMN ---")
null_rate = (df.isna().mean() * 100).round(1).sort_values(ascending=False)
print(null_rate.to_string())

print("\n--- LOW-CARDINALITY FIELDS (good SQL filters) ---")
for col in df.columns:
    if col == TEXT_COL:
        continue
    n_unique = df[col].nunique(dropna=True)
    if 1 < n_unique <= 30:
        print(f"\n{col}  ({n_unique} distinct):")
        print(df[col].value_counts(dropna=False).head(15).to_string())

if "event_year" in df.columns:
    print("\n--- ROWS PER YEAR ---")
    print(df["event_year"].value_counts(dropna=False).sort_index().to_string())

# ----- 5. Build the structured table (drop the heavy narrative text) -----
structured = df.drop(columns=[TEXT_COL])
con = sqlite3.connect(DB)
structured.to_sql("accidents", con, if_exists="replace", index=False)
con.execute(f"CREATE INDEX IF NOT EXISTS idx_key ON accidents({KEY_COL})")
con.commit()

print("\n--- SQLITE SCHEMA (this is what text-to-SQL will target) ---")
for row in con.execute("PRAGMA table_info(accidents)"):
    print(f"  {row[1]:<28} {row[2]}")
con.close()

# ----- 6. Split narratives into per-accident documents for the RAG side -----
written = 0
empty = 0
for _, r in df.iterrows():
    key = str(r[KEY_COL]).strip()
    text = r[TEXT_COL]
    if not key or pd.isna(text) or not str(text).strip():
        empty += 1
        continue
    safe = re.sub(r"[^0-9A-Za-z._-]", "_", key)
    (DOCS / f"{safe}.txt").write_text(str(text), encoding="utf-8")
    written += 1

print(f"\nWrote {written} narrative files to {DOCS}/")
print(f"Skipped {empty} rows with no usable narrative")
print(f"\nStructured DB: {DB}")
print("Ingest complete. Send me the printed schema and the profile output.")