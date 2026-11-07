"""Merge two independently filled annotation sheets into data/gold/gold.csv.

Usage: python src/merge_gold.py data/gold/annotator1.csv data/gold/annotator2.csv
Each sheet is a filled copy of data/gold/annotation_sheet.csv. Rows already in gold.csv
(the published Touwaide rows) are kept; annotated rows are added or updated.
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data/gold/gold.csv"


def read(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return {r["id"].strip(): r for r in csv.DictReader(f)}


def main(a1, a2):
    s1, s2 = read(a1), read(a2)
    chapters = {}
    for line in (ROOT / "data/processed/chapters.jsonl").open(encoding="utf-8"):
        import json
        c = json.loads(line)
        chapters[c["id"]] = c
    with GOLD.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    fields = ["id", "urn", "headword", "annotator1_taxon", "annotator2_taxon", "source_citation", "notes"]
    by_id = {r["id"]: r for r in rows}
    added = 0
    for cid in sorted(set(s1) | set(s2), key=lambda x: [int(p) for p in x.split(".")]):
        t1 = (s1.get(cid, {}).get("your_identification") or "").strip()
        t2 = (s2.get(cid, {}).get("your_identification") or "").strip()
        if not (t1 or t2):
            continue
        src = "; ".join(x for x in [(s1.get(cid, {}).get("your_source") or "").strip(),
                                    (s2.get(cid, {}).get("your_source") or "").strip()] if x)
        c = chapters.get(cid, {})
        by_id[cid] = {"id": cid, "urn": c.get("urn", ""), "headword": c.get("headword", ""),
                      "annotator1_taxon": t1, "annotator2_taxon": t2, "source_citation": src,
                      "notes": "independent annotation; confidence " +
                               "/".join(x for x in [(s1.get(cid, {}).get("confidence_1to3") or "").strip(),
                                                    (s2.get(cid, {}).get("confidence_1to3") or "").strip()] if x)}
        added += 1
    with GOLD.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in by_id.values():
            w.writerow({k: r.get(k, "") for k in fields})
    print(f"merged {added} annotated rows -> {GOLD} ({len(by_id)} rows total)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
