# Does This Experiment Show the Classic Knobe Effect? (2026-08-15)

**Status:** consolidates a same-day investigation
(`analysis/rq1_v1_1_robustness/31`, `32`, `33`, `34`, `35`, branch
`rq1-base-sign-main-effect-wcb` + `nonmoral-subdomain-sign-wcb`, full
provenance in `results/ANALYSIS_LOG.md`) that was previously only recorded
as raw log entries and conversation, not pulled into one place. Read
alongside `docs/RAIMONDI_REPLICATION_GAPS.md` (the comparison to Raimondi
et al. specifically) and `docs/RQ1_STATISTICAL_METHODS_v1.1.md` (the full
RQ1a-d methodology this sits on top of) — this document answers one
narrower question: **stripped of the moral/nonmoral, typicality, and
domain decomposition this project's own design adds, is the textbook
"bad side effects get rated more intentional than good ones" effect
actually present at all, and where?**

The classic effect always concerns the foreseen **side effect** of an
action, never the action itself. E.g. Ngo item 1: "Bill released a gadget
to make a deadline [the action — never in question]. Bill did not care at
all about the effect the gadget would have on babies. Bill knew his
gadget would kill babies [the side effect]. Did Bill intentionally
**cause the death of babies**?" The puzzle is that the identical
epistemic state (foresaw it, didn't care) gets a different intentionality
verdict depending only on whether the side effect is good or bad.

## 1. The flat, pooled version: mostly absent

The plainest test — bad vs. good, pooled across moral and nonmoral
content, finetuned models (`31_rq1_base_sign_main_effect_wcb.py`) — is
marginal-to-null in every family under a properly-sized test:

| family | β (sign_c) | WCB p |
|---|---|---|
| gemma | +0.322 | .106 |
| llama | +0.343 | .102 |
| mistral | −0.069 | .533 |

None survive. This is the term script 01 never actually bootstrapped
(it only tests `sign_c:tuning_c`); closing that gap was the first step
here.

## 2. It's not absent — it's concentrated in moral content

The direct moral-only split (`05_valence_split_wcb.py`, pre-existing) shows
the effect is real and robust *within* moral-valence content specifically:

| family | moral-only β | WCB p | nonmoral-only β | WCB p |
|---|---|---|---|---|
| gemma | +0.368 | **.021** | +0.276 | .436 |
| llama | +0.658 | **.0005** | +0.028 | .918 |
| mistral | +0.062 | .408 | −0.201 | .060 |

Gemma and llama show a real bad>good asymmetry for moral-harm content.
Mistral shows nothing in either half. Pooling moral and nonmoral together
(§1) washes this out — not because the moral effect is fake, but because
averaging a real effect with a genuine nonmoral null dilutes it below
threshold.

**This is not the same claim as "the effect is moral-specific."** That
stronger claim requires the direct interaction test (RQ1a's
`sign_c:vt_c`), which is a different, harder-to-clear bar — see
`docs/RQ1_STATISTICAL_METHODS_v1.1.md` §9-11 for why that one doesn't
survive severity adjustment in any family. What's established here is
narrower and safe: **a bad>good asymmetry exists, robustly, for moral
content in 2 of 3 families.** Whether it's larger than a matched nonmoral
asymmetry is the still-open question `analysis/ngo_prudential_pilot/`
was built to answer more cleanly than this release's confounded moral/
nonmoral pairs can.

## 3. The nonmoral null holds up under decomposition, not just in the pooled test

Splitting nonmoral content by subdomain (`32_nonmoral_subdomain_sign_wcb.py`)
to check whether the pooled nonmoral null was hiding a real effect within
a more homogeneous subset: it wasn't.

| subdomain (G) | gemma | llama | mistral |
|---|---|---|---|
| aesthetic (24) | p=.536 | p=.915 | p=.066 (trending reversed) |
| procedural (16) | p=.706 | p=.973 | p=.291 (trending reversed) |
| prudential | untestable — only 2 families in this release |

Null in every family, in both subdomains large enough to test. Mistral's
consistent (never-significant) reversed trend recurs across pooled
nonmoral, aesthetic, and procedural alike — the same unresolved pattern as
its RQ1b-nonmoral disagreement (`docs/OUTSTANDING_STATISTICAL_ANALYSIS.md`
item 2). Prudential — the subdomain the moralization literature
(`docs/SEVERITY_MORALIZATION_BACKGROUND.md`) flags as the best candidate
for a genuine severity/moral-status dissociation — has only 2 families in
this release and simply can't be tested here. That gap is what
`analysis/ngo_prudential_pilot/` exists to fill.

## 4. The pretrained arm: a real, corrected reversal-turned-replication

Splitting the flat test by tuning status (`33_rq1_base_sign_by_tuning_wcb.py`)
found pretrained models show a *significant, well-powered effect in the
reversed direction* (good rated more intentional than bad) in all three
families:

| family | pretrained β | WCB p |
|---|---|---|
| gemma | −0.130 | .000 |
| llama | −0.107 | .024 |
| mistral | −0.058 | .042 |

**This mostly did not survive scrutiny, and the story changed twice
before landing.** Restricting to moral-only content
(`34_rq1_base_sign_pretrained_moral_only_wcb.py`, matching Raimondi's
all-moral scope) killed llama's and mistral's significance but gemma's
reversal *persisted and strengthened* (β=−.172, p=.000) — ruling out
"just a moral/nonmoral pooling artifact." The actual explanation
(`35_rq1_base_sign_pretrained_parsed_rating_wcb.py`) was a scoring
artifact: gemma-pretrained's `ev_rating`/`parsed_rating` correlation on
this cell is ≈0 (parse rate 56.5%), and substituting the model's real
parsed answer **flips gemma to a significant classic-direction effect**
(β=+.539, p=.001) — closely matching Raimondi's own reported
gemma-pretrained delta (+0.51). Mistral's point estimate flips too
(not significant, n=1271). Llama stays genuinely unresolved (20.7% parse
rate, n=871, too underpowered either way).

**Practical upshot:** any pretrained-arm claim in this release that used
the default logit-fallback `ev_rating` without a parsed-rating
cross-check carries the same risk this cell turned out to have. Item 11
(`26_ev_scoring_validation.py`) only ever validated this substitution for
RQ1c's typicality×sign term — this is now the second cell it's been
checked for, and the second time it mattered.

## 5. The consolidated verdict, per family

| | gemma | llama | mistral |
|---|---|---|---|
| Pooled flat effect (finetuned) | marginal, ns | marginal, ns | null |
| Moral-only (finetuned) | **real, robust** | **real, robust (largest effect in the study)** | null |
| Nonmoral-only, any subdomain tested | null everywhere | null everywhere | null, trending reversed |
| Pretrained (corrected scoring) | real, classic-direction, matches Raimondi | unresolved (underpowered) | trends classic, ns |

**The classic Knobe effect is present in this experiment — it is not a
flat, content-agnostic bias, and it is not equally present in all three
families.** It shows up cleanly for moral-harm content in gemma and
llama, both before correction issues and after; it does not show up for
nonmoral content anywhere it can currently be tested; and mistral doesn't
show it in any tested condition, moral or nonmoral, pretrained or
finetuned — a real, multiply-confirmed non-effect for that family rather
than a gap in testing.

## What's still open

- **Prudential nonmoral content is untested in the actual release** (only
  2 families) — `analysis/ngo_prudential_pilot/` is built to test this
  directly on Raimondi's own storylines, pending curation
  (`ANTHROPIC_API_KEY` needed) and, if that passes, elicitation.
- **Whether the moral effect is genuinely moral-specific** (bigger than a
  matched nonmoral effect on the same severity/stakes) rather than a
  severity confound remains open — that's the whole reason the prudential/
  procedural extension exists rather than relying on this release's own
  unmatched MB/NMB pairs.
- **Llama's pretrained status** is a real, unresolved gap (not a finding)
  — 20.7% parse rate makes it untestable with the current elicitation/
  scoring setup, not evidence of anything about the model itself.
- **Whether other pretrained-arm results in this release carry the same
  scoring-artifact risk** found in §4 hasn't been checked systematically
  — worth auditing before citing any other pretrained-only claim.
