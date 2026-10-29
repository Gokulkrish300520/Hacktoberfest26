# LocalRoute + PromptShield

**An open-source, fully local gateway that makes Gemma 4 apps faster, cheaper and safe from prompt injection. One line of code to adopt.**

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8000/v1", api_key="my-app")  # ← the only change
```

Every request then goes through:

1. **PromptShield (input)** – regex rules → PII/secret redaction → embedding similarity to known attacks → **Gemma 4 as a security judge** for borderline cases.
2. **Visual injection defence** – Gemma 4 reads *all* text in uploaded images (including faint, hidden text) and runs it through the same checks.
3. **Semantic cache** – near-duplicate questions are answered instantly, with no model call.
4. **Router + fallback** – simple prompts go to the small model, hard ones to the big one (configurable); failures, timeouts and invalid JSON retry on the next model.
5. **PromptShield (output)** – blocks answers that leak secrets, canary tokens, the system prompt, or a secret hidden in the first letters of lines (acrostic attack).
6. **Multi-turn (crescendo) detection** – keeps a decaying risk history per conversation (`X-Session-Id`), so an attacker who probes slowly across several harmless-looking messages is still caught.
7. **Automatic canary tokens** – the gateway hides a unique marker in every system prompt; if it ever appears in an answer, the leak is blocked. Apps don't change anything.
8. **OWASP LLM Top 10 mapping** – every finding is tagged LLM01 (Prompt Injection), LLM02 (Sensitive Information Disclosure) or LLM07 (System Prompt Leakage).
9. **Auto red-team + self-learning shield** – Gemma 4 mutates seed attacks into new variants, fires them at a test bot, reports the attack success rate, and (`--learn`) teaches the shield every variant that got past it.
10. **Dashboard** – live view of requests, cache hits, model split, latency, OWASP findings, which layer stopped each attack, and the latest red-team report.

Everything runs offline on [Ollama](https://ollama.com). Data never leaves the machine.

**Live demo:** the gateway also serves the **Hacktoberfest Café** website at `/` (chat bubble bottom-left, protected by PromptShield) and a **live attack monitor** at `/dashboard`. See [DEPLOY.md](DEPLOY.md) to put it on Railway or Render.

## Quick start (macOS / Linux)

```bash
ollama pull gemma4:e2b-it-qat && ollama pull nomic-embed-text
pip install -r requirements.txt

# terminal 1: gateway + café website (http://localhost:8000) + attack monitor (/dashboard)
uvicorn app.main:app --port 8000
# terminal 2: dashboard
streamlit run dashboard/app.py --server.port 8502
# terminal 3: demo café chatbot (toggle the shield on/off)
streamlit run demo/victim_bot.py --server.port 8501
```

Make the hidden-text attack image: `python demo/make_attack_image.py` → `demo/receipt_attack.png`.

Auto red-team (run twice: the second run shows the shield has learned):

```bash
python redteam/run.py --variants 3 --learn   # attack, measure, teach the shield
python redteam/run.py --variants 3           # attack again: block rate goes up
```

Benchmark against always using the big model: `python benchmark/run.py` → `benchmark/results.md`.

## Response headers

| Header | Meaning |
|---|---|
| `X-PromptShield-Verdict` | `allow` or `block` |
| `X-PromptShield-Risk` | 0–100 |
| `X-PromptShield-Reason` | why it was blocked, and which layer |
| `X-PromptShield-OWASP` | OWASP LLM Top 10 category of the finding |
| `X-PromptShield-PII` | kinds of data masked (card, email, phone, api_key, iban) |
| `X-LocalRoute-Model` | which Gemma model answered (`cache` / `none` if no model call) |
| `X-LocalRoute-Cache` | `hit <score>`, `miss` or `skip` |

## Configuration

Environment variables (see `app/config.py`): `SMALL_MODEL`, `BIG_MODEL`, `JUDGE_MODEL`, `VISION_MODEL`, `CACHE_THRESHOLD` (0.92), `ATTACK_BLOCK` (0.85), `ATTACK_BORDER` (0.70), `SHIELD_SECRETS` (comma separated), `OLLAMA_URL`.

**Defaults** use `gemma4:e2b-it-qat` (4-bit) for everything so it runs on an 8–16 GB laptop. With more RAM, set `BIG_MODEL=gemma4:e4b` to get real small/big routing.

## Tests

```bash
pytest                                   # shield, redaction, output check, router
uvicorn tests.fake_ollama:app --port 11999 &
OLLAMA_URL=http://localhost:11999 uvicorn app.main:app --port 8000   # full pipeline without real models
```

## Limitations

- The router uses heuristics, not a trained classifier.
- Attack detection is tuned on English.
- Answers are fully checked before streaming, so streaming starts after the answer is ready.
- No filter is perfect: that's why it is layered and logs every attempt.

## Roadmap / good first issues

- Add new attacks to `app/shield/known_attacks.txt`
- Multilingual attack detection
- Per-app rate limits and API keys
- Prometheus metrics
- Red-team test suite in CI

## License

MIT. Gemma 4 models are released by Google under Apache 2.0.
# Hacktoberfest26
