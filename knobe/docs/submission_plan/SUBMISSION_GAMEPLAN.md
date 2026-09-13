# Submission Gameplan (2026-09-13)

**Status:** working plan, revised as claims clear or fail their gates. This
document answers "what do we submit, where, and in what order" — it does not
restate results. For the numbers themselves see
`docs/rq1_findings/RQ1_STATISTICAL_METHODS_v1.1.md` (main run) and
`docs/rq1_findings/ALIGNMENT_DISCUSSION_ngo_pilots.md` (both pilots); point
numbers below refer to that draft's numbering.

**Provenance for the audits this plan's rankings turn on:**
`analysis/ngo_extensions/measurement_selection_audit.py`, commit `395a9ed`
(`outputs/measurement_audit.csv`, `outputs/selection_attrition.csv`);
`analyze_sign_wcb.py --score parsed`, commit `6c73ab6`
(`outputs/sign_wcb*_parsed.csv`); `blame_praise_swing.py`, commit `244db46`
(`outputs/blame_praise_swing.csv`, `outputs/question_cell_means.csv`).

**2026-09-13 — §5 items 1 and 2 are done, and they changed the paper.** The
parsed-rating substitution flipped 14 of 30 q_intentionality cells and 0 of
30 q_praise cells. Net effect: the intentionality claims got simpler and
better, not worse. Under correct scoring the asymmetry is **domain-general**
— not moral-specific (nonmoral pilot) and not harm-specific (MF pilot) — in
every family, replacing the draft's three-way cross-model disagreement.
Rankings below are revised accordingly; see
`ALIGNMENT_DISCUSSION_ngo_pilots.md`'s correction note for what that
supersedes.

---

## 1. The framing decision

**The pilots are the paper. The main run is the methods backbone.**

The v1.1 main run's headline RQ1a comparison is confounded by a stimulus
manipulation failure that no amount of modeling fixes (MB exceeds NMB on
severity in 21 of 21 storylines, mean gap 5.42 —
`RQ1_MECHANISM_ANALYSIS_v1.1.md` §1). The pilots are built on Ngo's own
storylines, carry the genuinely novel multi-construct finding, and sidestep
that confound. The main run contributes the typicality reversal (RQ1c), the
wild-cluster-bootstrap machinery, and the measurement lesson.

There is currently no manuscript of any kind in this repo. The distance to a
submission is mostly writing, not analysis — which is why the worklist in §5
puts drafting in parallel with the one analysis task that gates everything.

---

## 2. Claim inventory, ranked

Ranked by how much survives review as of today, not by how interesting they
sound. "Gate" means the specific thing that has to be true before the claim
is citable.

### Rank 1 — Blame-vs-praise sensitivity on identical items (point 6)

Each family's blame swing compared against its own praise swing, same
vignettes. The negativity-bias prediction from the human literature
(Baumeister et al., "bad is stronger than good") holds in llama only; gemma
and mistral swing harder on praise, mistral by 3.76 vs. 0.80 on moral items.

This is the strongest claim in the project, for reasons the others don't
share:

- **Within-item.** Both questions are asked of the same vignettes, so item
  composition, severity, and curation selection are all differenced out
  exactly. No matching argument is needed because nothing is being matched.
- **Best-measured cells in the project.** Finetuned blame/praise
  `ev_rating`/`parsed_rating` agreement is r = .56–.82 (§3 below), well
  above the main run's instruct intentionality (.44–.50).
- Finetuned-only, so the pretrained scoring caveat never arises.
- Survives Holm within (family, tuning, question).

**Gate — CLEARED 2026-09-13** (`244db46`), and it changed the answer. The
scale check mattered: EV is a logprob-weighted mean whose compression depends
on a per-question logprob distribution, so it is the wrong scale for a
cross-question magnitude comparison, and the instability shows up directly —
under EV the raw and SD-standardized verdicts disagree in 2 of 6 cells, under
parsed they agree in 6 of 6. **Report point 6 under `parsed`, not as a
robustness check but as the primary scale.** Corrected claim: the
negativity-bias prior holds for **gemma and llama** in both domains, with
mistral reversed — not "llama only."

