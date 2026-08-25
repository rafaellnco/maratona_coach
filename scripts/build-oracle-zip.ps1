# Gera maratona-oracle.zip para deploy na Oracle Cloud Always Free
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

$zipName = "maratona-oracle.zip"
$staging = Join-Path $env:TEMP "maratona-oracle"

if (Test-Path $staging) { Remove-Item $staging -Recurse -Force }
if (Test-Path $zipName) { Remove-Item $zipName -Force }
New-Item -ItemType Directory -Path $staging | Out-Null

Copy-Item -Recurse "app" $staging\app
Copy-Item "app.py", "main.py", "requirements.txt", "pyproject.toml" $staging\

# install.sh na raiz do ZIP (Linux line endings)
$installSh = (Get-Content "scripts\oracle-install.sh" -Raw) -replace "`r`n", "`n" -replace "`r", "`n"
[System.IO.File]::WriteAllText((Join-Path $staging "install.sh"), $installSh, [System.Text.UTF8Encoding]::new($false))

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
    $envMap["TELEGRAM_WEBHOOK_URL"] = ""
    $envMap.Remove("TWILIO_ACCOUNT_SID")
    $envMap.Remove("TWILIO_AUTH_TOKEN")
    $envMap.Remove("TWILIO_WHATSAPP_FROM")
    $envMap.Remove("USER_WHATSAPP_NUMBER")

    $out = $envMap.Keys | Sort-Object | ForEach-Object { "$_=$($envMap[$_])" }
    $out | Set-Content (Join-Path $staging ".env") -Encoding UTF8
    Write-Host "Incluido .env de producao (confirma TELEGRAM_ALLOWED_USER_ID)."
} else {
    Write-Warning ".env nao encontrado - copia .env.example para .env antes do deploy."
}

Get-ChildItem $staging -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Compress-Archive -Path "$staging\*" -DestinationPath $zipName -Force
Remove-Item $staging -Recurse -Force

$sizeKb = [math]::Round((Get-Item $zipName).Length / 1024, 1)
Write-Host ""
Write-Host "Criado: $((Get-Item $zipName).FullName)"
Write-Host "Tamanho: $sizeKb KB"
Write-Host "Segue ORACLE.md para criar a VM e fazer upload."
