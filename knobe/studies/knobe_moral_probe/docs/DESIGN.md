# knobe_moral_probe: design (2026-09-28)

Study `knobe_moral_probe`, branch `knobe_moral_probe`. Written from the 2026-09-28 design session. It
replaces the pilot-era plan (`docs/submission_plan/FINAL_RUN_PLAN.md`), which
patched the old items and protocol. The pilots' data and scripts stay as they
are, as the pilot record.

References: `docs/REFERENCES.md` in this study folder (BibTeX in
`references.bib`).

**Amended 2026-09-28** by the three approved amendments at the top of
`IMPLEMENTATION_PLAN.md` (format-only worked examples, a temperature-0
reviewer client, one power-script exception to the README). Where they
differ, the amendments win.

**Amended 2026-10-01 (role-noun rule):** every item names its agent by a
role noun ("the manager", "the contractor"), never a personal name, and uses
no gendered pronouns. One role noun per storyline, shared by both versions
and every arm. Names and pronouns carry gender, ethnicity, age and class
cues that models respond to; in Ngo's pairs they also changed with the sign
(Bill harms, Robyn helps), confounding agent with sign, and mixed
conventions across arms would confound agent with arm. Ngo's 40 pairs are
therefore minimally adapted: names and pronouns become one shared role
noun, and nothing else changes. The paper discloses this as an adaptation.
`kmp.items.design_problems` checks same-agent for every pair and flags
gendered pronouns; personal names are a review-checklist item. This
supersedes the same-day exemption of Ngo pairs from the same-agent check.

**Amended 2026-10-01 (Ngo goals and verbatim set):** the adaptation also
aligns the goal where Ngo's two versions differ ("buy a house" / "buy a
car"). Some pairs still differ in the action, its object or who is
affected (gadget/invention, babies/toddlers); see the open decision on this
in `DEFINITIONS_AND_CHECKLIST.md`. Ngo's 40 pairs are also
kept word for word as a separate set, experiment `ngo_verbatim` (IDs
`kmp-nv-…`, arm `moral`), asked the same questions as the adapted moral
items. It is exempt from the role-noun and same-agent checks and nothing
else. It is a consistency check: the sign effect on verbatim vs adapted
text, per model. The main analyses use the adapted items.

**Amended 2026-10-01 (copying check):** §8's "no copying of the worked
examples' answers beyond chance" is measured against the same model run
without the examples, not a fixed share. 0 and 5 are natural answers (no
blame for a good effect, the midpoint), so a fixed share over-flags. For
each instruct model × experiment × question, copying = share of answers in
{0, 5, 9} with examples minus the same share without. It blocks when that
excess exceeds `protocol.COPY_EXCESS_MAX` (proposed 0.10, revisited against
the pilot and recorded). The §8 example check therefore runs with and
without examples for every instruct model in the pilot, not only Mistral.
Without a no-examples run, copying is "no data" and blocks instruct models.
Pretrained models get the same numbers as findings.

## 1. What the study asks

**Background.** In Ngo et al. (2015), people rate an agent as acting more
intentionally when a foreseen side effect is bad than when it is good.

**Research questions.**
1. Do language models show the same asymmetry on Ngo's paired scenarios?
2. Does it extend beyond harm and help:
   - to nonmoral bad and good outcomes (prudential, procedural)?
   - to moral outcomes outside harm (fairness, loyalty, authority, purity)?
3. Does fine-tuning introduce or strengthen it? Human input during
   fine-tuning is a plausible route for a human bias to enter a model, so
   this is compared across pretrained and instruct versions of each model.
4. Do intentionality, blame and praise follow the same pattern?
5. Does the asymmetry track how the model itself perceives the side effect:
   its significance, and how harm-like or moral it seems?

**What the analysis needs.** One reliable rating per model × scenario ×
question. Everything below exists to produce that.

## 2. Models

Gemma-2-9B, Llama-3.1-8B and Mistral-7B-v0.1, each pretrained and instruct
(`configs/models.yaml`, revisions pinned and recorded per row).

