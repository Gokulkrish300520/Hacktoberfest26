#!/usr/bin/env bash
# Start Ollama (unless an external OLLAMA_URL is used), pull models in the background, start the gateway.
# The website comes up immediately; chat answers start working once the models have downloaded.
set -uo pipefail

SMALL_MODEL="${SMALL_MODEL:-gemma4:e2b-it-qat}"
BIG_MODEL="${BIG_MODEL:-$SMALL_MODEL}"
EMBED_MODEL="${EMBED_MODEL:-nomic-embed-text}"
mkdir -p "$(dirname "${DB_PATH:-/data/localroute.db}")"

prepare_models() {
  for i in $(seq 1 60); do curl -sf http://127.0.0.1:11434/api/tags >/dev/null && break; sleep 1; done
  for m in "$EMBED_MODEL" "$SMALL_MODEL" "$BIG_MODEL"; do
    if ! ollama list | awk 'NR>1{print $1}' | grep -qx "$m"; then
      echo "[start] pulling $m (first boot only, can take several minutes)"
      ollama pull "$m" || echo "[start] ERROR: could not pull $m"
    fi
  done
  echo "[start] warming up $SMALL_MODEL"
  curl -s http://127.0.0.1:11434/api/generate \
    -d "{\"model\":\"$SMALL_MODEL\",\"prompt\":\"hi\",\"stream\":false}" >/dev/null || true
  curl -s -X POST "http://127.0.0.1:${PORT:-8000}/admin/reload" -H "X-Admin-Token: ${ADMIN_TOKEN:-}" >/dev/null || true
  echo "[start] models ready"
}

if [[ "${OLLAMA_URL}" == "http://127.0.0.1:11434" ]]; then
  echo "[start] starting bundled Ollama"
  ollama serve &
  prepare_models &
else
  echo "[start] using external Ollama at $OLLAMA_URL"
fi

if [[ -z "${ADMIN_TOKEN:-}" ]]; then
  echo "[start] WARNING: ADMIN_TOKEN is not set, so the dashboard and admin routes are open to anyone"
fi

echo "[start] starting gateway on port ${PORT:-8000}"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers --forwarded-allow-ips="*"
