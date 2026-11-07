"""MateriaLink: a Dioscorides concordance.

Greek chapter of De materia medica -> candidate plant identifications with confidence ->
accepted name and NCBI taxon -> known compounds -> modern literature signal per use.

Run: streamlit run app.py
"""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
P = ROOT / "data/processed"
R = ROOT / "results"

st.set_page_config(page_title="MateriaLink", page_icon="🌿", layout="wide")

TIER_HELP = {"A": "5+ PubMed abstracts co-mention plant and disease",
             "B": "2 to 4 co-mentioning abstracts",
             "C": "1 co-mentioning abstract",
             "D": "no co-mention found",
             "n/a": "category not in the MONDO disease ontology"}
TIER_COLOR = {"A": "#1e7b4f", "B": "#5a9e3a", "C": "#c49a1a", "D": "#9aa5b1", "n/a": "#c8ced6"}


@st.cache_data
def load():
    ch = {r["id"]: r for r in map(json.loads, (P / "chapters.jsonl").open(encoding="utf-8"))}
    en = [json.loads(l) for l in (P / "enriched.jsonl").open(encoding="utf-8")]
    base = {r["id"]: r for r in map(json.loads, (P / "baseline_predictions.jsonl").open(encoding="utf-8"))}
    return ch, en, base


def key(cid):
    b, c = cid.split(".", 1)
    num = "".join(x for x in c if x.isdigit()) or "0"
    return int(b), int(num), c


def badge(t):
    return (f"<span title='{TIER_HELP.get(t, '')}' style='background:{TIER_COLOR.get(t, '#ccc')};"
            f"color:white;padding:1px 8px;border-radius:9px;font-size:0.8em;font-weight:600'>{t}</span>")


ch, en, base = load()
en = sorted(en, key=lambda r: key(r["id"]))

st.title("MateriaLink")
st.caption("Dioscorides, *De materia medica* (1st c. CE), read in Greek and linked to modern botany, "
           "chemistry and literature. Research prototype: literature signals are not evidence of "
           "efficacy, and nothing here is medical advice.")

tab_ch, tab_stats, tab_chance, tab_about = st.tabs(["Chapter explorer", "Corpus overview", "Better than chance?", "Method and limits"])

