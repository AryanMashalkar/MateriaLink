"""Were Dioscorides' uses better than chance?

For every chapter whose top identification resolves to a taxon, we take each distinct
(plant, disease-category) use. Statistic S = share of those pairs for which modern sources
link the plant to that category:
  - 'literature': >= 1 PubMed abstract co-mentions the plant and a disease in the category (BERN2)
  - 'cross_cultural': the same use is recorded in an independent ethnomedicine database

Null model (label permutation within the corpus): keep every plant and its number of uses
(so each plant keeps its own research intensity) and keep the corpus-wide frequency of each
category; shuffle which category goes with which plant. Repeat 10,000 times.
p = share of shuffles with S >= observed. Effect = observed / mean(null).

Remaining bias, stated openly: popular categories (e.g. inflammation) attract more papers for
any plant; shuffling preserves category frequencies, so this is handled. Plants studied *because*
of their traditional use (circularity) is not handled and is discussed in the README.

Usage: python src/chance_test.py [--min-prob 0.3] [--n 10000]
Output: results/chance_test.json, results/chance_test.png
"""
import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "data/external/enveda"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-prob", type=float, default=0.3)
    ap.add_argument("--n", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    rng = random.Random(a.seed)

    mondo = pd.read_csv(ENV / "mondo_upper_level_mapping.tsv", sep="\t")
    parent_name = dict(zip(mondo["Parent MONDO id"], mondo["Parent name"]))
    dis = pd.read_csv(ENV / "plant_disease_collapsed.tsv.gz", sep="\t", low_memory=False)
    dis["category"] = dis["disease_curie"].map(parent_name)
    lit, trad = defaultdict(set), defaultdict(set)
    for t, c, db in dis[["plant_curie", "category", "database"]].itertuples(index=False):
        (lit if db == "bern2" else trad)[t].add(c)
    valid = set(dis["category"].dropna().unique())

    plants = []  # (chapter id, taxon ids, [categories])
    for line in (ROOT / "data/processed/enriched.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        if not r["candidates"]:
            continue
        top = r["candidates"][0]
        if top["prob"] < a.min_prob or not top["ncbitaxon"] or top["rank"] != "species":
            continue
        cats = sorted({u["category"] for u in r["uses"] if u["category"] in valid})
        if cats:
            plants.append((r["id"], top["ncbitaxon"], cats))

    def lit_cats(taxa):
        s = set()
        for t in taxa:
            s |= lit.get(t, set())
        return s

    def trad_cats(taxa):
        s = set()
        for t in taxa:
            s |= trad.get(t, set())
        return s

    L = [lit_cats(t) for _, t, _ in plants]
    T = [trad_cats(t) for _, t, _ in plants]
    sizes = [len(c) for _, _, c in plants]
    pool = [c for _, _, cs in plants for c in cs]

    def stat(assign, ref):
        hit = tot = 0
        for cats, known in zip(assign, ref):
            tot += len(cats)
            hit += sum(1 for c in cats if c in known)
        return hit / tot if tot else 0.0

    observed_assign = [set(c) for _, _, c in plants]
    results = {}
    for name, ref in (("literature", L), ("cross_cultural", T)):
        obs = stat(observed_assign, ref)
        null = []
        for _ in range(a.n):
            rng.shuffle(pool)
            assign, i = [], 0
            for k in sizes:
                assign.append(set(pool[i:i + k]))  # duplicates collapse -> conservative
                i += k
            null.append(stat(assign, ref))
        mean_null = sum(null) / len(null)
        p = (1 + sum(1 for x in null if x >= obs)) / (1 + len(null))
        null_sorted = sorted(null)
        results[name] = {
            "observed": round(obs, 4),
            "null_mean": round(mean_null, 4),
            "null_95": [round(null_sorted[int(0.025 * a.n)], 4), round(null_sorted[int(0.975 * a.n)], 4)],
            "enrichment": round(obs / mean_null, 3) if mean_null else None,
            "p_value": p,
            "null": null,
        }
    meta = {"n_plants": len(plants), "n_pairs": len(pool), "min_prob": a.min_prob, "n_perm": a.n, "seed": a.seed}
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    json.dump({"meta": meta, **{k: {kk: vv for kk, vv in v.items() if kk != "null"} for k, v in results.items()}},
              (out / "chance_test.json").open("w"), indent=1)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    for ax, (name, v) in zip(axes, results.items()):
        ax.hist(v["null"], bins=40, color="#9aa5b1")
        ax.axvline(v["observed"], color="#c0392b", lw=2.5, label=f"Dioscorides: {v['observed']:.0%}")
        ax.set_title({"literature": "Modern literature (PubMed co-mentions)",
                      "cross_cultural": "Other traditions (5 ethnomedicine DBs)"}[name], fontsize=10)
        ax.set_xlabel("share of uses with support")
        ax.legend(frameon=False, fontsize=9)
        ax.text(0.98, 0.7, f"chance: {v['null_mean']:.0%}\nx{v['enrichment']}  p={v['p_value']:.4f}",
                transform=ax.transAxes, ha="right", fontsize=9)
    fig.suptitle(f"Permutation test, {meta['n_plants']} plants, {meta['n_pairs']} uses, {a.n:,} shuffles", fontsize=10)
    fig.tight_layout()
    fig.savefig(out / "chance_test.png", dpi=160)
    print(json.dumps({"meta": meta, **{k: {kk: vv for kk, vv in v.items() if kk != "null"} for k, v in results.items()}}, indent=1))


if __name__ == "__main__":
    main()