| family | arm | blame | praise | bigger |
|---|---|---:|---:|---|
| gemma | moral | 1.81 | 1.11 | blame |
| gemma | nonmoral | 5.62 | 2.76 | blame |
| llama | moral | 1.61 | 0.76 | blame |
| llama | nonmoral | 4.73 | 2.54 | blame |
| mistral | moral | 1.48 | 3.39 | praise |
| mistral | nonmoral | 3.74 | 4.92 | praise |

All twelve swings are individually significant. Mistral inverting the
negativity-bias prior while two families obey it is the claim.

### Rank 2 — Foundation gradient, finetuned only (point 2b)

Joint 4-df wild cluster bootstrap-F over all five foundations per cell.
mistral-finetuned `p_wcb=.672` — the sign effect is statistically
indistinguishable across harm, loyalty, authority, fairness, and purity.
gemma (.049) and llama (.060) sit on opposite sides of the line.

The MF pilot's design is clean on the axis that damages the nonmoral pilot:
pair-level gating kept every cell perfectly sign-balanced (§3). Nothing in
the published Knobe-in-LLMs literature tests beyond harm, because neither
Ngo's nor Raimondi's paradigm leaves it.

**Strengthened 2026-09-13.** Under parsed scoring gemma's
harm-vs-non-harm interaction — the one significant finetuned cell, and the
only thing standing against "harm isn't special" — goes β=−1.24 (p=.012) →
−0.30 (p=.70). **No family now shows a significant harm-vs-non-harm
interaction**, and mistral's two primary arms both hold. The claim is
unanimous across three families rather than 2-of-3 with gemma dissenting.

**Gates, both reportable-with-caveat rather than blocking:**

- Frame the nulls as equivalence results, not absence of heterogeneity. A
  null joint F at G=26–30 is weak evidence *for* homogeneity on its own. Use
  the Bloom (2006) MDE machinery from `rq1_v1_1_robustness/09` + `15` —
  already used this way in `RQ1_STATISTICAL_METHODS_v1.1.md` §9.3 — and
  report "heterogeneity above X is ruled out." This now carries more weight,
  since the claim rests on three nulls rather than one.
- ~~Re-run the joint foundation-gradient F-test under parsed scoring~~ —
  DONE 2026-09-13, `70f1a34`. It adds one nuance: gemma-finetuned still shows
  significant heterogeneity across the five foundations (p=.043, the only
  cell significant under both scorings), even though its harm-vs-pooled-non-harm
  interaction is null. Pooling four foundations into one arm can hide
  variation among them. So state the claim as "the asymmetry is not
  privileged for harm," not "it is uniform across foundations."
- Pretrained foundation heterogeneity is resolved, and it was mostly
  artifact: gemma .011 → .295 and llama <.001 → .233 both vanish under
  parsed, leaving only mistral-pretrained. The draft's "all three pretrained
  cells, new and unexplained" was reading the EV artifact.

### Rank 3 — The asymmetry is domain-general (replaces old Rank 4)

**New as of 2026-09-13, and it is the direct product of refuting the old
Rank 4.** Under parsed scoring, no family shows a significant
moral-vs-nonmoral interaction on intentionality, and no family shows a
significant harm-vs-non-harm interaction. Every finetuned family shows a
large bad>good asymmetry in *every* arm tested — moral, prudential,
procedural, harm, loyalty, authority, fairness, purity.

Paired with Rank 2, this is one claim rather than two: the Knobe asymmetry
these models acquire under instruction tuning is **not specific to morality
and not specific to harm**. That is a cleaner and more surprising result than
the draft's three-way cross-model disagreement, and it is a sharper contrast
with the human literature, where moral-specificity is the live debate.

**Gates:**

- Inherits Rank 4's severity and attrition problems, since it is still an
  arm-vs-arm comparison. The difference is that the claim is now a null
  across arms, and the severity confound would have to *manufacture* a null
  to explain it away — a harder story to tell than manufacturing a
  difference. State it that way.
- Equivalence framing, as in Rank 2. "No significant interaction" at these
  cluster counts needs an MDE to mean anything.

### Rank 4 — Construct divergence (point 7), reduced

