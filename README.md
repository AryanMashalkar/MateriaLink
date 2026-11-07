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

## Headline results (Books 3 and 4, 292 chapters)

| | |
|---|---|
| Chapters processed | 292 (290 plants) |
| Plant chapters whose top identification resolves to a species | 229 |
| Therapeutic uses extracted | 1,237 |
| Uses with a PubMed literature signal (tiers A to C) | 282 |

**Better than chance?** For 211 confidently identified plants (691 plant-use pairs) we compared the real assignment of disease categories with 10,000 random reshuffles that keep each plant's number of uses and each category's overall frequency.

| Reference | Dioscorides | Chance | Enrichment | p |
|---|---|---|---|---|
| Independent traditions (IMPPAT, KTKP, ETM, VietHerb, Ewé) | 18.8% | 17.1% | ×1.10 | 0.044 |
| Modern literature (PubMed co-mentions, BERN2) | 23.9% | 22.1% | ×1.08 | 0.052 |

The effect is real but modest. We report it as it is: a small, consistent signal, stronger against other traditional systems than against the literature. See `results/chance_test.png`.

**Identification accuracy.** `src/evaluate.py` scores the spelling-only baseline against the model on a hand-curated gold set (top-1 and top-3, genus and species, bootstrap 95% CIs, Cohen's kappa between annotators, calibration error). The gold set currently holds 6 published identifications (Touwaide, *Pharmantica*, Solanaceae) and 54 chapters awaiting two independent annotators, so current numbers are illustrative only. On those 6 rows: baseline 1/6 at genus level, model 5/6 at species level.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
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
```

## How it works

1. **Parse** (`src/parse_tei.py`): the Wellmann edition from First1KGreek, split into 623 chapters with CTS URNs (`urn:cts:greekLit:tlg0656.tlg001.1st1K-grc1:4.78`), headwords and the synonyms Dioscorides records.
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
- **Coverage.** Books 3 and 4 (the herbal core) are processed; Books 1, 2 and 5 (aromatics, trees, animals, wines, minerals) are parsed but not yet extracted.
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
src/                       pipeline scripts
prompts/extract_v1.txt     extraction prompt
data/raw/                  Greek TEI
data/external/enveda/      grounding and evidence tables
data/processed/            chapters, predictions, enriched records
data/llm_cache/            raw model outputs (provenance)
data/gold/gold.csv         gold set (fill in and rerun evaluate.py)
results/                   chance test, evaluation, figures
docs/                      method notes, pitch and video outline
```
