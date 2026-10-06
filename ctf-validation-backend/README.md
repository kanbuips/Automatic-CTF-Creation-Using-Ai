# CTF Validation Backend

FastAPI service. Pipeline: JTXML -> parse -> features -> rules -> ML classifier -> anomaly -> report -> approval.

```
pip install -r requirements.txt
uvicorn app.main:app --reload      # docs at /docs
pytest
```

## API (`/api/v1`, optional `X-API-Key` when `API_KEY` is set)

| Method | Path | Purpose |
|---|---|---|
| POST | `/upload/jtxml`, `/upload/ctf` | multipart `file`; returns `file_id` |
| POST | `/validate` | `{jtxml_file_id, ctf_file_id?}` -> 202 job; runs in background |
| GET | `/validate`, `/validate/{job_id}` | job list / status, stage progress, findings |
| GET | `/reports/{job_id}` | full QC report |
| GET | `/reports/{job_id}/download?format=xlsx\|pdf` | export |
| POST/GET | `/approval/{job_id}` | approve/reject (reject needs a comment; failing jobs cannot be approved) / audit trail |
| GET | `/health` | liveness |

## Rules (severity)
- **TPL**: Beta 3 required, Beta 2 rejected (critical), missing/unknown version
- **NAMP/NAMM**: part / model name missing or invalid characters
- **NOM**: nominal missing/non-numeric, duplicate ids, conflicting nominals
- **TOL**: missing, wrong-sign, zero-width, asymmetric, over-wide tolerance
- **DIR**: direction missing / not in X,Y,Z,XY,XZ,YZ,XYZ
- **WRD**: empty, placeholder (TBD/TODO/???), too short, whitespace

Verdict: any critical/error -> `fail`; warnings only -> `review`; otherwise `pass`.

## ML
Both ML stages are advisory. Without artifacts the classifier is skipped and the anomaly detector fits an
Isolation Forest on the current file (needs >= 8 characteristics). Train artifacts into `ml/artifacts/`:

```
python -m ml.training.train_classifier --data labeled.csv      # feature columns + `label`
python -m ml.training.train_anomaly --jtxml-dir approved_jtxml/
```

## Assumptions
- No sample JTXML was provided; the parser accepts fields as attributes or child elements with common
  aliases (see `parsing/jtxml_parser.py`). Adjust `FIELD_ALIASES` to match the real schema.
- The CTF file is stored and linked to the job but not yet parsed or cross-checked.
- Tables are created at startup; use Alembic (`app/db/migrations`) for schema changes in production.

## Generate a CTF from a previous CTF's tolerances
Keeps the new CTF-PIS workbook (e.g. template `BETA_V003`, read from `Front page`) exactly as is - macros, styles,
validations - and rewrites only Nominal / Lower / Upper limit (columns P, Q, R) from a previous CTF.

```
python -m app.pipeline.generation.tolerance_transfer new.xlsm previous.xlsm out.xlsm [--map 01A02=01A05]
# API: POST /api/v1/generate {template_file_id, source_file_id, overrides}  ->  GET /api/v1/generate/{id}/download
```
Matching is strict on purpose: same Type, same first word of the wording (Size/Position/Flatness...) and the
same datum letter, and all matching previous rows must agree. Anything else (`no_match`, `no_key`, `ambiguous`)
is left untouched and reported; use `--map` / `overrides` to force a pairing. Wording similarity alone is not used,
because different parts share generic wording but not tolerances.
