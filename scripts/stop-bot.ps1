# Para o bot em background
$Root = Split-Path $PSScriptRoot -Parent
$PidFile = Join-Path $Root "logs\bot.pid"

if (-not (Test-Path $PidFile)) {
    Write-Host "Nenhum bot em background (ficheiro PID não existe)."
    exit 0
}

$botPid = [int](Get-Content $PidFile)
$proc = Get-Process -Id $botPid -ErrorAction SilentlyContinue
if ($proc) {
    Stop-Process -Id $botPid -Force
    Write-Host "Bot parado (PID $botPid)."
} else {
    Write-Host "Processo $botPid já não existe."
}
Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
