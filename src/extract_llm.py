"""LLM extraction: Greek chapter -> candidate taxa with probabilities, parts, uses (+ category).

Supports three back-ends (pick with --provider):
  anthropic  : needs ANTHROPIC_API_KEY   (pip install anthropic)
  gemini     : needs GEMINI_API_KEY      (pip install google-genai)
  openai     : any OpenAI-compatible server, e.g. Ollama (OPENAI_BASE_URL, OPENAI_API_KEY, pip install openai)

Results are cached per chapter in data/llm_cache/<run>/<id>.json so reruns are free and
the exact raw outputs used in the paper/demo are kept in the repo.

Usage:
  python src/extract_llm.py --provider anthropic --model claude-sonnet-5-5 --books 3 4 --run claude_v1
  python src/extract_llm.py --collect --run claude_v1      # merge cache -> data/processed/llm_predictions.jsonl
"""
import argparse
import json
import os
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHAPTERS = ROOT / "data/processed/chapters.jsonl"
PROMPT = (ROOT / "prompts/extract_v1.txt").read_text(encoding="utf-8")


def call_llm(provider: str, model: str, user: str) -> str:
    if provider == "anthropic":
        import anthropic

        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=model, max_tokens=1500, system=PROMPT, messages=[{"role": "user", "content": user}]
        )
        return msg.content[0].text
    if provider == "gemini":
        from google import genai

        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        r = client.models.generate_content(model=model, contents=PROMPT + "\n\n" + user)
        return r.text
    if provider == "openai":
        from openai import OpenAI

        client = OpenAI()
        r = client.chat.completions.create(
            model=model, messages=[{"role": "system", "content": PROMPT}, {"role": "user", "content": user}]
        )
        return r.choices[0].message.content
    raise ValueError(provider)


def parse_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no JSON in response")
    return json.loads(m.group(0))


def normalise(rec: dict) -> dict:
    """Clamp probabilities so they sum to <= 1 and keep the schema tidy."""
    cands = [c for c in rec.get("candidates", []) if c.get("taxon")]
    tot = sum(float(c.get("prob", 0)) for c in cands)
    if tot > 1:
        for c in cands:
            c["prob"] = float(c["prob"]) / tot
    rec["candidates"] = sorted(cands, key=lambda c: -float(c.get("prob", 0)))[:5]
    rec.setdefault("uses", [])
    rec.setdefault("parts", [])
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", default="anthropic")
    ap.add_argument("--model", default="claude-sonnet-5-5")
    ap.add_argument("--books", nargs="*", type=int, default=[3, 4])
    ap.add_argument("--ids", nargs="*", default=None)
    ap.add_argument("--run", default="run1")
    ap.add_argument("--collect", action="store_true")
    a = ap.parse_args()

    cache = ROOT / "data/llm_cache" / a.run
    cache.mkdir(parents=True, exist_ok=True)

    if a.collect:
        out = ROOT / "data/processed/llm_predictions.jsonl"
        n = 0
        with out.open("w", encoding="utf-8") as f:
            for p in sorted(cache.glob("*.json")):
                rec = normalise(json.loads(p.read_text(encoding="utf-8")))
                rec["method"] = f"llm:{a.run}"
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1
        print(f"collected {n} chapters -> {out}")
        return

    chapters = [json.loads(l) for l in CHAPTERS.open(encoding="utf-8")]
    todo = [c for c in chapters if (a.ids and c["id"] in a.ids) or (not a.ids and c["book"] in a.books)]
    for ch in todo:
        p = cache / f"{ch['id']}.json"
        if p.exists():
            continue
        user = f"Chapter id: {ch['id']}\nCTS URN: {ch['urn']}\n\nGreek text:\n{ch['text']}"
        for attempt in range(3):
            try:
                rec = normalise(parse_json(call_llm(a.provider, a.model, user)))
                rec["id"] = ch["id"]
                rec["_model"] = f"{a.provider}:{a.model}"
                p.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
                print("ok", ch["id"], rec["candidates"][:1])
                break
            except Exception as e:  # noqa: BLE001
                print("retry", ch["id"], e)
                time.sleep(2 * (attempt + 1))


if __name__ == "__main__":
    main()
