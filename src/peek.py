from pathlib import Path

RAW = Path("data/raw/final_reports_2016-23_cons_2024-12-24.csv")

with open(RAW, "r", encoding="utf-8", errors="replace") as f:
    lines = [next(f) for _ in range(3)]

for i, line in enumerate(lines, 1):
    print(f"--- line {i} (first 300 chars) ---")
    print(line[:300])
    print()

print("--- delimiter counts in line 1 (the header) ---")
header = lines[0]
for name, ch in [("comma", ","), ("semicolon", ";"), ("tab", "\\t"), ("pipe", "|")]:
    print(f"{name:10} {header.count(ch)}")