Blame and praise no longer disagree in direction. Point 5's "praise leans
the opposite way from blame" was a sign-convention error: `arm_c` is +0.5
moral / −0.5 nonmoral, so `sign_c:arm_c` = β_moral − β_nonmoral, and praise's
`sign_c` betas are negative, so a positive praise interaction means a
*smaller* magnitude swing in the moral arm. Praise swings bigger outside
morality in all three families under both scorings, the same direction as
blame.

What remains is real but narrower: blame and praise agree on direction and
disagree on magnitude (Rank 1), and intentionality — once correctly scored —
shows no domain effect at all where blame and praise both show a large one.
That last contrast is the defensible version of "these constructs are not
interchangeable," and it is worth a paragraph rather than a section.

### Rank 5 — Finetuning as the causal lever (point 1)

The 6/6 pretrained-null / finetuned-large pattern across three
architectures. Most headline-sounding, most exposed: every pretrained cell
is scored by `_logit_ev_rating`, the function script 35 proved manufactures
significant wrong-direction effects at low parse rate, and pretrained
agreement here is r = .026–.227.

**Gate — partly cleared 2026-09-13, and the answer is "split by family."**
Parsed scoring does not rescue a uniform pretrained null. llama-pretrained
keeps a large significant *reversed* nonmoral effect (β=−0.88, p<.0001);
mistral-pretrained's reversal goes null; gemma-pretrained stays marginal.
The finetuned side is unaffected and large everywhere. So the defensible
claim is "the asymmetry is finetuned-large and pretrained-inconsistent,"
which still supports instruction tuning as the lever but drops the clean 6/6
framing. The pretrained cells also parse at 25.5–29.9% for blame and praise,
so per-family pretrained claims stay thin regardless of scoring.

### Carried from the main run

- **Typicality runs backwards from humans** (gemma, mistral; RQ1c). Survives
  WCB, an independent random-slope model, and parsed-rating substitution.
  The most robust result in the main run and the one main-run claim that
  belongs in the paper unmodified.
- **Methodological pair:** logit-fallback EV scoring manufacturing spurious
  effects, and Wald/LRT overconfidence at G=21–84 in exactly the cells WCB
  rejects. Directly transferable to anyone scoring LLM Likert responses from
  logprobs. This is a section, not a footnote — and as of 2026-09-13 it is
  arguably the strongest contribution in the paper. The main run showed the
  artifact on one cell; the pilots now show it flips **14 of 30**
  q_intentionality cells while leaving all 30 praise cells untouched, on the
  same items, in the same run, differing only by question wording. The
  generalizable claim is that logprob-EV scoring is safe exactly where the
  question elicits a number and unsafe where it doesn't, and that agreement
  with `parsed_rating` — not parse rate — is the diagnostic. gemma-instruct
  parses intentionality *better* than blame (58.1% vs. 53.0%) and still lands
  at r=.180 vs. .823.
- **Mistral does not replicate Raimondi** at the finetuned stage, on two
  independent tests, at a 98.2% parse rate. Needs the cheap diagnostic
  (§5 item 4) before it's a claim rather than a loose end.

### Not going in

- RQ1a moral-specificity as a statistical finding — report as a design
  limitation.
- Evocativeness×sign — construct-invalid manipulation (no affect gap in any
  family) and survives only in gemma, marginally.
- Affect decoupling — never WCB'd or random-slope tested; a lead.

---

## 3. The two audit findings that set these rankings

Both from `measurement_selection_audit.py` (commit `395a9ed`).

### 3.1 The EV-scoring artifact is question-shaped, not just tuning-shaped

`r(ev_rating, parsed_rating)` on parse_ok rows, nonmoral pilot:

| model | q_blame | q_intentionality | q_praise |
|---|---:|---:|---:|
| gemma-2-9b-instruct | **.823** | **.180** | **.761** |
| llama-3.1-8b-instruct | **.656** | **.146** | **.558** |
| mistral-7b-v0.1-instruct | **.773** | **.421** | **.812** |
| gemma-2-9b-pretrained | .178 | .098 | .227 |
| llama-3.1-8b-pretrained | .026 | .138 | .176 |
| mistral-7b-v0.1-pretrained | .039 | .070 | .074 |

