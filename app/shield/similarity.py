"""Layer 2: embedding similarity against a list of known attacks."""
import numpy as np

from .. import config, ollama_client

PREFIX = "clustering: "  # nomic-embed-text task prefix
_matrix: np.ndarray | None = None
_texts: list[str] = []


def unit(v) -> np.ndarray:
    v = np.asarray(v, dtype=np.float32)
    n = np.linalg.norm(v)
    return v / n if n else v


async def embed_one(text: str) -> np.ndarray:
    return unit((await ollama_client.embed([PREFIX + text]))[0])


async def load() -> int:
    global _matrix, _texts
    with open(config.ATTACKS_FILE, encoding="utf-8") as f:
        _texts = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    vecs = await ollama_client.embed([PREFIX + t for t in _texts])
    _matrix = np.vstack([unit(v) for v in vecs])
    return len(_texts)


async def learn(texts: list[str]) -> int:
    """Add new attacks at runtime (used by the red-team --learn mode). Returns how many were new."""
    global _matrix, _texts
    if _matrix is None:
        await load()
    new = []
    for t in texts:
        t = " ".join(t.split())
        if t and t not in _texts and t not in new:
            new.append(t)
    if not new:
        return 0
    vecs = await ollama_client.embed([PREFIX + t for t in new])
    _matrix = np.vstack([_matrix] + [unit(v) for v in vecs])
    _texts.extend(new)
    with open(config.ATTACKS_FILE, "a", encoding="utf-8") as f:
        for t in new:
            f.write(t + "\n")
    return len(new)


def count() -> int:
    return len(_texts)


async def max_similarity(vec: np.ndarray) -> tuple[float, str]:
    if _matrix is None:
        await load()
    sims = _matrix @ vec
    i = int(np.argmax(sims))
    return float(sims[i]), _texts[i]
