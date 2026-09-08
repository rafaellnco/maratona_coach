# Corre no teu PC: define o secret GitHub a partir do MCP JustRunMy do Cursor
$ErrorActionPreference = "Stop"
$repo = if ($args[0]) { $args[0] } else { "rafaellnco/maratona_coach" }
$mcp = Join-Path $env:USERPROFILE ".cursor\mcp.json"
if (-not (Test-Path $mcp)) { throw "Falta $mcp" }
$identity = (Get-Content $mcp -Raw | ConvertFrom-Json).mcpServers.'justrunmy.app'.headers.'X-User-Identity'
$identity | gh secret set JUSTRUNMY_X_USER_IDENTITY --repo $repo
Write-Host "OK: secret definido em $repo"
Write-Host "Merge PR #1 e corre Actions → JustRunMy keepalive"
