# Verification Record

The project was verified before packaging.

## Automated tests

```text
9 passed
```

The test suite covers CSV extraction, REST extraction behavior, SQLite extraction, duplicates, missing values, transformations, integration, and final validation.

## End-to-end pipeline verification

A temporary HTTP server was used only during build-time verification to simulate the same JSON contract that the deployed online REST API will expose. The complete pipeline successfully produced:

- 18 integrated final records
- 11 rejected records with reasons
- 3 duplicate records detected
- 3 missing values handled
- 3 cross-source mismatches
- a successful second incremental run with source-cache reuse

The packaged project does **not** depend on that temporary server. The production pipeline requires the cloud-deployed HTTPS URL configured in `config.json` or `STUDENT_PIPELINE_API_URL`.
