"""Thin async client for the Ollama REST API + OpenAI <-> Ollama message conversion."""
import httpx

from . import config

_client = httpx.AsyncClient(base_url=config.OLLAMA_URL, timeout=config.MODEL_TIMEOUT)


async def embed(texts: list[str]) -> list[list[float]]:
    r = await _client.post("/api/embed", json={"model": config.EMBED_MODEL, "input": texts})
    r.raise_for_status()
    return r.json()["embeddings"]


async def chat(model: str, messages: list[dict], *, json_mode: bool = False,
               temperature: float | None = None) -> dict:
    payload = {"model": model, "messages": messages, "stream": False}
    if temperature is not None:
        payload["options"] = {"temperature": temperature}
    if json_mode:
        payload["format"] = "json"
    r = await _client.post("/api/chat", json=payload)
    r.raise_for_status()
    return r.json()


def split_content(content) -> tuple[str, list[str]]:
    """OpenAI content (str or list of parts) -> (text, [base64 images])."""
    if content is None:
        return "", []
    if isinstance(content, str):
        return content, []
    texts, images = [], []
    for part in content:
        if part.get("type") == "text":
            texts.append(part.get("text", ""))
        elif part.get("type") == "image_url":
            url = (part.get("image_url") or {}).get("url", "")
            if url.startswith("data:") and "," in url:
                images.append(url.split(",", 1)[1])  # strip "data:image/png;base64,"
    return "\n".join(texts), images


def to_ollama_messages(messages: list[dict]) -> list[dict]:
    out = []
    for m in messages:
        text, images = split_content(m.get("content"))
        msg = {"role": m.get("role", "user"), "content": text}
        if images:
            msg["images"] = images
        out.append(msg)
    return out
