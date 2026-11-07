"""Export the processed data into one compact JSON file for the static site in docs/.

Usage: python src/export_site.py   ->  docs/data.json
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data/processed"


PLAIN = {
    "nervous system disorder": "nerves and pain", "infectious disease": "infections and fevers",
    "inflammatory disease": "swelling and inflammation", "musculoskeletal system disease": "muscles and joints",
    "digestive system disease": "digestion", "integumentary system disease": "skin", "immune system disease": "immunity",
    "cancer": "tumours", "cardiovascular disease": "heart, blood vessels and dropsy", "connective tissue disease": "connective tissue",
    "metabolic disease": "metabolism", "endocrine system disease": "glands and hormones", "psychiatric disorder": "mind and mood",
    "hematologic disease": "blood and spleen", "respiratory system disease": "lungs and breathing",
    "urinary system disease": "kidneys and bladder", "otorhinolaryngologic disease": "ear, nose and throat",
    "nutritional disorder": "nutrition", "injury": "wounds and injuries", "vision disorder": "eyes",
    "breast disease": "breasts and milk", "poisoning": "bites, stings and poisons",
    "reproductive/obstetric": "women's health and childbirth", "other": "other",
}


def tsv(path):
    rows = (l.rstrip("\n").split("\t") for l in path.open(encoding="utf-8") if "\t" in l)
    next(rows)
    return {a: b for a, b in rows}


def join_en(xs):
    xs = [x for x in xs if x]
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1] if xs else ""


def summary(name, r, top, cands, uses):
    """Plain-English summary built only from the structured record (no new claims)."""
    if not r["is_plant"] or not top:
        s = f"This chapter is about {name or 'a substance'}, not a plant."
        if uses:
            s += f" Dioscorides recommends it for {join_en([u['en'] for u in uses[:4]])}."
        return s
    p = round(top["prob"] * 100)
    s = f"Dioscorides describes {name or 'a plant'}. From the description, the most likely plant is {top['taxon']} ({p}% likely)"
    if len(cands) > 1 and cands[1]["prob"] >= 0.15 and not top["taxon"].startswith(cands[1]["taxon"]):
        s += f"; the main alternative is {cands[1]['taxon']} ({round(cands[1]['prob'] * 100)}%)"
    s += "."
    if r.get("parts"):
        s += f" He uses the {join_en(r['parts'][:4])}."
    if uses:
        cats = []
        for u in uses:
            c = PLAIN.get(u.get("category"), "other")
            if c not in cats and c != "other":
                cats.append(c)
        s += f" He gives {len(uses)} use{'s' if len(uses) > 1 else ''}, mostly for {join_en(cats[:3]) or 'various complaints'}."
        scored = [u for u in uses if u.get("evidence", {}).get("tier", "n/a") != "n/a"]
        ok = [u for u in scored if u["evidence"]["tier"] in "ABC"]
        if scored:
            s += f" Modern papers mention the plant together with {len(ok)} of the {len(scored)} uses that can be checked"
            s += f" (for example {ok[0]['en']})." if ok else "."
    return s


def key(cid):
    b, c = cid.split(".", 1)
    return int(b), int("".join(x for x in c if x.isdigit()) or 0), c


def main():
    ch = {r["id"]: r for r in map(json.loads, (P / "chapters.jsonl").open(encoding="utf-8"))}
    base = {r["id"]: r for r in map(json.loads, (P / "baseline_predictions.jsonl").open(encoding="utf-8"))}
    names = tsv(ROOT / "data/editorial/taxon_common_names.tsv")
    over = tsv(ROOT / "data/editorial/chapter_english.tsv")
    out = []
    for r in sorted(map(json.loads, (P / "enriched.jsonl").open(encoding="utf-8")), key=lambda r: key(r["id"])):
        c = ch.get(r["id"], {})
        cands = r["candidates"]
        top = cands[0] if cands else {}
        comps = [x["name"] for x in (top.get("compounds") or []) if len(x["name"]) <= 30][:18]
        b = base.get(r["id"], {}).get("candidates", [])
        en = over.get(r["id"]) or (names.get(top.get("taxon", "")) if top else "") or ""
        out.append({
            "id": r["id"], "hw": r["headword"], "en": en,
            "sum": summary(en, r, top, cands, r["uses"]), "parts": r.get("parts", []), "urn": r["urn"], "plant": r["is_plant"],
            "syn": (c.get("synonyms") or [])[:8], "text": c.get("text", ""),
            "cands": [{"t": x["taxon"], "p": round(x["prob"], 2), "rank": x.get("rank"), "en": names.get(x["taxon"], "")} for x in cands[:4]],
            "ncomp": top.get("n_compounds", 0), "comps": comps,
            "base": [{"t": x["taxon"], "p": round(x["prob"], 2)} for x in b[:2]],
            "uses": [{"en": u.get("en"), "gr": u.get("greek"), "cat": u.get("category"), "plain": PLAIN.get(u.get("category"), "other"),
                      "tier": u.get("evidence", {}).get("tier", "n/a"),
                      "n": u.get("evidence", {}).get("n_pubmed", 0),
                      "pm": (u.get("evidence", {}).get("pmids") or [])[:3],
                      "cc": u.get("evidence", {}).get("cross_cultural") or []} for u in r["uses"]],
        })
    ct = json.loads((ROOT / "results/chance_test.json").read_text())
    ev = json.loads((ROOT / "results/evaluation.json").read_text())
    data = {"chapters": out, "chance": ct,
            "eval": {"n": ev["n_gold"], "methods": {m: {k: v["acc"] for k, v in r.items()} for m, r in ev["methods"].items()}}}
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs/data.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(len(out), "chapters ->", ROOT / "docs/data.json")


if __name__ == "__main__":
    main()
