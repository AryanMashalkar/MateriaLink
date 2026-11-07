# MateriaLink: slides (10) and video script (about 5 minutes)

Track: 1, Traditional knowledge and historical texts. Also fits Best AI and Scientific Rigor.

## Slides

1. **Title.** MateriaLink: reading Dioscorides in Greek and testing whether he was right. Team names. One image: a manuscript page (public-domain Vienna Dioscorides) next to the app.
2. **The problem.** For 1,500 years *De materia medica* was the pharmacology of Europe. Its ~600 plant chapters are written in Greek, with names that no longer match modern species, so the text is hard to use for science.
3. **What we built.** The pipeline in one line: Greek chapter -> candidate species with confidence -> NCBI taxon -> compounds -> modern evidence per use. Show 4.78 κώνειον -> *Conium maculatum* 0.90 -> coniine.
4. **Spelling is not enough.** Baseline: transliterate and fuzzy-match names. κέστρον -> *Cestrum* (wrong, a New World genus). Reading the description gets *Stachys officinalis*. Gold set: baseline 1/6, model 5/6 (state that n is small and annotation continues).
5. **Honest uncertainty.** Multiple candidates with probabilities; "disputed" flag (στρύχνον μανικόν: *Datura* vs *Atropa*, 0.35 each). Reliability plot.
6. **Linking to modern science.** All five books: 822 chapters, 570 plants, 478 resolved to species, 2,471 uses, 646 with a PubMed signal, 681 chapters tagged with how the remedy was given (no doses). Evidence tiers A to D, with links to the abstracts. Every chapter has an English name and a plain-English summary, so no Greek is needed.
7. **Was Dioscorides better than chance?** The permutation histogram. Complete text, 422 plants: literature 26.4% vs 23.3%, p < 0.001; other traditions 24.2% vs 22.6%, p = 0.025. Earlier runs disagreed (Books 3 and 4 alone: only traditions; five books with the parser bug: only literature). We show all three: a real but modest signal.
8. **Limits.** Disputed identifications, co-mention is not efficacy, circularity, database noise, gaps in the literature data for famous plants (garlic, onion). Not medical advice.
9. **Open and reproducible.** CTS URNs, every model output cached, MIT code, CC BY-SA data, one command to run. Gold set open for scholars to correct.
10. **Next.** Scholar annotation round with the gold set; Byzantine and Arabic translations of Dioscorides as further layers; plug into ETHCSTWIN.

## Video script

- 0:00 to 0:30. Hook: "This book told doctors what to prescribe for 1,500 years. We asked a simple question: was it right more often than chance?"
- 0:30 to 1:15. Problem and data (slide 2), the Greek text on screen.
- 1:15 to 3:00. Live demo on the website. Point out that everything reads in English first ("κώνειον means hemlock") with the Greek underneath. Open 4.78 κώνειον: Greek text and URN, *Conium maculatum* 0.90, coniine in compounds, uses with tiers. Then κέστρον (4.1) to show baseline vs model. Then στρύχνον μανικόν (4.73) for the disputed flag. Search "cough" in the plant index and switch between Books 1 to 5.
- 3:00 to 4:00. Chance test tab: explain the shuffle in one sentence, show both numbers and p-values, say plainly the effect is modest (about 1.1 times chance) and that the result moved as the text grew; show all three stages.
- 4:00 to 4:40. Limits and disclosure of AI use.
- 4:40 to 5:00. What comes next, repository link.
