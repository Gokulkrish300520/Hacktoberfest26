# All-in-one image: Ollama + Gemma 4 + LocalRoute/PromptShield + café website + dashboard.
# Works on Railway, Render, Fly.io or any Docker host with ~8 GB RAM.
FROM ollama/ollama:latest

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    OLLAMA_HOST=127.0.0.1:11434 \
    OLLAMA_URL=http://127.0.0.1:11434 \
    OLLAMA_MODELS=/data/ollama \
    OLLAMA_MAX_LOADED_MODELS=2 \
    OLLAMA_KEEP_ALIVE=24h \
    DB_PATH=/data/localroute.db \
    PORT=8000

RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip python3-venv curl \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /srv
COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

COPY app ./app
COPY start.sh .
RUN chmod +x start.sh && mkdir -p /data

EXPOSE 8000
ENTRYPOINT []
CMD ["./start.sh"]
