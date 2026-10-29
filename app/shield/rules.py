"""Layer 1: fast regex rules. 'block' = known attack, 'suspect' = send to the Gemma judge."""
import re

_F = re.IGNORECASE | re.MULTILINE

RULES = [
    # (severity, label, pattern)
    ("block", "instruction override",
     r"\b(ignore|disregard|forget|override)\s+(all\s+|any\s+|the\s+|your\s+|my\s+)?(previous|prior|above|earlier|preceding|original)\s+(instructions?|rules|prompts?|messages|guidelines|directions)"),
    ("block", "instruction override",
     r"\bforget\s+(everything|all)\s+(you\s+(were|have\s+been)\s+told|above)"),
    ("block", "system prompt extraction",
     r"\b(reveal|print|show|repeat|output|display|dump|leak|tell\s+me|give\s+me|what\s+(is|are|was))\s+(me\s+)?(your|the)\s+(full\s+|entire\s+|exact\s+)?(system|hidden|initial|original|internal)\s+(prompt|instructions?|message|rules)"),
    ("block", "jailbreak / role override",
     r"\b(you\s+are\s+now\s+(an?\s+)?(unrestricted|unfiltered|jailbroken|evil|dan)|developer\s+mode|do\s+anything\s+now|no\s+longer\s+bound\s+by)"),
    ("block", "jailbreak / role override",
     r"\b(pretend|imagine|act\s+as\s+if)\s+(you\s+have|there\s+are|you\s+had)\s+no\s+(rules|restrictions|guidelines|filters)"),
    ("block", "fake role tag",
     r"(<\s*/?\s*(system|assistant)\s*>|\[\s*(system|INST)\s*\]|^\s*(system|assistant)\s*:)"),
    ("suspect", "asks for a secret",
     r"\b(staff|discount|secret|admin|internal|employee|api)\s+(code|key|password|token|pin)"),
    ("suspect", "obfuscation trick",
     r"\b(spell|encode|base64|reverse|backwards|first\s+letters?|acrostic|letter\s+by\s+letter|rot13|hex)\b"),
]

_COMPILED = [(sev, label, re.compile(p, _F)) for sev, label, p in RULES]


def check(text: str) -> tuple[str | None, str | None]:
    """Return (severity, label) of the worst match, or (None, None)."""
    suspect = None
    for sev, label, rx in _COMPILED:
        if rx.search(text):
            if sev == "block":
                return "block", label
            suspect = suspect or label
    return ("suspect", suspect) if suspect else (None, None)
