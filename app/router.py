"""Pick the smallest Gemma that can handle the prompt, plus a fallback chain."""
import re

from . import config

HARD = re.compile(
    r"\b(explain|why|compare|analy[sz]e|reason|step[- ]by[- ]step|debug|code|function|script|"
    r"algorithm|prove|calculate|summari[sz]e|translate|plan|essay|pros and cons)\b", re.I)


def choose(text: str, *, has_images: bool = False, json_mode: bool = False,
           requested: str | None = None) -> tuple[list[str], str]:
    """Return (model chain, reason). The first model is tried first, the rest are fallbacks."""
    if requested and requested not in ("auto", "localroute", ""):
        return [requested], "model requested by app"
    words = len(text.split())
    if has_images:
        return [config.BIG_MODEL, config.SMALL_MODEL], "image input"
    if json_mode:
        return [config.BIG_MODEL, config.SMALL_MODEL], "structured JSON output"
    if "```" in text or words > 60:
        return [config.BIG_MODEL, config.SMALL_MODEL], f"long or code prompt ({words} words)"
    if HARD.search(text):
        return [config.BIG_MODEL, config.SMALL_MODEL], "reasoning keywords"
    return [config.SMALL_MODEL, config.BIG_MODEL], f"simple prompt ({words} words)"
