#!/usr/bin/env bash
set -euo pipefail
cd /workspace/vptauto
export PIP_CACHE_DIR=/workspace/.cache/vptauto/pip
export XDG_CACHE_HOME=/workspace/.cache/vptauto
mkdir -p "$PIP_CACHE_DIR" "$XDG_CACHE_HOME"
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
fi
.venv/bin/python -m pip install --disable-pip-version-check -r requirements-dev.txt
if ! command -v makensis >/dev/null 2>&1; then
  .venv/bin/python scripts/prepare_nsis.py
fi
