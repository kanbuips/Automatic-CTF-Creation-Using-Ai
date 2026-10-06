"""XGBoost / Random Forest inference. No artifact present -> stage is a no-op."""
from pathlib import Path

import joblib
import pandas as pd

from app.pipeline.features.extractor import FEATURE_COLUMNS
from app.pipeline.rules.base import RuleFinding

ARTIFACT_NAME = "classifier.joblib"


def predict(df: pd.DataFrame, settings) -> list[RuleFinding]:
    path = Path(settings.artifact_dir) / ARTIFACT_NAME
    if not path.exists() or df.empty:
        return []
    bundle = joblib.load(path)  # trusted: written by ml/training/train_classifier.py
    columns = bundle.get("columns", FEATURE_COLUMNS)
    proba = bundle["model"].predict_proba(df[columns])[:, 1]
    return [
        RuleFinding(
            "ML001",
            "warning",
            f"Classifier flags this characteristic as likely defective ({p:.0%})",
            df["characteristic_id"].iloc[i],
            source="ml",
            confidence=round(float(p), 3),
        )
        for i, p in enumerate(proba)
        if p >= settings.classifier_threshold
    ]
