import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier

from app.core.config import Settings
from app.pipeline.features.extractor import FEATURE_COLUMNS, extract_features
from app.pipeline.ml import anomaly, classifier
from app.pipeline.parsing.jtxml_parser import Characteristic, ParsedJtxml, parse_jtxml_bytes


def _parsed(n=12, outlier=True):
    chars = [
        Characteristic(id=f"C{i}", nominal=10.0 + i * 0.1, upper_tol=0.2, lower_tol=-0.2, unit="mm", direction="X", description="CHECK FEATURE FROM DATUM A")
        for i in range(n)
    ]
    if outlier:
        chars[-1] = Characteristic(id="OUT", nominal=5000.0, upper_tol=900.0, lower_tol=-1.0, unit="", direction=None, description="")
    return ParsedJtxml("P", "M", "Beta 3", chars)


def test_extract_features_shape_and_values(good_bytes):
    df = extract_features(parse_jtxml_bytes(good_bytes))
    assert list(df.columns) == ["characteristic_id", *FEATURE_COLUMNS]
    assert len(df) == 3
    row = df.iloc[0]
    assert row["band"] == 0.4 and row["direction_code"] == 1 and row["unit_known"] == 1 and row["missing_tol"] == 0


def test_missing_values_become_flags_not_nan(bad_bytes):
    df = extract_features(parse_jtxml_bytes(bad_bytes))
    assert not df[FEATURE_COLUMNS].isna().any().any()
    assert df.iloc[0]["missing_nominal"] == 1


def test_anomaly_flags_outlier_on_batch(tmp_path):
    s = Settings(artifact_dir=tmp_path, anomaly_min_batch=8)
    found = anomaly.detect(extract_features(_parsed()), s)
    assert "OUT" in {f.characteristic_id for f in found} and all(f.source == "anomaly" for f in found)


def test_anomaly_skipped_for_small_batch(tmp_path):
    s = Settings(artifact_dir=tmp_path, anomaly_min_batch=8)
    assert anomaly.detect(extract_features(_parsed(n=3, outlier=False)), s) == []


def test_classifier_noop_without_artifact_and_flags_with_one(tmp_path):
    s = Settings(artifact_dir=tmp_path, classifier_threshold=0.5)
    df = extract_features(_parsed())
    assert classifier.predict(df, s) == []
    y = (df["characteristic_id"] == "OUT").astype(int)
    model = RandomForestClassifier(n_estimators=20, random_state=0).fit(df[FEATURE_COLUMNS], y)
    joblib.dump({"model": model, "columns": FEATURE_COLUMNS}, tmp_path / "classifier.joblib")
    found = classifier.predict(df, s)
    assert [f.characteristic_id for f in found] == ["OUT"] and found[0].confidence >= 0.5


def test_anomaly_uses_saved_artifact(tmp_path):
    df = extract_features(_parsed(outlier=False))
    joblib.dump(IsolationForest(random_state=0).fit(df[FEATURE_COLUMNS]), tmp_path / "anomaly.joblib")
    out = extract_features(_parsed(n=3, outlier=True))
    assert any(f.characteristic_id == "OUT" for f in anomaly.detect(out, Settings(artifact_dir=tmp_path)))
