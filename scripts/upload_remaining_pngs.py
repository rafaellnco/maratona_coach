"""Upload remaining 3 PNG files (hero-coach already done)."""
import sys

sys.path.insert(0, __file__.rsplit("\\", 1)[0] if "\\" in __file__ else __file__.rsplit("/", 1)[0])
from upload_pngs_jrnm import load_identity, upload_file

FILES = [
    ("docs/assets/architecture-flow.png", "/app/docs/assets/architecture-flow.png"),
    ("docs/assets/training-plan.png", "/app/docs/assets/training-plan.png"),
    ("docs/assets/telegram-chat.png", "/app/docs/assets/telegram-chat.png"),
]

if __name__ == "__main__":
    identity = load_identity()
    results = []
    for local, remote in FILES:
        print(f"Uploading {local} -> {remote}", flush=True)
        r = upload_file(identity, local, remote)
        results.append(r)
        status = "OK" if r["success"] else "FAIL"
        print(f"  => {status}: local={r['local_size']} remote={r.get('remote_size')} | {r.get('ls', '')}", flush=True)

    print("\n=== SUMMARY ===", flush=True)
    for r in results:
        status = "SUCCESS" if r["success"] else "FAILURE"
        print(f"{r['file']}: {status} | local={r['local_size']} remote={r.get('remote_size')} | {r.get('ls', '')}")

    if not all(r["success"] for r in results):
        sys.exit(1)