MF pilot (q_intentionality only): gemma-instruct .523, llama-instruct .130,
mistral-instruct .530; all three pretrained .059–.094.

The main run only ever framed this artifact as a pretrained/finetuned split,
because it had no reason to look at the question axis. The pilots collect
three question types on identical items, which makes that axis checkable for
the first time. Two consequences:

- Blame and praise ask for a number and get one. Those cells are the
  best-measured in the project, which is what makes Rank 1 safe.
- Finetuned intentionality is measured at or below the pretrained cells where
  the artifact struck. Every intentionality-based claim — Ranks 2, 3, 4, 5 —
  inherits that.

Not a parse-rate story: gemma-instruct parses intentionality *better* than
blame (58.1% vs. 53.0%) and still lands at .180. The forced-scoring vector
fails to track the intentionality answer even when the model gives one.

### 3.2 The nonmoral pilot lost 65% of its moral-good cell to curation

Both pilots authored balanced designs. Post-curation survival, nonmoral
pilot:

| arm | bad | good |
|---|---:|---:|
| moral | **97.5%** (39/40) | **35.0%** (14/40) |
| nonmoral_procedural | 92.5% | 95.0% |
| nonmoral_prudential | 87.5% | 82.5% |

The MF pilot, which switched to pair-level gating mid-curation for exactly
this reason (2026-08-19 log), came out perfectly balanced in every cell
(30/30, 10/10, 9/9, 8/8, 6/6).

Cause is on record: the curation questions "name only the violation pole, so
good-sign items score near zero... regardless of authoring quality"
(2026-08-19 log). The nonmoral pilot kept per-item selection; the MF pilot
did not.

Consequence: every moral-arm coefficient in the nonmoral pilot compares 39
bad items against 14 items selected for scoring highest on moral loadedness.
**This is a third candidate explanation for point 4a's elevated moral-good
blame floor** (6.56–7.05 vs. nonmoral-good 3.98–4.64), alongside severity and
indifference-tracking, and it is the most mechanical of the three. 4a cannot
be cut from the writeup — cutting it removes the acknowledgment, not the
problem.

---

## 4. Venue targets

Deadlines are not listed because they need checking against the current
cycle before any of this is actionable.

| Target | The paper it fits | Fit notes |
|---|---|---|
| **TMLR** | Ranks 1–3 plus the measurement section, heterogeneity intact | Best fit. Claims-matched-to-evidence review rewards exactly this project's strength; three-models-three-answers reads as a finding here rather than as inconclusiveness |
| **AIES / FAccT** | Same evidence, audit framing: auditing one moral construct doesn't transfer to another, and bias must be audited per-model | Lowest additional work — a reframe of the same core |
| **CogSci** | Knobe + Hindriks + foundations + the typicality reversal, psychology-facing | 6 pages, fast, stakes the claim early without spending the full result set |
| ***ACL via ARR** | As TMLR but needs a tighter single story | Rolling submission removes deadline pressure; needs the heterogeneity framed as the finding or reviewers read it as a null result |
| **BlackboxNLP / ICLR** | Only if the mech arm runs | See §6 |

---

## 5. Worklist, in order

### Done

1. ~~**Parsed-rating substitution across both pilots, all cells**~~ — DONE
   2026-09-13, `6c73ab6`. 14/30 q_intentionality cells flip, 5/30 blame (all
   pretrained), 0/30 praise. Refuted old Rank 4, produced new Rank 3,
   strengthened Rank 2, split Rank 5 by family.
2. ~~**Praise scale-comparability check**~~ — DONE 2026-09-13, `244db46`.
   Changed Rank 1's verdict from "llama only" to "gemma and llama," and
   established `parsed` as the primary scale for point 6 rather than a
   robustness check.

### Do next

2a. ~~**Re-run `foundation_gradient_wcb.py` under parsed scoring**~~ — DONE
   2026-09-13, `70f1a34`. Killed two of three pretrained heterogeneity
   results; added the gemma-finetuned nuance to Rank 2.

2b. **MDE / equivalence bounds for Ranks 2 and 3.** Both now rest on nulls
   across arms, which makes the Bloom machinery load-bearing rather than
   nice-to-have.

