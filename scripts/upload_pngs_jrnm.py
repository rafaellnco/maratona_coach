"""Upload PNG files to JustRunMy app via MCP execute_command API."""
import base64
import json
import os
import sys
import urllib.request

import time

APP_ID = 34679
CHUNK_SIZE = 4000
MCP_URL = "https://justrunmy.app/api/mcp"

FILES = [
    ("docs/assets/hero-coach.png", "/app/docs/assets/hero-coach.png"),
    ("docs/assets/architecture-flow.png", "/app/docs/assets/architecture-flow.png"),
    ("docs/assets/training-plan.png", "/app/docs/assets/training-plan.png"),
    ("docs/assets/telegram-chat.png", "/app/docs/assets/telegram-chat.png"),
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_identity():
    mcp_path = os.path.expanduser("~/.cursor/mcp.json")
    with open(mcp_path, encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg["mcpServers"]["justrunmy.app"]["headers"]["X-User-Identity"]


def parse_mcp_response(raw: str) -> dict:
    """Parse JSON or SSE (event: message / data: {...}) MCP response."""
    raw = raw.strip()
    if not raw:
        raise RuntimeError("Empty MCP response")
    if raw.startswith("event:") or raw.startswith("data:"):
        body = None
        for line in raw.splitlines():
            if line.startswith("data:"):
                body = json.loads(line[5:].strip())
        if body is None:
            raise RuntimeError(f"No data line in SSE response: {raw[:200]}")
    else:
        body = json.loads(raw)
    if "error" in body:
        raise RuntimeError(body["error"])
    content = body.get("result", {}).get("content", [])
    if content and content[0].get("type") == "text":
        text = content[0]["text"]
        if not text:
            raise RuntimeError("Empty text in MCP content")
        return json.loads(text)
    return body.get("result", {})


def mcp_call(identity: str, tool: str, arguments: dict, retries: int = 5) -> dict:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": arguments},
    }
    last_err = None
    for attempt in range(retries):
        try:
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
            with urllib.request.urlopen(req, timeout=120) as resp:
                return parse_mcp_response(resp.read().decode())
        except Exception as exc:
            last_err = exc
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"MCP call failed after {retries} attempts: {last_err}")


def execute(identity: str, command: list[str], stdin: str = "") -> dict:
    return mcp_call(
        identity,
        "jrnm_execute_command_in_app",
        {"appId": APP_ID, "commandAndArguments": command, "stdin": stdin},
    )


def upload_file(identity: str, local_rel: str, remote_path: str) -> dict:
    local_path = os.path.join(BASE_DIR, local_rel.replace("/", os.sep))
    filename = os.path.basename(remote_path)
    local_size = os.path.getsize(local_path)

    with open(local_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    chunks = [b64[i : i + CHUNK_SIZE] for i in range(0, len(b64), CHUNK_SIZE)]
    print(f"  {filename}: {local_size} bytes, {len(chunks)} chunks", flush=True)

    # Reset temp file
    r = execute(identity, ["sh", "-c", "cat > /tmp/up.b64"], chunks[0])
    if r.get("exitCode", -1) != 0:
        return {"file": filename, "success": False, "error": f"first chunk: {r}", "local_size": local_size}

    for i, chunk in enumerate(chunks[1:], 2):
        r = execute(identity, ["sh", "-c", "cat >> /tmp/up.b64"], chunk)
        if r.get("exitCode", -1) != 0:
            return {"file": filename, "success": False, "error": f"chunk {i}: {r}", "local_size": local_size}
        if i % 100 == 0:
            print(f"    chunk {i}/{len(chunks)}", flush=True)

    decode_cmd = (
        f"import base64; open('{remote_path}','wb').write("
        f"base64.b64decode(open('/tmp/up.b64').read()))"
    )
    r = execute(identity, ["python3", "-c", decode_cmd], "")
    if r.get("exitCode", -1) != 0:
        return {"file": filename, "success": False, "error": f"decode: {r}", "local_size": local_size}

    r = execute(identity, ["ls", "-la", remote_path], "")
    ls_out = r.get("stdOut", "").strip()
    remote_size = None
    if ls_out:
        parts = ls_out.split()
        if len(parts) >= 5:
            remote_size = int(parts[4])

    success = remote_size == local_size
    return {
        "file": filename,
        "success": success,
        "local_size": local_size,
        "remote_size": remote_size,
        "ls": ls_out,
        "error": None if success else f"size mismatch local={local_size} remote={remote_size}",
    }


def main():
    identity = load_identity()

    print("Creating remote directory...", flush=True)
    r = execute(identity, ["sh", "-c", "mkdir -p /app/docs/assets"], "")
    if r.get("exitCode", -1) != 0:
        print(f"mkdir failed: {r}", file=sys.stderr)
        sys.exit(1)

    results = []
    for local_rel, remote_path in FILES:
        print(f"Uploading {local_rel} -> {remote_path}", flush=True)
        result = upload_file(identity, local_rel, remote_path)
        results.append(result)
        status = "OK" if result["success"] else "FAIL"
        print(f"  => {status}: local={result['local_size']} remote={result.get('remote_size')} | {result.get('ls', '')}", flush=True)
        if result.get("error"):
            print(f"     error: {result['error']}", flush=True)

    print("\n=== SUMMARY ===", flush=True)
    for r in results:
        status = "SUCCESS" if r["success"] else "FAILURE"
        print(f"{r['file']}: {status} | local={r['local_size']} remote={r.get('remote_size')} | {r.get('ls', '')}")

    if not all(r["success"] for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
