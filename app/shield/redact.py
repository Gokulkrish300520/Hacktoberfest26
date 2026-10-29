"""Mask personal data and secrets before anything reaches a model or a log."""
import re

KEYS = re.compile(r"\b(sk-[A-Za-z0-9_-]{16,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|AIza[0-9A-Za-z_-]{30,})\b")
IBAN = re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}(?:\s?[A-Z0-9]{1,3})?\b")
CARD = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"(?<![\w+])\+?\d[\d ()-]{7,}\d(?!\w)")


def _luhn(digits: str) -> bool:
    total, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d = d * 2 - 9 if d > 4 else d * 2
        total += d
        alt = not alt
    return total % 10 == 0


def redact(text: str) -> tuple[str, list[str]]:
    """Return (masked_text, [kinds found])."""
    found: list[str] = []

    def sub(rx, label, repl):
        nonlocal text
        def _r(m):
            out = repl(m)
            if out != m.group(0):
                found.append(label)
            return out
        text = rx.sub(_r, text)

    sub(KEYS, "api_key", lambda m: "[API_KEY]")
    sub(IBAN, "iban", lambda m: "[IBAN]")

    def card(m):
        digits = re.sub(r"\D", "", m.group(0))
        return f"[CARD ending {digits[-4:]}]" if 13 <= len(digits) <= 19 and _luhn(digits) else m.group(0)
    sub(CARD, "card", card)
    sub(EMAIL, "email", lambda m: "[EMAIL]")

    def phone(m):
        digits = re.sub(r"\D", "", m.group(0))
        return "[PHONE]" if 9 <= len(digits) <= 15 else m.group(0)
    sub(PHONE, "phone", phone)
    return text, found
