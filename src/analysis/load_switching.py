"""Load switching_matrix.csv and relation_classified.csv into DuckDB."""
import duckdb
import pandas as pd

con = duckdb.connect(r"D:\projects\non-tech\data\warehouse\releaseradar.duckdb")
con.execute("CREATE SCHEMA IF NOT EXISTS raw")

matrix = pd.read_csv(r"D:\projects\non-tech\data\interim\switching_matrix.csv")
con.execute("DROP TABLE IF EXISTS raw.switching_matrix")
con.execute("CREATE TABLE raw.switching_matrix AS SELECT * FROM matrix")
print(f"Loaded {len(matrix)} flow rows into raw.switching_matrix")

rel = pd.read_csv(r"D:\projects\non-tech\data\interim\relation_classified.csv")
con.execute("DROP TABLE IF EXISTS raw.review_relations")
con.execute("CREATE TABLE raw.review_relations AS SELECT * FROM rel")
print(f"Loaded {len(rel)} review-relation rows into raw.review_relations")

con.close()
