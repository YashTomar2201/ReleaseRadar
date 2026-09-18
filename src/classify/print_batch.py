"""Print a batch of the gold sample for manual/AI labeling, in a compact
numbered format. Usage: python print_batch.py <start> <count>"""
import sys
import pandas as pd

start = int(sys.argv[1])
count = int(sys.argv[2])

df = pd.read_csv(r"D:\projects\non-tech\data\labels\gold_sample.csv")
batch = df.iloc[start:start+count]

for i, row in batch.iterrows():
    text = str(row['review_text']).replace('\n', ' ').replace('\r', ' ')
    print(f"[{i}] id={row['review_id'][:8]} app={row['app_key']} rating={row['rating']} :: {text}")
