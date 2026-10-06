"""Isolation Forest anomaly detection.

Uses a trained artifact when available; otherwise fits on the current batch (needs a minimum
number of characteristics to be meaningful).
"""
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest

from app.pipeline.features.extractor import FEATURE_COLUMNS
from app.pipeline.rules.base import RuleFinding

ARTIFACT_NAME = "anomaly.joblib"


def detect(df: pd.DataFrame, settings) -> list[RuleFinding]:
    if df.empty:
        return []
    path = Path(settings.artifact_dir) / ARTIFACT_NAME
    if path.exists():
        model = joblib.load(path)  # trusted: written by ml/training/train_anomaly.py
    elif len(df) >= settings.anomaly_min_batch:
        model = IsolationForest(n_estimators=100, random_state=0).fit(df[FEATURE_COLUMNS])
    else:
        return []

    X = df[FEATURE_COLUMNS]
    flags = model.predict(X)
    scores = -model.score_samples(X)  # > 0.5 means more anomalous
    return [
        RuleFinding(
            "ANM001",
            "warning",
            "Characteristic is statistically unusual compared with typical records",
            df["characteristic_id"].iloc[i],
            source="anomaly",
            confidence=round(float(min(1.0, max(0.0, (scores[i] - 0.5) * 2 + 0.5))), 3),
        )
        for i in range(len(df))
        if flags[i] == -1
    ]
