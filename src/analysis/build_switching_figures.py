"""Phase 7.5: figures for the switching map -- heatmap of tracked-app
flows, raw outflow bar chart (incl. untracked competitors), and
reason-topic breakdown for the top flows."""
import duckdb
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

FIG_DIR = r"D:\projects\non-tech\reports\figures"
TRACKED_APPS = ["phonepe", "gpay", "paytm"]
APP_COLORS = {'phonepe': '#5f259f', 'gpay': '#4285F4', 'paytm': '#00baf2'}


def main():
    flows = pd.read_csv(r"D:\projects\non-tech\data\interim\switching_matrix.csv")
    rel = pd.read_csv(r"D:\projects\non-tech\data\interim\relation_classified.csv")

    # --- Figure 1: heatmap among tracked apps only ---
    matrix = pd.DataFrame(index=TRACKED_APPS, columns=TRACKED_APPS, dtype=float)
    for a in TRACKED_APPS:
        for b in TRACKED_APPS:
            if a == b:
                matrix.loc[a, b] = np.nan
                continue
            row = flows[(flows.source == a) & (flows.dest == b)]
            matrix.loc[a, b] = row["per_10k"].values[0] if len(row) else 0.0

    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(matrix.values.astype(float), cmap="Reds", vmin=0)
    ax.set_xticks(range(3)); ax.set_xticklabels(TRACKED_APPS)
    ax.set_yticks(range(3)); ax.set_yticklabels(TRACKED_APPS)
    ax.set_xlabel("Destination (switched TO)")
    ax.set_ylabel("Source (switched FROM)")
    ax.set_title("Switching-mention rate per 10k reviews\n(tracked apps only -- has a known denominator)")
    for i in range(3):
        for j in range(3):
            v = matrix.values[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:.2f}", ha='center', va='center',
                        color='white' if v > matrix.values[~np.isnan(matrix.values.astype(float))].max()/2 else 'black')
    fig.colorbar(im, label="per 10k reviews")
    fig.tight_layout()
    fig.savefig(f"{FIG_DIR}/12_switching_heatmap.png", dpi=130)
    print("Saved 12_switching_heatmap.png")

    # --- Figure 2: raw outflow counts including untracked competitors ---
    away = flows[flows["source"].isin(TRACKED_APPS)].sort_values(["source", "n"], ascending=[True, False])
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.5), sharey=False)
    for ax, app in zip(axes, TRACKED_APPS):
        sub = away[away.source == app]
        ax.bar(sub["dest"], sub["n"], color=APP_COLORS[app])
        ax.set_title(f"Switching-away mentions FROM {app}")
        ax.tick_params(axis='x', rotation=45)
        ax.set_ylabel("Count")
    fig.tight_layout()
    fig.savefig(f"{FIG_DIR}/13_outflow_by_app.png", dpi=130)
    print("Saved 13_outflow_by_app.png")

    # --- Figure 3: reason-topic breakdown for the 2 largest flows into PhonePe ---
    con = duckdb.connect(r"D:\projects\non-tech\data\warehouse\releaseradar.duckdb", read_only=True)
    topics = con.execute("SELECT review_id, topic FROM main.stg_review_topics").df()
    con.close()

    away_rel = rel[rel.relation == "switching_away"]
    top_flows = [("gpay", "phonepe"), ("paytm", "phonepe")]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for ax, (src, dst) in zip(axes, top_flows):
        ids = away_rel[(away_rel.app_key == src) & (away_rel.other_app == dst)]["review_id"]
        topic_counts = topics[topics.review_id.isin(ids)]["topic"].value_counts()
        topic_counts = topic_counts[~topic_counts.index.isin(["general_praise", "uninformative"])].head(6)
        ax.barh(topic_counts.index[::-1], topic_counts.values[::-1], color=APP_COLORS[src])
        ax.set_title(f"Reasons cited: {src} -> {dst} (n={len(ids)} reviews)")
        ax.set_xlabel("Review count")
    fig.tight_layout()
    fig.savefig(f"{FIG_DIR}/14_switching_reasons.png", dpi=130)
    print("Saved 14_switching_reasons.png")


if __name__ == "__main__":
    main()
