# Contributing

Thanks for helping make local LLM apps safer.

1. Fork the repo and create a branch.
2. Run `pytest` before and after your change.
3. Open a pull request with a short description.

**Easiest first contribution:** add a new prompt-injection example to `app/shield/known_attacks.txt` (one per line), plus a test in `tests/test_shield.py` if it needs a new regex rule.

Please never commit real secrets, API keys or personal data in examples.
