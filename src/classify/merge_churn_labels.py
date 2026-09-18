"""Merge churn boost batch labels and save the combined file."""
import json
from pathlib import Path

import pandas as pd

LABELS_DIR = Path(r"D:\projects\non-tech\data\labels")
BATCH_FILES = ["churn_batch_0_74.json", "churn_batch_75_149.json"]

sample = pd.read_csv(LABELS_DIR / "churn_boost_sample.csv")

all_labels = []
for fname in BATCH_FILES:
    with open(LABELS_DIR / fname, encoding="utf-8") as f:
        all_labels.extend(json.load(f))

labels_df = pd.DataFrame(all_labels).set_index("i").sort_index()
assert len(labels_df) == len(sample), f"Expected {len(sample)}, got {len(labels_df)}"
assert list(labels_df.index) == list(range(len(sample)))

sample["churn_intent"] = labels_df["churn_intent"].values
sample["labeler"] = "ai_v1"

out_path = LABELS_DIR / "churn_boost_labels.csv"
sample.to_csv(out_path, index=False, encoding="utf-8")
print(f"Merged {len(sample)} churn-boost-labeled reviews -> {out_path}")
print(f"Positive rate: {sample['churn_intent'].sum()} / {len(sample)} "
      f"({sample['churn_intent'].sum()/len(sample)*100:.1f}%)")
