# Architecture Decision Record

## 1. Source adapters

Every source has its own module under `app/sources/`. This isolates connection, parsing, source-specific schema normalization, and source-level quality handling.

## 2. Orchestration

`app/pipeline.py` orchestrates the workflow but does not own source-specific rules.

## 3. Integration key

`student_id` is the shared business key across CSV, REST API, and SQLite, matching the assignment scenario.

## 4. Final dataset grain

`final_dataset.csv` is one row per **student-course enrollment** because SQLite contains a many-to-many academic relationship. This preserves course-level facts rather than collapsing them prematurely.

A second derived output, `student_ml_dataset.csv`, provides a one-row-per-student analytical grain for ML-oriented use.

## 5. Invalid data policy

- Missing numeric values: median imputation where configured.
- Invalid range values: reject with explicit reason.
- Duplicates: reject and keep the first valid occurrence.
- Cross-source mismatch: reject the incompatible record and preserve traceability.

## 6. Incremental strategy

The project uses deterministic SHA-256 fingerprints of source files plus the configured API endpoint. When no fingerprints change and existing outputs are present, the pipeline reuses existing results.

For production-scale true row-level incremental processing, the next evolution would add a durable source watermark/change-tracking mechanism.

## 7. Data lineage

The final `source` field records `CSV+API+DATABASE`. Rejected data also records the originating source and raw record representation.

## 8. Extensibility

New source adapters can be added under `app/sources/` without rewriting transformation and output modules.

Potential future adapters:

- Excel
- JSON
- MySQL
- PostgreSQL
- MongoDB
