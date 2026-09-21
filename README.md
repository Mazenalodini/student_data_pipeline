# Student Multi-Source Data Pipeline

A professional Python Data Engineering project that extracts student data from three independent sources — CSV, an online REST API, and SQLite — then validates, cleans, integrates, transforms, quality-checks, and loads reusable analytical datasets.

## Why this project exists

This project implements the comprehensive practical assignment:

`CSV + REST API + SQLite -> Extract -> Validate -> Clean -> Integrate -> Transform -> Final Validation -> Load`

The required output is `data/processed/final_dataset.csv`; invalid records are routed to `data/rejected/rejected_records.csv`.

## Architecture

```text
                         MULTI-SOURCE DATA
                ┌────────────┬────────────┐
                │            │            │
               CSV      ONLINE REST     SQLITE
                │            │            │
                └────────────┼────────────┘
                             ▼
                         EXTRACTION
                             ▼
                    SOURCE VALIDATION
                             ▼
                           CLEAN
                             ▼
                         INTEGRATION
                             ▼
                       TRANSFORMATION
                             ▼
                      FINAL VALIDATION
                         /         \
                        /           \
               VALID RECORDS     INVALID RECORDS
                     │                  │
                     ▼                  ▼
          final_dataset.csv     rejected_records.csv
                     │
                     ▼
             ML / BI / ANALYSIS
```

## Project structure

```text
student_data_pipeline/
├── app/
│   ├── sources/
│   │   ├── csv_source.py
│   │   ├── api_source.py
│   │   └── database_source.py
│   ├── transformation/
│   │   ├── cleaner.py
│   │   ├── integration.py
│   │   └── transformer.py
│   ├── validation/
│   │   └── quality.py
│   ├── output/
│   │   └── csv_writer.py
│   ├── utils/
│   │   ├── logger.py
│   │   ├── metrics.py
│   │   └── hashing.py
│   ├── config.py
│   ├── models.py
│   └── pipeline.py
├── api_service/
│   ├── main.py
│   ├── data/students_api.json
│   ├── Dockerfile
│   ├── render.yaml
│   ├── README.md
│   └── requirements.txt
├── data/
│   ├── raw/students.csv
│   ├── processed/
│   └── rejected/
├── database/
├── logs/
├── reports/
├── state/
├── scripts/setup_database.py
├── tests/
├── config.json
├── main.py
└── requirements.txt
```

## Data sources

### 1. CSV

`data/raw/students.csv`

Student identity/demographic data:

- `student_id`
- `student_name`
- `age`
- `major`
- `city`

The file intentionally contains realistic data-quality problems required by the assignment.

### 2. Online REST API

The pipeline consumes a public HTTPS endpoint with the contract:

```json
[
  {
    "student_id": 1001,
    "gpa": 3.45,
    "attendance": 92,
    "status": "Active"
  }
]
```

The API implementation is under `api_service/` and is designed to be deployed to a cloud platform such as Render or Railway. The pipeline reads its URL from `config.json` or `STUDENT_PIPELINE_API_URL`.

> The repository is deployment-ready. A public HTTPS URL still requires deploying `api_service/` to a cloud account and then configuring that URL in `config.json` or the environment variable.

### 3. SQLite

`database/students.db` contains:

- `courses`
- `enrollments`

The extraction uses SQL JOINs to produce course-enrollment records.

## Data quality rules

The pipeline enforces the assignment rules:

| Field | Rule |
|---|---|
| `student_id` | required and unique within a source |
| `age` | 16–80 |
| `gpa` | 0–4 |
| `attendance` | 0–100 |
| `score` | 0–100 |
| text fields | trimmed and normalized |

Missing numeric values are imputed using the configured median strategy. Invalid range values are rejected rather than silently corrected. Duplicate records are rejected, and cross-source incompatibilities are recorded as rejected records.

## Rejected records

`data/rejected/rejected_records.csv` contains:

- source
- record_type
- student_id
- error_reason
- raw_record
- detected_at

This preserves traceability instead of silently discarding bad data.

## Transformations

The final integrated dataset contains the original attributes plus derived features:

- `performance_level`
- `attendance_status`
- `score_band`
- `source`

`source` provides basic Data Lineage by showing that the final row is composed from `CSV+API+DATABASE`.

An additional student-level feature dataset is generated at:

`data/processed/student_ml_dataset.csv`

It aggregates course activity into:

- course count
- total credit hours
- average score
- highest score
- lowest score

## Configuration

`config.json` keeps paths, API URL, retry settings, output locations, and processing rules outside the business logic.

For deployment, prefer an environment variable instead of hardcoding a production URL:

```powershell
$env:STUDENT_PIPELINE_API_URL="https://YOUR-DEPLOYED-API.example.com/students"
```

## Setup

