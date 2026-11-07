# MateriaLink

**Reading Dioscorides in Greek and asking, with statistics, whether he was right.**

*De materia medica* (Dioscorides, 1st century CE) was the core pharmacology text of Europe and the Mediterranean for about 1,500 years. MateriaLink reads the original Greek, chapter by chapter, and links each entry to modern science:

```
Greek chapter (CTS URN)
  -> candidate plant identifications, each with a confidence
  -> accepted name and NCBI taxon
  -> compounds known from that plant (LOTUS / COCONUT)
  -> each use Dioscorides gives, checked against PubMed and five other ethnomedicine traditions
```

Then it asks one question no concordance has asked before: **do Dioscorides' uses line up with modern findings more often than chance would predict?**

## Headline results (all five books, 822 chapters)

| | |
|---|---|
| Chapters processed | 822 (570 plants; the rest are animals, wines, minerals and prepared products) |
| Plant chapters whose top identification is a named species | 478 |
| Therapeutic uses extracted | 2,471 |
| Uses with a PubMed literature signal (tiers A to C) | 646 |
| Chapters with an English name and a plain-English summary | 822 |
| Chapters tagged with how the remedy was given (drunk, poultice, in wine ...) | 681 |

**Better than chance?** For 422 confidently identified plants (1,370 plant-use pairs) we compared the real assignment of disease categories with 10,000 random reshuffles that keep each plant's number of uses and each category's overall frequency.

| Reference | Dioscorides | Chance | Enrichment | p |
|---|---|---|---|---|
| Modern literature (PubMed co-mentions, BERN2) | 26.4% | 23.3% | ×1.13 | < 0.001 |
| Independent traditions (IMPPAT, KTKP, ETM, VietHerb, Ewé) | 24.2% | 22.6% | ×1.07 | 0.025 |
| Literature, only plants the PubMed table covers (229 plants) | 44.2% | 39.3% | ×1.12 | < 0.001 |

The result changed as the text grew, and we report every stage rather than pick one. A first run on Books 3 and 4 only (211 plants): traditions significant (×1.10, p = 0.044), literature just missed (×1.08, p = 0.052). All five books, before we fixed the parser (268 plants): literature significant (×1.09, p = 0.025), traditions not (×1.05, p = 0.13). The complete text (422 plants, above): both significant. The honest reading: Dioscorides' uses match modern findings more often than chance, the effect is real but modest (about 1.1 times chance), and part of the literature gain may come from the newly added trees, fruits and vegetables, which are well-studied food plants. See `results/chance_test.png`.