## 3. Stimuli

### 3.1 Shared authoring rules (every pair)

- Same agent, same main action, same unrelated goal in both versions.
- The agent is a role noun, never a personal name; no gendered pronouns.
- An indifference clause: "[Agent] did not care at all about the effect this
  would have on X."
- A foreseen side effect. The questions are about the side effect, never
  the main action.
- The bad and good versions differ only in the side effect's direction. The
  good version mirrors the bad one at similar magnitude. This is an authoring
  rule, not screened; the subject models' significance ratings show how well
  it held.
- Plain, concrete wording. No graphic content beyond what the side effect
  requires.

### 3.2 Nonmoral experiment (Ngo's 3-clause template)

- **Moral:** Ngo's 40 original pairs, unchanged except for the role-noun
  adaptation (amendment above). The side effect affects
  other people's welfare or rights.
- **Prudential:** the side effect affects only the agent's own interests
  (health, money, reputation, safety). No one else is affected.
- **Procedural:** the side effect concerns an arbitrary convention or rule (a
  dress code, a seating chart, a filing convention). No one's welfare is at
  stake.
- **Target:** a passing prudential and procedural pair for all 40 storylines,
  so 240 items. Every item, old or new, is re-screened under the new rule
  (§4). As a starting point, rewrite the variants that failed in the pilot
  (pairs 2, 5, 8, 23, 29, 30 and 31 prudential; 23 and 37 procedural; 27
  both, per `nonmoral_pilot/outputs/selection_report.md`) and keep the rest
  as drafts.
- Ngo's moral-good items were dropped in the pilot because the old screening
  question named only the bad pole. The two-sided valence screen (§4)
  replaces it; the originals are not rewritten.

### 3.3 Foundations experiment (4-clause template)

The four clauses: background norm, unrelated goal, indifference, foreseen
side effect. Harm controls use the same template, so clause count isn't a
confound.

- **Harm (control):** physical or emotional harm to someone, or care for them.
- **Fairness:** unequal or unjust treatment, cheating, or reneging, with no
  one's welfare damaged.
- **Loyalty:** betraying, or standing by, one's group, team, family or ally.
- **Authority:** undermining, or upholding, a legitimate authority, hierarchy
  or tradition.
- **Purity:** violating, or honoring, a taboo or something treated as sacred,
  with no harm.
- Each good version upholds the same foundation its bad version violates.

**Structure: shared scaffolds (pilot option B).** Each storyline is written
once as a scaffold (agent, action, goal) and gets a harm version plus one or
more foundation versions. Harm vs non-harm is then compared within
storyline. Purity, which rarely fits shared scaffolds, gets purpose-written
storylines, flagged as such.

**Targets:**
- 20 passing storylines per foundation, floor 15.
- Harm versions on the shared scaffolds, about 30–40 pairs.
- Draft about 30% extra to allow for screening failures.
- Basis for 20: the power check in §9. It covers the pooled harm-vs-non-harm
  comparison and per-foundation detection for models that show the effect.
  It does not power comparisons between individual foundations; those are
  exploratory.

### 3.4 Authoring process

1. Written definitions and a review checklist (the rules in §3.1–3.3, plus
   template conformance and consistency of names and pronouns). You review
   these first.
2. Claude drafts the items; you review every item against the checklist.
3. Screening (§4), then pair selection.

The paper discloses that items were drafted with an LLM and reviewed by the
authors.

## 4. Screening (reviewer model, before any subject model sees an item)

- **Reviewer:** Claude via the API, never a subject model
  (`curate.check_reviewer_not_subject`). The model ID is pinned in config and
  recorded on every row; the pilots didn't record it.
- **Settings:** temperature 0, one call per item per question, each question
  as its own prompt.
- **Valence:** "How good or bad is the side effect for those it affects?"
  0 = very bad, 5 = neither, 10 = very good.
