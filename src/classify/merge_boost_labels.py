"""Merge the rare-topic boost batch labels, join to sample metadata,
and append to a combined training file (dev split + boost, test split
untouched)."""
import json
from pathlib import Path

import pandas as pd

LABELS_DIR = Path(r"D:\projects\non-tech\data\labels")
BATCH_FILES = ["boost_batch_0_74.json", "boost_batch_75_149.json", "boost_batch_150_223.json"]

sample = pd.read_csv(LABELS_DIR / "rare_topic_boost_sample.csv")

all_labels = []
for fname in BATCH_FILES:
    with open(LABELS_DIR / fname, encoding="utf-8") as f:
        all_labels.extend(json.load(f))

labels_df = pd.DataFrame(all_labels).set_index("i").sort_index()
assert len(labels_df) == len(sample), f"Expected {len(sample)} labels, got {len(labels_df)}"
assert labels_df.index.is_unique
assert list(labels_df.index) == list(range(len(sample)))

sample["topics"] = labels_df["topics"].apply(lambda t: ";".join(t)).values
sample["churn_intent"] = labels_df["churn_intent"].values
sample["competitor_mentioned"] = labels_df["competitor_mentioned"].values
sample["labeler"] = "ai_v1"

out_path = LABELS_DIR / "rare_topic_boost_labels.csv"
sample.to_csv(out_path, index=False, encoding="utf-8")
print(f"Merged {len(sample)} boost-labeled reviews -> {out_path}")

from collections import Counter
counter = Counter()
for t in labels_df["topics"]:
    counter.update(t)
print("\nTopic frequency in boost set:")
for topic, n in counter.most_common():
    print(f"  {topic:20s} {n:4d}")
