"""Phase 7.4: build the switching matrix from classified relations.

Flow direction:
  switching_away rows           -> source = app_key (leaving), dest = other_app (going to)
  switched_from_competitor rows -> source = other_app (came from), dest = app_key (arrived at)

Normalization: "per 10k reviews of source app" only makes sense when
the source is one of our 3 tracked apps (we know their total review
counts) -- flows FROM an untracked competitor (BHIM, CRED, etc. as
source) are reported as raw counts only, since we have no denominator
for apps we don't scrape.

Bootstrap: for each TRACKED source app, resample its full review set
(with replacement, 1000x) and recompute the flow rate per 10k each
time, for a 95% CI -- properly reflects that these are rare events
against the app's full review volume, not just against the small
candidate pool.
"""
import duckdb
import numpy as np
import pandas as pd

TRACKED_APPS = ["phonepe", "gpay", "paytm"]
N_BOOTSTRAP = 1000
SEED = 2026


def main():
    con = duckdb.connect(r"D:\projects\non-tech\data\warehouse\releaseradar.duckdb", read_only=True)
    total_reviews = con.execute("""
        SELECT app_key, COUNT(*) as n FROM main.stg_reviews GROUP BY 1
    """).df().set_index("app_key")["n"].to_dict()
    con.close()
    print("Total reviews per tracked app:", total_reviews)

    rel = pd.read_csv(r"D:\projects\non-tech\data\interim\relation_classified.csv")

    away = rel[rel.relation == "switching_away"].copy()
    away["source"] = away["app_key"]
    away["dest"] = away["other_app"]

    from_comp = rel[rel.relation == "switched_from_competitor"].copy()
    from_comp["source"] = from_comp["other_app"]
    from_comp["dest"] = from_comp["app_key"]

    flows = pd.concat([away[["source", "dest", "review_id"]], from_comp[["source", "dest", "review_id"]]])
    flow_counts = flows.groupby(["source", "dest"]).size().reset_index(name="n")

    # Rate per 10k reviews of source, only where source is tracked (has a known denominator)
    flow_counts["source_total_reviews"] = flow_counts["source"].map(total_reviews)
    flow_counts["per_10k"] = flow_counts.apply(
        lambda r: r["n"] / r["source_total_reviews"] * 10_000 if pd.notna(r["source_total_reviews"]) else np.nan,
        axis=1)

    # Bootstrap CIs for tracked-source flows
    rng = np.random.default_rng(SEED)
    ci_rows = []
    for source in TRACKED_APPS:
        n_total = total_reviews[source]
        source_flows = flow_counts[flow_counts.source == source]
        # Indicator array: which of this app's reviews are which flow (0 for the vast majority)
        flow_review_ids = {dest: set(flows[(flows.source == source) & (flows.dest == dest)]["review_id"])
                            for dest in source_flows["dest"]}
        all_review_ids = con_ids = None  # not needed -- resample counts directly via binomial-style bootstrap
        for dest, ids in flow_review_ids.items():
            k = len(ids)  # observed count
            # Bootstrap: resample n_total "reviews" where k are flow-positive, rest are not
            # (equivalent to resampling indices from a 0/1 array of length n_total with k ones)
            boot_rates = []
            base = np.zeros(n_total, dtype=np.int8)
            base[:k] = 1
            for _ in range(N_BOOTSTRAP):
                sample = rng.choice(base, size=n_total, replace=True)
                boot_rates.append(sample.sum() / n_total * 10_000)
            lo, hi = np.percentile(boot_rates, [2.5, 97.5])
            ci_rows.append({"source": source, "dest": dest, "per_10k_ci_low": lo, "per_10k_ci_high": hi})

    ci_df = pd.DataFrame(ci_rows)
    flow_counts = flow_counts.merge(ci_df, on=["source", "dest"], how="left")

    flow_counts = flow_counts.sort_values("n", ascending=False)
    print("\n=== Switching flows ===")
    print(flow_counts.to_string(index=False))

    # Net flow between tracked-app pairs only (both directions have a comparable denominator)
    print("\n=== Net flow between tracked apps (per 10k) ===")
    for i, a in enumerate(TRACKED_APPS):
        for b in TRACKED_APPS[i+1:]:
            ab = flow_counts[(flow_counts.source == a) & (flow_counts.dest == b)]["per_10k"].sum()
            ba = flow_counts[(flow_counts.source == b) & (flow_counts.dest == a)]["per_10k"].sum()
            net = ab - ba
            direction = f"{a}->{b}" if net > 0 else f"{b}->{a}"
            print(f"{a} <-> {b}: {a}->{b}={ab:.2f}/10k, {b}->{a}={ba:.2f}/10k, net={abs(net):.2f}/10k toward {direction}")

    flow_counts.to_csv(r"D:\projects\non-tech\data\interim\switching_matrix.csv", index=False)
    print("\nSaved to data/interim/switching_matrix.csv")


if __name__ == "__main__":
    main()
