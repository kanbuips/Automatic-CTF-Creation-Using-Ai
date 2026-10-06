# CTF Validation Backend

FastAPI service: JTXML parsing -> feature extraction -> rules + ML + anomaly detection -> QC report -> approval.

```
pip install -r requirements.txt
uvicorn app.main:app --reload
pytest
```
