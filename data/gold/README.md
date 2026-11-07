# Gold set

Current state (7 Nov 2026): 59 of 60 chapters filled. annotator1 = Gunther, *The Greek Herbal of Dioscorides* (1934); annotator2 = Osbaldeston, *Dioscorides: De materia medica* (2000), both cited by chapter in `source_citation`. Identifications were transcribed from the books (AI-assisted; team spot check on 7 Nov 2026: 10 random rows x 2 books, 20/20 matched, see `spotcheck.md`), never chosen by the model being evaluated. The original instructions for human annotators follow, for anyone extending the set.

## How to fill it

`gold.csv` is what `src/evaluate.py` scores against. Six rows come from a published source (Touwaide, *Pharmantica*, Solanaceae). The other 54 chapters were drawn at random (seed 7) and need two people to identify them **independently**.

## Rules that keep the test fair

1. **Do not look at MateriaLink's answer first.** Don't open the website, the app or `data/processed/` for these chapters. The sheet deliberately leaves out our identification and English name.
2. Each annotator works alone, on their own copy of `annotation_sheet.csv`.
3. Use a published identification, not a guess. Good sources, in order:
   - L. Beck (trans.), *Pedanius Dioscorides of Anazarbus: De materia medica*, 3rd ed., Olms 2017. Chapter numbers match ours (Wellmann).
   - T. Osbaldeston, *Dioscorides: De materia medica*, IBIDIS 2000 (numbering differs slightly; search by the Greek name).
   - The Pharmantica pages at medimanus.chs.harvard.edu, where they exist.
4. Write the accepted Latin name (for example `Conium maculatum`). If the source gives two options, write both separated by `|`. If it only gives a genus, write the genus.
5. Fill `your_source` (book and page) and `confidence_1to3` (3 = the source is certain).

## Then

Copy annotator 1's names into `annotator1_taxon` and annotator 2's into `annotator2_taxon` in `gold.csv` (same `id`), put the sources in `source_citation`, and run:

```bash
python src/evaluate.py
```

It reports top-1 and top-3 accuracy at genus and species level with bootstrap 95% intervals, Cohen's kappa between the two of you, and a calibration plot. About two hours per person for 54 chapters.

Shortcut: save the two filled sheets as `data/gold/annotator1.csv` and `data/gold/annotator2.csv`, then run
`python src/merge_gold.py data/gold/annotator1.csv data/gold/annotator2.csv` instead of copying by hand.
