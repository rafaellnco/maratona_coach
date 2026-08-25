# Arranca o bot em background (Windows)
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Main = Join-Path $Root "main.py"
$LogDir = Join-Path $Root "logs"
$LogFile = Join-Path $LogDir "bot.log"
$PidFile = Join-Path $LogDir "bot.pid"

if (-not (Test-Path $Python)) {
    Write-Error "Venv não encontrado. Corre: python -m venv .venv && .venv\Scripts\pip install -e ."
}

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

if (Test-Path $PidFile) {
    $oldPid = Get-Content $PidFile -ErrorAction SilentlyContinue
    if ($oldPid -and (Get-Process -Id $oldPid -ErrorAction SilentlyContinue)) {
        Write-Host "Bot já a correr (PID $oldPid). Logs: $LogFile"
        exit 0
    }
}

$env:DATABASE_URL = "sqlite:///./data/maratona_coach.db"
$env:PYTHONPATH = $Root

Start-Process -FilePath $Python `
    -ArgumentList $Main `
    -WorkingDirectory $Root `
    -WindowStyle Hidden `
    -RedirectStandardOutput $LogFile `
    -RedirectStandardError (Join-Path $LogDir "bot.err.log") `
    -PassThru | ForEach-Object {
        $_.Id | Set-Content $PidFile -Encoding ASCII
        Write-Host "Bot arrancado (PID $($_.Id))"
        Write-Host "Logs: $LogFile"
    }
