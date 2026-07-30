# WO-4 — Pilot analysis and simulation-based power determination
**Stage:** S4 (local). **Depends on:** G1 pilot data (WO-5 run on current 105-family
set at N=25). **Blocks:** G2 freeze (it may demand more families) and the final
main-run N.

## Objective
Implement `src/knobe/power.py`: estimate variance components from the pilot, then run
the Westfall–Judd–Kenny-style crossed-random-effects simulation (DR §16) to set
(a) response-level N per item and (b) whether 250 families suffice for the
*interaction* contrasts, which are the binding estimands.

## Requirements
1. **Variance decomposition** from pilot `results.jsonl`: fit mixed models per subject
   model (intentionality as DV) with random intercepts for family and residual
   response-level variance; report ICCs. Implementation: `statsmodels` mixedlm or
   bridge to R `lme4` via a documented rpy2-optional path — choose one, document why.
2. **Simulation engine:** given variance components and assumed effect sizes (defaults:
   half the pilot's observed MB−MG gap for each interaction contrast, configurable),
   simulate the full design (families × 4 variants × N samples), fit the planned
   contrast, repeat ≥1,000 sims per grid point over item-count × N; output power
   curves per RQ1 sub-question (1a valence-type interaction, 1b blame/praise slope
   difference, 1c typicality×sign and evocativeness×sign, 1d NEU offset).
3. **Decision report:** markdown + PNG output stating chosen N, whether item count
   must grow (and in which cells), at 80% and 90% power. This report is a gate
   artifact attached to the G2 manifest.
4. Seeded, resumable (sim grid checkpoints), runs on a laptop overnight or shards
   trivially.

## Acceptance criteria
- Recovers known variance components from synthetic data generated with specified
  parameters (tolerance test).
- Power monotonically increases with item count and N on the synthetic grid
  (sanity property test).
- End-to-end run on a bundled toy pilot fixture completes < 5 min and emits the
  decision report.
