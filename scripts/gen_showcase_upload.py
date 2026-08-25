import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
files = [
    ("docs/index.html", "/app/docs/index.html", "text"),
    ("docs/showcase.html", "/app/docs/showcase.html", "text"),
    ("docs/assets-web/hero-coach.jpg", "/app/docs/assets/hero-coach.jpg", "b64"),
    ("docs/assets-web/architecture-flow.jpg", "/app/docs/assets/architecture-flow.jpg", "b64"),
    ("docs/assets-web/training-plan.jpg", "/app/docs/assets/training-plan.jpg", "b64"),
    ("docs/assets-web/telegram-chat.jpg", "/app/docs/assets/telegram-chat.jpg", "b64"),
]

for i, (local, remote, kind) in enumerate(files):
    path = ROOT / local
    if kind == "text":
        payload = {
            "appId": 34679,
            "commandAndArguments": ["/bin/sh", "-c", f"cat > {remote}"],
            "stdin": path.read_text(encoding="utf-8"),
        }
    else:
        b64 = base64.b64encode(path.read_bytes()).decode()
        payload = {
            "appId": 34679,
            "commandAndArguments": [
                "python3",
                "-c",
                f"import sys,base64; open('{remote}','wb').write(base64.b64decode(sys.stdin.read()))",
            ],
            "stdin": b64,
        }
    out = ROOT / f"_upload_{i}.json"
    out.write_text(json.dumps(payload), encoding="utf-8")
    print(i, local, len(json.dumps(payload)))
