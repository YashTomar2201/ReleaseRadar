"""Print a batch of the churn boost sample for labeling."""
import sys
import pandas as pd

start = int(sys.argv[1])
count = int(sys.argv[2])

df = pd.read_csv(r"D:\projects\non-tech\data\labels\churn_boost_sample.csv")
batch = df.iloc[start:start+count]

for i, row in batch.iterrows():
    text = str(row['review_text']).replace('\n', ' ').replace('\r', ' ')
    print(f"[{i}] app={row['app_key']} rating={row['rating']} :: {text[:280]}")
