"""Load all scraped parquet pages into the DuckDB warehouse as raw.reviews.

Safe to re-run: it always rebuilds raw.reviews from every parquet file
currently on disk (across all scrape runs / weekly refreshes). Dedup by
reviewId happens downstream in the dbt staging layer, not here — raw
should stay a faithful copy of everything collected.
"""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[2]
WAREHOUSE_PATH = ROOT / "data" / "warehouse" / "releaseradar.duckdb"
RAW_REVIEWS_GLOB = ROOT / "data" / "raw" / "reviews" / "*" / "*.parquet"


def main():
    WAREHOUSE_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(WAREHOUSE_PATH))
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")

    con.execute(f"""
        CREATE OR REPLACE TABLE raw.reviews AS
        SELECT * FROM read_parquet('{RAW_REVIEWS_GLOB.as_posix()}', union_by_name = true)
    """)

    print("Loaded raw.reviews. Summary by app:")
    print(con.execute("""
        SELECT
            app_key,
            COUNT(*)                    AS n_reviews,
            COUNT(DISTINCT reviewId)    AS n_unique_review_ids,
            MIN("at")                   AS oldest_review,
            MAX("at")                   AS newest_review,
            ROUND(AVG(CASE WHEN reviewCreatedVersion IS NULL THEN 1.0 ELSE 0 END), 3) AS share_missing_version
        FROM raw.reviews
        GROUP BY 1
        ORDER BY 1
    """).df().to_string(index=False))

    con.close()


if __name__ == "__main__":
    main()
