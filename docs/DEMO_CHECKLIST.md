# Doctor Demo Checklist

## 1. Show the three sources

- `data/raw/students.csv`
- the deployed online REST endpoint and its `/docs`
- `database/students.db` with `courses` and `enrollments`

## 2. Show the architecture

Open `README.md` and explain:

`CSV + API + SQLite → Extract → Validate → Clean → Integrate → Transform → Final Validation → Load`

## 3. Run a full refresh

```powershell
python main.py --mode full
```

## 4. Explain Data Quality

Open:

```text
data/rejected/rejected_records.csv
```

Show invalid Age, invalid GPA, invalid Attendance, invalid Score, duplicate records, and cross-source mismatches.

## 5. Show the final integrated dataset

Open:

```text
data/processed/final_dataset.csv
```

Point out the merged columns and derived features:

- `performance_level`
- `attendance_status`
- `score_band`
- `source`

## 6. Show the ML-oriented dataset

Open:

```text
data/processed/student_ml_dataset.csv
```

Explain that it provides one row per student with aggregate course features.

## 7. Show observability

Open:

```text
reports/pipeline_metrics.json
reports/pipeline_run.md
logs/pipeline.log
```

Explain source counts, rejected counts, duplicates, missing values, processing time, and source hashes.

## 8. Demonstrate incremental processing

Run:

```powershell
python main.py
```

again without modifying the sources. Explain that local source hashes and the remote API payload hash allow the pipeline to reuse validated source results.

## 9. Run tests

```powershell
pytest -q
```
