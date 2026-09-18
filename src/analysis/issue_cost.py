"""Phase 8: issue cost and RICE backlog.

8.1 Rating penalty per topic via OLS regression (robust SE).
8.2-8.3 Prevalence, penalty, churn-intent rate, Issue Cost Index (ICI)
per app per topic, last 90 days of complete data.
8.4 RICE scoring: Reach x Impact x Confidence / Effort.

Reach data note (decision_log.md, 2026-09-19): "true" MAU figures for
these apps are not consistently, reliably disclosed -- search results
for third-party "MAU" stats were inconsistent across sources (some
content-mill sites, not primary reporting) and not used. Reach instead
uses Play Store download counts verified directly against each app's
listing in Phase 0 (PhonePe 500M+, Google Pay 1B+, Paytm 500M+) -- a
publicly verifiable proxy for user base size, documented as
overstating true *active* reach (not all downloads remain active
users), not presented as a true MAU figure.
"""
import pickle

import duckdb
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

TOPICS = [
    "payment_failure", "refund_delay", "login_otp_kyc", "account_blocked",
    "bank_linking", "app_performance", "ui_ux", "customer_support",
    "fraud_security", "rewards_cashback", "fees_charges", "ads_spam",
    "bills_recharge", "autopay_mandates", "investments_gold",
    "travel_booking",
]  # excludes general_praise / uninformative -- not "issues" to fix

# Play Store download counts (verified Phase 0, 2026-09-17) -- proxy for reach
DOWNLOADS = {"phonepe": 500_000_000, "gpay": 1_000_000_000, "paytm": 500_000_000}

# Classifier reliability per topic (Phase 4 test-set F1) -- feeds RICE Confidence
CLASSIFIER_F1 = {
    "payment_failure": 0.600, "refund_delay": 0.438, "login_otp_kyc": 0.348,
    "account_blocked": 0.462, "bank_linking": 0.667, "app_performance": 0.663,
    "ui_ux": 0.500, "customer_support": 0.565, "fraud_security": 0.533,
    "rewards_cashback": 0.731, "fees_charges": 0.636, "ads_spam": 0.353,
    "bills_recharge": 0.588, "autopay_mandates": 0.467, "investments_gold": 0.364,
    "travel_booking": 0.600,
}

# Effort assumptions (person-weeks) -- clearly marked as a judgment call,
# not derived from data. Roughly: pure bug fixes < UX polish < backend
# reliability work < new-feature-scale build-outs.
EFFORT_WEEKS = {
    "payment_failure": 8, "refund_delay": 4, "login_otp_kyc": 3,
    "account_blocked": 3, "bank_linking": 3, "app_performance": 6,
    "ui_ux": 2, "customer_support": 5, "fraud_security": 6,
    "rewards_cashback": 3, "fees_charges": 2, "ads_spam": 1,
    "bills_recharge": 3, "autopay_mandates": 4, "investments_gold": 5,
    "travel_booking": 4,
}


