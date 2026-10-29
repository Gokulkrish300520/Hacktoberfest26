"""Map every PromptShield finding to the OWASP Top 10 for LLM Applications (2025)."""

LLM01 = "LLM01 Prompt Injection"
LLM02 = "LLM02 Sensitive Information Disclosure"
LLM07 = "LLM07 System Prompt Leakage"


def classify(layer: str | None, reason: str | None, pii: list[str] | None = None) -> str | None:
    r = (reason or "").lower()
    if layer == "output":
        if "canary" in r or "system prompt" in r:
            return LLM07
        return LLM02
    if layer:  # any input-side block
        if "system prompt" in r:
            return LLM07
        return LLM01
    if pii:
        return LLM02  # allowed, but personal data was masked
    return None
