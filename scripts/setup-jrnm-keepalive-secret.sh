#!/usr/bin/env bash
# Corre no teu PC (com gh autenticado). Lê a identity do Cursor MCP e mete o secret no GitHub.
set -euo pipefail
REPO="${1:-rafaellnco/maratona_coach}"
MCP_JSON="${MCP_JSON:-$HOME/.cursor/mcp.json}"
if [[ ! -f "$MCP_JSON" ]]; then
  echo "Não encontrei $MCP_JSON — passa a identity via stdin:  echo 'IDENTITY' | $0"
  exit 1
fi
IDENTITY="$(python3 - <<PY
import json
cfg=json.load(open("$MCP_JSON", encoding="utf-8"))
print(cfg["mcpServers"]["justrunmy.app"]["headers"]["X-User-Identity"])
PY
)"
printf '%s' "$IDENTITY" | gh secret set JUSTRUNMY_X_USER_IDENTITY --repo "$REPO"
echo "OK: secret JUSTRUNMY_X_USER_IDENTITY definido em $REPO"
echo "Agora: merge do PR #1 + Actions → JustRunMy keepalive → Run workflow"
