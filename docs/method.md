### Pipeline

1. **Parse** the Wellmann Greek text (First1KGreek TEI) into chapters with CTS URNs, headwords and the synonyms Dioscorides lists (`src/parse_tei.py`).
2. **Baseline**: transliterate the Greek headword and synonyms and fuzzy-match them against 15,992 plant genera (`src/baseline.py`). This is the "spelling only" reference any smarter method has to beat.
3. **Reading the chapter**: a large language model (Claude, Anthropic) reads the full Greek description and returns candidate taxa with probabilities, plant parts, and each therapeutic use with the Greek phrase, an English gloss and a disease category (`prompts/extract_v1.txt`, `src/extract_llm.py`). Every output is cached and versioned.
4. **Grounding**: names are resolved to NCBI taxa; known compounds come from LOTUS/COCONUT; each use is checked against BERN2 PubMed plant-disease co-mentions and five independent ethnomedicine databases (IMPPAT, KTKP, ETM, VietHerb, Ewé) through the enveda/ethnobotany knowledge graph (`src/enrich.py`).
5. **Evaluation** against a hand-curated gold set with two annotators, bootstrap confidence intervals, Cohen's kappa and a calibration check (`src/evaluate.py`).
6. **Chance test**: a label-permutation test asking whether Dioscorides' uses match modern findings more often than random reassignment would (`src/chance_test.py`).

### Limits

- Ancient identifications are often disputed; the app shows several candidates and flags close calls rather than pretending to certainty.
- A PubMed co-mention is a literature signal, not proof that a plant works.
- Plants may have been studied *because* of their traditional reputation, which inflates the literature match (circularity).
- Natural-product databases contain noisy records.
- The model's output was checked by hand only on a sample. Corrections are welcome as pull requests to `data/gold/gold.csv`.
- Not medical advice. Several plants here (hemlock, aconite, mandrake, henbane) are lethal.
