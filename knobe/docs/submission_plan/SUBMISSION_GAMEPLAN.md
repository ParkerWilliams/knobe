# Submission Gameplan (2026-09-13)

**Status:** working plan, revised as claims clear or fail their gates. This
document answers "what do we submit, where, and in what order" — it does not
restate results. For the numbers themselves see
`docs/rq1_findings/RQ1_STATISTICAL_METHODS_v1.1.md` (main run) and
`docs/rq1_findings/ALIGNMENT_DISCUSSION_ngo_pilots.md` (both pilots); point
numbers below refer to that draft's numbering.

**Provenance for the two audits this plan's rankings turn on:**
`analysis/ngo_extensions/measurement_selection_audit.py`, commit `395a9ed`,
tables at each pilot's `outputs/measurement_audit.csv` and
`outputs/selection_attrition.csv`.

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

**Gate:** a scale-comparability check. The blame-vs-praise swing comparison
assumes the two 0–10 scales behave alike. Produce the point-4a analogue for
praise — raw cell means to expose floor/ceiling structure — and report
swings in per-cell SD units alongside raw units. The draft already concedes
"praise's own pattern is still open." Cost: hours, reanalysis only.

### Rank 2 — Foundation gradient, finetuned only (point 2b)

Joint 4-df wild cluster bootstrap-F over all five foundations per cell.
mistral-finetuned `p_wcb=.672` — the sign effect is statistically
indistinguishable across harm, loyalty, authority, fairness, and purity.
gemma (.049) and llama (.060) sit on opposite sides of the line.

The MF pilot's design is clean on the axis that damages the nonmoral pilot:
pair-level gating kept every cell perfectly sign-balanced (§3). Nothing in
the published Knobe-in-LLMs literature tests beyond harm, because neither
Ngo's nor Raimondi's paradigm leaves it.

**Gates, both reportable-with-caveat rather than blocking:**

- Frame mistral's null as an equivalence result, not an absence of
  heterogeneity. A null joint F at G=26–30 is weak evidence *for* homogeneity
  on its own. Use the Bloom (2006) MDE machinery from
  `rq1_v1_1_robustness/09` + `15` — already used this way in
  `RQ1_STATISTICAL_METHODS_v1.1.md` §9.3 — and report "heterogeneity above X
  is ruled out."
- llama's cell is measured at r = .130. Flag it on measurement grounds, not
  only as a borderline p-value.
- Pretrained foundation heterogeneity (all three cells significant) stays
  "under investigation" pending §5 item 1. Do not block Rank 2 on it.

### Rank 3 — Full construct divergence (point 7)

Intentionality, blame, and praise tell three different stories on the same
items. Recoverable, but it is not within-item the way Rank 1 is: as the
draft writes it, point 7 rests on the three moral-vs-nonmoral *interactions*
(points 3, 4, 5), which are between-arm and inherit both the severity gap
and the attrition in §3.

**Gates:**

- Re-run the pilots' finetuned q_intentionality fits with `parsed_rating`
  substituted on parse_ok rows (script 35's method). At r = .146–.180, the
  intentionality leg is currently the weak one, and a reviewer will say the
  constructs diverge because one of them is badly measured.
- State the differencing argument explicitly in place of "within-item":
  blame's interaction is negative and praise's is positive over the *same*
  arm contrast, so a severity main effect cancels. It survives as a confound
  only if severity hits blame and praise asymmetrically — which is what
  point 4a's raw-means table would look like if it did.

### Rank 4 — Cross-architecture disagreement on moral-specificity (point 3)

llama moral-specific (interaction p=.017), mistral leaning the opposite way,
gemma neither. Good framing ("no single LLM notion of intentionality
attribution; it's recipe-dependent"), three independent problems:

1. The 65% attrition in the moral-good cell (§3) — this *is* the
   moral-vs-nonmoral contrast, in the pilot that has the problem.
2. Severity is unchecked across arms in both pilots; no reviewer-rated
   severity question exists for either.
3. The deciding cell, llama-instruct q_intentionality, is measured at
   r = .146.

Future-work paragraph this cycle unless there's bandwidth for a curation
pass. Note it is *not* cross-pilot — all three arms live in the nonmoral
pilot and share a `pair_id` — but `pair_id` clusters a four-clause template
family, not a matched item (within pair 1: Bill/gadget/babies vs.
Priya/app-update/job-security vs. Trevor/font vs. Naomi/template). Better
matched than the main run's MB/NMB pairs; not a matched-stimulus design.

### Rank 5 — Finetuning as the causal lever (point 1)

The 6/6 pretrained-null / finetuned-large pattern across three
architectures. Most headline-sounding, most exposed: every pretrained cell
is scored by `_logit_ev_rating`, the function script 35 proved manufactures
significant wrong-direction effects at low parse rate, and pretrained
agreement here is r = .026–.227.

**Gate:** §5 item 1. Until then the honest version is "pretrained shows
nothing reliable," not "finetuning installs this bias." Reviewers in this
subfield will know to ask, because the artifact is documented in this
project's own logs.

### Carried from the main run

- **Typicality runs backwards from humans** (gemma, mistral; RQ1c). Survives
  WCB, an independent random-slope model, and parsed-rating substitution.
  The most robust result in the main run and the one main-run claim that
  belongs in the paper unmodified.
- **Methodological pair:** logit-fallback EV scoring manufacturing spurious
  effects, and Wald/LRT overconfidence at G=21–84 in exactly the cells WCB
  rejects. Directly transferable to anyone scoring LLM Likert responses from
  logprobs. This is a section, not a footnote.
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

### Do first — gates other work

1. **Parsed-rating substitution across both pilots, all cells** — reanalysis,
   no elicitation, no GPU, reuses script 35's method. Covers pretrained cells
   (gates Rank 5, clears the pretrained half of Rank 2) **and finetuned
   q_intentionality cells** (gates Rank 3, sharpens Ranks 2 and 4). The
   single highest-leverage task left in the project.

2. **Praise scale-comparability check** — raw cell means for praise plus
   swings in per-cell SD units. Gates Rank 1, the claim being drafted first.

### Do in parallel with 1–2

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
