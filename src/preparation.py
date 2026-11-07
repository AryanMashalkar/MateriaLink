"""Deterministic 'how he prepared it' tags from Dioscorides' Greek (no dosages, no LLM).

Each tag is a stem pattern searched in the accent-stripped chapter text, so a tag means only
"this word family occurs in the chapter". It records the historical route or vehicle
(drunk, poultice, decoction, with wine ...), never an amount. Quantities (drachmai, obols,
kyathoi ...) are deliberately not extracted: this is a history-of-medicine tool, not advice.

Usage: from preparation import prep_tags; prep_tags(greek_text) -> [{"tag":..., "n":...}]
"""
import re
import unicodedata

# (English tag, kind, regex over accent-stripped lowercase Greek with final sigma -> σ)
RULES = [
    ("drunk", "route", r"\bπο(θε|θει|θεισ|θεν|θη|τιζ|τον\b)|\bπιν(ομεν|εται|ουσ|ειν)|\bπιοντ"),
    ("eaten", "route", r"\bεσθι(ομεν|εται|ειν)|\bβρω(θε|θει|σει|σιν)\b|\bβρωθ"),
    ("chewed", "route", r"\bδιαμασ"),
    ("poultice or plaster", "route", r"\bκαταπλα(σ|ττ)|\bεπιπλα(σ|ττ)|\bκαταπλασμ"),
    ("rubbed on (ointment)", "route", r"\bεπιχρι|\bκαταχρι|\bχρι(ομεν|εται|σθ|εσθ)|\bαλειφ|\bσυγχρι"),
    ("sprinkled on as a powder", "route", r"\bεπιπα(σ|ττ)|\bκαταπα(σ|ττ)"),
    ("smoke or fumigation", "route", r"\bυποθυμι|\bθυμι(ωμεν|αθε|ωμεν)|\bεπιθυμι(ωμεν|αθε)"),
    ("boiled (decoction)", "preparation", r"\bαφεψ|\bαποζε(σ|θ)|\bεψη(θ|σ)|\bεψομεν|\bεφθ"),
    ("pessary (inserted)", "route", r"\bπροστι(θ|θεμεν)|\bπροστε(θ|θει)|\bπεσσ"),
    ("enema or douche", "route", r"\bεγκλυ(σ|ζ)|\bκλυσ(μ|τηρ)|\bενιεμεν"),
    ("mouthwash or gargle", "route", r"\bδιακλυ(ζ|σ)|\bαναγαργαρ"),
    ("drops (ear, eye or nose)", "route", r"\bεν(σταζ|σταχθ|σταλαζ)|\bεγχε(ομεν|ιται|ομεν)|\bεγχυ(θ|μ)"),
    ("eye salve", "preparation", r"\bκολλυρ"),
    ("sitz bath", "route", r"\bεγκαθισ"),
    ("worn as an amulet", "route", r"\bπεριαπτ|\bπεριαφθ|\bπεριαπτομεν|\bπεριαψ"),
    ("with wine", "vehicle", r"\b(συν|μετ|μετα|εν) οιν(ω|ου)\b|\bοινω\b"),
    ("with vinegar", "vehicle", r"\bοξει\b|\bοξουσ\b|\bοξυκρατ"),
    ("with honey", "vehicle", r"\bμελιτ(ι|οσ)\b|\bμελικρατ|\bυδρομελιτ|\bμελιτι"),
    ("with oil", "vehicle", r"\bελαι(ω|ου)\b|\bροδιν(ω|ου)\b"),
]
COMPILED = [(t, k, re.compile(p)) for t, k, p in RULES]


def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn").lower()
    s = re.sub(r"[ʼ’᾽'`ʹ]", " ", s).replace("ς", "σ")
    return re.sub(r"\s+", " ", s)


def prep_tags(text: str):
    t = norm(text)
    out = []
    for tag, kind, rx in COMPILED:
        n = len(rx.findall(t))
        if n:
            out.append({"tag": tag, "kind": kind, "n": n})
    return sorted(out, key=lambda x: (-x["n"], x["tag"]))


if __name__ == "__main__":
    import json
    from collections import Counter
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    c = Counter()
    n = 0
    for r in map(json.loads, (root / "data/processed/chapters.jsonl").open(encoding="utf-8")):
        tags = prep_tags(r.get("text", ""))
        n += bool(tags)
        c.update(x["tag"] for x in tags)
    print(n, "chapters with at least one tag")
    for k, v in c.most_common():
        print(f"{v:4d}  {k}")
