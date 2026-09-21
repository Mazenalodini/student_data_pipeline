# Assignment Mapping

This project is designed directly against the practical assignment requirements.

| Assignment area | Where it is implemented |
|---|---|
| CSV extraction | `app/sources/csv_source.py` |
| REST API extraction | `app/sources/api_source.py` |
| SQLite extraction | `app/sources/database_source.py` |
| Source validation | Source adapters + `RejectedRecord` |
| Missing values | `app/transformation/cleaner.py` via median strategy |
| Duplicate records | Source adapters |
| Invalid Age/GPA/Attendance/Score | Source adapters |
| Text inconsistency | `normalize_text_columns` |
| Column normalization | CSV/API source contracts |
| Type conversion | Source adapters |
| Derived columns | `app/transformation/transformer.py` |
| Integration | `app/transformation/integration.py` |
| Data Quality | `app/validation/quality.py` |
| Rejected records | `data/rejected/rejected_records.csv` |
| Final load | `data/processed/final_dataset.csv` |
| Logging | `logs/pipeline.log` |
| Configuration | `config.json` |
| Incremental processing | SHA-256 source/payload fingerprints + validated caches |
| Data lineage | `source` column + rejected source metadata |
| Pipeline metrics | `reports/pipeline_metrics.json` |
| Reusable architecture | `app/sources/` adapters |
| Tests | `tests/` |
| README | `README.md`, `README_AR.md` |
