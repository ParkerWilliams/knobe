# WO-1 — Generation tooling: scale the matrix from 105 to 250 families
**Stage:** S1 (local). **Depends on:** master spec §3.1. **Blocks:** G2 freeze.
Generation itself stays human-in-the-loop (DR §14); this work order builds the tooling
that makes the remaining ~145 families fast and drift-free.

## Objective
A `knobe generate` CLI workflow that: prepares per-set prompts (GS §8.2) from the
current matrix, ingests one returned CSV set (5 families) at a time, validates it
immediately, updates the tracking log, and enforces balance targets — so a human (or a
supervised LLM session) can run the GS §10.5 cadence without hand-bookkeeping.

## Inputs
- `data/authoring/ALL_DOMAINS_master_matrix.csv` (105 families, current state).
- The static system prompt text (GS §8.1) — store verbatim in `constants.py`.
- `update_tracking_log.py` (port into `src/knobe/tracking.py`).

## Requirements
1. `knobe generate next-prompt --domain ENV` → emits the exact per-set prompt block
   (GS §8.2) including the auto-built "already used" tracking log and the recommended
   nonmoral subdomain for this set (rebalancing logic below).
2. `knobe generate ingest set.csv` → runs full S2 validation (structural checks from
   `assemble.py`) + duplicate-storyline heuristics (agent-name reuse, goal-similarity
   flag) against the existing matrix BEFORE merge; on pass, appends to the authoring
   matrix with provenance columns (`generator_model`, `ingest_date`, `human_approved`
   default false). A human flips `human_approved` after review; only approved rows
   count toward targets.
3. **Balance enforcement (hard):** target end-state per domain = 5 sets × 5 valences;
   nonmoral subdomains across the *full* matrix must end within 2× of each other.
   Current deficit to steer toward: etiquette (0), prudential (2) vs aesthetic (24),
   procedural (16). The next-prompt command must inject the needed subdomain as an
   instruction, not a suggestion, until the deficit closes.
4. `knobe generate status` → dashboard table: families per domain×valence, subdomain
   tallies, approval backlog, agent-name diversity summary (GS §10.4).
5. Batch-QA support: `knobe generate qa --domain X` emits the GS §8.3 prompt with the
   domain's matrix inlined.

## Acceptance criteria
- Round-trip test: ingesting a synthetic valid set updates matrix + tracking log;
  ingesting each documented failure mode (banned word, "to"-prefixed goal, noun-phrase
  outcome_verb, NMB missing subdomain, duplicate agent within domain) is rejected with
  the specific error.
- `status` output on the real current matrix reports exactly the imbalance stated
  above (regression-pins the counts).
- No network calls anywhere in this WO (prompts are emitted for a human to run).
