# ---------------------------------------------------------------------------
# Start-GovRAG.ps1 -- the only sanctioned way to open a GovernRAG run terminal.
# Approved by Vivek 2026-07-19 after the wrong-tree M1 incident: pins the repo
# working directory, starts a dated transcript, activates the venv, loads the
# API key from the repo .env (quote-safe), and PRINTS the resulting state so a
# misconfigured terminal is visible before any command is typed.
#
# USAGE (any new PowerShell):
#   & "C:\Users\gunav\repos\conceptual_GraphRAG\Start-GovRAG.ps1"
# ---------------------------------------------------------------------------
Set-Location "C:\Users\gunav\repos\conceptual_GraphRAG"

New-Item -ItemType Directory -Force -Path ".\logs" | Out-Null
try {
    Start-Transcript -Path (".\logs\PhD_Run_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmm")) | Out-Null
} catch {
    Write-Host "[note] transcript already running in this session; continuing." -ForegroundColor Yellow
}

& "C:\Users\gunav\OneDrive - UA Little Rock\PhD\3 Dissertation\conceptual_GraphRAG\venv\Scripts\Activate.ps1"

$line = Get-Content .env | Where-Object { $_ -match '^GEMINI_API_KEY=' } | Select-Object -First 1
if ($line) {
    $env:GEMINI_API_KEY = ($line -replace '^GEMINI_API_KEY=', '').Trim().Trim('"').Trim("'")
}

Write-Host ""
Write-Host "=== GovernRAG terminal ready ===" -ForegroundColor Green
Write-Host ("folder : {0}" -f (Get-Location))
if ($env:GEMINI_API_KEY) {
    Write-Host ("key    : {0}...  (run-2 key should start with AIzaSyDhK)" -f $env:GEMINI_API_KEY.Substring(0, [Math]::Min(10, $env:GEMINI_API_KEY.Length)))
} else {
    Write-Host "key    : MISSING -- .env has no GEMINI_API_KEY line! Do not run pipeline stages." -ForegroundColor Red
}
python -c "import sys; print('python :', sys.executable)"
Write-Host "================================" -ForegroundColor Green