### Do in parallel

3. **Draft Rank 1**, not claim 1 whole. The spine of the draft should be the
   part that cannot be attacked on item composition; points 3/4/5/7 attach to
   it once their gates clear.

4. **Mistral revision / chat-template check** — compare weight revision tags
   and chat template handling against Raimondi's. An afternoon, and it turns
   "we don't replicate" into either a methodological explanation or a real
   finding.

5. **Recover the four curation provenance files** —
   `moral_relevance_raw.jsonl` + `selection_report.md` (nonmoral),
   `foundation_relevance_raw.jsonl` + `selection_report.md` (MF), from
   whoever ran the 2026-08-19 curation. Promoted from housekeeping to
   blocking by §3.2: these are the only way to check whether the 26 dropped
   moral-good items differ systematically from the 14 that survived.

### Do if bandwidth allows

6. **Severity curation pass over both pilots' items** — ~400 reviewer calls,
   same machinery as the 244+240 already run. Unblocks Rank 4 and firms up
   Ranks 2 and 3. Consider pairing with **Phase 0** of
   `docs/severity_confound/SEVERITY_PILOT_PLAN.md` (the reworded
   severity question), which is pure API cost, needs no new authoring, and
   could partly rehabilitate RQ1a.

7. **Point 4a indifference-clause ablation** — vary "did not care at all
   about X" (present / absent / active concern) holding outcome and domain
   fixed. Small new elicitation on existing items. Only decisive once §3.2's
   selection explanation is ruled out first, which is why item 5 precedes it.

8. **q_blame / q_praise for the MF pilot** — re-elicitation on already-curated
   items. Would extend Rank 1 across foundations and merge Ranks 1 and 2 into
   one paper instead of two half-papers.

### Before any venue submission

9. **State the multiplicity exposure explicitly** (`OUTSTANDING_STATISTICAL_ANALYSIS.md`
   item 9). The mechanism doc is a garden-of-forking-paths document by its own
   description, and the pilots' Holm grouping is a flagged judgment call. The
   clean fix is a preregistered confirmatory run on fresh items — and the ICC
   analysis (design effects 6–160×) already says more families, not more
   samples, is what buys power. Converting two or three Rank 1–2 claims from
   exploratory to confirmed is worth more than any further reanalysis.

---

## 6. Deliberately deferred

- **The mechanistic arm.** `src/knobe/mech/` is ~145 KB of built, tested code
  — activation caching, pretrained→finetuned layer patching, per-layer probes,
  RQ2–RQ4 decomposition — that has never been run on real data (no `acts/`,
  `patch/`, or `mech_report/` anywhere under `results/`). It is the novelty
  ceiling, since Raimondi's paper is itself a mech-interp paper. It is also
  the wrong next step: `pytest -m gpu` has never run against real backends,
  the nnsight slice-0 patch path is flagged as shaky, and the lm-eval
  capability check is still a stub raising `NotImplementedError`. Paper two,
  or after the behavioral paper is submitted.
- **Random-slope ordinal refit** (`OUTSTANDING` item 3). Compute-bound.
  "Ordinal and LMM disagree here" is a respectable limitation to report.
- **RQ1b joint latent-variable model.** SIMEX already ruled out the
  measurement-error explanation; this resolves one cell of one contrast in
  the run that is becoming the backbone rather than the headline.
- **Escalated-severity Phase 1** (`SEVERITY_PILOT_PLAN.md`). Expensive;
  Phase 0 is the cheap part worth reconsidering (item 6).
- **Promoting random slopes into the pipeline** (`OUTSTANDING` item 7).
  Highest-leverage *pipeline* change on the list, and irrelevant to this
  submission.

---

## 7. Open provenance gaps

- The four curation files in item 5. Until they arrive, the 196/240 and
  126/152 selected-item sets are reconstructed by inference — verified against
  logged counts and bit-identical WCB reproduction, but not against the actual
  per-item scores, and with no way to check why any specific item was
  excluded.
- `analyze_sign_wcb.py`'s `--question` flag is documented only in the script
  docstring and `ALIGNMENT_DISCUSSION_ngo_pilots.md`, not in either pilot's
  README or HANDOFF.
