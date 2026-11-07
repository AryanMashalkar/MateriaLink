# MateriaLink — Devpost submission draft

**Tagline (under 200 characters):** We read Dioscorides' 2,000-year-old pharmacology in the original Greek, linked every plant to modern science, and tested whether his remedies beat chance.

**Track:** 1, Traditional knowledge and historical texts.

**Links:** website https://aryanmashalkar.github.io/MateriaLink/ · analysis app https://materialink-dioscorides.streamlit.app · code https://github.com/AryanMashalkar/MateriaLink · video: (add YouTube link)

## Inspiration

For about 1,500 years, *De materia medica* by Dioscorides (1st century CE) decided what doctors in Europe and the Mediterranean prescribed. It is still cited by ethnopharmacologists, but almost nobody reads it as data: it is in ancient Greek, and its plant names don't map cleanly onto modern species. We wanted to turn the book into something a scientist, a student or a curious reader with no Greek can use, and then ask it a falsifiable question: **were Dioscorides' uses right more often than chance would predict?**

## What it does

For each of the 822 chapters of the Greek text, MateriaLink gives you:

- the Greek name, how to say it, and **what it means in English** (κώνειον means hemlock);
- a **plain-English summary** of the chapter;
- the **most likely modern species**, with a probability and the alternatives scholars could argue for (we flag disputed chapters instead of hiding them);
- **how he prepared it** (drunk, poultice, boiled, in wine, as a pessary ...), taken word for word from the Greek, with doses left out on purpose;
- a **modern photo** of the most likely plant, with the photographer's credit;
- the **chemical compounds** recorded in that plant (LOTUS and COCONUT);
- **every use Dioscorides gives**, as the Greek phrase plus an English gloss, each checked against PubMed co-mentions (evidence tiers A to D, with links to the papers) and against five living medical traditions (Indian, Korean, Chinese, Vietnamese, West African).

Then a **permutation test** shuffles his prescriptions between plants 10,000 times and asks whether the real pairing matches modern findings more often than the shuffled ones.

## Results

- 822 chapters, 570 plants, 478 pinned to a species, 2,471 uses extracted, 646 with a PubMed signal.
- **Literature:** 26.4% of his uses match, against 23.3% by chance (×1.13, p < 0.001, 422 plants).
- **Other traditions:** 24.2% against 22.6% (×1.07, p = 0.025).
- **Robustness:** our PubMed source has no rows for some famous plants (garlic, olive, grape). Rerunning on only the 229 plants it covers gives the same answer (44.2% against 39.3%, ×1.12, p < 0.001).
- The result changed as the text grew, and we show every stage: Books 3 and 4 alone (traditions p = 0.044, literature p = 0.052), five books with a parser bug that dropped 199 chapters (literature p = 0.025, traditions p = 0.13), and the complete text (both significant). The honest reading: better than chance, but modest, about 1.1 times chance.
- **Identification:** on the six published identifications we could find (Touwaide, *Pharmantica*), matching names by spelling gets 1 of 6 right; reading the description gets 5 of 6 to species. That is too few to claim accuracy, so the repository includes a 54-chapter blind annotation sheet and an evaluation script (bootstrap intervals, Cohen's kappa, calibration).

## How we built it

1. **Parse** the Wellmann edition (First1KGreek, CC BY-SA) into chapters with CTS URNs and the synonyms Dioscorides records.
2. **Baseline:** transliterate the Greek name and fuzzy-match it to 15,992 plant genera, to show what spelling alone can do.
3. **Read the description:** a language model (Claude) reads each full Greek chapter, including leaves, flowers, habitat, smell and taste, and returns ranked candidate species with probabilities, the parts used, and each use with its Greek phrase, an English gloss and a disease category. Every raw output is saved in the repository.
4. **Ground** names to NCBI taxa, compounds to LOTUS/COCONUT, uses to BERN2 PubMed co-mentions and to IMPPAT, KTKP, ETM, VietHerb and Ewé (enveda/ethnobotany, MIT).
5. **Test** with label permutation that keeps each plant's number of uses and each category's overall frequency fixed.
6. **Show it** in a static website (vanilla JS and SVG) and a Streamlit analysis app.

## Challenges

- **Spelling lies.** κέστρον looks like *Cestrum*, a New World genus Dioscorides could never have seen; the description says betony. That is why we read descriptions rather than match names.
- **Honest statistics.** As we added chapters, the significant result moved from one comparison to the other and then to both. It would have been easy to report only the best run. We report all three.
- **A hidden parser bug.** The TEI file nests some chapters inside the previous one, so our first parser silently stopped at 623 of 822 chapters. We found it, fixed it, and reran everything.
- **No gold standard.** Published identifications of Dioscorides plants are scattered and disputed. We refused to have the model label its own test set, because that would be circular.
- **Readers without Greek.** We added English names for all 822 chapters, plain-English summaries, and English glosses for every use, so the Greek is there for those who want it but nobody needs it.

## What we learned

A traditional text can be tested, not just admired, as long as you keep each step traceable (URN, cached model output, PubMed ID) and say plainly what a co-mention does and does not prove.

## Limits

A PubMed co-mention is a signal, not proof that a plant works. Some plants were studied because of their reputation, which inflates the literature match. Identifications are disputed. The literature data has gaps for some famous plants (garlic, onion), so a missing signal is not evidence against a use. Preparation tags record how a remedy was given, never how much. Several plants here (hemlock, aconite, mandrake, henbane) are lethal: nothing here is medical advice.

## Use of generative AI

The extraction step (candidate species, uses and English glosses) was produced by Claude (Anthropic) with the prompt in `prompts/extract_v1.txt`; every raw output is kept in `data/llm_cache/`. Generative AI also helped write code. English common names in `data/editorial/` were written by the team. All results were checked by the team.

## What's next

Complete the two-annotator gold set with scholars, add the Byzantine and Arabic translations of Dioscorides as further layers, and open the gold set for corrections.

## Built with

python, streamlit, altair, pandas, javascript, svg, github-pages, claude, first1kgreek, lotus, coconut, ncbi-taxonomy, pubmed
