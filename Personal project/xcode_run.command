#!/bin/zsh
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
PY="/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12"


cd "$ROOT"
exec "$PY" "$ROOT/run.py"

