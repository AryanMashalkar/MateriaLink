"""Score the identifiers against the hand-curated gold set.

Gold: data/gold/gold.csv. A row counts once annotator1_taxon (or annotator2_taxon) is filled.
'|' separates several accepted identifications (scholars disagree; any of them counts).
The accepted set for a row is the union of both annotators' names.

Methods
  baseline  fuzzy transliteration vs. plant genera (genus level only)
  llm       Claude extraction (species level)
  hybrid    llm, falling back to baseline when the llm gives no candidate

Metrics: top-1 / top-3 accuracy at genus and species level with 95% bootstrap CIs,
Cohen's kappa between annotators (genus level, rows both filled), and for the llm the
expected calibration error (ECE) of its top-1 probability plus a reliability diagram.

Usage: python src/evaluate.py [--boot 2000]
Output: results/evaluation.json, results/reliability.png
"""
import argparse
import csv
import json
import random
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def genus(name):
    return name.strip().split()[0].lower() if name and name.strip() else ""


def species(name):
    p = name.strip().lower().split()
    return " ".join(p[:2]) if len(p) >= 2 else ""


def load_jsonl(p):
    return {r["id"]: r for r in map(json.loads, p.open(encoding="utf-8"))}


def hit(cands, accepted, level, k):
    f = genus if level == "genus" else species
    acc = {f(a) for a in accepted} - {""}
    if not acc:
        return None  # gold has no species-level answer for this row
    return any(f(c) in acc for c in cands[:k])


def boot_ci(xs, n, rng):
    if not xs:
        return [None, None]
    means = sorted(sum(rng.choice(xs) for _ in xs) / len(xs) for _ in range(n))
    return [round(means[int(0.025 * n)], 3), round(means[int(0.975 * n) - 1], 3)]


def kappa(a, b):
    n = len(a)
    if not n:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in ca) / n / n
    return round((po - pe) / (1 - pe), 3) if pe < 1 else 1.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=2000)
    a = ap.parse_args()
    rng = random.Random(0)

    base = load_jsonl(ROOT / "data/processed/baseline_predictions.jsonl")
    llm = load_jsonl(ROOT / "data/processed/llm_predictions.jsonl")
    gold = []
    for row in csv.DictReader((ROOT / "data/gold/gold.csv").open(encoding="utf-8")):
        a1, a2 = row["annotator1_taxon"].strip(), row["annotator2_taxon"].strip()
        if not (a1 or a2) or row["id"] not in llm:
            continue
        acc = [x for s in (a1, a2) for x in s.split("|") if x.strip()]
        gold.append({"id": row["id"], "accepted": acc, "a1": a1, "a2": a2})

    def preds(method, cid):
        b = [c["taxon"] for c in base.get(cid, {}).get("candidates", [])]
        l = [c["taxon"] for c in llm[cid].get("candidates", [])]
        return {"baseline": b, "llm": l, "hybrid": l or b}[method]

    out = {"n_gold": len(gold), "methods": {}}
    for m in ("baseline", "llm", "hybrid"):
        res = {}
        for level in ("genus", "species"):
            for k in (1, 3):
                xs = [hit(preds(m, g["id"]), g["accepted"], level, k) for g in gold]
                xs = [float(x) for x in xs if x is not None]
                res[f"{level}_top{k}"] = {"acc": round(sum(xs) / len(xs), 3) if xs else None,
                                          "ci95": boot_ci(xs, a.boot, rng), "n": len(xs)}
        out["methods"][m] = res

    both = [g for g in gold if g["a1"] and g["a2"]]
    out["kappa_genus"] = {"n": len(both), "kappa": kappa([genus(g["a1"].split("|")[0]) for g in both],
                                                        [genus(g["a2"].split("|")[0]) for g in both])}

    # calibration of the llm's top-1 probability (genus-level correctness)
    pts = []
    for g in gold:
        c = llm[g["id"]].get("candidates", [])
        if c:
            pts.append((float(c[0]["prob"]), bool(hit([c[0]["taxon"]], g["accepted"], "genus", 1))))
    bins = [[] for _ in range(5)]
    for p, y in pts:
        bins[min(int(p * 5), 4)].append((p, y))
    ece = sum(len(b) / len(pts) * abs(sum(p for p, _ in b) / len(b) - sum(y for _, y in b) / len(b))
              for b in bins if b) if pts else None
    out["llm_calibration"] = {"n": len(pts), "ece": round(ece, 3) if ece is not None else None,
                              "bins": [{"range": [i / 5, (i + 1) / 5], "n": len(b),
                                        "mean_conf": round(sum(p for p, _ in b) / len(b), 3) if b else None,
                                        "accuracy": round(sum(y for _, y in b) / len(b), 3) if b else None}
                                       for i, b in enumerate(bins)]}
    if len(gold) < 30:
        out["warning"] = (f"only {len(gold)} gold rows filled; numbers are illustrative, not conclusive. "
                          "Fill data/gold/gold.csv (two independent annotators) and rerun.")

    res_dir = ROOT / "results"
    res_dir.mkdir(exist_ok=True)
    json.dump(out, (res_dir / "evaluation.json").open("w"), indent=1)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(4.2, 4))
    ax.plot([0, 1], [0, 1], ls="--", color="#9aa5b1", lw=1)
    xs = [b["mean_conf"] for b in out["llm_calibration"]["bins"] if b["n"]]
    ys = [b["accuracy"] for b in out["llm_calibration"]["bins"] if b["n"]]
    ns = [b["n"] for b in out["llm_calibration"]["bins"] if b["n"]]
    ax.scatter(xs, ys, s=[30 + 12 * n for n in ns], color="#c0392b", zorder=3)
    ax.plot(xs, ys, color="#c0392b", lw=1.5)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1.02)
    ax.set_xlabel("stated confidence (top-1)"); ax.set_ylabel("share correct (genus)")
    ax.set_title(f"Reliability, n={len(pts)}, ECE={out['llm_calibration']['ece']}", fontsize=10)
    fig.tight_layout()
    fig.savefig(res_dir / "reliability.png", dpi=160)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
