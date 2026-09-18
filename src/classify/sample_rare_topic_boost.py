"""Address the rare-topic training-data shortage found in the first
evaluation pass (decision_log.md 2026-09-18): random stratified sampling
alone gives 0-3 training examples for topics at <2% prevalence
(ads_spam, investments_gold, travel_booking, autopay_mandates,
bank_linking, refund_delay, bills_recharge, account_blocked,
fees_charges). Keyword-guided sampling pulls candidate reviews likely to
carry each rare topic, for ADDITIONAL LABELING -- training data only.

Critically: explicitly excludes every review_id already in gold_sample
(dev AND test) so the test split stays untouched and uncontaminated,
and this boost can never leak into the held-out evaluation set.
"""
import duckdb
import numpy as np
import pandas as pd

RNG_SEED = 99
N_PER_TOPIC = 25

KEYWORD_PATTERNS = {
    "ads_spam": r"(too many ads|advertisement|notification.*spam|ads everywhere|pop.?up)",
    "investments_gold": r"(digital gold|digital silver|mutual fund|gold locker|sip\b|gold saving|silver saving)",
    "travel_booking": r"(bus ticket|flight ticket|train ticket|bus operator|irctc|ticket booking|ticket cancel)",
    "autopay_mandates": r"(autopay|auto.?pay|mandate|auto.?debit|recurring payment)",
    "bank_linking": r"(link.*bank account|add.*bank account|bank account.*link|cannot link)",
    "refund_delay": r"(refund.*(not|nahi|delay|pending)|reversal.*(pending|delay))",
    "bills_recharge": r"(recharge (failed|not|plan)|bill payment (failed|not)|electricity bill|dth recharge)",
    "account_blocked": r"(account.*(blocked|suspended|frozen)|blocked.*account)",
    "fees_charges": r"(platform fee|convenience fee|hidden charge|extra charge|service charge)",
}


def main():
    con = duckdb.connect(r"D:\projects\non-tech\data\warehouse\releaseradar.duckdb", read_only=True)
    already_sampled = pd.read_csv(r"D:\projects\non-tech\data\labels\gold_sample.csv")["review_id"].tolist()
    exclude_list = "', '".join(already_sampled)

    rng = np.random.default_rng(RNG_SEED)
    parts = []

    for topic, pattern in KEYWORD_PATTERNS.items():
        pool = con.execute(f"""
            SELECT review_id, app_key, rating, review_text, text_length
            FROM main.stg_reviews
            WHERE regexp_matches(lower(review_text), '{pattern}')
              AND review_id NOT IN ('{exclude_list}')
        """).df()
        n = min(N_PER_TOPIC, len(pool))
        if n == 0:
            print(f"WARNING: no candidates found for {topic}")
            continue
        sub = pool.sample(n=n, random_state=RNG_SEED)
        sub["target_topic"] = topic
        parts.append(sub)
        print(f"{topic}: pool={len(pool)}, sampled={n}")

    boost = pd.concat(parts, ignore_index=True)
    # A review could match multiple keyword patterns and get pulled twice; dedupe
    boost = boost.drop_duplicates(subset="review_id").reset_index(drop=True)
    boost["split"] = "dev_boost"

    out_path = r"D:\projects\non-tech\data\labels\rare_topic_boost_sample.csv"
    boost.to_csv(out_path, index=False, encoding="utf-8")
    print(f"\nTotal unique boost reviews: {len(boost)}")
    print(f"Saved to {out_path}")


if __name__ == "__main__":
    main()
