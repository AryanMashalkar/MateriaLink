"""Parse Wellmann's Greek edition of Dioscorides (First1KGreek TEI, CC BY-SA 4.0)
into one record per chapter with a stable CTS URN.

Usage: python src/parse_tei.py
Output: data/processed/chapters.jsonl
"""
import json
import re
import unicodedata
from pathlib import Path

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/raw/tlg0656.tlg001.1st1K-grc1.xml"
OUT = ROOT / "data/processed/chapters.jsonl"
NS = {"t": "http://www.tei-c.org/ns/1.0"}
BASE_URN = "urn:cts:greekLit:tlg0656.tlg001.1st1K-grc1"

GREEK_WORD = re.compile(r"[Ͱ-Ͽἀ-῿]+")


def clean_text(el) -> str:
    """Text of a section with footnotes and editorial deletions removed."""
    el = etree.fromstring(etree.tostring(el))  # copy
    # the TEI nests some chapters inside the previous one (unclosed divs); never pull their text in
    for sub in el.xpath("./t:div[@subtype='chapter']", namespaces=NS):
        el.remove(sub)
    for bad in el.xpath(".//t:note|.//t:del", namespaces=NS):
        tail = bad.tail
        parent = bad.getparent()
        prev = bad.getprevious()
        if tail:
            if prev is not None:
                prev.tail = (prev.tail or "") + tail
            else:
                parent.text = (parent.text or "") + tail
        parent.remove(bad)
    text = " ".join(el.itertext())
    text = re.sub(r"\s+", " ", text).strip()
    # drop Wellmann's leading line/section numbers
    text = re.sub(r"(?<![\w])\d+\s", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def synonyms_from_notes(chapter_el) -> list[str]:
    """Collect the ancient synonym lists ('οἱ δὲ X, Ῥωμαῖοι Y') kept in the RV footnotes."""
    syn = []
    own = [n for n in chapter_el.xpath(".//t:note", namespaces=NS)
           if next((a for a in n.iterancestors() if a.get("subtype") == "chapter"), None) is chapter_el]
    for note in own:
        txt = re.sub(r"\s+", " ", " ".join(note.itertext()))
        if "οἱ δὲ" in txt or "Ῥωμαῖοι" in txt or "Αἰγύπτιοι" in txt:
            for m in re.finditer(r"(?:οἱ δὲ|Ῥωμαῖοι|Αἰγύπτιοι|Γάλλοι|Δάκοι|Ἀφροι|προφῆται)\s+([^,·.;]+)", txt):
                s = m.group(1).strip()
                if 0 < len(s) < 40:
                    syn.append(s)
    seen, out = set(), []
    for s in syn:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out[:25]


STOP = {"ἡ", "ὁ", "τό", "τὸ", "ἡ", "ἄλλη", "ἄλλος", "ἄλλο", "ἔτι", "ἐστι", "ἔστι", "καλοῦσί", "καλοῦσι",
        "ἔνιοι", "δέ", "δὲ", "καί", "καὶ", "τῆς", "τοῦ", "οἱ", "αἱ", "τὰ", "ἀπὸ", "ἐκ", "περὶ"}
PUNCT = "·;,.:\u0387\u00b7"


def headword(text: str) -> str:
    words = [w.strip(PUNCT) for w in GREEK_WORD.findall(text)]
    words = [w for w in words if w and w not in STOP]
    if not words:
        return ""
    hw = words[0]
    # common two-word headwords: adjective following the noun (e.g. ἶρις Ἰλλυρική, στρύχνον κηπαῖον)
    if len(words) > 1 and words[1][0].isupper():
        hw = f"{words[0]} {words[1]}"
    return hw


def main():
    tree = etree.parse(str(SRC))
    records = []
    for book in tree.xpath("//t:div[@subtype='book']", namespaces=NS):
        b = book.get("n")
        seen = set()
        # './/' not './': in Books 1, 2 and 4 the TEI nests later chapters inside earlier ones
        for ch in book.xpath(".//t:div[@subtype='chapter']", namespaces=NS):
            c = ch.get("n")
            if c == "preface" or c in seen:
                continue
            seen.add(c)
            secs = ch.xpath("./t:div[@subtype='section']", namespaces=NS) or [ch]
            sections = []
            for s in secs:
                n = s.get("n", "1") if s is not ch else "1"
                sections.append({"n": n, "text": clean_text(s)})
            full = " ".join(s["text"] for s in sections)
            records.append(
                {
                    "id": f"{b}.{c}",
                    "book": int(b),
                    "chapter": c,
                    "urn": f"{BASE_URN}:{b}.{c}",
                    "headword": headword(full),
                    "headword_norm": unicodedata.normalize("NFC", headword(full)),
                    "synonyms": synonyms_from_notes(ch),
                    "sections": sections,
                    "text": full,
                    "n_words": len(full.split()),
                }
            )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    by_book = {}
    for r in records:
        by_book[r["book"]] = by_book.get(r["book"], 0) + 1
    print(f"{len(records)} chapters -> {OUT}  per book: {by_book}")


if __name__ == "__main__":
    main()
