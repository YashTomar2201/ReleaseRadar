"""Load alert_events.csv and config/incidents.csv into DuckDB."""
import duckdb
import pandas as pd

con = duckdb.connect(r"D:\projects\non-tech\data\warehouse\releaseradar.duckdb")
con.execute("CREATE SCHEMA IF NOT EXISTS raw")

alerts = pd.read_csv(r"D:\projects\non-tech\data\interim\alert_events.csv")
con.execute("DROP TABLE IF EXISTS raw.alerts")
con.execute("CREATE TABLE raw.alerts AS SELECT * FROM alerts")
print(f"Loaded {len(alerts)} alert events into raw.alerts")

incidents = pd.read_csv(r"D:\projects\non-tech\config\incidents.csv")
con.execute("DROP TABLE IF EXISTS raw.incidents")
con.execute("CREATE TABLE raw.incidents AS SELECT * FROM incidents")
print(f"Loaded {len(incidents)} confirmed incidents into raw.incidents")

con.close()
