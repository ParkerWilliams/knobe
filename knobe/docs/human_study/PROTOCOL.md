# Human Replication Protocol — Ngo Extensions (drafted 2026-09-13)

**Status:** design document, not yet submitted for review. Doubles as the
study-description section of an IRB exempt application. Costs from
`analysis/human_study/cost_model.py` (`d8d2170`); item structure verified
against the committed authored datasets.

**Two arms, run as one study.** Running them together pays IRB, instrument
build, and piloting costs once instead of twice; participant payment is
unchanged either way.

| arm | items | question | buys |
|---|---:|---|---|
| **A. Moral vs. nonmoral** | 240 | blame | Direct human test of CLAIMS.md **C3**, the LLM paper's most striking and least secure claim |
| **C. Moral foundations** | 152 | intentionality | Standalone contribution — whether the Knobe effect extends past harm has never been tested in humans |

---

## 1. Two instrument problems found during design

Both would have damaged the study if carried over unexamined.

### 1.1 The intentionality question needs scale anchors for humans

The LLM elicitation frame is:

> Read carefully the following scenario and then answer the question with a
> number from 0 to 10.
>
> Scenario: {scenario}
>
> Question: {question}

Blame and praise carry their own anchors inside the question text ("on a
scale from 0 (not at all) to 10 (extremely)"). **Intentionality does not** —
it reads "Did Bill intentionally cause the death of babies?", a yes/no
question answered on an unanchored 0–10 scale.

A language model will emit a number regardless. Humans given an unanchored
0–10 scale on a yes/no question will either pile up at the endpoints or ask
what the middle means, and the resulting distribution will not be comparable
to anything.

**Decision: add anchors for the human version** — "0 (definitely not) to 10
(definitely yes)" — and report the deviation explicitly. The alternative,
exact instrument fidelity, buys a comparison to LLM numbers that human
responses would not support. Note the direction of the compromise in the
paper: human and LLM intentionality scales are anchored differently, so
**compare patterns and contrasts, not raw means**, across species.

This does not affect arm A, whose blame question is already anchored.

### 1.2 Storylines span conditions, so counterbalancing is on `pair_id`

Neither set is a flat list of independent items.

- **Nonmoral:** 40 storylines × 3 framings × 2 signs = 240. One `pair_id`
  covers the moral, prudential, and procedural framings of the same
  scaffold, in both signs.
- **Foundations:** 34 `pair_id`s covering 152 items — 18 with 4 items, 12
  with 6, 4 with 2. A single scaffold appears as its harm control *and* as
  one or more foundation variants, in both signs. (Example: `pair_id` 01
  yields harm-01-bad/good, loyalty-01-bad/good, authority-01-bad/good.)

A participant who sees two items from the same `pair_id` sees the same
scenario twice with one element swapped, which reveals the manipulation.

**Rule: at most one item per `pair_id` per participant.** With 74 `pair_id`s
total and 30 ratings per session, this is comfortably satisfiable and is
enforced by the block generator rather than by per-participant randomization.

---

## 2. Design and sample size

| | value |
|---|---|
| Items | 392 (240 nonmoral + 152 foundations) |
| Ratings per item | 10 (pilot-calibrated — see §5) |
| Total ratings | 3,920 |
| Ratings per session | 30, max one per `pair_id` |
| Participants | ~131 |
| Session length | ~15.5 min |
| **Cost** | **~$540** main + **~$80** pilot |

Rating count is deliberately modest. This project's own ICC analysis
(`23_icc_variance_decomposition.py`) found design effects of 6–160×, meaning
clusters buy power and within-cluster samples have sharply diminishing
returns. The binding constraints are 40 storylines and 34 foundation
scaffolds, not raters per item. Past ~15 ratings per item you are buying
precision the cluster structure cannot use.

**Run the authored sets (240 / 152), not the post-curation subsets
(196 / 126).** This is the design decision with the highest incidental
payoff: the LLM paper's outstanding confound is that the moral-good cell lost
65% of its items to curation and the provenance files needed to characterize
what was dropped are missing. Rating all 40 authored moral-good items gives
that comparison directly — do the 14 retained differ from the 26 dropped on
human blame? — and converts a blocked, person-dependent gate into something
under your control.

### Optional module: praise (+$330)

Arm A as specified collects blame only. Adding praise on the same 240 items
would:

1. Complete the stakes test in humans. In the LLM data the absence of a
   praise stakes-gradient is what most cleanly rules out a stakes account of
   C3; the human version would be one-sided without it.
2. Turn **C4** — currently the paper's strongest claim — into a direct human
   comparison. C4 presently cites the general negativity-bias literature
   (Baumeister et al.) as the human prior. Collecting praise on these items
   replaces a literature citation with data on the same stimuli.

Recommended if the budget stretches. Decide before the pilot, since it
changes the block structure.

---

## 3. Instrument

Per item, matching the LLM frame except as noted in §1.1:

> Read carefully the following scenario and then answer the question with a
> number from 0 to 10.
>
> **Scenario:** Bill released a gadget to make a deadline. Bill did not care
> at all about the effect the gadget would have on babies. Bill knew his
> gadget would kill babies.
>
> **Question:** How blameworthy is Bill for this, on a scale from 0 (not at
> all) to 10 (extremely)?

Scenario and question text are taken verbatim from the committed authored
CSVs. **Do not re-key them by hand** — export from
`ngo_prudential_dataset.csv` and `mf_pilot_dataset.csv` so the human and LLM
studies provably use identical strings.

Response: 0–10, discrete, radio buttons or slider with labelled endpoints.
No "prefer not to answer" — an unanswered item is an exclusion, not a
category.

---

## 4. Quality controls

**Attention checks.** Two instructed-response items embedded at random
positions ("For this item, select 7"). Fail either → exclude. Pre-register
this rather than deciding after seeing the data.

**Naivety screen.** The 80 Ngo originals in arm A's moral framing are among
the most-run stimuli in experimental philosophy, and the chairman/environment
case is in that set. Purpose-written items (prudential, procedural, all
foundations) carry no exposure risk.

- Use platform-level prior-study exclusion where available.
- Post-task, before debrief: *"Have you encountered scenarios like these in a
  previous study?"* (yes / no / unsure).
- Pre-register excluding self-reported "yes" from primary analyses and
  reporting both corrected and uncorrected results.

**Timing exclusions.** Drop sessions faster than 40% of median completion
time. Do not drop slow responders — there is no principled ceiling.

**Demographics.** Age, gender, education, native-English. Minimal, collected
for reporting only.

---

## 5. Pilot first

n = 20, one block, ~$80. Purposes, in priority order:

1. **Verify the §1.1 anchoring fix works** — inspect the intentionality
   response distribution for endpoint piling or a confused middle.
2. **Timing** — confirm ~25 s/rating. If it runs long, cut ratings per
   session, not ratings per item.
3. **Comprehension** — a free-text "was anything unclear?" item.
4. **Variance estimate** — the number that should set the final ratings per
   item, replacing the default of 10. Human between-item variance on these
   stimuli is unknown and there is no reason it matches the LLM variance
   components.

Do not skip this to save $80. The anchoring question alone justifies it.

---

## 6. Analysis plan

Pre-register before collection. Mirrors the LLM analysis so the comparison is
like-for-like: same effect coding (sign: bad +0.5 / good −0.5; arm: moral
+0.5 / nonmoral −0.5), same clustering on `pair_id`, same wild cluster
bootstrap (Cameron–Gelbach–Miller, Rademacher weights, B = 1999), reusing
`analysis/rq1_v1_1_robustness/lib.py` rather than a reimplementation.

**Primary, arm A (tests C3):**
1. `blame ~ sign_c * arm_c`, term `sign_c:arm_c` — does the moral/nonmoral
   difference in blame depend on sign in humans as it does in models?
2. Good-cell / bad-cell gap decomposition, mirroring
   `domain_gap_decomposition.csv`. **The prediction under C3 is a good-cell
   gap several times the bad-cell gap.**
3. Stakes gradient: `blame ~ stakes_c` within good-sign nonmoral items
   (prudential +0.5 / procedural −0.5), mirroring `stakes_gradient_check.py`.

**Primary, arm C (standalone):**
4. `intentionality ~ sign_c` within harm control and within pooled non-harm,
   plus the `sign_c:arm_c` interaction — does the Knobe asymmetry appear for
   non-harm foundations in humans?
5. Joint 4-df bootstrap-F across all five foundations, mirroring
   `foundation_gradient_wcb.py`.

**Secondary:**
6. Retained-vs-dropped comparison on the 40 authored moral-good items (§2).
7. Per-foundation breakdown, flagged exploratory; purity is underpowered at
   7 pairs by design.

**Corrections.** Holm within (arm, question), matching the LLM convention in
`holm_correct_pilots.py`. Equivalence bounds for any null that carries a
claim, matching `equivalence_bounds.py` — a null across arms means nothing at
these cluster counts without one.

**Model–human comparison.** Patterns and contrasts, not raw means, given
§1.1. Pre-specify this so it cannot look like a post-hoc retreat.

---

## 7. IRB notes

Anonymous adult participants rating hypothetical third-party vignettes on
Likert scales, no deception, no sensitive personal data, no intervention.
This is the standard shape for an **exempt** determination under 45 CFR
46.104(d)(2) (benign behavioural interventions / survey procedures). Confirm
the category with your own IRB rather than assuming it.

Points reviewers typically ask about, pre-answered:

- **Compensation:** ~$12/hr equivalent, at or above platform-recommended
  rates.
- **Content:** vignettes reference hypothetical harms (including harm to
  infants, in the Ngo originals). Flag this in the consent text. It is
  published, widely-used stimulus material, which is worth stating.
- **Data:** no identifiers collected; platform IDs used only for payment and
  not retained in the analysis dataset.
- **Withdrawal:** participants may exit at any point and are paid for
  completed work.

If a collaborator holds an existing behavioural protocol, an amendment is
usually faster than a new application. Worth checking before filing fresh.

---

## 8. Open decisions

1. **Praise module** (§2) — +$330, recommended. Decide before the pilot.
2. **Platform** — Prolific recommended over MTurk, primarily for the naivety
   problem in §4.
3. **Instrument host** — Qualtrics is familiar; Gorilla handles the §1.2
   blocking natively and will be less work. Either is fine.
4. **Ratings per item** — set from the pilot, not from the default of 10.
5. **Foundations blame/praise** — not collected here, since the LLM side
   never collected it either. Adding it to the human study would create an
   asymmetry the paper would have to explain. **Revisit (2026-09-25):** the
   LLM-side foundations blame/praise elicitation is now staged (gameplan
   item 6); once it runs, this reasoning inverts.
