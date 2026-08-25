"""Launcher FPS.ms — PY_FILE=app.py (default) executa bot.py num processo limpo."""
import os
import sys

_root = os.path.dirname(os.path.abspath(__file__))
os.execv(sys.executable, [sys.executable, os.path.join(_root, "bot.py")])
