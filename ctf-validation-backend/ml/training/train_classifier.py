"""Train the defect classifier.

Input: a CSV with the feature columns from app.pipeline.features.extractor.FEATURE_COLUMNS plus a
binary `label` column (1 = characteristic had a QC defect). Output: ml/artifacts/classifier.joblib.

    python -m ml.training.train_classifier --data labeled.csv
"""
import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

from app.pipeline.features.extractor import FEATURE_COLUMNS

ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", default=str(ARTIFACTS / "classifier.joblib"))
    args = ap.parse_args()

    df = pd.read_csv(args.data)
    X, y = df[FEATURE_COLUMNS], df["label"]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=0, stratify=y)
    model = RandomForestClassifier(n_estimators=300, class_weight="balanced", random_state=0).fit(X_tr, y_tr)
    print(classification_report(y_te, model.predict(X_te)))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "columns": FEATURE_COLUMNS}, args.out)
    print("saved", args.out)


if __name__ == "__main__":
    main()
