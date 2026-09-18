"""Load issue_backlog_with_sensitivity.csv into DuckDB."""
import duckdb
import pandas as pd

df = pd.read_csv(r"D:\projects\non-tech\data\interim\issue_backlog_with_sensitivity.csv")
con = duckdb.connect(r"D:\projects\non-tech\data\warehouse\releaseradar.duckdb")
con.execute("CREATE SCHEMA IF NOT EXISTS raw")
con.execute("DROP TABLE IF EXISTS raw.issue_backlog")
con.execute("CREATE TABLE raw.issue_backlog AS SELECT * FROM df")
print(f"Loaded {len(df)} rows into raw.issue_backlog")
con.close()
