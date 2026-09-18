"""Phase 5.6/5.3: for a candidate release, explain WHICH topics drove
the change (before/after topic-share comparison) and corroborate with
the secondary method (comparing old vs. new version reviews on the SAME
calendar days during the staged rollout, which controls for time
without needing a competitor-app control group).
"""
import sys

import duckdb
import pandas as pd
import statsmodels.formula.api as smf

VERSION = sys.argv[1] if len(sys.argv) > 1 else "26.05.08.0"
WINDOW = 21
ROLLOUT_BUFFER = (1, 2)


def main():
    con = duckdb.connect(r"D:\projects\non-tech\data\warehouse\releaseradar.duckdb", read_only=True)

    adoption = con.execute("""
        SELECT adoption_date FROM main.int_version_adoption
        WHERE app_key='phonepe' AND review_version = ?
    """, [VERSION]).fetchone()
    d = pd.Timestamp(adoption[0])
    print(f"=== {VERSION} -- adoption_date {d.date()} ===\n")

    pre_lo, pre_hi = d - pd.Timedelta(days=WINDOW), d - pd.Timedelta(days=ROLLOUT_BUFFER[0])
    post_lo, post_hi = d + pd.Timedelta(days=ROLLOUT_BUFFER[1]), d + pd.Timedelta(days=WINDOW)

    print(f"Pre window:  {pre_lo.date()} to {pre_hi.date()}")
    print(f"Post window: {post_lo.date()} to {post_hi.date()}\n")

    # --- 1. Topic-share before/after for PhonePe specifically ---
    topics = con.execute("""
        SELECT review_date, topic, n_topic_reviews, n_reviews_that_day
        FROM main.fct_daily_topic_metrics
        WHERE app_key = 'phonepe' AND is_complete_day
    """).df()
    topics["review_date"] = pd.to_datetime(topics["review_date"])

    pre = topics[(topics.review_date >= pre_lo) & (topics.review_date <= pre_hi)]
    post = topics[(topics.review_date >= post_lo) & (topics.review_date <= post_hi)]

    pre_share = pre.groupby("topic")["n_topic_reviews"].sum() / pre.groupby("topic")["n_reviews_that_day"].sum().groupby("topic").sum().sum() \
        if False else pre.groupby("topic")["n_topic_reviews"].sum() / pre.drop_duplicates("review_date")["n_reviews_that_day"].sum()
    post_share = post.groupby("topic")["n_topic_reviews"].sum() / post.drop_duplicates("review_date")["n_reviews_that_day"].sum()

    comparison = pd.DataFrame({"pre_share": pre_share, "post_share": post_share}).fillna(0)
    comparison["change_pp"] = (comparison["post_share"] - comparison["pre_share"]) * 100
    comparison = comparison.sort_values("change_pp", ascending=False)
    print("Topic share change (percentage points), pre -> post:")
    print(comparison.round(3).to_string())

    # --- 2. Rollout version-overlap comparison (secondary method) ---
    print(f"\n=== Rollout overlap check: old vs. new version, same calendar days ===")
    overlap = con.execute("""
        SELECT review_date, review_version, rating
        FROM main.stg_reviews
        WHERE app_key = 'phonepe' AND review_version IS NOT NULL
          AND review_date BETWEEN ? AND ?
    """, [(d - pd.Timedelta(days=3)).date(), (d + pd.Timedelta(days=10)).date()]).df()

    prior_versions = con.execute("""
        SELECT DISTINCT review_version FROM main.int_version_adoption
        WHERE app_key='phonepe' AND adoption_date < ? ORDER BY adoption_date DESC LIMIT 1
    """, [d.date()]).fetchone()
    prior_version = prior_versions[0] if prior_versions else None

    overlap_relevant = overlap[overlap.review_version.isin([VERSION, prior_version])]
    if overlap_relevant.empty or overlap_relevant.review_version.nunique() < 2:
        print(f"Not enough overlapping-day data between {VERSION} and prior version {prior_version} to compare.")
    else:
        overlap_relevant = overlap_relevant.copy()
        overlap_relevant["is_new_version"] = (overlap_relevant.review_version == VERSION).astype(int)
        summary = overlap_relevant.groupby("review_version")["rating"].agg(["mean", "count"])
        print(f"Comparing {VERSION} vs prior version {prior_version}, reviews posted on the SAME calendar days "
              f"({(d - pd.Timedelta(days=3)).date()} to {(d + pd.Timedelta(days=10)).date()}):")
        print(summary.to_string())
        m = smf.ols("rating ~ is_new_version + C(review_date)", data=overlap_relevant).fit()
        if "is_new_version" in m.params:
            print(f"\nRegression-adjusted (controlling for calendar day) rating difference "
                  f"for {VERSION} vs {prior_version}: {m.params['is_new_version']:.3f} "
                  f"(p={m.pvalues['is_new_version']:.3f})")

    con.close()


if __name__ == "__main__":
    main()
