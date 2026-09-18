"""Phase 9.2: export every dim/fact table to CSV for Power BI import."""
import duckdb

TABLES = [
    "dim_date", "dim_app", "dim_topic", "dim_version",
    "fct_daily_app_metrics", "fct_daily_topic_metrics", "fct_release_impact",
    "fct_alerts", "fct_switching", "fct_issue_backlog", "fct_review_samples",
]

con = duckdb.connect(r"D:\projects\non-tech\data\warehouse\releaseradar.duckdb", read_only=True)
for t in TABLES:
    out_path = rf"D:\projects\non-tech\data\exports\{t}.csv".replace("\\", "/")
    con.execute(f"COPY (SELECT * FROM main.{t}) TO '{out_path}' (HEADER, DELIMITER ',')")
    n = con.execute(f"SELECT COUNT(*) FROM main.{t}").fetchone()[0]
    print(f"Exported {t}: {n:,} rows -> data/exports/{t}.csv")
con.close()
