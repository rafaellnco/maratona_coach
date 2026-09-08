#!/usr/bin/env python3
"""Keep JustRunMy free-tier app alive by renewing ping via start/restart.

Free tier stops after ~36h without ping. Call this daily (or every 12h).
Requires env:
  JUSTRUNMY_X_USER_IDENTITY  — from JustRunMy → MCP Server Config
  JUSTRUNMY_APP_ID           — optional, default 60540
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

MCP_URL = "https://justrunmy.app/api/mcp"
DEFAULT_APP_ID = 60540


def parse_mcp_response(raw: str):
    raw = (raw or "").strip()
    if not raw:
        return {}
    if raw.startswith("event:") or raw.startswith("data:"):
        body = None
        for line in raw.splitlines():
            if line.startswith("data:"):
                body = json.loads(line[5:].strip())
        if body is None:
            raise RuntimeError(f"No data line in SSE: {raw[:300]}")
    else:
        body = json.loads(raw)
    if "error" in body:
        raise RuntimeError(body["error"])
    content = body.get("result", {}).get("content", [])
    if content and content[0].get("type") == "text":
        text = content[0].get("text") or ""
        if not text:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"text": text}
    return body.get("result", {})


def mcp_call(identity: str, tool: str, arguments: dict | None = None, timeout: int = 180):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": arguments or {}},
    }
    req = urllib.request.Request(
        MCP_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "X-User-Identity": identity,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return parse_mcp_response(resp.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:400]
        raise RuntimeError(f"HTTP {exc.code} calling {tool}: {detail}") from exc


def ping_left(app: dict) -> str | None:
    for prop in app.get("properties") or []:
        if prop.get("name") == "com.jrnm.computed.ping_left":
            return prop.get("value")
    return None


def main() -> int:
    identity = os.environ.get("JUSTRUNMY_X_USER_IDENTITY", "").strip()
    if not identity:
        print("ERRO: falta JUSTRUNMY_X_USER_IDENTITY", file=sys.stderr)
        return 2

    app_id = int(os.environ.get("JUSTRUNMY_APP_ID", str(DEFAULT_APP_ID)))
    print(f"Keepalive JustRunMy appId={app_id}", flush=True)

    before = mcp_call(identity, "jrnm_get_app_status", {"appId": app_id})
    print(f"Antes: {before}", flush=True)

    mcp_call(identity, "jrnm_start_or_restart_app", {"appId": app_id})
    print("start_or_restart enviado", flush=True)

    # Dar tempo ao container a subir
    deadline = time.time() + 120
    status = {}
    while time.time() < deadline:
        time.sleep(5)
        status = mcp_call(identity, "jrnm_get_app_status", {"appId": app_id})
        if status.get("isStarted") or status.get("status") == "RUNNING":
            break

    apps = mcp_call(identity, "jrnm_get_user_apps")
    items = apps.get("result", apps).get("items", apps.get("items", []))
    app_meta = next((a for a in items if a.get("id") == app_id), None)
    left = ping_left(app_meta or {})

    print(f"Depois: {status}", flush=True)
    print(f"ping_left: {left}", flush=True)

    if not (status.get("isStarted") or status.get("status") == "RUNNING"):
        print("ERRO: app nao ficou RUNNING", file=sys.stderr)
        return 1

    if left and str(left).startswith("-"):
        print("AVISO: ping_left ainda negativo — free tier pode falhar", file=sys.stderr)
        return 1

    print("OK: app viva e ping renovado", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
