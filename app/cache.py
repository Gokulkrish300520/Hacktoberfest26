"""Semantic cache: near-duplicate questions get the stored answer without a model call."""
import sqlite3
import time

import numpy as np


class SemanticCache:
    def __init__(self, path: str):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("""CREATE TABLE IF NOT EXISTS cache(
            ns TEXT, prompt TEXT, vec BLOB, answer TEXT, model TEXT, ts REAL)""")
        self.db.execute("CREATE INDEX IF NOT EXISTS cache_ns ON cache(ns)")
        self.db.commit()

    def lookup(self, ns: str, vec: np.ndarray, threshold: float):
        rows = self.db.execute("SELECT prompt, vec, answer, model FROM cache WHERE ns=?", (ns,)).fetchall()
        if not rows:
            return None
        m = np.vstack([np.frombuffer(r[1], dtype=np.float32) for r in rows])
        sims = m @ vec.astype(np.float32)
        i = int(np.argmax(sims))
        if sims[i] >= threshold:
            return {"answer": rows[i][2], "model": rows[i][3], "score": float(sims[i]), "matched": rows[i][0]}
        return None

    def store(self, ns: str, prompt: str, vec: np.ndarray, answer: str, model: str):
        self.db.execute("INSERT INTO cache VALUES (?,?,?,?,?,?)",
                        (ns, prompt, vec.astype(np.float32).tobytes(), answer, model, time.time()))
        self.db.commit()
