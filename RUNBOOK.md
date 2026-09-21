# Runbook

## Standard setup

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts\setup_database.py
```

## Configure the online API

```powershell
$env:STUDENT_PIPELINE_API_URL="https://YOUR-DEPLOYED-API.example.com/students"
```

Or edit `config.json`.

## Full refresh

```powershell
python main.py --mode full
```

## Incremental run

```powershell
python main.py
```

## Tests

```powershell
pytest -q
```

## API deployment

The production source is the cloud-deployed service under `api_service/`.
See `api_service/README.md`.

## Troubleshooting

### API URL error

The message `Online API URL is not configured` means the placeholder in `config.json` was not replaced and `STUDENT_PIPELINE_API_URL` is not set.

### SQLite database missing

Run:

```powershell
python scripts\setup_database.py
```

### Rebuild all outputs

Run:

```powershell
python main.py --mode full
```
