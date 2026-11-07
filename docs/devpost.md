# MateriaLink — Devpost submission draft

**Tagline (under 200 characters):** We read Dioscorides' 2,000-year-old pharmacology in the original Greek, linked every plant to modern science, and tested whether his remedies beat chance.

**Track:** 1, Traditional knowledge and historical texts.

**Links:** website https://aryanmashalkar.github.io/MateriaLink/ · analysis app https://materialink-dioscorides.streamlit.app · code https://github.com/AryanMashalkar/MateriaLink · video: (add YouTube link)

## Inspiration

For about 1,500 years, *De materia medica* by Dioscorides (1st century CE) decided what doctors in Europe and the Mediterranean prescribed. It is still cited by ethnopharmacologists, but almost nobody reads it as data: it is in ancient Greek, and its plant names don't map cleanly onto modern species. We wanted to turn the book into something a scientist, a student or a curious reader with no Greek can use, and then ask it a falsifiable question: **were Dioscorides' uses right more often than chance would predict?**

## What it does

For each of the 623 chapters of the Greek text, MateriaLink gives you:

- the Greek name, how to say it, and **what it means in English** (κώνειον means hemlock);
- a **plain-English summary** of the chapter;
- the **most likely modern species**, with a probability and the alternatives scholars could argue for (we flag disputed chapters instead of hiding them);
- the **chemical compounds** recorded in that plant (LOTUS and COCONUT);
- **every use Dioscorides gives**, as the Greek phrase plus an English gloss, each checked against PubMed co-mentions (evidence tiers A to D, with links to the papers) and against five living medical traditions (Indian, Korean, Chinese, Vietnamese, West African).

Then a **permutation test** shuffles his prescriptions between plants 10,000 times and asks whether the real pairing matches modern findings more often than the shuffled ones.

## Results

- 623 chapters, 374 plants, 293 pinned to a species, 1,625 uses extracted, 390 with a PubMed signal.
- **Literature:** 23.8% of his uses match, against 21.9% by chance (×1.09, p = 0.025, 268 plants).
- **Other traditions:** 23.3% against 22.3% (×1.05, p = 0.13).
- On Books 3 and 4 alone the two results were reversed (traditions p = 0.044, literature p = 0.052). We report both. The honest reading is a modest signal that is better than chance, not strong evidence on either measure alone.
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
- **Honest statistics.** When we added Books 1, 2 and 5, the significant result moved from one comparison to the other. It would have been easy to report only the better one. We didn't.
- **No gold standard.** Published identifications of Dioscorides plants are scattered and disputed. We refused to have the model label its own test set, because that would be circular.
- **Readers without Greek.** We added English names for all 623 chapters, plain-English summaries, and English glosses for every use, so the Greek is there for those who want it but nobody needs it.

## What we learned

A traditional text can be tested, not just admired, as long as you keep each step traceable (URN, cached model output, PubMed ID) and say plainly what a co-mention does and does not prove.

## Limits

A PubMed co-mention is a signal, not proof that a plant works. Some plants were studied because of their reputation, which inflates the literature match. Identifications are disputed. The parser stops early in Books 1 and 2. Several plants here (hemlock, aconite, mandrake, henbane) are lethal: nothing here is medical advice.

## Use of generative AI

The extraction step (candidate species, uses and English glosses) was produced by Claude (Anthropic) with the prompt in `prompts/extract_v1.txt`; every raw output is kept in `data/llm_cache/`. Generative AI also helped write code. English common names in `data/editorial/` were written by the team. All results were checked by the team.

## What's next

Finish parsing Books 1 and 2, complete the two-annotator gold set with scholars, add the Byzantine and Arabic translations of Dioscorides as further layers, and open the gold set for corrections.

## Built with

python, streamlit, altair, pandas, javascript, svg, github-pages, claude, first1kgreek, lotus, coconut, ncbi-taxonomy, pubmed
