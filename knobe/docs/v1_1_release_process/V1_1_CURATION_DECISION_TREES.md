# Curation gate: decision trees for the Phase 2 → freeze judgment calls

Use this once `curated_v1.1.csv` exists (`V1_1_WORKFLOW.md` Phase 2, step 5).
Five judgment calls gate whether it's safe to move to the freeze. Trees 1,
2, 4, 5 apply to the upcoming curation run. Tree 3 does **not** — per the
decision to revert the Type-1 question reword for this run, it applies to
that fix's own, later, separate validation cycle instead.

Shared principle across all five: **never resubmit-and-tweak an individual
family until its number moves.** Every branch below that ends in "revise"
means diagnose the rule-level cause and rewrite once, the same method used
for the original 24 — not iterate against the reviewer.

---

## Tree 1 — Threshold pass/fail (per family, all 24)

For each of the 24 Type-2 families, look at all 4 variants' `moral_relevance`.

```
score <= 3 for all variants?
├── YES → clean pass. No action.
└── NO → score == 4 for the variant(s) in question?
    ├── YES → check the family's OTHER 3 variants:
    │   ├── all <=4 too → treat as clean pass (borderline but consistent)
    │   └── mixed (some variants much higher) → treat as the family-level
    │         case below, not a clean pass
    └── NO (score 5-7) → check breadth within the family:
        ├── isolated to 1 of 4 variants, score 5-6 (mild) →
        │     route to Tree 4 (residual-failure handling) — don't
        │     re-diagnose from scratch, likely noise-level
        └── affects 2+ variants, OR any single variant >=7 →
              systematic miss for this family — the fix likely didn't
              address the actual bleed source. Re-read that family's
              revised text against the dimensional-independence rule
              before touching it (check: did the entity/outcome swap
              still share a domain-plausible link to the goal's real
              stakes that wasn't obvious at draft time?). One
              considered rewrite, not iteration.
score >= 8 for any variant?
└── Clean fail regardless of the above — same rule-diagnosis path,
      higher priority (something about this family's revision
      structurally didn't work, not a borderline case).
```

## Tree 2 — Real reviewer vs. ChatGPT disagreement (per family)

Compare against `data/authoring/v1.1_candidate/chatgpt_validation_results.csv`.

```
Real reviewer score <=4 AND ChatGPT score <=4 (both pass)?
├── YES → no disagreement. Feed the real score into Tree 1 as normal.
└── NO → real reviewer says FAIL (>=6) — this is the practically likely
    case, since ChatGPT's actual scores were uniformly low (0-3):
    ├── Trust the real reviewer's fail (it's what production uses).
    │   Route the family to Tree 4 (residual-failure handling).
    ├── Log the disagreement explicitly — do not silently override
    │   either signal. Record: family_id, ChatGPT score, real score.
    └── Count how many families disagree this way:
        ├── 1-2 families → isolated; note as "judge-dependent" for
        │     those specific families in the release changelog.
        └── 3+ families → broader pattern; this says something about
              reviewer-model consistency/calibration generally, not just
              about these families' content. Flag as its own finding
              (possibly related to the already-noted MG reviewer-instrument
              asymmetry) — worth a note in the writeup independent of
              whether these specific families pass or fail.
```

(The reverse — real reviewer passes, ChatGPT flagged — isn't expected
given ChatGPT's actual score distribution, but if it happens: same
principle, trust the real reviewer's pass, log the disagreement.)

## Tree 3 — Regression check for the Type-1 wording change (separate, later cycle only)

Applies when you run the *reverted* wording's replacement as its own
validation cycle, against: (a) the 11 originally-flagged MG families, (b) a
clean-MB comparison sample, (c) a clean-nonmoral comparison sample.

```
(a) Do the 11 target families move to >=6?
├── All/most do → target fix works as intended.
└── Some/none do → partial or no effect; note the residual as possible
      genuine instrument limitation (already flagged as a real
      possibility, not necessarily a failure of the attempt).

(b) Do the clean-MB comparison sample scores stay >=6?
├── YES → no regression on the harm side.
└── NO (any drop below 6) → REGRESSION. Do not adopt the new wording
      broadly regardless of (a)'s result — a fix that breaks already-
      correct cases is worse than the asymmetry it was meant to fix.

(c) Do the clean-nonmoral comparison sample scores stay <=4?
├── YES → no new false positives introduced.
└── NO (any rise above 4) → REGRESSION (the "count benefits as moral"
      language is over-firing on borderline nonmoral content). Do not
      adopt broadly.

Overall gate: adopt the reworded question ONLY if (a) shows real
improvement AND (b) and (c) both show zero regression. If either (b) or
(c) fails, revert permanently and document the MG asymmetry as an
accepted instrument limitation (v1.0's own precedent for evocativeness),
not something to keep iterating on.
```

## Tree 4 — "Good enough to proceed" on residual failures

Count families still failing after Tree 1/2 routing (i.e., not resolved as
clean passes).

```
0 residual failures?
└── Proceed to freeze. Nothing to decide.

1-2 residual failures?
├── Each mild (score 5-6) → accept as documented limitation
│     (v1.0's own precedent for evocativeness). Proceed to freeze,
│     note in the release changelog which families and why.
└── Any severe (score 8+) → one targeted revision for just that
      family (same rule-based method), not a full redo of the batch.
      Re-curate only that family before freezing.

3+ residual failures?
└── Look for a shared pattern (same domain? same subdomain? same
    kind of entity-swap?):
    ├── Pattern found → the general guardrail rule likely needs
    │     refinement for that specific case type, not just those
    │     items patched ad hoc. Update the rule, then revise that
    │     whole cluster together in one pass.
    └── No pattern (scattered, different domains/reasons) →
          handle individually via the mild/severe split above —
          likely still acceptable as scattered documented limitations
          if each is mild, but don't assume that without checking
          each one's severity.
```

## Tree 5 — Coverage completeness

```
Pull curated_v1.1.csv, filter to all 24 patched family_ids (the 19
originally flagged + the 5 sibling-consistency additions: ENV-NMG-02,
FIN-NMG-02, PRIV-NMG-01, PS-NMG-02, FOOD-NMB-02).

All 24 present in the output?
├── NO → stop. Investigate the pipeline gap before drawing any
│     conclusion from what IS present — a missing family means
│     something didn't run, not that it passed silently.
└── YES → for each of the 5 sibling additions specifically, does it
    pass whenever its already-targeted partner (same set, same
    outcome axis) also passes?
    ├── YES for all 5 → full pair consistency confirmed.
    └── NO for any (partner passes, sibling doesn't, or vice versa) →
          priority investigation: these two variants share nearly
          identical text (differ only in the sign-appropriate framing
          of the same outcome), so a split result is surprising.
          Check (a) whether the drafted sibling text actually matches
          the partner's fix quality — re-read it for a drafting error
          — before assuming it's a genuine content issue requiring
          the Tree 4 path.
```
