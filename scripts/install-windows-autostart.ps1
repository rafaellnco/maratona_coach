# Arranque automático via pasta Startup (não precisa de admin)
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Runner = Join-Path $Root "scripts\run-bot-background.ps1"
$Startup = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $Startup "Maratona Coach Bot.lnk"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($ShortcutPath)
$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$Runner`""
$shortcut.WorkingDirectory = $Root
$shortcut.Description = "Maratona Coach Telegram bot"
$shortcut.Save()

Write-Host "Arranque automático instalado:"
Write-Host "  $ShortcutPath"
Write-Host ""
Write-Host "O bot arranca quando inicias sessão no Windows."
Write-Host "A arrancar agora..."
& $Runner
