"""Export the processed data into one compact JSON file for the static site in docs/.

Usage: python src/export_site.py   ->  docs/data.json
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data/processed"


def key(cid):
    b, c = cid.split(".", 1)
    return int(b), int("".join(x for x in c if x.isdigit()) or 0), c


def main():
    ch = {r["id"]: r for r in map(json.loads, (P / "chapters.jsonl").open(encoding="utf-8"))}
    base = {r["id"]: r for r in map(json.loads, (P / "baseline_predictions.jsonl").open(encoding="utf-8"))}
    out = []
    for r in sorted(map(json.loads, (P / "enriched.jsonl").open(encoding="utf-8")), key=lambda r: key(r["id"])):
        c = ch.get(r["id"], {})
        cands = r["candidates"]
        top = cands[0] if cands else {}
        comps = [x["name"] for x in (top.get("compounds") or []) if len(x["name"]) <= 30][:18]
        b = base.get(r["id"], {}).get("candidates", [])
        out.append({
            "id": r["id"], "hw": r["headword"], "urn": r["urn"], "plant": r["is_plant"],
            "syn": (c.get("synonyms") or [])[:8], "text": c.get("text", ""),
            "cands": [{"t": x["taxon"], "p": round(x["prob"], 2), "rank": x.get("rank")} for x in cands[:4]],
            "ncomp": top.get("n_compounds", 0), "comps": comps,
            "base": [{"t": x["taxon"], "p": round(x["prob"], 2)} for x in b[:2]],
            "uses": [{"en": u.get("en"), "gr": u.get("greek"), "cat": u.get("category"),
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
