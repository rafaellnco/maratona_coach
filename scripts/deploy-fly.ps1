#!/usr/bin/env pwsh
# Deploy Maratona Coach para Fly.io (requer cartão em https://fly.io/dashboard/personal/billing)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Carregar .env
Get-Content .env | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
    }
}

$appName = "maratona-coach"
$region = "ams"
$flyUrl = "https://${appName}.fly.dev/webhook/telegram"

Write-Host "==> Verificar login Fly.io..."
flyctl auth whoami

Write-Host "==> Criar app (se não existir)..."
flyctl apps list | Select-String $appName
if ($LASTEXITCODE -ne 0 -or -not (flyctl apps list 2>$null | Select-String $appName)) {
    flyctl launch --no-deploy --region $region --copy-config --yes --name $appName
}

Write-Host "==> Criar volume (ignora se já existir)..."
flyctl volumes create maratona_data --region $region --size 1 -a $appName 2>$null

Write-Host "==> Configurar secrets..."
flyctl secrets set `
    "ANTHROPIC_API_KEY=$env:ANTHROPIC_API_KEY" `
    "ANTHROPIC_MODEL=$env:ANTHROPIC_MODEL" `
    "TELEGRAM_BOT_TOKEN=$env:TELEGRAM_BOT_TOKEN" `
    "TELEGRAM_WEBHOOK_URL=$flyUrl" `
    "SCHEDULER_TIMEZONE=$env:SCHEDULER_TIMEZONE" `
    -a $appName

Write-Host "==> Deploy..."
flyctl deploy -a $appName

Write-Host "==> Registar webhook Telegram..."
try {
    Invoke-RestMethod -Method Post -Uri "https://${appName}.fly.dev/webhook/telegram/register"
} catch { Write-Host "Registo manual pode ser necessário após deploy." }

Write-Host ""
Write-Host "Deploy concluído: $flyUrl"
Write-Host "Testa /start no Telegram."