- **Domain profile (nonmoral):** moral, prudential and procedural, each rated
  0–10 separately, each with its one-line definition.
- **Foundation profile (foundations):** harm, fairness, loyalty, authority
  and purity, each rated 0–10 separately, each with its definition.

**Pass rule, pair-level** (a pair passes only if both versions pass):

| check | pass |
|---|---|
| valence | bad version ≤ 3, good version ≥ 7 |
| nonmoral domain | the intended domain rates ≥ 6 and highest of the three |
| foundation item | the intended foundation rates ≥ 6 and higher than harm |
| harm control | harm rates ≥ 6 |

Thresholds start from `configs/curation.yaml`'s `moral_min=6` and
`nonmoral_max=4`, and are revisited only against real screening
distributions, with the change recorded. Unparseable reviewer answers are
retried once, then reported by name in the selection report, not silently
dropped.

## 5. Subject-model instrument

Every question is its own single-turn prompt, so none primes another.

| question | wordings | answer |
|---|---|---|
| intentionality | 3 | 0–10 |
| blame | 3 | 0–10 |
| praise | 3 | 0–10 |
| significance | 1 | 0–10 |
| domain profile, nonmoral (moral / prudential / procedural) | 1 each | 0–10 each |
| harm, plus the intended foundation (foundations) | 1 each | 0–10 each |

- **Wordings.** Two paraphrases with normal anchors, and one with reversed
  anchors (0 = the high pole). Reversed answers are recoded as 10 − x at
  analysis time. Following Scherrer et al. (2023), and Dominguez-Olmedo et
  al. (2024) on ordering bias. Wordings are drafted and reviewed with the
  items.
- **Significance, draft:** "How significant is the side effect? Consider how
  much weight its impact has and how many people or things it reaches.
  0 = not significant at all, 10 = extremely significant." Subject models
  only, not screened. It tests whether the model's "moral" reading tracks
  significance.
- **Valence** is screening-only.

## 6. Prompt format

**Rule: identical text for both stages; only the wrapper differs.**

- **Pretrained:** the text as a raw completion prompt.
- **Instruct:** the same text as one user message in the model's own chat
  template, with no system prompt (the production `render.py` "chat" shape).

**Text:** `RAIMONDI_PROMPT_TEMPLATE`'s instruction, then three worked
examples, then the scenario, the question, and "Answer:".

**Worked examples:**
- Three short items, unrelated to the paradigm: no side effects, no
  indifference clause, obvious answers.
- They use the same question wording as the real item.
- Their answers spread across the scale (low, middle, high).
- Included for both stages, so the text stays identical.
- You review them.

**Readout:** the number the model writes, parsed from sampled text (Wang et
al., 2024). No logprob-EV score is computed or used.

**Sampling:**
- 24 samples per question: 8 per wording, or 24 for single-wording questions.
- Temperature drawn from U(0.85, 1.15), per Raimondi et al.
- `MAX_TOKENS` is set in the pilot (§8), starting at 10.
- Release string `knobe_moral_probe`, so seeds are fresh and can't collide
  with the pilots' or the main run's.
- Item IDs carry the prefix `kmp-`, so they can't be mistaken for pilot
  `variant_id`s.
- Prompt IDs: `item::question::wording::format`.
- `RUNNER_VERSION` strings start with `knobe_moral_probe`.

## 7. Code: `studies/knobe_moral_probe/`

One pipeline for both experiments, driven by a config per experiment. It
reuses `src/knobe/` for the engine, registry, seeding and result format; the
pilots' drift is why nothing is implemented twice (CLAUDE.md §7).

| module | job |
|---|---|
| `stimuli/` | authored items as reviewable files (one per experiment), plus review status |
| `protocol.py` | every question, its wordings and anchors, the worked examples, definitions, and the format per stage. Single source of truth |
| `screen.py` | runs the reviewer, applies the §4 pass rule, writes the selection report |
| `build_prompts.py` | items × questions × wordings × stage → prompt records. Deterministic, byte-stable |
| `elicit.py` | all six models, both experiments. Fake engine for testing; checkpoint and resume; `--model-keys`, `--registry` for the cluster runner |
| `checks.py` | the pre-analysis gate (§8) |
| analysis | new `load_frame` (recodes reversed anchors), then the existing sign-effect fits with `lib.wild_cluster_bootstrap` |

