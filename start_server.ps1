$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonCandidates = @(
    (Join-Path $projectRoot ".venv\Scripts\python.exe"),
    (Join-Path $projectRoot "venv\Scripts\python.exe"),
    "C:\Program Files\MySQL\MySQL Shell 8.0\lib\Python3.13\Lib\venv\scripts\nt\python.exe"
)

$python = $pythonCandidates |
    Where-Object { Test-Path $_ } |
    Select-Object -First 1

if (-not $python) {
    throw "No working Python installation was found. Install Python from python.org and create a virtual environment."
}

Set-Location $projectRoot
Write-Host "Starting ChildGuard AI at http://127.0.0.1:8000/"
& $python manage.py migrate
& $python manage.py runserver 127.0.0.1:8000
