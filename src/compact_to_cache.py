"""Convert the compact pipe-delimited LLM output (written in the agent session, see README
'LLM provenance') into the per-chapter JSON cache used by extract_llm.py --collect.

Line format: id|headword|is_plant|taxon:prob;...|parts|greek=english=CAT;...
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATS = {
    "NS": "nervous system disorder", "INF": "infectious disease", "INFL": "inflammatory disease",
    "MSK": "musculoskeletal system disease", "DIG": "digestive system disease",
    "SKIN": "integumentary system disease", "IMM": "immune system disease", "CAN": "cancer",
    "CV": "cardiovascular disease", "CT": "connective tissue disease", "MET": "metabolic disease",
    "ENDO": "endocrine system disease", "PSY": "psychiatric disorder", "HEM": "hematologic disease",
    "RESP": "respiratory system disease", "URO": "urinary system disease",
    "ENT": "otorhinolaryngologic disease", "NUT": "nutritional disorder", "INJ": "injury",
    "EYE": "vision disorder", "BREAST": "breast disease", "POIS": "poisoning",
    "REPRO": "reproductive/obstetric", "OTH": "other",
}


def parse_line(line: str) -> dict:
    parts = line.rstrip("\n").split("|")
    if len(parts) < 6:
        parts += [""] * (6 - len(parts))
    cid, hw, plant, cands, plant_parts, uses = parts[:6]
    cand_list = []
    for c in filter(None, cands.split(";")):
        taxon, prob = c.rsplit(":", 1)
        cand_list.append({"taxon": taxon.strip(), "prob": float(prob), "why": ""})
    use_list = []
    for u in filter(None, uses.split(";")):
        g, e, cat = u.split("=")
        use_list.append({"greek": g.strip(), "en": e.strip(), "category": CATS[cat.strip()]})
    return {
        "id": cid.strip(),
        "headword": hw.strip(),
        "is_plant": plant.strip() == "1",
        "candidates": cand_list,
        "parts": [p.strip() for p in plant_parts.split(",") if p.strip()],
        "uses": use_list,
        "_model": "claude (Anthropic) in agent session; prompts/extract_v1.txt; compact format",
    }


def main(run: str = "claude_agent_v1"):
    src = ROOT / "data/llm_cache" / f"{run}_compact"
    out = ROOT / "data/llm_cache" / run
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in sorted(src.glob("*.txt")):
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            rec = parse_line(line)
            (out / f"{rec['id']}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
            n += 1
    print(f"wrote {n} chapter records -> {out}")


if __name__ == "__main__":
    main(*sys.argv[1:])
