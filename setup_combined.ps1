param([switch]$SeedDemo, [switch]$ScamModel)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.env')) {
    throw 'Create root .env from .env.example and configure PostgreSQL locally before setup.'
}
if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
    & python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python virtual environment creation failed.' }
}
$taskPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
& $taskPython -m pip install -r backend/requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Backend dependency installation failed.' }
if ($ScamModel) {
    & $taskPython -m pip install -r requirements-scam.txt
    if ($LASTEXITCODE -ne 0) { throw 'Original scam model dependency installation failed.' }
}
Push-Location -LiteralPath 'front end'
try {
    & npm.cmd ci
    if ($LASTEXITCODE -ne 0) { throw 'Frontend installation failed.' }
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
} finally { Pop-Location }
if ($SeedDemo) {
    & $taskPython scripts/seed_demo_patterns.py
    if ($LASTEXITCODE -ne 0) { throw 'Demo seeding failed.' }
}
Write-Host 'Ready: .\.venv\Scripts\python backend/run_server.py'
