"""Multi-turn (crescendo) attack detection.

Attackers often probe slowly: harmless-looking messages that each score a bit risky,
building up to the real attack. A single-message filter misses this. We keep a short,
decaying risk history per conversation and block when the total crosses a threshold.
"""
import time
from collections import defaultdict, deque

WINDOW = 6            # messages remembered per conversation
HALF_LIFE = 300.0     # seconds: older risk counts less
THRESHOLD = 120.0     # summed (decayed) risk that triggers a block
SUSPECT_LIMIT = 2     # this many 'suspect' messages in a window also triggers a block
COUNTED_FROM = 25     # risk below this is normal chatter and is not counted

_history: dict[str, deque] = defaultdict(lambda: deque(maxlen=WINDOW))


def _decayed(now: float, items) -> tuple[float, int]:
    total, suspects = 0.0, 0
    for ts, risk, suspect in items:
        w = 0.5 ** ((now - ts) / HALF_LIFE)
        total += risk * w
        suspects += suspect
    return total, suspects


def record(session: str, risk: int, suspect: bool) -> None:
    if risk >= COUNTED_FROM or suspect:
        _history[session].append((time.time(), risk, int(suspect)))


def check(session: str, risk: int, suspect: bool) -> str | None:
    """Return a reason if this message pushes the conversation over the line."""
    if not suspect and risk < COUNTED_FROM:
        return None  # an innocent follow-up is never blocked by history alone
    now = time.time()
    total, suspects = _decayed(now, _history[session])
    total += risk if risk >= COUNTED_FROM else 0
    suspects += int(suspect)
    if suspects >= SUSPECT_LIMIT:
        return f"multi-turn probing: {suspects} suspicious messages in this conversation"
    if total >= THRESHOLD:
        return f"multi-turn escalation: conversation risk {total:.0f} ≥ {THRESHOLD:.0f}"
    return None


def reset(session: str | None = None) -> None:
    if session is None:
        _history.clear()
    else:
        _history.pop(session, None)
