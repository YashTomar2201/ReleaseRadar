"""Print a batch of the rare-topic boost sample for labeling."""
import sys
import pandas as pd

start = int(sys.argv[1])
count = int(sys.argv[2])

df = pd.read_csv(r"D:\projects\non-tech\data\labels\rare_topic_boost_sample.csv")
batch = df.iloc[start:start+count]

for i, row in batch.iterrows():
    text = str(row['review_text']).replace('\n', ' ').replace('\r', ' ')
    print(f"[{i}] target={row['target_topic']} app={row['app_key']} rating={row['rating']} :: {text[:300]}")
