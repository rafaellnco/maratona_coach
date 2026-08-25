import base64
import io
import json
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w") as tar:
    tar.add(ROOT / "docs/index.html", arcname="docs/index.html")
    tar.add(ROOT / "docs/showcase.html", arcname="docs/showcase.html")
    for jpg in (ROOT / "docs/assets-web").glob("*.jpg"):
        tar.add(jpg, arcname=f"docs/assets/{jpg.name}")

raw = buf.getvalue()
b64 = base64.b64encode(raw).decode()
payload = {
    "appId": 34679,
    "commandAndArguments": [
        "python3",
        "-c",
        "import sys,base64,tarfile,io; buf=io.BytesIO(base64.b64decode(sys.stdin.read())); tarfile.open(fileobj=buf).extractall('/app')",
    ],
    "stdin": b64,
}
out = ROOT / "_upload_showcase_bundle.json"
out.write_text(json.dumps(payload), encoding="utf-8")
print("tar bytes", len(raw), "b64", len(b64), "json", out.stat().st_size)
