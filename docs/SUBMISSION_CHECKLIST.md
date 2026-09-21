# Submission Checklist

## Assignment requirements

- [x] CSV source
- [x] Online REST API source contract + deployable service
- [x] SQLite source
- [x] Extraction layer
- [x] Validation rules
- [x] Cleaning and missing-value strategy
- [x] Column normalization
- [x] Data type conversion
- [x] Three derived columns
- [x] Integration using `student_id`
- [x] Rejected records with reasons
- [x] `final_dataset.csv`
- [x] Logging
- [x] Tests
- [x] README and documentation

## Excellence requirements

- [x] External configuration with `config.json`
- [x] Source-aware incremental processing
- [x] Data lineage field
- [x] Pipeline metrics
- [x] Reusable source-adapter architecture
- [x] Cloud-deployable online API service
- [x] Additional one-row-per-student ML feature dataset
- [x] SQL schema and indexes
- [x] Raw source snapshots for traceability
- [x] API retry/backoff handling

## Before submission

1. Deploy `api_service/` to your chosen cloud platform.
2. Put the production HTTPS `/students` URL into `config.json` or `STUDENT_PIPELINE_API_URL`.
3. Run the full pipeline once.
4. Run the incremental pipeline again without changing the sources.
5. Run `pytest -q`.
6. Review `final_dataset.csv`, `rejected_records.csv`, `pipeline_metrics.json`, and `pipeline.log`.
7. Capture screenshots for the submission report.
