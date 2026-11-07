"""Resolve candidate taxa to NCBI Taxonomy, attach compounds (LOTUS + COCONUT) and modern
evidence (PubMed literature co-mentions mined by BERN2, plus five independent ethnomedicine
databases), all from the open, offline data released with Domingo-Fernández et al. 2023
(github.com/enveda/ethnobotany, MIT).

Evidence tiers per (plant, disease-category) use:
  A  >= 5 PubMed abstracts co-mention the plant and a disease in the category
  B  2-4 abstracts
  C  1 abstract
  D  none found  (absence of evidence != evidence of absence)
These are literature *signals* (co-mentions found by a NER model), not proof of efficacy.
Independently, 'cross-cultural' = the same plant-category use is recorded in at least one of
IMPPAT (India), KTKP (Korea), ETM-DB (Ethiopia), VietHerb (Vietnam), Ewé (Brazil/Africa).

Usage: python src/enrich.py
Output: data/processed/enriched.jsonl
"""
import json
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "data/external/enveda"
OUT = ROOT / "data/processed/enriched.jsonl"

CATEGORY_ALIASES = {"reproductive/obstetric": None, "other": None}


def tier(n: int) -> str:
    return "A" if n >= 5 else "B" if n >= 2 else "C" if n >= 1 else "D"


def load_reference():
    names = json.loads((ENV / "trefle_grounding.json").read_text())
    # name -> (ncbitaxon, ncbi name)
    name2tax = {k.lower(): (v[0], v[1]) for k, v in names.items() if v[0]}
    mondo = pd.read_csv(ENV / "mondo_upper_level_mapping.tsv", sep="\t")
    parent_name = dict(zip(mondo["Parent MONDO id"], mondo["Parent name"]))
    dis = pd.read_csv(ENV / "plant_disease_collapsed.tsv.gz", sep="\t", low_memory=False)
    dis["category"] = dis["disease_curie"].map(parent_name)
    dis = dis.dropna(subset=["category"])
    chem = pd.read_csv(ENV / "plant_chemical_associations.tsv", sep="\t")
    return name2tax, dis, chem


def build_indexes(dis, chem):
    lit = defaultdict(set)      # (taxon, category) -> PMIDs
    trad = defaultdict(set)     # (taxon, category) -> databases
    for t, c, db, ev in dis[["plant_curie", "category", "database", "evidence"]].itertuples(index=False):
        if db == "bern2":
            lit[(t, c)].add(str(ev).split("_")[0])
        else:
            trad[(t, c)].add(db)
    plant_name = dict(zip(dis.plant_curie, dis.plant_name))
    plant_name.update(dict(zip(chem.plant_curie, chem["plant name"])))
    genus_members = defaultdict(set)
    for t, n in plant_name.items():
        if isinstance(n, str) and n:
            genus_members[n.split()[0].lower()].add(t)
    compounds = defaultdict(list)
    for t, cname, ccurie, db in chem[["plant_curie", "chemical name", "chemical_curie", "database"]].itertuples(index=False):
        compounds[t].append((cname, ccurie, db))
    return lit, trad, genus_members, compounds, plant_name


def resolve(taxon: str, name2tax, genus_members):
    """Return (rank, list_of_ncbitaxon_ids, resolved_name)."""
    t = taxon.strip()
    if " " in t:
        hit = name2tax.get(t.lower())
        if hit:
            return "species", [hit[0]], hit[1]
        # fall back to genus
        t = t.split()[0]
    members = genus_members.get(t.lower(), set())
    return ("genus", sorted(members), t) if members else ("unresolved", [], taxon)


def main():
    name2tax, dis, chem = load_reference()
    lit, trad, genus_members, compounds, plant_name = build_indexes(dis, chem)
    preds = {json.loads(l)["id"]: json.loads(l) for l in (ROOT / "data/processed/llm_predictions.jsonl").open()}
    chapters = {json.loads(l)["id"]: json.loads(l) for l in (ROOT / "data/processed/chapters.jsonl").open()}
    n_out = 0
    with OUT.open("w", encoding="utf-8") as f:
        for cid, p in preds.items():
            ch = chapters[cid]
            cands = []
            for c in p["candidates"]:
                rank, taxa, rname = resolve(c["taxon"], name2tax, genus_members)
                comp = []
                for tx in taxa:
                    comp += compounds.get(tx, [])
                # de-duplicate compounds by name, keep up to 40 for display
                seen, comp_u = set(), []
                # curated LOTUS records first, then trivial (short) names before IUPAC strings
                comp.sort(key=lambda x: (x[2] != "lotus", len(str(x[0]))))
                for cname, ccurie, db in comp:
                    if isinstance(cname, str) and cname and cname not in seen:
                        seen.add(cname)
                        comp_u.append({"name": cname, "id": ccurie, "source": db})
                cands.append({**c, "rank": rank, "ncbitaxon": taxa[:50], "resolved_name": rname,
                              "n_compounds": len(comp_u), "compounds": comp_u[:40]})
            top = cands[0] if cands else None
            uses = []
            for u in p["uses"]:
                cat = u["category"]
                pm, dbs = set(), set()
                if top and cat in set(dis["category"].unique()):
                    for tx in top["ncbitaxon"]:
                        pm |= lit.get((tx, cat), set())
                        dbs |= trad.get((tx, cat), set())
                    ev = {"tier": tier(len(pm)), "n_pubmed": len(pm), "pmids": sorted(pm)[:10],
                          "cross_cultural": sorted(dbs)}
                else:
                    ev = {"tier": "n/a", "n_pubmed": 0, "pmids": [], "cross_cultural": []}
                uses.append({**u, "evidence": ev})
            rec = {"id": cid, "urn": ch["urn"], "book": ch["book"], "chapter": ch["chapter"],
                   "headword": p.get("headword") or ch["headword"], "is_plant": p.get("is_plant", True),
                   "parts": p.get("parts", []), "candidates": cands, "uses": uses}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n_out += 1
    print(f"enriched {n_out} chapters -> {OUT}")


if __name__ == "__main__":
    main()