**Identification accuracy.** `src/evaluate.py` scores the spelling-only baseline against the model on a hand-curated gold set (top-1 and top-3, genus and species, bootstrap 95% CIs, Cohen's kappa between annotators, calibration error). The gold set currently holds 6 published identifications (Touwaide, *Pharmantica*, Solanaceae) and 54 chapters awaiting two independent annotators (`data/gold/annotation_sheet.csv`, instructions in `data/gold/README.md`), so current numbers are illustrative only. The model did not fill these rows: scoring a system against its own answers would be circular. On those 6 rows: baseline 1/6 at genus level, model 5/6 at species level.

**Explore it: https://aryanmashalkar.github.io/MateriaLink/** (interactive site)  
**Analysis app: https://materialink-dioscorides.streamlit.app**

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py              # analysis app
python src/export_site.py         # refresh docs/data.json for the static site in docs/
```

All processed data is in the repo, so the app runs without any API key.

## Reproduce from scratch

```bash
python src/parse_tei.py                    # Greek TEI -> data/processed/chapters.jsonl
python src/baseline.py                     # fuzzy transliteration baseline
# model extraction (cached outputs used for the demo are in data/llm_cache/claude_agent_v1/)
python src/extract_llm.py --provider anthropic --model <model> --books 3 4 --run my_run
python src/extract_llm.py --collect --run my_run
python src/enrich.py                       # taxa, compounds, evidence tiers
python src/chance_test.py --n 10000        # permutation test
python src/evaluate.py                     # accuracy, kappa, calibration
python src/export_site.py                  # English names, summaries, site data
```

## How it works

1. **Parse** (`src/parse_tei.py`): the Wellmann edition from First1KGreek, split into 822 chapters with CTS URNs (`urn:cts:greekLit:tlg0656.tlg001.1st1K-grc1:4.78`), headwords and the synonyms Dioscorides records.
2. **Baseline** (`src/baseline.py`): the Greek name is transliterated (rough breathing to *h*, initial rho to *rh*, Greek endings to Latin) and fuzzy-matched to 15,992 plant genera. This is what spelling alone can do.
3. **Reading the description** (`prompts/extract_v1.txt`, `src/extract_llm.py`): a language model reads the full Greek description (leaves, flowers, habitat, smell, taste) and returns ranked candidate taxa with probabilities, the parts used, and each use with its Greek phrase, an English gloss and one of the 23 MONDO upper-level disease categories (plus reproductive/obstetric and other). Dosages are deliberately not extracted.
4. **Grounding** (`src/enrich.py`): names are resolved to NCBI taxa; a genus-level answer expands to its member species. Compounds come from LOTUS (preferred) and COCONUT. Each use gets an evidence tier: **A** 5+ PubMed abstracts co-mention plant and disease, **B** 2 to 4, **C** 1, **D** none; plus whether any of five other ethnomedicine databases record the same use.
5. **Chance test** (`src/chance_test.py`): label permutation as described above.
6. **Evaluation** (`src/evaluate.py`): see above.

## Limits, stated plainly

- **Identifications are disputed.** Scholars disagree on many Dioscorides plants. We show several candidates with probabilities and flag a chapter as disputed when the second candidate is at least half as likely as the first.
- **A literature signal is not efficacy.** A PubMed co-mention means a paper mentions the plant and the disease together, not that the plant works.
- **Circularity.** Some plants were studied *because* of their traditional reputation, which inflates the literature match. The cross-cultural comparison is partly independent of this, which is why we report both.
- **Database noise.** LOTUS and COCONUT contain some wrong occurrence records.
- **Coverage.** All 822 chapters of the five books are extracted. (An earlier version stopped at 623 because the TEI file nests some chapters inside the previous one; `src/parse_tei.py` now walks nested chapters.) Animal, mineral and wine chapters get an English name but are left out of the statistics.
- **Missing literature for famous plants.** The BERN2 PubMed table we use has no rows at all for about 40% of our identified plant chapters, including garlic, olive, grape and pomegranate. The site says so on those chapters instead of showing "0 papers". Tier D means "not in this dataset", not "no evidence". As a check we reran the literature test on the 229 confidently identified plants that do have data: 44.2% against 39.3% by chance (×1.12, p < 0.001), so the result does not depend on the gaps.
- **Preparation tags.** "How he prepared it" tags (drunk, poultice, boiled, with wine ...) come from fixed Greek word patterns in `src/preparation.py`, with no model involved. A tag means the word family occurs in the chapter, not that it applies to every use. Doses are deliberately not extracted.
- **Plant photos.** The website loads a modern photo of the most likely species from iNaturalist (or Wikipedia) in your browser, with the photographer's credit. It is for comparison only and is not part of the data.
- **English.** Every chapter has an English name and a plain-English summary built only from the extracted data, and every use carries an English gloss of its Greek phrase. This is not a full literary translation; for that see Beck (2005) or Osbaldeston (2000). Common names are in `data/editorial/` and were written by us.
- **Not medical advice.** Several plants here (hemlock, aconite, mandrake, henbane, hellebore) are lethal.

## Use of generative AI (disclosure)

The extraction step in `data/llm_cache/claude_agent_v1/` was produced by Claude (Anthropic), working through an agent session with the prompt in `prompts/extract_v1.txt`, and written in a compact format converted by `src/compact_to_cache.py`. Every raw output is kept in the repo. `src/extract_llm.py` re-runs the same step through the Anthropic, Gemini or any OpenAI-compatible API. Generative AI also assisted in writing code. All results were checked by the team; corrections go into `data/gold/gold.csv`.

## Data and licences

| Source | Use | Licence |
|---|---|---|
| Dioscorides, *De materia medica*, ed. Wellmann, via [First1KGreek](https://github.com/OpenGreekAndLatin/First1KGreek) (`tlg0656.tlg001.1st1K-grc1`) | Greek text | CC BY-SA 4.0 |
| [enveda/ethnobotany](https://github.com/enveda/ethnobotany): Trefle grounding, LOTUS/COCONUT plant-compound pairs, BERN2 PubMed plant-disease co-mentions, IMPPAT/KTKP/ETM/VietHerb/Ewé, MONDO categories | Grounding and evidence | MIT |
| Touwaide, *Pharmantica*, Solanaceae (medimanus.chs.harvard.edu) | 6 gold identifications | cited |

Code is MIT. Everything derived from the Greek text (processed data, model outputs, gold set) is CC BY-SA 4.0. See `LICENSE`.

## Traditional knowledge

*De materia medica* is a published text in the public domain, not knowledge held by a living community. The five comparison databases record knowledge of living traditions (Indian, Korean, Chinese, Vietnamese and West African). We use only their published, aggregated records, cite them, and make no commercial claim on any use.

## Repository layout

```
app.py                     Streamlit demo
src/                       pipeline scripts (preparation.py: Greek route and vehicle tags, no doses)
prompts/extract_v1.txt     extraction prompt
data/raw/                  Greek TEI
data/external/enveda/      grounding and evidence tables
data/processed/            chapters, predictions, enriched records
data/llm_cache/            raw model outputs (provenance)
data/gold/gold.csv         gold set (fill in and rerun evaluate.py)
results/                   chance test, evaluation, figures
docs/                      method notes, pitch and video outline
```
