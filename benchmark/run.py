"""Benchmark: LocalRoute (routing + cache) vs always calling the big model directly.

Run (gateway must be running):  python benchmark/run.py
Writes benchmark/results.md with the numbers to show judges.
"""
import os
import statistics
import time
import uuid

from openai import OpenAI

SYSTEM = "You are the assistant for Hacktoberfest Café. Opening hours 8am-10pm, Sunday 10am-6pm. Answer briefly."

PROMPTS = [
    "What time do you close?", "When do you shut tonight?", "Are you open on Sunday?",
    "What are your Sunday opening hours?", "Do you have vegan food?", "Any vegan options?",
    "Do you do gluten-free cakes?", "Is there anything gluten free?", "Where are you located?",
    "What's your address?", "What time do you close?", "Do you have vegan food?",
    "Can I book a table for 4?", "Can I reserve a table for four people?",
    "Explain step by step how to plan a birthday party for 10 people at your café.",
    "Compare your breakfast and lunch menus and explain which suits a student budget.",
    "What time do you open?", "When do you open in the morning?", "Are you open on Sunday?",
    "Where are you located?",
]


def run(base_url, api_key, model):
    client = OpenAI(base_url=base_url, api_key=api_key)
    times, routes = [], []
    for p in PROMPTS:
        t = time.perf_counter()
        raw = client.chat.completions.with_raw_response.create(
            model=model, messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": p}])
        raw.parse()
        times.append((time.perf_counter() - t) * 1000)
        routes.append(raw.headers.get("x-localroute-model", model))
        print(f"  {times[-1]:7.0f} ms  {routes[-1]:<12} {p[:60]}")
    return times, routes


if __name__ == "__main__":
    app_key = "bench-" + uuid.uuid4().hex[:6]  # fresh cache namespace each run
    print("LocalRoute (auto routing + cache):")
    lr, routes = run("http://localhost:8000/v1", app_key, "auto")
    print("\nDirect to Ollama, always the big model:")
    direct, _ = run("http://localhost:11434/v1", "ollama", os.getenv("BIG_MODEL", "gemma4:e2b-it-qat"))

    def row(name, t):
        return f"| {name} | {sum(t) / 1000:.1f} s | {statistics.mean(t):.0f} ms | {statistics.median(t):.0f} ms |"

    saving = 1 - sum(lr) / sum(direct)
    md = "\n".join([
        f"# Benchmark ({len(PROMPTS)} prompts, {time.strftime('%Y-%m-%d %H:%M')})", "",
        "| Setup | Total | Mean | Median |", "|---|---|---|---|",
        row("Always gemma4:e4b (direct)", direct), row("LocalRoute (routing + cache)", lr), "",
        f"**Time saved: {saving:.0%}**", "",
        "Who answered (LocalRoute): " + ", ".join(f"{m}: {routes.count(m)}" for m in sorted(set(routes))),
    ])
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.md")
    with open(path, "w") as f:
        f.write(md + "\n")
    print("\n" + md + f"\n\nSaved to {path}")
