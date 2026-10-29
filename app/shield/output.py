"""Output check: never let secrets, canaries or the system prompt out, even if a model was tricked."""
import re

from .. import config

CANARY_RX = re.compile(r"CANARY-[A-Za-z0-9]+")


def normalise(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def check(answer: str, system_text: str) -> str | None:
    """Return a reason string if the answer leaks something, else None."""
    flat = normalise(answer)

    for canary in CANARY_RX.findall(system_text):
        if normalise(canary) in flat:
            return "canary token leaked (system prompt leak)"

    secrets = [normalise(s) for s in config.SECRETS if normalise(s)]
    for s in secrets:
        if s in flat:
            return "secret leaked"

    # Acrostic / hidden-in-first-letters trick
    lines = [l.strip().lstrip("-*•>#\"'`_ ") for l in answer.splitlines()]
    firsts = normalise("".join(l[:1] for l in lines if l))
    for s in secrets:
        if s in firsts:
            return "secret hidden in first letters of lines"

    # Long verbatim chunk of the system prompt
    sys_flat = normalise(system_text)
    win = 40
    for i in range(0, max(len(sys_flat) - win + 1, 0), 10):
        if sys_flat[i:i + win] in flat:
            return "system prompt leaked verbatim"
    return None
