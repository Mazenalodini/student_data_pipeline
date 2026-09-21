# Project Map

| Area | File | Responsibility |
|---|---|---|
| Entry point | `main.py` | CLI entry point |
| Orchestration | `app/pipeline.py` | Coordinates the complete workflow |
| Config | `app/config.py` | External configuration + environment overrides |
| Shared model | `app/models.py` | Rejected-record contract |
| CSV source | `app/sources/csv_source.py` | Extract + source-level quality handling |
| REST source | `app/sources/api_source.py` | Online HTTPS extraction, retry, parsing, quality handling |
| SQLite source | `app/sources/database_source.py` | SQL JOIN extraction + quality handling |
| Cleaning | `app/transformation/cleaner.py` | Text normalization + median imputation |
| Integration | `app/transformation/integration.py` | Cross-source compatibility + joins |
| Transformation | `app/transformation/transformer.py` | Derived features + ML aggregation |
| Validation | `app/validation/quality.py` | Final dataset quality rules |
| Output | `app/output/csv_writer.py` | Dataset/rejection materialization |
| Logging | `app/utils/logger.py` | File + console logging |
| Metrics | `app/utils/metrics.py` | Pipeline metrics |
| Hashing | `app/utils/hashing.py` | Source/config fingerprints |
| API service | `api_service/` | Deployable online REST API |
| Database setup | `scripts/setup_database.py` | SQLite schema + intentionally imperfect seed data |
| Tests | `tests/` | Automated source, integration, transformation and quality checks |
