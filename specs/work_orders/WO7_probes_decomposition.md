# WO-7 — Probes, patch decomposition, probe-alignment (RQ2/RQ3/RQ4)
**Stage:** S7 (probe training local or H200 — inputs are the shipped-back caches).
**Depends on:** WO-6 caches + patch results; curated ratings (WO-3). **Blocks:** S8
mechanistic write-up.

## Objective
`mech/probes.py` + `mech/decompose.py`: train per-layer linear probes for each
construct, test localization dissociation (RQ2), decompose patch effects by construct
(RQ3), and test alignment of patch-induced activation shifts with probe directions
(RQ4). Optional Gemma Scope upgrade for Gemma-2 models.

## Requirements
1. **Probe targets** (spec §3.9), per model per layer, on final-token residuals:
   classification probes (moral vs nonmoral valence; bad vs good sign; common vs
   uncommon condition; low vs high evocativeness condition; NEU vs valenced) and ridge
   regression probes (curation severity, vividness, typicality_perception; behavioral
   mean intentionality and blame per item from S5).
2. **Leakage control (hard rule):** train/test splits by *set/scaffold* (families
   sharing agent/goal/actions must never straddle a split), stratified by domain.
   Domain-held-out generalization reported as a secondary metric.
3. **Confound control:** constructs correlate across items. For every probe, also
   report the *residualized* version (target residualized on the other constructs via
   OLS at the item level) and partial-correlation localization curves. RQ2 claims of
   "distinct localization" must be made on residualized probes; raw curves are
   descriptive only.
4. **RQ2 outputs:** per-construct accuracy/R² × layer curves with family-split CIs;
   dissociation stats (are peak layers/subspaces distinct? — bootstrap over families;
   subspace overlap via principal angles between probe weight spans).
5. **RQ3 decomposition:** from WO-6 patch metrics, one table + figure per model:
   layer patched × component gap (Δ_moral, Δ_nonmoral, E_typ, E_evoc, NEU offset),
   normalized to unpatched baselines; test uniform-suppression vs selective-suppression
   (interaction of patch × component in a mixed model over families).
6. **RQ4 probe alignment:** for each patched config, compute Δh = patched − unpatched
   final-token residual per item at downstream layers; report cos(Δh̄, probe_c
   direction) per construct c, against a null of random directions matched for
   dimensionality (and a stronger null: random *probe-like* directions trained on
   permuted labels). Evocativeness probe explicitly flagged exploratory (DR §6.1).
7. **Gemma Scope option (config-gated):** encode unpatched/patched residuals with the
   pretrained SAE at matched layers; report top-k features by |Δ activation|, with
   Neuronpedia feature labels where available. Secondary, descriptive.

## Acceptance criteria
- Synthetic recovery test: planted linear signal for construct A at layer i and B at
  layer j is recovered with correct dissociation calls; residualization removes a
  planted confound.
- Split-leakage test: shuffling family ids across sets breaks the split builder
  (assert it detects and errors).
- Full run on debug-model caches < 1 hr CPU; all figures/tables emitted to
  `results/<release>/mech_report/`.
