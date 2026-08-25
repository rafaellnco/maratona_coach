# ZIP para FPS.ms (Pterodactyl)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

$zipName = "maratona-fps.zip"
$staging = Join-Path $env:TEMP "maratona-fps"

if (Test-Path $staging) { Remove-Item $staging -Recurse -Force }
if (Test-Path $zipName) { Remove-Item $zipName -Force }
New-Item -ItemType Directory -Path $staging | Out-Null

Copy-Item -Recurse "app" $staging\app
Copy-Item "bot.py", "app.py", "requirements-fps.txt" (Join-Path $staging "requirements.txt")

if (Test-Path ".env") {
    $lines = Get-Content ".env" | Where-Object { $_ -notmatch '^\s*#' -and $_ -match '\S' }
    $envMap = @{}
    foreach ($line in $lines) {
        if ($line -match '^([^=]+)=(.*)$') {
            $envMap[$matches[1].Trim()] = $matches[2].Trim()
        }
    }
    $envMap["DATABASE_URL"] = "sqlite:///./data/maratona_coach.db"
    $envMap["APP_ENV"] = "production"
    $envMap["PYTHONPATH"] = "."
    $envMap["SHOWCASE_ENABLED"] = "false"
    $envMap["PYTHONUNBUFFERED"] = "1"
    $envMap["TELEGRAM_WEBHOOK_URL"] = ""
    $envMap.Remove("TWILIO_ACCOUNT_SID")
    $envMap.Remove("TWILIO_AUTH_TOKEN")
    $envMap.Remove("TWILIO_WHATSAPP_FROM")
    $envMap.Remove("USER_WHATSAPP_NUMBER")
    $out = $envMap.Keys | Sort-Object | ForEach-Object { "$_=$($envMap[$_])" }
    $out | Set-Content (Join-Path $staging ".env") -Encoding UTF8
}

Get-ChildItem $staging -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Compress-Archive -Path "$staging\*" -DestinationPath $zipName -Force
Remove-Item $staging -Recurse -Force

$sizeKb = [math]::Round((Get-Item $zipName).Length / 1024, 1)
Write-Host "Criado: $((Get-Item $zipName).FullName) ($sizeKb KB)"
Write-Host "Startup: PY_FILE=bot.py  REQUIREMENTS_FILE=requirements.txt"
