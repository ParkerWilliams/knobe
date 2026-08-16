# Does the Knobe Effect Generalize Beyond Harm? A Moral-Foundations Extension of Ngo's Set (design doc, 2026-08-17)

**Status:** design agreed via brainstorming, not yet built. This is the
plan; `analysis/ngo_extensions/nonmoral_pilot/` (a sibling investigation, same
underlying stimuli, different axis, grouped under `analysis/ngo_extensions/`
for the shared strategy) is the closest precedent for how this would
actually get built once approved. Will live at
`analysis/ngo_extensions/moral_foundations_pilot/` once built.

## 1. Motivation

`docs/rq1_findings/RAIMONDI_REPLICATION_GAPS.md` and
`docs/rq1_findings/KNOBE_EFFECT_STATUS.md` establish that this project's
"moral" category — and Raimondi's/Ngo's original 80 items — are entirely
**harm/welfare-side-effect structured**: an agent pursues an unrelated
goal, doesn't care about a foreseen consequence, and the consequence is
always a change in someone's welfare. `docs/severity_confound/
SEVERITY_MORALIZATION_BACKGROUND.md` already surveys why this matters:
Moral Foundations Theory (Graham, Haidt) treats harm as only one of
several independent moral foundations — loyalty, authority, and
purity/sanctity can register as strongly moral with no harm structure at
all (Haidt's moral-dumbfounding paradigm is the clearest demonstration).
This project's own generation prompt explicitly excludes those three.

**The gap this leaves:** even a clean "the Knobe effect is moral-specific"
finding (from `analysis/ngo_extensions/nonmoral_pilot/`'s harm-vs-nonmoral test)
would only license a claim about *harm-structured* moral content. Whether
the same asymmetry shows up when moral wrongness is presented via a
different normative ground entirely is untested by anything built so far.

## 2. Research question

**Primary:** does the classic Knobe asymmetry (bad>good intentionality
for a foreseen side effect) hold for non-harm-structured moral violations,
or is it specific to the harm/welfare structure Raimondi's paradigm is
built on? Operationalized as a single pooled contrast: harm-control vs.
all non-harm foundations combined.

**Secondary, explicitly exploratory:** does it look the same across the
four non-harm foundations individually (loyalty, authority,
fairness-without-harm, purity)? Reported with honest per-foundation
cluster counts, not treated as equally powered or load-bearing for the
primary claim.

**Explicitly deferred, not this pilot:** a properly-powered,
purpose-built comparison of the four foundations against each other
(rather than opportunistically sourced from Ngo's existing storylines).
Worth doing only if this pilot's pooled result, or the exploratory
per-foundation breakdown, looks suggestive enough to justify the
investment.

**Also explicitly out of scope:** blame/praise questions. The Ngo
prudential/procedural pilot added `q_blame`/`q_praise` to test whether
blame is doing mechanistic work behind the intentionality asymmetry
(the Hindriks hypothesis, RQ1b). That's a mechanism question about *why*
the effect happens, not *whether* it happens — not yet earned here, since
this pilot hasn't established the asymmetry exists for these foundations
at all. Revisit if results are suggestive enough to chase the mechanism.

## 3. Vignette structure

Every item — including a freshly-written harm-control, not reused
verbatim from Ngo — uses the same **4-clause template**, one clause more
than Ngo's original 3-clause structure:

1. **Background fact** establishing the relevant norm (a promise, a rule,
   a taboo, an agreed process). Necessary because harm is self-explanatory
   from physical causation alone, but "this violates a promise" only makes
   sense if the reader/model already knows the promise existed — omitting
   this clause was an early design error caught during brainstorming (an
   implicit background condition was "smuggled in" through the outcome
   clause itself in a first-draft loyalty example).
2. **Unrelated instrumental goal** — the agent does something for a stated
   reason that has nothing to do with the foundation in question (same as
   Ngo).
3. **Stated indifference** — "did not care at all about the effect this
   would have on X" (same as Ngo).
4. **Foreseen violation** — the side effect the intentionality question
   targets. Never the main action (per the general Knobe-paradigm
   invariant already established in `docs/rq1_findings/KNOBE_EFFECT_STATUS.md`).

Applying this 4-clause structure to the harm-control too (not just the
four new foundations) removes clause-count/complexity as a confound
between harm and non-harm conditions — an explicit design choice made
during brainstorming in favor of internal symmetry over literal reuse of
Ngo's shorter original wording.

## 4. Sourcing plan

Reuse Ngo's 40 storylines (`analysis/ngo_extensions/nonmoral_pilot/
ngo_2015_original_80.txt`) as shared scaffolds — same agent archetypes,
goals, and domains — rather than inventing unrelated content, to keep this
a recognizable extension rather than a disconnected new battery.

Domain survey of the 40 (see conversation log for the full breakdown):
corporate/financial (~9), personal/family (~9), political/civic (~7),
medical (~4), extreme/violent (~4), neighborly/everyday (~4),
media/reputation (~3), academic (~2), law enforcement (~2),
animal/wildlife (~2), religious (~2), sports (~1).

- **Harm-control + loyalty + authority + fairness-without-harm**: drawn
  from a large shared core subset of the 40 — corporate, political,
  family, academic, neighborly, and media domains all bend naturally into
  a broken promise, an undermined hierarchy, or an unfair process.
  Target ~25-30 of the 40 storylines; exact count depends on which hold up
  under actual drafting. The three storylines already flagged as
  unadaptable in `analysis/ngo_extensions/nonmoral_pilot/prudential_variants.py`
  (wartime bombing, terrorism, cult mass-suicide — items 13-14, 67-68,
  73-74) are skipped or substituted the same way they were there.
- **Purity/sanctity**: the hard case. Only ~3-5 of Ngo's 40 storylines have
  a natural taboo/disgust angle without forcing (church-protest items
  61-62, marriage items 65-66 are the clearest candidates). Rather than
  force purity onto corporate/political storylines where it doesn't fit,
  supplement with a handful of purpose-written storylines in domains Ngo's
  set doesn't have at all (food, ritual, bodily contact) — explicitly
  flagged in the eventual implementation as new, not pretended-equivalent
  to the Ngo-derived items, the same way the three substituted extreme
  storylines are already flagged in the prudential pilot.

**Consequence, decided explicitly rather than treated as an oversight:**
loyalty/authority/fairness will have more items than purity. This is
acceptable because the primary analysis pools all four into one non-harm
contrast (§2) — pooling several different non-harm triggers rather than
relying on one is what makes a null or positive result generalizable, not
what breaks it. It only becomes a problem for the secondary per-foundation
breakdown, where purity's smaller N gets reported as more tentative,
mirroring exactly how `analysis/rq1_v1_1_robustness/
32_nonmoral_subdomain_sign_wcb.py` already handled prudential's
untestable G=2 within this project's own release.

## 5. Manipulation check (curation)

Two curation questions per item, not a full cross-check against all five
conditions (kept lean, matching the single-question scope of
`analysis/ngo_extensions/nonmoral_pilot/curate_moral_relevance.py`):

1. **Harm relevance** (every item, every condition):
   > *"To what extent does this outcome involve harm or damage to
   > someone's welfare — health, safety, finances, or material
   > well-being? (0 = not at all, 10 = entirely about harm to welfare)"*

2. **Target-foundation relevance** (one per item, matching its intended
   condition — all four use the same bracketing clause, fixed after
   catching an inconsistency where only purity/fairness had it in an
   earlier draft):
   > Loyalty: *"Setting aside any harm to someone's welfare, to what
   > extent does this outcome involve loyalty to, or betrayal of, one's
   > group, team, family, or ally? (0-10)"*
   > Authority: *"Setting aside any harm to someone's welfare, to what
   > extent does this outcome involve respecting or undermining a
   > legitimate authority, rule, or hierarchy? (0-10)"*
   > Purity: *"Setting aside any harm to someone's welfare, to what
   > extent does this outcome involve a taboo, disgust, or violation of
   > purity/sanctity? (0-10)"*
   > Fairness: *"Setting aside any harm to someone's welfare, to what
   > extent does this outcome involve unequal or unjust treatment?
   > (0-10)"*

**Pass/fail**, mirroring `configs/curation.yaml`'s existing
`moral_min`/`nonmoral_max` pattern rather than inventing new thresholds
from scratch: a foundation item needs high target-foundation-relevance
and low harm-relevance; the harm-control needs high harm-relevance.
Exact threshold values TBD at implementation time (start from the
existing `moral_min=6`/`nonmoral_max=4` values and adjust only if the
real curation data shows they don't discriminate well for this new
question).

**Known gap, not solved here:** no check between the four non-harm
foundations themselves (e.g., confirming a loyalty item doesn't also read
as authority-relevant). Judged secondary to the harm/non-harm check during
brainstorming; revisit if cross-foundation contamination turns out to be
common once real curation data comes in.

## 6. Analysis plan

Reuses this project's existing WCB machinery
(`analysis/rq1_v1_1_robustness/lib.py::wild_cluster_bootstrap`), not new
inference code:

- **Primary**: `sign_c` main effect, harm-control vs. pooled non-harm
  (loyalty + authority + fairness + purity combined), family-clustered
  WCB, all three subject models (gemma/llama/mistral), same tuning-status
  split (pretrained/finetuned) already used throughout this project.
- **Secondary**: the same test repeated within each foundation
  individually, reported with its own cluster count and no claim of equal
  power across foundations — same honesty standard as the nonmoral
  subdomain breakdown.

## 7. Open items for whoever picks this up

- Exact core-subset storyline count (target ~25-30) depends on which
  actually draft cleanly — expect this number to move during authoring,
  the same way the prudential/procedural pilot's domain-fit judgment calls
  did.
- Purity's purpose-written storylines need their own small design pass
  (food/ritual/bodily domains) before drafting — not scoped in detail
  here.
- q_blame/q_praise, and the genuine equally-powered four-foundation
  comparison, are both explicitly deferred (§2) pending how suggestive
  this pilot's results look.
- Curation threshold values (§5) are a starting point, not final —
  validate against real reviewer data before trusting them.
