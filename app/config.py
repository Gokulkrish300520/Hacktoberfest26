"""All settings in one place. Override any of them with environment variables."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# Models (Gemma 4 via Ollama)
SMALL_MODEL = os.getenv("SMALL_MODEL", "gemma4:e2b-it-qat")
BIG_MODEL = os.getenv("BIG_MODEL", "gemma4:e2b-it-qat")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", BIG_MODEL)    # security judge
VISION_MODEL = os.getenv("VISION_MODEL", BIG_MODEL)  # reads text inside images
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")

# Thresholds (cosine similarity, tune after watching the dashboard)
CACHE_THRESHOLD = float(os.getenv("CACHE_THRESHOLD", "0.92"))
ATTACK_BLOCK = float(os.getenv("ATTACK_BLOCK", "0.85"))    # >= this: block without judge
ATTACK_BORDER = float(os.getenv("ATTACK_BORDER", "0.70"))  # >= this: ask the Gemma judge

MODEL_TIMEOUT = float(os.getenv("MODEL_TIMEOUT", "120"))

# Secrets that must never appear in a response (comma separated)
SECRETS = [s.strip() for s in os.getenv("SHIELD_SECRETS", "STAFF20").split(",") if s.strip()]

DB_PATH = os.getenv("DB_PATH", "localroute.db")
ATTACKS_FILE = os.getenv("ATTACKS_FILE", os.path.join(HERE, "shield", "known_attacks.txt"))

REFUSAL = "Sorry, I can't help with that request."

# Production security (leave empty for local development)
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")  # protects /dashboard data and /admin/*
API_KEYS = {k.strip() for k in os.getenv("API_KEYS", "").split(",") if k.strip()}  # allowed /v1 keys
RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "20"))  # café chat, per visitor IP
