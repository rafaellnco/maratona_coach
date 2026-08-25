"""Deploy hotfix bundle to JustRunMy app via MCP."""
import json
import os
import sys
import time
import urllib.request

MCP_URL = "https://justrunmy.app/api/mcp"
BUNDLE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "_upload_hotfix_bundle.json",
)


def load_identity():
    with open(os.path.expanduser("~/.cursor/mcp.json"), encoding="utf-8") as f:
        return json.load(f)["mcpServers"]["justrunmy.app"]["headers"]["X-User-Identity"]


def parse_mcp_response(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("event:") or raw.startswith("data:"):
        body = None
        for line in raw.splitlines():
            if line.startswith("data:"):
                body = json.loads(line[5:].strip())
        if body is None:
            raise RuntimeError("No data line in SSE response")
    else:
        body = json.loads(raw)
    if "error" in body:
        raise RuntimeError(body["error"])
    content = body.get("result", {}).get("content", [])
    if content and content[0].get("type") == "text":
        text = content[0]["text"]
        return json.loads(text) if text else {}
    return body.get("result", {})


def mcp_call(identity: str, tool: str, arguments: dict) -> dict:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": arguments},
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
    with urllib.request.urlopen(req, timeout=300) as resp:
        return parse_mcp_response(resp.read().decode())


def execute(identity: str, app_id: int, command: list[str], stdin: str = "") -> dict:
    return mcp_call(
        identity,
        "jrnm_execute_command_in_app",
        {"appId": app_id, "commandAndArguments": command, "stdin": stdin},
    )


def main() -> int:
    identity = load_identity()
    bundle = json.load(open(BUNDLE_PATH, encoding="utf-8"))
    app_id = bundle["appId"]
    results = {}

    results["upload"] = execute(
        identity, app_id, bundle["commandAndArguments"], bundle["stdin"]
    ).get("exitCode", -1)

    results["rm_pycache"] = execute(
        identity, app_id, ["sh", "-c", "rm -rf /app/app/**/__pycache__"], ""
    ).get("exitCode", -1)

    results["pkill"] = execute(
        identity, app_id, ["sh", "-c", 'pkill -f "python.*main.py" || true'], ""
    ).get("exitCode", -1)

    time.sleep(70)

    results["grep_verify"] = execute(
        identity,
        app_id,
        ["grep", "-q", "_coerce_tool_value", "/app/app/services/tool_executor.py"],
        "",
    ).get("exitCode", -1)

    print(json.dumps(results))
    return 0 if all(v == 0 for v in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
