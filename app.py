"""MateriaLink: a Dioscorides concordance.

Greek chapter of De materia medica -> candidate plant identifications with confidence ->
accepted name and NCBI taxon -> known compounds -> modern literature signal per use.

Run: streamlit run app.py
"""
import html as H
import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
P = ROOT / "data/processed"
R = ROOT / "results"
# plain-English names for the disease categories (same as src/export_site.py)
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


st.set_page_config(page_title="MateriaLink · Dioscorides", page_icon="🌿", layout="wide",
                   initial_sidebar_state="collapsed")

INK, MUTED, PAPER, CARD, LINE = "#2a2620", "#7a6f5f", "#f5efe3", "#fffaf1", "#e4d9c4"
HERB, RUBRIC, GOLD = "#2f5d3a", "#a8442a", "#b8892b"
TIER_COLOR = {"A": HERB, "B": "#6c8f3d", "C": GOLD, "D": "#b9ad98", "n/a": "#d9cfbd"}
TIER_HELP = {"A": "5+ PubMed abstracts co-mention plant and disease",
             "B": "2 to 4 co-mentioning abstracts",
             "C": "1 co-mentioning abstract",
             "D": "no co-mention found",
             "n/a": "category outside the MONDO disease ontology"}

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,500;1,600&family=GFS+Didot&family=Inter:wght@400;500;600&display=swap');
html, body, [class*="st-"], .stMarkdown, p, label, li {{ font-family: 'Inter', sans-serif; }}
.stApp {{ background: radial-gradient(circle at 15% 0%, #fbf7ee 0%, {PAPER} 45%, #efe6d4 100%); }}
header[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 2.2rem; max-width: 1280px; }}
h1, h2, h3 {{ font-family: 'Cormorant Garamond', serif !important; color: {INK}; letter-spacing: .2px; }}
.hero {{ display:flex; align-items:flex-end; justify-content:space-between; gap:2rem; flex-wrap:wrap;
        border-bottom: 1px solid {LINE}; padding-bottom: 1.1rem; margin-bottom: 1.2rem; }}
.hero .kicker {{ font: 600 .72rem 'Inter'; letter-spacing: .22em; text-transform: uppercase; color: {RUBRIC}; }}
.hero .title {{ font: 700 4.6rem/.95 'Cormorant Garamond', serif; color: {INK}; margin: .3rem 0 .4rem 0; letter-spacing: -.5px; }}
.hero .title span {{ color: {RUBRIC}; font-style: italic; }}
.hero .greek {{ font-family: 'GFS Didot', serif; font-size: 1.25rem; color: {MUTED}; }}
.hero .sub {{ max-width: 560px; color: {MUTED}; font-size: .95rem; line-height: 1.5; margin-top: .4rem; }}
.stats {{ display:flex; gap: .7rem; flex-wrap: wrap; }}
.stat {{ background: {CARD}; border: 1px solid {LINE}; border-radius: 14px; padding: .7rem 1rem; min-width: 118px; }}
.stat b {{ display:block; font: 700 1.9rem 'Cormorant Garamond', serif; color: {INK}; line-height: 1; }}
.stat small {{ color: {MUTED}; font-size: .72rem; letter-spacing: .04em; }}
.card {{ background: {CARD}; border: 1px solid {LINE}; border-radius: 18px; padding: 1.2rem 1.35rem;
        box-shadow: 0 1px 0 rgba(255,255,255,.7) inset, 0 10px 30px -18px rgba(60,40,10,.35); margin-bottom: 1rem; }}
.label {{ font: 600 .7rem 'Inter'; letter-spacing: .18em; text-transform: uppercase; color: {MUTED}; margin-bottom: .55rem; }}
.manuscript {{ font-family: 'GFS Didot', serif; font-size: 1.12rem; line-height: 1.75; color: #3a3329;
              max-height: 520px; overflow-y: auto; padding-right: .4rem; }}
.manuscript::first-letter {{ float:left; font: 700 3.6rem/0.85 'Cormorant Garamond', serif; color: {RUBRIC};
                             padding: .35rem .45rem 0 0; }}
.headword {{ font-family: 'GFS Didot', serif; font-size: 2.1rem; color: {INK}; line-height: 1.1; }}
.urn {{ font: 500 .72rem ui-monospace, monospace; color: {MUTED}; background: #f1e8d6; padding: .15rem .5rem;
       border-radius: 6px; display:inline-block; margin-top: .4rem; }}
.syn {{ color: {MUTED}; font-size: .82rem; margin-top: .55rem; font-style: italic; }}
.taxon {{ font: italic 600 2.3rem 'Cormorant Garamond', serif; color: {HERB}; line-height: 1.05; }}
.taxon-meta {{ color: {MUTED}; font-size: .82rem; margin-top: .2rem; }}
.conf {{ display:flex; align-items:center; gap:.7rem; margin: .45rem 0; }}
.conf .name {{ width: 42%; font: italic 500 1.08rem 'Cormorant Garamond', serif; color: {INK}; }}
.conf .bar {{ flex:1; height: 8px; background: #efe5d2; border-radius: 99px; overflow:hidden; }}
.conf .bar i {{ display:block; height:100%; border-radius: 99px; background: linear-gradient(90deg, {HERB}, #5d8a55); }}
.conf .pct {{ width: 44px; text-align:right; font: 600 .82rem 'Inter'; color: {INK}; }}
.seal {{ display:inline-block; font: 600 .72rem 'Inter'; letter-spacing:.08em; text-transform: uppercase; color: {RUBRIC};
        border: 1.5px solid {RUBRIC}; border-radius: 99px; padding: .18rem .65rem; margin-left: .5rem; vertical-align: middle; }}
.baseline {{ margin-top: .9rem; padding-top: .7rem; border-top: 1px dashed {LINE}; color: {MUTED}; font-size: .8rem; }}
.baseline b {{ color: {INK}; font-weight: 600; }}
.chips {{ display:flex; flex-wrap:wrap; gap:.4rem; }}
.chip {{ background: #f3ead8; border: 1px solid {LINE}; border-radius: 99px; padding: .22rem .7rem; font-size: .8rem; color: #4a4134; }}
.use {{ display:grid; grid-template-columns: 34px 1fr auto; gap: .8rem; align-items:center;
       padding: .62rem 0; border-bottom: 1px solid #efe6d3; }}
.use:last-child {{ border-bottom: 0; }}
.tier {{ width: 30px; height: 30px; border-radius: 50%; color: #fff; font: 700 .8rem 'Inter';
        display:flex; align-items:center; justify-content:center; }}
.use .en {{ font-weight: 600; color: {INK}; font-size: .95rem; }}
.use .gr {{ font-family: 'GFS Didot', serif; color: {MUTED}; font-size: .95rem; }}
.use .cat {{ font-size: .74rem; color: {MUTED}; letter-spacing: .02em; }}
.use .ev {{ text-align:right; font-size: .76rem; color: {MUTED}; }}
.use .ev a {{ color: {HERB}; text-decoration: none; border-bottom: 1px dotted {HERB}; }}
.cc {{ display:inline-block; background: #e9f0e3; color: {HERB}; border-radius: 6px; padding: .05rem .4rem; margin-left:.2rem; font-size:.7rem; }}
.legend {{ display:flex; flex-wrap:wrap; gap: .9rem; font-size: .74rem; color: {MUTED}; margin-top: .6rem; }}
.legend span i {{ display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:.3rem; vertical-align: -1px; }}
.big {{ font: 700 3.4rem 'Cormorant Garamond', serif; color: {INK}; line-height: 1; }}
.vs {{ color: {MUTED}; font-size: .9rem; margin-top: .3rem; }}
.pill {{ display:inline-block; border-radius:99px; padding:.15rem .6rem; font: 600 .75rem 'Inter'; }}
.lead {{ font: 500 1.35rem/1.5 'Cormorant Garamond', serif; color: {INK}; max-width: 900px; }}
.note {{ color: {MUTED}; font-size: .82rem; line-height: 1.5; }}
.stTabs [data-baseweb="tab-list"] {{ gap: 1.6rem; border-bottom: 1px solid {LINE}; }}
.stTabs [data-baseweb="tab"] {{ font: 600 .86rem 'Inter'; color: {MUTED}; padding: .6rem 0; background: transparent; }}
.stTabs [aria-selected="true"] {{ color: {RUBRIC} !important; }}
.stTabs [data-baseweb="tab-highlight"] {{ background-color: {RUBRIC}; }}
div[data-baseweb="select"] > div, .stTextInput input {{ background: {CARD} !important; border-color: {LINE} !important; border-radius: 10px !important; }}
footer {{ visibility: hidden; }}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def html(s):
    st.markdown("\n".join(l.strip() for l in s.splitlines()), unsafe_allow_html=True)


def e(x):
    return H.escape(str(x)) if x is not None else ""


@st.cache_data
def load():
    ch = {r["id"]: r for r in map(json.loads, (P / "chapters.jsonl").open(encoding="utf-8"))}
    en = [json.loads(l) for l in (P / "enriched.jsonl").open(encoding="utf-8")]
    base = {r["id"]: r for r in map(json.loads, (P / "baseline_predictions.jsonl").open(encoding="utf-8"))}
    site = json.loads((ROOT / "docs/data.json").read_text(encoding="utf-8"))
    eng = {c["id"]: c for c in site["chapters"]}  # English names and plain summaries (src/export_site.py)
    return ch, en, base, eng


def key(cid):
    b, c = cid.split(".", 1)
    return int(b), int("".join(x for x in c if x.isdigit()) or 0), c


ch, en, base, eng = load()


def prep_html(tags):
    if not tags:
        return ""
    chips = " ".join(f'<span style="display:inline-block;border:1px solid #b08d57;border-radius:999px;padding:.1rem .6rem;margin:.15rem;font-size:.85rem">{e(t["tag"])} <b>{t["n"]}</b></span>' for t in tags)
    return (f'<div class="label">How he prepared it</div><div>{chips}</div>'
            '<div class="note" style="margin:.3rem 0 .9rem">Ways of giving the remedy named in the Greek (number = how often). '
            'Doses left out on purpose. History, not medical advice.</div>')
EN = lambda cid: eng.get(cid, {}).get("en", "")
en = sorted(en, key=lambda r: key(r["id"]))
plants = [r for r in en if r["is_plant"] and r["candidates"]]
uses_all = [u for r in en for u in r["uses"]]
n_species = sum(1 for r in plants if r["candidates"][0].get("rank") == "species")
n_signal = sum(1 for u in uses_all if u.get("evidence", {}).get("tier") in ("A", "B", "C"))

html(f"""
<div class="hero">
  <div>
    <div class="kicker">A concordance of Dioscorides · 1st century CE</div>
    <div class="title">Materia<span>Link</span></div>
    <div class="greek">Περὶ ὕλης ἰατρικῆς · De materia medica</div>
    <div class="sub">Read in the original Greek, each chapter is linked to a modern species, the compounds that plant
    is known to contain, and what today's literature says about every use Dioscorides gives.</div>
  </div>
  <div class="stats">
    <div class="stat"><b>{len(en)}</b><small>chapters read</small></div>
    <div class="stat"><b>{n_species}</b><small>pinned to a species</small></div>
    <div class="stat"><b>{len(uses_all):,}</b><small>uses extracted</small></div>
    <div class="stat"><b>{n_signal}</b><small>with a PubMed signal</small></div>
  </div>
</div>
""")

tab_ch, tab_chance, tab_stats, tab_about = st.tabs(
    ["📜  Chapter explorer", "🎲  Better than chance?", "📊  Corpus overview", "⚖️  Method and limits"])

# ---------------------------------------------------------------- explorer
with tab_ch:
    f1, f2, f3 = st.columns([1, 2.2, 3])
    allch = st.checkbox("Also show animals, minerals and wines (not plants)", value=False)
    with f1:
        books = sorted({r["book"] for r in en})
        book = st.selectbox("Book", books, index=books.index(4) if 4 in books else 0,
                            format_func=lambda b: f"Book {b}")
    with f2:
        q = st.text_input("Search", "", placeholder="hemlock, κώνειον, Conium, cough, burns …")
    rows = [r for r in en if r["book"] == book and (r["is_plant"] or allch)]
    if q:
        ql = q.lower()
        rows = [r for r in en if ql in r["headword"].lower() or ql in EN(r["id"]).lower()
                or any(ql in c["taxon"].lower() for c in r["candidates"])
                or any(ql in (u.get("en") or "").lower() for u in r["uses"])]
    if not rows:
        st.info("No chapters match.")
        st.stop()
    labels = [f"{r['id']} · {EN(r['id']) or r['headword']} ({r['headword']})" + (f" — {r['candidates'][0]['taxon']}" if r['candidates'] else "")
              for r in rows]
    default = next((i for i, r in enumerate(rows) if r["id"] == "4.78"), 0)
    with f3:
        pick = st.selectbox("Chapter", range(len(rows)), index=default, format_func=lambda i: labels[i])
    r = rows[pick]
    c = ch.get(r["id"], {})
    cands = r["candidates"]

    left, right = st.columns([1, 1.25], gap="large")
    with left:
        syn = c.get("synonyms") or []
        html(f"""
        <div class="card">
          <div class="label">Chapter {e(r['id'])} · the Greek text</div>
          <div class="headword">{e(r['headword'])}</div>
          <div style="font-size:1.25rem;font-style:italic;margin-top:.2rem">in English: {e(EN(r['id']))}</div>
          <div class="urn">{e(r['urn'])}</div>
          {f'<div class="syn">also called: {e(", ".join(syn[:10]))}</div>' if syn else ''}
          <div style="height:.9rem"></div>
          <div class="label">In plain English</div>
          <div style="line-height:1.6">{e(eng.get(r['id'], {}).get('sum', ''))}</div>
          <div class="note" style="margin:.4rem 0 .9rem">Built from the uses, each translated phrase by phrase. Not a full literary translation.</div>
          {prep_html(eng.get(r['id'], {}).get('prep', []))}
          <div class="label">The original Greek</div>
          <div class="manuscript">{e(c.get('text', ''))}</div>
          <div class="note" style="margin-top:.8rem">Wellmann edition via First1KGreek · CC BY-SA 4.0</div>
        </div>""")

    with right:
        if not r["is_plant"]:
            html('<div class="card"><div class="label">Identification</div>Not a plant: an animal, mineral or prepared product.</div>')
        elif cands:
            top = cands[0]
            disputed = len(cands) > 1 and cands[1]["prob"] >= 0.5 * top["prob"]
            bars = "".join(
                f'<div class="conf"><div class="name">{e(x["taxon"])}</div>'
                f'<div class="bar"><i style="width:{max(2, x["prob"] * 100):.0f}%"></i></div>'
                f'<div class="pct">{x["prob"]:.0%}</div></div>' for x in cands)
            meta = []
            if top.get("resolved_name"):
                meta.append(f"resolved to {e(top['resolved_name'])} ({e(top.get('rank'))})")
            if top.get("ncbitaxon"):
                meta.append(f"{len(top['ncbitaxon'])} NCBI taxa")
            b = base.get(r["id"], {}).get("candidates", [])
            bl = ", ".join(f"{e(x['taxon'])} {x['prob']:.0%}" for x in b[:3]) if b else "no match"
            html(f"""
            <div class="card">
              <div class="label">Most likely plant{'<span class="seal">disputed</span>' if disputed else ''}</div>
              <div class="taxon">{e(top['taxon'])}</div>
              <div class="taxon-meta">{' · '.join(meta)}</div>
              <div style="height:.8rem"></div>
              {bars}
              <div class="baseline"><b>Spelling alone would say:</b> {bl}
              <br>(the Greek name transliterated and fuzzy-matched to plant genera, for comparison)</div>
            </div>""")
            comps = top.get("compounds") or []
            if comps:
                names = [n for n in (x["name"] if isinstance(x, dict) else str(x) for x in comps) if len(n) <= 32][:20]
                chips = "".join(f'<span class="chip">{e(n)}</span>' for n in names)
                html(f"""
                <div class="card">
                  <div class="label">Known compounds · {e(top.get('n_compounds', len(comps)))} recorded</div>
                  <div class="chips">{chips}</div>
                  <div class="note" style="margin-top:.7rem">LOTUS / COCONUT occurrence records via enveda/ethnobotany (MIT). Records can be noisy.</div>
                </div>""")

        items = []
        for u in r["uses"]:
            ev = u.get("evidence", {})
            t = ev.get("tier", "n/a")
            pm = ev.get("pmids") or []
            links = " ".join(f'<a href="https://pubmed.ncbi.nlm.nih.gov/{p}/" target="_blank">{p}</a>' for p in pm[:2])
            cc = "".join(f'<span class="cc">{e(x)}</span>' for x in (ev.get("cross_cultural") or []))
            n = ev.get("n_pubmed", 0)
            evtxt = (f"{n} abstract{'s' if n != 1 else ''}<br>{links}" if n else "") + (f"<br>{cc}" if cc else "")
            items.append(
                f'<div class="use"><div class="tier" style="background:{TIER_COLOR.get(t, "#ccc")}" '
                f'title="{e(TIER_HELP.get(t, ""))}">{"–" if t == "n/a" else t}</div>'
                f'<div><div class="en">{e(u.get("en"))}</div><div class="gr">{e(u.get("greek"))}</div>'
                f'<div class="cat">{e(PLAIN.get(u.get("category"), u.get("category")))}</div></div><div class="ev">{evtxt}</div></div>')
        legend = "".join(f'<span><i style="background:{TIER_COLOR[k]}"></i>{k}: {v}</span>' for k, v in TIER_HELP.items())
        html(f"""
        <div class="card">
          <div class="label">What Dioscorides prescribes it for · and what modern sources say</div>
          {''.join(items) if items else '<div class="note">No uses extracted.</div>'}
          <div class="legend">{legend}</div>
        </div>""")

# ---------------------------------------------------------------- chance test
with tab_chance:
    ct = R / "chance_test.json"
    if ct.exists():
        d = json.loads(ct.read_text())
        m = d["meta"]
        html(f"""
        <div class="lead">If Dioscorides' prescriptions were guesses, they should match modern findings no more often than
        the same prescriptions shuffled at random between plants. We tested that on <b>{m['n_plants']}</b> confidently
        identified plants and <b>{m['n_pairs']}</b> plant-use pairs, with {m['n_perm']:,} shuffles.</div>
        <div style="height:1rem"></div>""")
        cols = st.columns(2, gap="large")
        for col, name, label in ((cols[0], "cross_cultural", "Agrees with five other medical traditions"),
                                 (cols[1], "literature", "Agrees with the modern literature (PubMed)")):
            v = d[name]
            sig = v["p_value"] < 0.05
            pill = (f'<span class="pill" style="background:#e3eedc;color:{HERB}">significant · p {"< 0.001" if v["p_value"] < 0.001 else "= " + format(v["p_value"], ".3f")}</span>' if sig
                    else f'<span class="pill" style="background:#f4e9cf;color:#8a6414">{"borderline" if v["p_value"] < 0.1 else "not significant alone"} · p = {v["p_value"]:.3f}</span>')
            with col:
                html(f"""
                <div class="card">
                  <div class="label">{label}</div>
                  <div class="big">{v['observed']:.1%}</div>
                  <div class="vs">of uses match, against <b>{v['null_mean']:.1%}</b> by chance (×{v['enrichment']})</div>
                  <div style="margin-top:.7rem">{pill}</div>
                </div>""")
        st.image(str(R / "chance_test.png"), width="stretch")
        html(f"""<div class="card"><div class="note">How the shuffle works: each plant keeps its number of uses and each disease category keeps
        how often it appears overall, so popular categories such as inflammation get no unfair advantage. Only the
        pairing of plant and category is randomised.<br><br><b>Reading it honestly:</b> on the complete text both comparisons beat
        chance, but the effect is modest (about 1.1 times chance). Earlier, smaller runs disagreed: Books 3 and 4 alone favoured
        the traditions, and a run missing 199 chapters favoured only the literature. We show every stage rather than the best one. Plants studied <i>because</i> of their
        traditional reputation can inflate the literature figure (circularity).</div></div>""")
    else:
        st.info("Run `python src/chance_test.py` first.")

# ---------------------------------------------------------------- overview
with tab_stats:
    tiers = (pd.Series([u.get("evidence", {}).get("tier", "n/a") for u in uses_all]).value_counts()
             .reindex(["A", "B", "C", "D", "n/a"]).fillna(0).reset_index())
    tiers.columns = ["tier", "uses"]
    cats = pd.Series([u.get("category") for u in uses_all]).value_counts().head(12).reset_index()
    cats.columns = ["category", "uses"]
    a, b = st.columns(2, gap="large")
    with a:
        html('<div class="label">Evidence tier of every extracted use</div>')
        ch1 = alt.Chart(tiers).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
            x=alt.X("tier:N", sort=None, title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("uses:Q", title=None),
            color=alt.Color("tier:N", scale=alt.Scale(domain=list(TIER_COLOR), range=list(TIER_COLOR.values())), legend=None),
            tooltip=["tier", "uses"]).properties(height=300)
        st.altair_chart(ch1.configure_view(strokeWidth=0).configure(background="transparent")
                        .configure_axis(grid=False, labelColor=MUTED, domainColor=LINE, tickColor=LINE), width="stretch")
    with b:
        html('<div class="label">What the uses treat · top 12 categories</div>')
        ch2 = alt.Chart(cats).mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6, color=HERB).encode(
            y=alt.Y("category:N", sort="-x", title=None), x=alt.X("uses:Q", title=None),
            tooltip=["category", "uses"]).properties(height=300)
        st.altair_chart(ch2.configure_view(strokeWidth=0).configure(background="transparent")
                        .configure_axis(grid=False, labelColor=MUTED, domainColor=LINE, tickColor=LINE, labelLimit=220),
                        width="stretch")
    def pct(x):
        return "" if x is None else f"{x:.0%}"

    ev_path = R / "evaluation.json"
    if ev_path.exists():
        ev = json.loads(ev_path.read_text())
        rows_ = "".join(
            f"<tr><td>{m}</td>" + "".join(f"<td>{pct(v['acc'])}</td>" for v in res.values()) + "</tr>"
            for m, res in ev["methods"].items())
        html(f"""
        <div class="card">
          <div class="label">Identification accuracy against the gold set · n = {ev['n_gold']}</div>
          <table style="width:100%;border-collapse:collapse;font-size:.9rem">
            <tr style="color:{MUTED};text-align:left"><th>method</th><th>genus, top 1</th><th>genus, top 3</th>
            <th>species, top 1</th><th>species, top 3</th></tr>{rows_}
          </table>
          <div class="note" style="margin-top:.6rem">{e(ev.get('warning', ''))}</div>
        </div>""")

# ---------------------------------------------------------------- about
with tab_about:
    md = (ROOT / "docs/method.md").read_text(encoding="utf-8") if (ROOT / "docs/method.md").exists() else "See README.md."
    st.markdown(md)
    html('<div class="note" style="margin-top:1rem">Research prototype. A literature signal is not evidence that a plant works, '
         'and nothing here is medical advice. Several plants in this text are lethal.</div>')
