"""Train and evaluate a dedicated binary churn_intent classifier.
Training data: dev(150) + rare_topic_boost(224) + churn_boost(150) = 674
rows. Test: the same untouched 450-row test split used throughout Phase
4 -- churn_boost rows were sampled excluding gold_sample and
rare_topic_boost_sample ids, so there is no leakage into test.
"""
import pickle

import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, cohen_kappa_score

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


def main():
    gold = pd.read_csv(r"D:\projects\non-tech\data\labels\gold_labels.csv")
    dev = gold[gold["split"] == "dev"][["review_id", "review_text", "churn_intent"]]
    test = gold[gold["split"] == "test"][["review_id", "review_text", "churn_intent"]]

    boost = pd.read_csv(r"D:\projects\non-tech\data\labels\rare_topic_boost_labels.csv")[
        ["review_id", "review_text", "churn_intent"]]
    churn_boost = pd.read_csv(r"D:\projects\non-tech\data\labels\churn_boost_labels.csv")[
        ["review_id", "review_text", "churn_intent"]]

    train = pd.concat([dev, boost, churn_boost], ignore_index=True)
    print(f"Training rows: {len(train)} (positive: {train['churn_intent'].sum()}, "
          f"{train['churn_intent'].sum()/len(train)*100:.1f}%)")
    print(f"Test rows: {len(test)} (positive: {test['churn_intent'].sum()}, "
          f"{test['churn_intent'].sum()/len(test)*100:.1f}%)")

    encoder = SentenceTransformer(MODEL_NAME)
    X_train = encoder.encode(train["review_text"].fillna("").tolist(), show_progress_bar=True, batch_size=64)
    X_test = encoder.encode(test["review_text"].fillna("").tolist(), show_progress_bar=True, batch_size=64)

    clf = LogisticRegression(max_iter=2000, class_weight="balanced")
    clf.fit(X_train, train["churn_intent"])

    y_pred = clf.predict(X_test)
    print("\n" + classification_report(test["churn_intent"], y_pred, digits=3, zero_division=0))
    print(f"Cohen's kappa vs test labels: {cohen_kappa_score(test['churn_intent'], y_pred):.3f}")

    with open(r"D:\projects\non-tech\data\interim\churn_classifier.pkl", "wb") as f:
        pickle.dump({"clf": clf, "model_name": MODEL_NAME}, f)
    print("\nSaved to data/interim/churn_classifier.pkl")


if __name__ == "__main__":
    main()
