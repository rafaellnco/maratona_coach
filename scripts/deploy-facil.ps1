# Deploy facil - gera ZIP e abre FPS.ms
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

Write-Host ""
Write-Host "=== Maratona Coach - deploy facil (FPS.ms) ===" -ForegroundColor Cyan
Write-Host ""

& "$PSScriptRoot\build-fps-zip.ps1"

Write-Host ""
Write-Host "Proximos passos:" -ForegroundColor Yellow
Write-Host "  1. Create Server -> Python Telegram Bot"
Write-Host "  2. Files -> upload maratona-fps.zip -> extrair"
Write-Host "  3. Console -> Start"
Write-Host "  4. Telegram -> /start"
Write-Host ""
Write-Host "Guia: FACIL.md"
Write-Host ""

Start-Process "https://fps.ms/free-telegram-bot-hosting/"
