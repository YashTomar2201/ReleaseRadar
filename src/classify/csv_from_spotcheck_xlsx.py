"""Convert the filled-in spotcheck_blind.xlsx back to spotcheck_blind.csv
so score_spotcheck.py can read it. Run this after labeling is complete.
"""
import pandas as pd

SRC = r"D:\projects\non-tech\data\labels\spotcheck_blind.xlsx"
DST = r"D:\projects\non-tech\data\labels\spotcheck_blind.csv"

df = pd.read_excel(SRC, dtype=str).fillna("")
df.to_csv(DST, index=False)
print(f"Wrote {DST} ({len(df)} rows)")
