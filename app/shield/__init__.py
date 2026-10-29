"""PromptShield: layered input inspection.

regex (fast) -> PII redaction -> embedding similarity -> Gemma judge (borderline only)
-> image text extraction + the same checks.
"""
from dataclasses import dataclass, field

import numpy as np

from .. import config
from . import image, judge, redact, rules, similarity


@dataclass
class Verdict:
    allow: bool
    risk: int
    layer: str | None = None
    reason: str | None = None
    redacted: str = ""
    pii: list[str] = field(default_factory=list)
    similarity: float = 0.0
    image_text: str = ""
    vec: np.ndarray | None = None
    suspect: bool = False  # borderline but allowed: counts towards multi-turn detection


async def _check_text(text: str, vec: np.ndarray, source: str) -> tuple[Verdict | None, bool]:
    """Run regex -> similarity -> judge on one piece of text.

    Returns (blocking Verdict or None, suspect flag)."""
    sev, label = rules.check(text)
    if sev == "block":
        return Verdict(False, 95, "regex", f"{label} ({source})"), True

    sim, _nearest = await similarity.max_similarity(vec)
    if sim >= config.ATTACK_BLOCK:
        return Verdict(False, 85, "similarity", f"matches known attack ({sim:.2f}) ({source})", similarity=sim), True

    suspect = sev == "suspect" or sim >= config.ATTACK_BORDER
    if suspect or source != "user message":
        attack, why = await judge.judge(text, source)
        if attack:
            return Verdict(False, 80, "judge", f"{why} ({source})", similarity=sim), True
    return None, suspect


async def inspect(text: str, images: list[str] | None = None) -> Verdict:
    images = images or []
    masked, pii = redact.redact(text)
    sev, label = rules.check(masked)  # regex first: known attacks cost no model time at all
    if sev == "block":
        return Verdict(False, 95, "regex", f"{label} (user message)", masked, pii, suspect=True)
    vec = await similarity.embed_one(masked)

    suspect = False
    if masked.strip():
        blocked, suspect = await _check_text(masked, vec, "user message")
        if blocked:
            blocked.redacted, blocked.pii, blocked.vec = masked, pii, vec
            return blocked

    img_text = ""
    if images:
        img_text = await image.extract_text(images)
        if img_text:
            img_vec = await similarity.embed_one(img_text)
            blocked, img_suspect = await _check_text(img_text, img_vec, "text hidden in image")
            suspect = suspect or img_suspect
            if blocked:
                blocked.redacted, blocked.pii, blocked.vec, blocked.image_text = masked, pii, vec, img_text
                blocked.risk = max(blocked.risk, 90)
                return blocked

    sim, _ = await similarity.max_similarity(vec)
    risk = max(5, min(60, round(sim * 50)))
    if suspect:
        risk = max(risk, 45)
    return Verdict(True, risk, None, None, masked, pii, sim, img_text, vec, suspect)
