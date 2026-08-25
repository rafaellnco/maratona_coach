"""Cria ZIP com paths POSIX (forward slashes) — Compress-Archive no Windows quebra no Linux."""
from __future__ import annotations

import argparse
import os
import sys
import zipfile


def create_posix_zip(source_dir: str, output_path: str) -> None:
    source_dir = os.path.abspath(source_dir)
    output_path = os.path.abspath(output_path)

    if os.path.exists(output_path):
        os.remove(output_path)

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(source_dir):
            for name in files:
                full_path = os.path.join(root, name)
                arcname = os.path.relpath(full_path, source_dir).replace("\\", "/")
                zf.write(full_path, arcname)

    # Verificar entradas criticas
    with zipfile.ZipFile(output_path, "r") as zf:
        names = zf.namelist()
        bad = [n for n in names if "\\" in n]
        if bad:
            print("ERRO: entradas com backslash:", bad[:5], file=sys.stderr)
            sys.exit(1)
        for required in ("app/__init__.py", "main.py", "start.sh", "requirements.txt"):
            if required not in names:
                print(f"ERRO: falta {required} no ZIP", file=sys.stderr)
                sys.exit(1)
        print(f"OK: {len(names)} ficheiros, paths POSIX (ex: app/__init__.py)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir")
    parser.add_argument("output_path")
    args = parser.parse_args()
    create_posix_zip(args.source_dir, args.output_path)