def main():
    con = duckdb.connect(r"D:\projects\non-tech\data\warehouse\releaseradar.duckdb", read_only=True)

    reviews = con.execute("""
        SELECT r.review_id, r.app_key, r.rating, r.text_length, r.review_date,
               strftime(r.review_date, '%Y-%m') as month
        FROM main.stg_reviews r
    """).df()

    topics_long = con.execute("SELECT review_id, topic FROM main.stg_review_topics").df()
    flags = con.execute("SELECT review_id, churn_intent FROM main.stg_review_flags").df()
    con.close()

    # Wide topic dummy matrix
    topic_wide = topics_long[topics_long.topic.isin(TOPICS)].assign(val=1).pivot_table(
        index="review_id", columns="topic", values="val", fill_value=0)
    topic_wide.columns = [f"t_{c}" for c in topic_wide.columns]

    df = reviews.merge(topic_wide, on="review_id", how="left").merge(flags, on="review_id", how="left")
    for t in TOPICS:
        col = f"t_{t}"
        if col not in df.columns:
            df[col] = 0
        df[col] = df[col].fillna(0)
    df["churn_intent"] = df["churn_intent"].fillna(False)
    df["log_len"] = np.log1p(df["text_length"])

    # --- 8.1 Rating-penalty regression (overall, all apps pooled) ---
    present_topics = [t for t in TOPICS if df[f"t_{t}"].sum() > 0]
    formula = "rating ~ " + " + ".join(f"t_{t}" for t in present_topics) + " + C(app_key) + C(month) + log_len"
    print(f"Fitting rating-penalty regression on {len(df):,} reviews, {len(present_topics)} topics...")
    model = smf.ols(formula, data=df).fit(cov_type="HC1")

    penalties = pd.DataFrame({
        "topic": present_topics,
        "penalty": [model.params.get(f"t_{t}", np.nan) for t in present_topics],
        "penalty_se": [model.bse.get(f"t_{t}", np.nan) for t in present_topics],
        "penalty_p": [model.pvalues.get(f"t_{t}", np.nan) for t in present_topics],
    })
    penalties["penalty_ci_low"] = penalties["penalty"] - 1.96 * penalties["penalty_se"]
    penalties["penalty_ci_high"] = penalties["penalty"] + 1.96 * penalties["penalty_se"]
    print("\n=== Rating penalty per topic (overall, stars lost per review carrying this topic) ===")
    print(penalties.sort_values("penalty").to_string(index=False))

    # --- 8.2 Prevalence, churn-intent rate per (app, topic), last 90 days ---
    max_date = df["review_date"].max()
    recent = df[pd.to_datetime(df["review_date"]) >= pd.to_datetime(max_date) - pd.Timedelta(days=90)]

    rows = []
    for app in ["phonepe", "gpay", "paytm"]:
        app_df = recent[recent.app_key == app]
        n_total = len(app_df)
        for t in present_topics:
            n_topic = app_df[f"t_{t}"].sum()
            prevalence = n_topic / n_total if n_total else 0
            churn_rate = app_df.loc[app_df[f"t_{t}"] == 1, "churn_intent"].mean() if n_topic else 0
            rows.append({"app_key": app, "topic": t, "prevalence": prevalence,
                         "n_topic_reviews_90d": int(n_topic), "n_total_reviews_90d": n_total,
                         "churn_intent_rate": churn_rate})
    issue_df = pd.DataFrame(rows).merge(penalties[["topic", "penalty", "penalty_ci_low", "penalty_ci_high"]], on="topic")

    # --- 8.3 Issue Cost Index ---
    issue_df["rating_lift_if_fixed"] = issue_df["prevalence"] * issue_df["penalty"].abs()
    issue_df["churn_exposure"] = issue_df["prevalence"] * issue_df["churn_intent_rate"]

    # --- 8.4 RICE ---
    issue_df["reach"] = issue_df["app_key"].map(DOWNLOADS) * issue_df["prevalence"]

    def impact_score(lift):
        if lift >= 0.03: return 3
        if lift >= 0.015: return 2
        if lift >= 0.005: return 1
        if lift >= 0.001: return 0.5
        return 0.25
    issue_df["impact"] = issue_df["rating_lift_if_fixed"].apply(impact_score)

    def confidence_score(topic):
        f1 = CLASSIFIER_F1.get(topic, 0.4)
        if f1 >= 0.6: return 1.0
        if f1 >= 0.45: return 0.8
        return 0.5
    issue_df["confidence"] = issue_df["topic"].map(confidence_score)
    issue_df["effort_weeks"] = issue_df["topic"].map(EFFORT_WEEKS)
    issue_df["rice"] = (issue_df["reach"] * issue_df["impact"] * issue_df["confidence"]) / issue_df["effort_weeks"]

    issue_df = issue_df.sort_values(["app_key", "rice"], ascending=[True, False])
    print("\n=== Top 5 RICE-ranked issues per app ===")
    for app in ["phonepe", "gpay", "paytm"]:
        print(f"\n--- {app} ---")
        print(issue_df[issue_df.app_key == app].head(5)[
            ["topic", "prevalence", "penalty", "churn_intent_rate", "rating_lift_if_fixed",
             "reach", "impact", "confidence", "effort_weeks", "rice"]
        ].to_string(index=False))

    issue_df.to_csv(r"D:\projects\non-tech\data\interim\issue_backlog.csv", index=False)
    penalties.to_csv(r"D:\projects\non-tech\data\interim\rating_penalties.csv", index=False)
    with open(r"D:\projects\non-tech\data\interim\rating_penalty_model_summary.txt", "w", encoding="utf-8") as f:
        f.write(str(model.summary()))
    print("\nSaved data/interim/issue_backlog.csv, rating_penalties.csv, rating_penalty_model_summary.txt")


if __name__ == "__main__":
    main()
