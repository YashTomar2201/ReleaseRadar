"""Phase 8.5: prevalence-vs-penalty bubble chart (bubble size = churn
exposure) and the per-app backlog table with anonymized example
reviews."""
import duckdb
import matplotlib.pyplot as plt
import pandas as pd

FIG_DIR = r"D:\projects\non-tech\reports\figures"
APP_COLORS = {'phonepe': '#5f259f', 'gpay': '#4285F4', 'paytm': '#00baf2'}
FLAG_TOPICS = {"ui_ux"}  # needs manual interpretation -- see decision_log.md


def main():
    df = pd.read_csv(r"D:\projects\non-tech\data\interim\issue_backlog_with_sensitivity.csv")

    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharex=True, sharey=True)
    for ax, app in zip(axes, ["phonepe", "gpay", "paytm"]):
        sub = df[df.app_key == app]
        sizes = sub["churn_exposure"] * 8000
        colors = ['#999999' if t in FLAG_TOPICS else APP_COLORS[app] for t in sub["topic"]]
        ax.scatter(sub["prevalence"] * 100, sub["penalty"], s=sizes, alpha=0.6, color=colors, edgecolors='white')
        for _, row in sub.iterrows():
            label = f"{row['topic']}*" if row['topic'] in FLAG_TOPICS else row['topic']
            ax.annotate(label, (row["prevalence"] * 100, row["penalty"]), fontsize=7,
                        xytext=(4, 4), textcoords="offset points")
        ax.axhline(0, color='gray', linewidth=0.5)
        ax.set_title(app)
        ax.set_xlabel("Prevalence (% of reviews, last 90d)")
    axes[0].set_ylabel("Rating penalty (stars, negative = worse)")
    fig.suptitle("Issue prevalence vs. rating penalty (bubble size = churn exposure)\n"
                  "* ui_ux flagged: positive penalty means this topic often co-occurs with praise -- needs manual read, not an automated fix priority",
                  fontsize=10)
    fig.tight_layout()
    fig.savefig(f"{FIG_DIR}/15_issue_prevalence_vs_penalty.png", dpi=130)
    print("Saved 15_issue_prevalence_vs_penalty.png")

    # --- Backlog table with 2 anonymized example reviews per top issue ---
    con = duckdb.connect(r"D:\projects\non-tech\data\warehouse\releaseradar.duckdb", read_only=True)
    lines = []
    for app in ["phonepe", "gpay", "paytm"]:
        lines.append(f"\n{'='*70}\n{app.upper()} -- Top 5 RICE-ranked issues (last 90 days)\n{'='*70}")
        top5 = df[(df.app_key == app)].sort_values("rice", ascending=False).head(5)
        for _, row in top5.iterrows():
            flag = "  [NEEDS MANUAL REVIEW -- see note]" if row["topic"] in FLAG_TOPICS else ""
            lines.append(f"\n#{top5.index.get_loc(row.name)+1 if False else ''} {row['topic']}{flag}")
            lines.append(f"  RICE={row['rice']:.0f} | top-3 stability={row['top3_stability_pct']:.0f}% | "
                         f"prevalence={row['prevalence']*100:.1f}% | rating lift if fixed={row['rating_lift_if_fixed']:.3f}★ | "
                         f"churn exposure={row['churn_exposure']*100:.2f}%")
            examples = con.execute("""
                SELECT r.review_text FROM main.stg_reviews r
                JOIN main.stg_review_topics t ON r.review_id = t.review_id
                WHERE r.app_key = ? AND t.topic = ? AND r.rating <= 2
                ORDER BY random() LIMIT 2
            """, [app, row["topic"]]).df()
            for ex in examples["review_text"]:
                lines.append(f"    - \"{str(ex)[:140]}\"")
    con.close()

    out_text = "\n".join(lines)
    with open(r"D:\projects\non-tech\reports\briefs\issue_backlog_examples.txt", "w", encoding="utf-8") as f:
        f.write(out_text)
    print(out_text)
    print("\nSaved reports/briefs/issue_backlog_examples.txt")


if __name__ == "__main__":
    main()
