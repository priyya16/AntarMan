$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) { return "py -3" }
    if (Get-Command python -ErrorAction SilentlyContinue) { return "python" }
    throw "Python not found. Install Python 3.10+ and retry."
}

$pythonCmd = Get-PythonCommand

Write-Host "Preparing virtual environment..."
if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment at .\venv ..."
    Invoke-Expression "$pythonCmd -m venv venv"
}

Write-Host "Installing dependencies..."
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host "Opening browser at http://127.0.0.1:8000 ..."
Start-Process "http://127.0.0.1:8000"

Write-Host "Starting backend server (stable mode)..."
Write-Host "Press Ctrl+C to stop the server."
.\venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
