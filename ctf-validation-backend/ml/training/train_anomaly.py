"""Train the Isolation Forest on known-good JTXML files.

    python -m ml.training.train_anomaly --jtxml-dir path/to/approved_jtxml
Output: ml/artifacts/anomaly.joblib
"""
import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest

from app.pipeline.features.extractor import FEATURE_COLUMNS, extract_features
from app.pipeline.parsing.jtxml_parser import parse_jtxml

ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jtxml-dir", required=True)
    ap.add_argument("--out", default=str(ARTIFACTS / "anomaly.joblib"))
    args = ap.parse_args()

    files = [p for p in Path(args.jtxml_dir).rglob("*") if p.suffix.lower() in {".jtxml", ".xml"}]
    frames = [extract_features(parse_jtxml(p)) for p in files]
    if not frames:
        raise SystemExit("no JTXML files found")
    X = pd.concat(frames)[FEATURE_COLUMNS]
    model = IsolationForest(n_estimators=200, random_state=0).fit(X)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, args.out)
    print(f"trained on {len(X)} characteristics from {len(files)} files -> {args.out}")


if __name__ == "__main__":
    main()
