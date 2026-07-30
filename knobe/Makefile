.PHONY: check check-wo0 check-wo2a check-wo2bc check-wo1 check-wo3 check-wo5 check-wo4 check-wo6 check-wo7 check-wo8 paper

PYTHON := .venv/bin/python

# `make paper` inputs -- override on the command line for a real release, e.g.
#   make paper RELEASE=v1.0 RESULTS="results/v1.0/results.jsonl"
# Regenerates every number + figure from raw artifacts into
# results/<release>/paper/ (WO-8 §5). The G0 button-press proof itself is the
# end-to-end test in check-wo8.
RELEASE   ?= v1.0
RESULTS   ?= results/$(RELEASE)/results.jsonl
VIGNETTES ?= data/release/$(RELEASE)/vignettes.csv
CURATED   ?= data/release/$(RELEASE)/curated.csv
JOBS      ?= results/$(RELEASE)/jobs.jsonl
PAPER_OUT ?= results/$(RELEASE)/paper

check:
	$(PYTHON) -m pytest

# T0 / Foundation: constants, schemas, parsing, registry, CLI skeleton.
check-wo0:
	$(PYTHON) -m pytest tests/test_constants.py tests/test_schemas.py tests/test_parsing.py tests/test_registry.py tests/test_cli.py -v

# WO-2 Part A: assemble.py port, golden-file byte-identity, release mode.
check-wo2a:
	$(PYTHON) -m pytest tests/test_assemble.py -v

# WO-2 Parts B & C: render.py (prompts.jsonl) + jobs.py (jobs.jsonl,
# seeding fixtures, resume diff).
check-wo2bc:
	$(PYTHON) -m pytest tests/test_render.py tests/test_jobs.py -v

# WO-1: tracking.py (set summaries, tracking-log text, balance math) +
# knobe generate CLI (next-prompt/ingest/approve/status/qa).
check-wo1:
	$(PYTHON) -m pytest tests/test_tracking.py tests/test_generate.py -v

# WO-3: curate.py (async curation engine, resume, reviewer!=subject,
# pair/typicality/category checks, acceptance workflow, --mock).
check-wo3:
	$(PYTHON) -m pytest tests/test_curate.py -v

# WO-5: elicit_vllm.py (GenerationEngine protocol incl. FakeEngine,
# manifest guard, resume/shard/durability loop, throughput reporting) +
# knobe.storage (S3/local/null adapter). Never requires torch/vllm/boto3.
check-wo5:
	$(PYTHON) -m pytest tests/test_storage.py tests/test_elicit.py -v

# WO-4: power.py (pilot variance decomposition via statsmodels mixedlm +
# Westfall-style simulation-based power grid) + power_sim.py (DGP/contrast
# simulators) + `knobe power estimate/simulate/report/run` CLI.
check-wo4:
	$(PYTHON) -m pytest tests/test_power.py -v

# WO-6: mech/backend.py (ResidualAccess protocol; FakeBackend with REAL
# patching semantics + planted-signal mode; guarded TL/nnsight impls),
# cache_acts.py (activation cache + δ_l), patch.py (layer sweep + metrics +
# capability hook). GPU-free: the gpu-marked TL/nnsight + real-model tests
# are deselected by default (pyproject addopts -m "not gpu").
check-wo6:
	$(PYTHON) -m pytest tests/test_mech.py -v

# WO-7: mech/probes.py (per-layer linear probes; scaffold-split leakage
# control; residualization; RQ2 localization/dissociation) + mech/decompose.py
# (RQ3 patch decomposition via MixedLM; RQ4 probe alignment + dual nulls;
# Gemma Scope stub). GPU-free: planted-signal synthetic caches + hand-built
# patch metrics; the real SAE/backend paths are gpu-marked.
check-wo7:
	$(PYTHON) -m pytest tests/test_mech_probes.py -v

# WO-8: analysis/ (ingest.py stream-join + never-silent exclusions ledger;
# models.py RQ1 LMMs + contrasts.yaml governance, LMM-primary/ordinal-
# sensitivity; figstyle.py + figures.py; report.py paper artifacts). The
# `slow` 200-sim Type-I test is deselected by default (a 25-sim smoke stays
# in the suite); run it with `pytest -m slow`.
check-wo8:
	$(PYTHON) -m pytest tests/test_analysis.py -v

# `make paper`: regenerate every number + figure from raw artifacts into
# results/<release>/paper/ (WO-8 §5). Override RELEASE/RESULTS/... for a real
# run; see the variable block at the top of this file.
paper:
	$(PYTHON) -m knobe analyze --release $(RELEASE) --results $(RESULTS) \
		--vignettes $(VIGNETTES) --curated $(CURATED) --jobs $(JOBS) \
		--out-dir $(PAPER_OUT)
