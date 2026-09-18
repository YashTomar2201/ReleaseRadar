"""Phase 5.7: figures for the release-impact analysis.
1. Health scores across all usable releases (none significant after
   correction -- the top candidate stands out but doesn't survive).
2. Placebo histogram for the top candidate, real effect marked.
3. Diagnostic event-study chart for the top candidate showing all 3
   apps' negative_share trajectories -- visually shows the
   parallel-trends violation (controls improving, PhonePe flat) that
   explains why this candidate is a methodology artifact, not a real
   release effect.
"""
import pickle

import duckdb
import matplotlib.pyplot as plt
import pandas as pd

FIG_DIR = r"D:\projects\non-tech\reports\figures"
APP_COLORS = {'phonepe': '#5f259f', 'gpay': '#4285F4', 'paytm': '#00baf2'}


def main():
    results = pd.read_csv(r"D:\projects\non-tech\data\interim\release_impact.csv")
    results["adoption_date"] = pd.to_datetime(results["adoption_date"])
    usable = results[results["usable"]].sort_values("adoption_date")

    # --- Figure 1: health scores across releases ---
    fig, ax = plt.subplots(figsize=(11, 4.5))
    colors = ['#d62728' if sig else '#5f259f' for sig in usable["is_significant"]]
    ax.bar(usable["version"], usable["health_score"], color=colors)
    ax.axhline(0, color='black', linewidth=0.8)
    ax.axhline(1.96, color='gray', linestyle='--', linewidth=0.8, label='~naive p<0.05 (uncorrected)')
    ax.axhline(-1.96, color='gray', linestyle='--', linewidth=0.8)
    top_idx = usable["health_score"].abs().idxmax()
    ax.annotate(f"strongest candidate\n(q={usable.loc[top_idx,'q_value']:.2f},\nfails correction)",
                (usable.index.get_loc(top_idx), usable.loc[top_idx, "health_score"]),
                textcoords="offset points", xytext=(35, 0), fontsize=8,
                arrowprops=dict(arrowstyle='->', lw=0.8))
    ax.set_ylabel("Health score (placebo-normalized effect)")
    ax.set_title("PhonePe release health scores -- none significant after BH correction (q<0.10)")
    ax.set_ylim(top=ax.get_ylim()[1] * 1.15)
    ax.tick_params(axis='x', rotation=45)
    ax.legend(fontsize=8, loc='lower right')
    fig.tight_layout()
    fig.savefig(f"{FIG_DIR}/07_release_health_scores.png", dpi=130)
    print("Saved 07_release_health_scores.png")

    # --- Figure 2: placebo histogram for the top candidate ---
    with open(r"D:\projects\non-tech\data\interim\placebo_effects.pkl", "rb") as f:
        placebo_store = pickle.load(f)
    top_version = usable.loc[top_idx, "version"]
    top_effect = usable.loc[top_idx, "real_effect"]
    placebo_effects = placebo_store[top_version]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(placebo_effects, bins=25, color='#cccccc', edgecolor='white', label='placebo effects (fake dates)')
    ax.axvline(top_effect, color='#d62728', linewidth=2, label=f'real effect ({top_version}) = {top_effect:.3f}')
    ax.set_xlabel("DiD effect on negative_share")
    ax.set_ylabel("Count (placebo dates)")
    ax.set_title(f"Placebo distribution vs. real effect: {top_version}\n"
                 f"(uncorrected p={usable.loc[top_idx,'placebo_p']:.3f}, but see diagnostic chart -- "
                 f"this is a parallel-trends violation, not a release effect)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(f"{FIG_DIR}/08_placebo_histogram_top_candidate.png", dpi=130)
    print("Saved 08_placebo_histogram_top_candidate.png")

    # --- Figure 3: diagnostic event-study for the top candidate ---
    con = duckdb.connect(r"D:\projects\non-tech\data\warehouse\releaseradar.duckdb", read_only=True)
    d = usable.loc[top_idx, "adoption_date"]
    window_df = con.execute("""
        SELECT app_key, review_date, negative_share
        FROM main.fct_daily_app_metrics
        WHERE review_date BETWEEN ? AND ? AND is_complete_day
        ORDER BY app_key, review_date
    """, [(d - pd.Timedelta(days=21)).date(), (d + pd.Timedelta(days=21)).date()]).df()
    window_df["review_date"] = pd.to_datetime(window_df["review_date"])
    con.close()

    fig, ax = plt.subplots(figsize=(11, 5))
    for app in ["phonepe", "gpay", "paytm"]:
        sub = window_df[window_df.app_key == app]
        ax.plot(sub.review_date, sub.negative_share, label=app, color=APP_COLORS[app], marker='o', markersize=3)
    ax.axvline(d, color='black', linestyle='--', linewidth=1, label=f'{top_version} adoption')
    ax.axvspan(d - pd.Timedelta(days=1), d + pd.Timedelta(days=2), color='gray', alpha=0.2, label='rollout buffer (excluded)')
    ax.set_ylabel("Daily negative share")
    ax.set_title(f"Diagnostic: {top_version} window -- PhonePe stays flat while highly volatile\n"
                 f"controls swing lower (parallel-trends violation, not a genuine release effect)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(f"{FIG_DIR}/09_diagnostic_parallel_trends.png", dpi=130)
    print("Saved 09_diagnostic_parallel_trends.png")


if __name__ == "__main__":
    main()