with tab_ch:
    left, right = st.columns([1, 2.2])
    with left:
        books = sorted({r["book"] for r in en})
        book = st.radio("Book", books, horizontal=True, index=books.index(4) if 4 in books else 0)
        q = st.text_input("Search (Greek headword, Latin taxon or English use)", "")
        rows = [r for r in en if r["book"] == book]
        if q:
            ql = q.lower()
            rows = [r for r in en if ql in r["headword"].lower()
                    or any(ql in c["taxon"].lower() for c in r["candidates"])
                    or any(ql in (u.get("en") or "").lower() for u in r["uses"])]
        only_plants = st.checkbox("Plants only", True)
        if only_plants:
            rows = [r for r in rows if r["is_plant"]]
        if not rows:
            st.info("No chapters match.")
            st.stop()
        labels = [f"{r['id']}  {r['headword']}  ({r['candidates'][0]['taxon'] if r['candidates'] else '—'})" for r in rows]
        pick = st.selectbox("Chapter", range(len(rows)), format_func=lambda i: labels[i])
        r = rows[pick]
        c = ch.get(r["id"], {})
        st.markdown(f"**{r['headword']}**  \n`{r['urn']}`")
        if c.get("synonyms"):
            st.caption("Other names given: " + ", ".join(c["synonyms"][:12]))
        with st.expander("Greek text", expanded=True):
            st.markdown(f"<div style='font-size:1.02em;line-height:1.55'>{c.get('text', '')}</div>",
                        unsafe_allow_html=True)
        st.caption("Text: Wellmann edition via First1KGreek, CC BY-SA 4.0.")

    with right:
        cands = r["candidates"]
        if not r["is_plant"]:
            st.warning("This chapter is not about a plant (animal, mineral or prepared product).")
        if cands:
            top = cands[0]
            disputed = len(cands) > 1 and cands[1]["prob"] >= 0.5 * top["prob"]
            st.subheader("Identification")
            if disputed:
                st.markdown("⚖️ **Disputed:** the second candidate is at least half as likely as the first.")
            df = pd.DataFrame([{"candidate": x["taxon"], "confidence": x["prob"], "resolved to": x.get("resolved_name") or "",
                                "rank": x.get("rank"), "NCBI taxa": len(x.get("ncbitaxon") or []),
                                "compounds known": x.get("n_compounds", 0)} for x in cands])
            st.dataframe(df, hide_index=True, width='stretch',
                         column_config={"confidence": st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.2f")})
            b = base.get(r["id"], {}).get("candidates", [])
            if b:
                st.caption("Spelling-only baseline (Greek name transliterated and fuzzy-matched to genera): "
                           + ", ".join(f"{x['taxon']} {x['prob']:.2f}" for x in b[:3]))
            comps = top.get("compounds") or []
            if comps:
                st.subheader(f"Known compounds in {top.get('resolved_name') or top['taxon']}")
                names = [x["name"] if isinstance(x, dict) else str(x) for x in comps[:24]]
                st.markdown(" · ".join(names))
                st.caption("From LOTUS / COCONUT natural-product occurrence records (via enveda/ethnobotany, MIT). "
                           "Records can be noisy.")
        st.subheader("Uses Dioscorides gives, and what modern sources say")
        if r["uses"]:
            for u in r["uses"]:
                ev = u.get("evidence", {})
                t = ev.get("tier", "n/a")
                pm = ev.get("pmids") or []
                links = " ".join(f"[{p}](https://pubmed.ncbi.nlm.nih.gov/{p}/)" for p in pm[:3])
                cc = ev.get("cross_cultural") or []
                extra = f" · also recorded in {', '.join(cc)}" if cc else ""
                st.markdown(f"{badge(t)} &nbsp;**{u.get('en')}** · *{u.get('greek')}* · "
                            f"<span style='color:#6b7785'>{u.get('category')}</span>"
                            f"{' · ' + str(ev.get('n_pubmed', 0)) + ' abstracts ' + links if ev.get('n_pubmed') else ''}{extra}",
                            unsafe_allow_html=True)
        else:
            st.caption("No uses extracted.")
        st.caption("Tiers: " + " · ".join(f"{k} = {v}" for k, v in TIER_HELP.items()))

with tab_stats:
    plants = [r for r in en if r["is_plant"] and r["candidates"]]
    ranks = pd.Series([r["candidates"][0].get("rank") for r in plants]).value_counts()
    uses = [u for r in en for u in r["uses"]]
    tiers = pd.Series([u.get("evidence", {}).get("tier", "n/a") for u in uses]).value_counts()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Chapters processed", len(en))
    c2.metric("Plant chapters", len(plants))
    c3.metric("Resolved to a species", int(ranks.get("species", 0)))
    c4.metric("Uses extracted", len(uses))
    a, b = st.columns(2)
    with a:
        st.markdown("**Evidence tier of each use**")
        st.bar_chart(tiers.reindex(["A", "B", "C", "D", "n/a"]).fillna(0))
    with b:
        st.markdown("**Most common disease categories**")
        st.bar_chart(pd.Series([u.get("category") for u in uses]).value_counts().head(12))
    ev_path = R / "evaluation.json"
    if ev_path.exists():
        ev = json.loads(ev_path.read_text())
        st.markdown(f"**Accuracy against the gold set** (n = {ev['n_gold']})")
        if ev.get("warning"):
            st.caption(ev["warning"])
        st.dataframe(pd.DataFrame({m: {k: v["acc"] for k, v in res.items()} for m, res in ev["methods"].items()}).T)
        if (R / "reliability.png").exists():
            st.image(str(R / "reliability.png"), width=360)

with tab_chance:
    ct = R / "chance_test.json"
    if ct.exists():
        d = json.loads(ct.read_text())
        m = d["meta"]
        st.markdown(
            f"For each of **{m['n_plants']} confidently identified plants** we took the disease categories "
            f"Dioscorides assigns ({m['n_pairs']} plant-use pairs) and asked how often modern sources link that "
            f"plant to that category. Then we shuffled the categories between plants {m['n_perm']:,} times, keeping "
            "each plant's number of uses and each category's overall frequency, to see what chance alone gives.")
        cols = st.columns(2)
        for col, name, label in ((cols[0], "literature", "PubMed co-mentions"),
                                 (cols[1], "cross_cultural", "Independent traditions (5 ethnomedicine databases)")):
            v = d[name]
            col.metric(label, f"{v['observed']:.1%}", f"chance {v['null_mean']:.1%}, ×{v['enrichment']}, p = {v['p_value']:.3f}")
        st.image(str(R / "chance_test.png"), width='stretch')
        st.caption("Reading: the uses line up with modern findings a little more often than chance, and the signal is "
                   "stronger against other traditional systems than against the literature. Plants that were studied "
                   "because of their traditional use (circularity) can inflate the literature number; see the README.")
    else:
        st.info("Run `python src/chance_test.py` first.")

with tab_about:
    st.markdown((ROOT / "docs/method.md").read_text(encoding="utf-8") if (ROOT / "docs/method.md").exists()
                else "See README.md.")
