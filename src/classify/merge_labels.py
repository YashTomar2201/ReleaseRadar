"""Merge the 6 AI-labeling batch JSON files into the final gold labels
CSV, joined back to the sample metadata. Marks every row as
labeler='ai_v1' -- these are AI-assisted labels (Claude applying the
codebook v1 rules directly), NOT independent blind human labels. See
decision_log.md (2026-09-18, Phase 4 labeling method decision) for why,
and the hybrid validation plan: a human blind spot-check on a subset is
layered on top separately (src/classify/build_spotcheck_packet.py /
score_spotcheck.py).
"""
import json
from pathlib import Path

import pandas as pd

LABELS_DIR = Path(r"D:\projects\non-tech\data\labels")
BATCH_FILES = [
    "batch_0_99.json", "batch_100_199.json", "batch_200_299.json",
    "batch_300_399.json", "batch_400_499.json", "batch_500_599.json",
]

sample = pd.read_csv(LABELS_DIR / "gold_sample.csv")

all_labels = []
for fname in BATCH_FILES:
    with open(LABELS_DIR / fname, encoding="utf-8") as f:
        all_labels.extend(json.load(f))

labels_df = pd.DataFrame(all_labels).set_index("i").sort_index()

assert len(labels_df) == 600, f"Expected 600 labels, got {len(labels_df)}"
assert labels_df.index.is_unique, "Duplicate row indices in labels"
assert list(labels_df.index) == list(range(600)), "Missing/gapped indices"

sample["topics"] = labels_df["topics"].apply(lambda t: ";".join(t)).values
sample["churn_intent"] = labels_df["churn_intent"].values
sample["competitor_mentioned"] = labels_df["competitor_mentioned"].values
sample["labeler"] = "ai_v1"

out_path = LABELS_DIR / "gold_labels.csv"
sample.to_csv(out_path, index=False, encoding="utf-8")
print(f"Merged {len(sample)} labeled reviews -> {out_path}")

# Quick sanity summary
print("\nTopic frequency (rows can have multiple topics):")
from collections import Counter
counter = Counter()
for t in labels_df["topics"]:
    counter.update(t)
for topic, n in counter.most_common():
    print(f"  {topic:20s} {n:4d}  ({n/600*100:.1f}%)")

print(f"\nchurn_intent=True: {labels_df['churn_intent'].sum()} ({labels_df['churn_intent'].sum()/600*100:.1f}%)")
print(f"competitor_mentioned (non-null): {labels_df['competitor_mentioned'].notna().sum()}")
