# Gera maratona-coach-deploy.zip (JustRunMy.App — polling, build fiavel)
param(
    [switch]$IncludeEnv = $true,
    [switch]$BotOnly
)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

$zipName = "maratona-coach-deploy.zip"
$staging = Join-Path $env:TEMP "maratona-coach-deploy"

if (Test-Path $staging) { Remove-Item $staging -Recurse -Force }
if (Test-Path $zipName) { Remove-Item $zipName -Force }

New-Item -ItemType Directory -Path $staging | Out-Null

# Estrutura obrigatoria na raiz do ZIP (nao metas numa subpasta)
Copy-Item -Recurse "app" $staging\app
Copy-Item "main.py" $staging\
Copy-Item "requirements-jrm.txt" (Join-Path $staging "requirements.txt")
Copy-Item "pyproject-jrm.toml" (Join-Path $staging "pyproject.toml")

if (-not $BotOnly) {
    Copy-Item -Recurse "docs" $staging\docs
    Copy-Item "run.py" $staging\
}

$startSh = (Get-Content "start.sh" -Raw) -replace "`r`n", "`n" -replace "`r", "`n"
[System.IO.File]::WriteAllText((Join-Path $staging "start.sh"), $startSh, [System.Text.UTF8Encoding]::new($false))

if ($IncludeEnv -and (Test-Path ".env")) {
    $lines = Get-Content ".env" | Where-Object { $_ -notmatch '^\s*#' -and $_ -match '\S' }
    $envMap = @{}
    foreach ($line in $lines) {
        if ($line -match '^([^=]+)=(.*)$') {
            $envMap[$matches[1].Trim()] = $matches[2].Trim()
        }
    }
    $envMap["DATABASE_URL"] = "sqlite:///./data/maratona_coach.db"
    $envMap["APP_ENV"] = "production"
    $envMap["PYTHONPATH"] = "/app"
    $envMap["PYTHONUNBUFFERED"] = "1"
    $envMap["TELEGRAM_MODE"] = "polling"
    $envMap["PUBLIC_BASE_URL"] = ""
    $envMap["TELEGRAM_WEBHOOK_URL"] = ""
    $envMap["TELEGRAM_WEBHOOK_SECRET"] = ""
    if ($BotOnly) {
        $envMap["SHOWCASE_ENABLED"] = "false"
    }
    $envMap["MORNING_BRIEFING_HOUR"] = "9"
    $envMap["MORNING_BRIEFING_MINUTE"] = "0"
    $envMap["LUNCH_SUPPLEMENTS_HOUR"] = "14"
    $envMap["LUNCH_SUPPLEMENTS_MINUTE"] = "0"
    $envMap["RUN_DAY_REMINDER_HOUR"] = "17"
    $envMap["RUN_DAY_REMINDER_MINUTE"] = "0"
    $envMap["DINNER_SUPPLEMENTS_HOUR"] = "21"
    $envMap["DINNER_SUPPLEMENTS_MINUTE"] = "30"
    $envMap["EVENING_RECOVERY_HOUR"] = "22"
    $envMap["EVENING_RECOVERY_MINUTE"] = "30"
    $envMap.Remove("TWILIO_ACCOUNT_SID")
    $envMap.Remove("TWILIO_AUTH_TOKEN")
    $envMap.Remove("TWILIO_WHATSAPP_FROM")
    $envMap.Remove("USER_WHATSAPP_NUMBER")

    $out = @()
    foreach ($key in ($envMap.Keys | Sort-Object)) {
        $out += "$key=$($envMap[$key])"
    }
    $out | Set-Content (Join-Path $staging ".env") -Encoding UTF8
    Write-Host "Incluido .env de producao (polling)."
}

Get-ChildItem $staging -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

# Verificar estrutura antes de comprimir
$required = @("app\__init__.py", "main.py", "requirements.txt", "pyproject.toml", "start.sh")
foreach ($f in $required) {
    if (-not (Test-Path (Join-Path $staging $f))) {
        throw "ZIP incompleto: falta $f"
    }
}

# ZIP com paths POSIX (forward slashes) — Compress-Archive no Windows partia no Linux
$zipOut = Join-Path (Get-Location) $zipName
$python = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
& $python (Join-Path $PSScriptRoot "make_posix_zip.py") $staging $zipOut
if ($LASTEXITCODE -ne 0) { throw "Falha ao criar ZIP POSIX" }
Remove-Item $staging -Recurse -Force

$sizeKb = [math]::Round((Get-Item $zipName).Length / 1KB, 1)
Write-Host ""
Write-Host ('Criado: {0} ({1} KB) - paths POSIX app/__init__.py' -f (Get-Item $zipName).FullName, $sizeKb)
Write-Host ""
Write-Host "=== JustRunMy (ULTIMA BUILD) ==="
Write-Host "Start Command (UNICO comando, cola exactamente):"
Write-Host '  sh start.sh'
Write-Host ""
Write-Host "Se o painel tiver Start Command antigo, APAGA e cola so: sh start.sh"
Write-Host 'Conteudo ZIP: app/ main.py requirements.txt pyproject.toml start.sh .env'
