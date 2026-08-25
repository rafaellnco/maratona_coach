import base64
import io
import json
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = [
    "app/services/tool_executor.py",
    "app/services/telegram_handler.py",
]

buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w") as tar:
    for rel in FILES:
        tar.add(ROOT / rel, arcname=rel)

payload = {
    "appId": 34679,
    "commandAndArguments": [
        "python3",
        "-c",
        "import sys,base64,tarfile,io; buf=io.BytesIO(base64.b64decode(sys.stdin.read())); tarfile.open(fileobj=buf).extractall('/app')",
    ],
    "stdin": base64.b64encode(buf.getvalue()).decode(),
}
out = ROOT / "_upload_hotfix_bundle.json"
out.write_text(json.dumps(payload), encoding="utf-8")
print("json", out.stat().st_size)