## 8. Gates

**Pilot (a few dozen screened items, all six models) must pass before the
full run:**
1. **Numbers:** ≥ 90% of answers are numbers, per model × question × wording.
2. **Pretrained validity:**
   - blame higher for bad than good side effects, praise the reverse
   - significance higher for serious than trivial outcomes
   - no copying of the worked examples' answers beyond chance
3. **Example check:** Mistral-instruct with and without the worked examples;
   its ratings shouldn't shift.
4. **Anchor reversal:** reversed-anchor answers agree with normal ones after
   recoding.
5. **Throughput** confirms the cost estimate (CLAUDE.md §4).

**If pretrained models fail check 2,** the tuning comparison (RQ3) is
reported as not measurable under this protocol, and the study proceeds with
instruct models. That's a finding, not a blocker.

**Before analysis, on the full run:** the same checks per model × question ×
wording. Cells failing check 1 are reported, not silently analyzed.

## 9. Scale and cost

| | count |
|---|---:|
| nonmoral items | ~240 |
| foundations items | ~230 |
| prompts per item | 13 nonmoral, 12 foundations |
| samples per item per model | 168 nonmoral, 144 foundations |
| total rows | ~440k |

The samples per item are 3 core questions × 24, plus significance × 24,
plus the manipulation checks × 24 each (3 nonmoral, 2 foundations). That's
about 73k rows per model, roughly 75 minutes per model at the measured
15–20 rows/s. If that's too slow, the first cut is to take the
manipulation checks down to 8 samples, which leaves the core questions
untouched. Screening is about 470 items × 4–6 reviewer calls.

**Power basis for 20 per foundation:** `required_sets()` from
`rq1_v1_1_robustness/15_rq1a_severity_mde_and_power_planning.py`, applied
to the pilot's finetuned per-foundation sign effects under parsed scoring:

| foundation | Gemma | Mistral | Llama |
|---|---:|---:|---:|
| loyalty | 13 | 66 | 99 |
| authority | already enough | 357 (effect ≈ 0) | 14 |
| fairness | 17 | 11 | none (effect ≈ 0) |
| purity | 10 | 10 | 58 (reversed sign) |

Llama's effects are mostly small or unstable: fairness ≈ 0, purity in the
reversed direction, loyalty needing ~99 storylines. The exception is
authority (β ≈ 1.07, 14 storylines). These are rough: pilot estimates on
6–10 storylines, under the old protocol. Committed as
`analysis/power_basis.py` → `outputs/power_basis.csv` (commit a67a29a); an
earlier version of this paragraph, computed in a scratch session, said
Llama showed no effect to power.

## 10. Analysis (unchanged in kind)

- Sign effect (bad vs good) per model, arm and question.
- Arm interactions: moral vs nonmoral; harm vs non-harm pooled.
- Tuning interaction: pretrained vs instruct.
- Wild cluster bootstrap, clustered by storyline, B = 1999.
- Holm correction within (family, tuning, question).
- Per-wording estimates and agreement across wordings reported alongside the
  pooled result.
- **New, RQ5:** does the sign effect vary with the model's own significance,
  harm and domain ratings?
- An analysis plan with predictions is committed before the full run.

## 11. Out of scope

- The indifference-clause ablation.
- Human ratings (the separate human study, which needs an IRB determination).
- Comparisons between individual foundations as tests; reported
  descriptively.
- Logprob-based scoring.
- More model families.

## 12. Open items, resolved during implementation

- Final question wordings, worked examples and definitions (drafted, then
  reviewed by you).
- The reviewer model ID.
- Pilot item selection.
- `MAX_TOKENS` for each format.
