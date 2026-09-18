"""Load release_impact.csv into DuckDB as raw.release_impact."""
import duckdb
import pandas as pd

df = pd.read_csv(r"D:\projects\non-tech\data\interim\release_impact.csv")
con = duckdb.connect(r"D:\projects\non-tech\data\warehouse\releaseradar.duckdb")
con.execute("CREATE SCHEMA IF NOT EXISTS raw")
con.execute("DROP TABLE IF EXISTS raw.release_impact")
con.execute("CREATE TABLE raw.release_impact AS SELECT *, 'phonepe' as app_key FROM df")
print(f"Loaded {len(df)} rows into raw.release_impact")
con.close()
