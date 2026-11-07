"""Zero-LLM baseline: transliterate the Greek headword (and the ancient Latin synonyms
recorded in Wellmann's apparatus) into Latin script and fuzzy-match against plant genus names.

Many Linnaean genera were coined from Dioscoridean names (Hyoscyamus < ὑοσκύαμος,
Mandragora < μανδραγόρας), so this is a strong, honest baseline that any LLM method must beat.

Usage: python src/baseline.py
Output: data/processed/baseline_predictions.jsonl
"""
import json
import unicodedata
from pathlib import Path

from rapidfuzz import fuzz, process

ROOT = Path(__file__).resolve().parents[1]
CHAPTERS = ROOT / "data/processed/chapters.jsonl"
GENERA = ROOT / "data/reference/plant_genera.txt"
OUT = ROOT / "data/processed/baseline_predictions.jsonl"

# Conventional Greek -> Latin transliteration used by botanists (ου->u, αι->ae, κ->c, -ος->-us ...)
DIGRAPHS = [
    ("ου", "u"), ("αι", "ae"), ("οι", "oe"), ("ει", "i"), ("αυ", "au"), ("ευ", "eu"),
    ("γγ", "ng"), ("γκ", "nc"), ("γχ", "nch"), ("γξ", "nx"),
]
LETTERS = {
    "α": "a", "β": "b", "γ": "g", "δ": "d", "ε": "e", "ζ": "z", "η": "e", "θ": "th",
    "ι": "i", "κ": "c", "λ": "l", "μ": "m", "ν": "n", "ξ": "x", "ο": "o", "π": "p",
    "ρ": "r", "σ": "s", "ς": "s", "τ": "t", "υ": "y", "φ": "ph", "χ": "ch", "ψ": "ps", "ω": "o",
}
ENDINGS = [("os", "us"), ("on", "um"), ("e", "a"), ("is", "is"), ("as", "a"), ("ion", "ium")]


def strip_accents(s: str) -> tuple[str, bool]:
    """Remove diacritics; report whether the word started with rough breathing (-> h)."""
    nfd = unicodedata.normalize("NFD", s.lower())
    rough = "̔" in nfd[:3]
    base = "".join(ch for ch in nfd if not unicodedata.combining(ch))
    return base, rough


def translit(word: str) -> list[str]:
    """Return candidate Latin spellings for one Greek word."""
    base, rough = strip_accents(word)
    out = base
    for g, l in DIGRAPHS:
        out = out.replace(g, l)
    out = "".join(LETTERS.get(ch, ch) for ch in out)
    if rough and out[:1] in "aeiouy":
        out = "h" + out
    if out.startswith("r"):
        out = "rh" + out[1:]
    out = "".join(ch for ch in out if ch.isascii() and ch.isalpha())
    cands = {out}
    for g, l in ENDINGS:
        if out.endswith(g):
            cands.add(out[: -len(g)] + l)
            cands.add(out[: -len(g)])  # stem only
    return [c for c in cands if len(c) >= 3]


def load_genera() -> list[str]:
    return [g.strip() for g in GENERA.read_text().splitlines() if g.strip()]


def predict(headword: str, synonyms: list[str], genera_lc: dict, k: int = 5):
    queries = []
    for w in headword.split()[:1]:
        queries += [(q, "headword") for q in translit(w)]
    for s in synonyms:
        for w in s.split()[:1]:
            queries += [(q, "synonym") for q in translit(w)]
    best = {}
    for q, src in queries:
        for name, score, _ in process.extract(q, list(genera_lc.keys()), scorer=fuzz.ratio, limit=k):
            # headword evidence counts more than an apparatus synonym
            s = score * (1.0 if src == "headword" else 0.85)
            g = genera_lc[name]
            if s > best.get(g, (0, None))[0]:
                best[g] = (s, q)
    ranked = sorted(best.items(), key=lambda kv: -kv[1][0])[:k]
    # map similarity to a pseudo-probability: softmax with temperature on 0-100 scores
    import math
    if not ranked:
        return []
    T = 6.0
    ex = [math.exp((s - ranked[0][1][0]) / T) for _, (s, _) in ranked]
    Z = sum(ex) + math.exp((70 - ranked[0][1][0]) / T)  # mass reserved for "none of these"
    return [
        {"taxon": g, "rank": "genus", "prob": round(e / Z, 4), "similarity": round(s, 1), "matched_on": q}
        for (g, (s, q)), e in zip(ranked, ex)
    ]


def main():
    genera = load_genera()
    genera_lc = {g.lower(): g for g in genera}
    n = 0
    with OUT.open("w", encoding="utf-8") as f:
        for line in CHAPTERS.open(encoding="utf-8"):
            ch = json.loads(line)
            cands = predict(ch["headword"], ch.get("synonyms", []), genera_lc)
            f.write(json.dumps({"id": ch["id"], "method": "baseline_fuzzy", "candidates": cands}, ensure_ascii=False) + "\n")
            n += 1
    print(f"baseline predictions for {n} chapters -> {OUT}")


if __name__ == "__main__":
    main()
