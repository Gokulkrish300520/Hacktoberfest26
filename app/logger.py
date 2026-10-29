"""Request log in SQLite. The dashboard reads this table."""
import json
import sqlite3
import time

from .shield import owasp

COLUMNS = ["id", "ts", "app", "session", "prompt", "verdict", "layer", "reason", "owasp", "risk",
           "cache", "model", "route_reason", "fallback", "latency_ms", "tokens_out", "pii", "image_text"]


class RequestLog:
    def __init__(self, path: str):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute(f"CREATE TABLE IF NOT EXISTS requests({', '.join(COLUMNS)})")
        have = {r[1] for r in self.db.execute("PRAGMA table_info(requests)")}
        for c in COLUMNS:  # upgrade a database made by an older version
            if c not in have:
                self.db.execute(f"ALTER TABLE requests ADD COLUMN {c}")
        self.db.commit()

    def write(self, **row):
        row.setdefault("ts", time.time())
        row.setdefault("owasp", owasp.classify(row.get("layer") if row.get("verdict") == "block" else None,
                                               row.get("reason"), row.get("pii")))
        row["pii"] = json.dumps(row.get("pii") or [])
        cols = ", ".join(COLUMNS)
        self.db.execute(f"INSERT INTO requests ({cols}) VALUES ({', '.join('?' * len(COLUMNS))})",
                        [row.get(c) for c in COLUMNS])
        self.db.commit()