Recommended Python versions: 3.11–3.13.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts\setup_database.py
```

## Configure the online API

Update `config.json`:

```json
"api": {
  "url": "https://YOUR-DEPLOYED-API.example.com/students",
  "timeout_seconds": 15
}
```

or set:

```powershell
$env:STUDENT_PIPELINE_API_URL="https://YOUR-DEPLOYED-API.example.com/students"
```

## Run

Full refresh:

```powershell
python main.py --mode full
```

Incremental mode:

```powershell
python main.py
```

The default is the configured incremental mode. If no source fingerprint has changed and outputs already exist, the pipeline reuses the current results.

## Outputs

Required:

```text
data/processed/final_dataset.csv
data/rejected/rejected_records.csv
logs/pipeline.log
```

Additional engineering outputs:

```text
data/processed/student_ml_dataset.csv
reports/pipeline_metrics.json
reports/pipeline_run.md
state/source_manifest.json
```

## Pipeline metrics

The metrics report includes:

- total records
- source record counts
- integrated records
- valid records
- rejected records
- duplicate records
- missing values handled
- rejection reasons
- processing time
- source fingerprints
- incremental cache information

## Online API deployment

### Online deployment

1. Push the repository to GitHub.
2. Deploy the `api_service/` directory using the included `render.yaml` or `Dockerfile`.
3. After deployment, copy the public HTTPS `/students` endpoint into `config.json`.
4. Verify `/health` and `/docs`.

`api_service/Dockerfile` is ready for container-based deployment.

## Tests

Run:

```powershell
pytest -q
```

The tests cover:

1. CSV loading
2. API extraction
3. SQLite extraction
4. duplicate detection
5. missing value handling
6. rejection of invalid records
7. source integration
8. transformation
9. final validation

## Clean Code and engineering practices

- Separation of Concerns
- Single Responsibility
- Explicit source adapters
- Typed Python interfaces
- Small testable functions
- No business logic in `main.py`
- Configuration outside the code
- Structured logging
- Rejected-record traceability
- Source fingerprints and incremental mode
- Reusable transformation functions
- Deterministic outputs
- SQL extraction separated from business transformation

## How this maps to the assignment

| Assignment requirement | Implementation |
|---|---|
| CSV extraction | `app/sources/csv_source.py` |
| REST API extraction | `app/sources/api_source.py` |
| SQLite extraction | `app/sources/database_source.py` |
| Validation | `app/validation/quality.py` + source validators |
| Cleaning | `app/sources/*` validation/cleaning + `app/transformation/cleaner.py` |
| Transformation | `app/transformation/transformer.py` |
| Integration | `app/transformation/integration.py` |
| Rejected data | `app/output/csv_writer.py` |
| Load | `app/output/csv_writer.py` |
| Logging | `app/utils/logger.py` |
| Configuration | `config.json` |
| Metrics | `app/utils/metrics.py` |
| Incremental processing | `app/pipeline.py` source fingerprints |
| Data lineage | `source` column + run metadata |
| Reusable architecture | source adapter modules |
| Tests | `tests/` |
| Documentation | `README.md`, `README_AR.md`, `docs/` |

## Final assignment answers

### 1. Why do we need a data pipeline with multiple sources?

Because production data is usually distributed across files, APIs, and databases. A pipeline gives the project a controlled process for extracting, validating, cleaning, integrating, transforming, and loading that data.

### 2. Raw vs Processed

Raw data preserves what came from the source. Processed data has been cleaned, standardized, validated, and transformed for downstream use.

### 3. Extract, Transform, Load

Extract obtains data from source systems. Transform changes structure, quality, or business representation. Load writes the final dataset to its destination.

### 4. Integration problems

Typical issues include missing IDs, different text casing, duplicates, missing values, invalid ranges, and records that exist in one source but not another.

### 5. Missing values

The numeric fields use median imputation because the strategy is simple, deterministic, and less sensitive to extreme values than a mean. The strategy is documented in configuration.

### 6. Duplicate records

Exact duplicates and duplicate business keys are detected and rejected with an explicit reason.

### 7. Invalid records

Records violating business rules are separated into `rejected_records.csv` rather than silently being included in the final dataset.

### 8. Why separate Extraction from Transformation?

It isolates source-specific I/O concerns from business rules. A new source can be added without rewriting the transformation layer.

### 9. Why is validation essential?

A downstream model or report is only as reliable as the data it receives. Validation makes quality expectations explicit and prevents invalid records from silently entering the final dataset.

### 10. How can the pipeline run automatically?

It can be scheduled with Windows Task Scheduler, cron, CI/CD, or a workflow orchestrator such as Airflow.

### 11. How can it handle millions of records?

Use chunked reads, incremental extraction, database-side filtering/aggregation, partitioning, parallel processing where appropriate, and a scalable storage/compute platform.

### 12. Batch vs Streaming

Batch processing handles data in groups at scheduled or triggered intervals. Streaming processes events continuously or near-real-time as they arrive.
