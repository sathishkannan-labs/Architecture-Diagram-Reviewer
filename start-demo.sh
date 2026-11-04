#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
if [[ "${1:-}" == "--python-only" ]]; then
  python3 -m venv .venv
  .venv/bin/python -m pip install -e '.[test]'
  echo 'Python-only demo: restricted validation requires Linux/non-root or Docker.'
  exec .venv/bin/python -m streamlit run streamlit_app.py --browser.gatherUsageStats=false
fi
if ! command -v docker >/dev/null 2>&1; then
  echo 'Docker is required for full validation. Use ./start-demo.sh --python-only for UI-only mode.' >&2
  exit 1
fi
if [[ ! -f .env ]]; then cp .env.example .env; fi
echo 'Set MODEL_API_KEY in .env for live extraction. Empty key supports fixtures.'
docker compose up --build -d
echo 'Open http://localhost:8501. Stop with: docker compose down'
