$ErrorActionPreference = "Stop"

Write-Host "== Student Multi-Source Pipeline Bootstrap ==" -ForegroundColor Cyan

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    py -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
& ".\.venv\Scripts\python.exe" scripts\setup_database.py

Write-Host "Bootstrap completed." -ForegroundColor Green
