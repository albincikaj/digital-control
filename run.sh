#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
if [ ! -x .venv/bin/streamlit ]; then
  if command -v uv >/dev/null; then
    uv venv --python /usr/bin/python3.12 .venv && uv pip install --python .venv/bin/python -r requirements.txt
  else
    python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
  fi
fi
exec .venv/bin/streamlit run app.py "$@"
