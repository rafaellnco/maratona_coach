import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
b64 = base64.b64encode((ROOT / "app/config.py").read_bytes()).decode()
payload = {
    "appId": 34679,
    "commandAndArguments": [
        "python3",
        "-c",
        'import sys,base64; open("/app/app/config.py","wb").write(base64.b64decode(sys.stdin.read()))',
    ],
    "stdin": b64,
}
(ROOT / "_upload_config.json").write_text(json.dumps(payload), encoding="utf-8")
print(len(json.dumps(payload)))
