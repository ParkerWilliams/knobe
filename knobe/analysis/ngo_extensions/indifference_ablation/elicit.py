"""Elicitation for the indifference-clause ablation: a thin wrapper around
``../nonmoral_pilot/elicit.py``, NOT a copy of it.

The pilot script's ``main()`` already does everything this run needs --
engine abstraction, frozen seeding rule, registry resolution, the Raimondi
prompt frame, raw-completion format, logprob capture, job_id
checkpoint/resume, production ``ResultRecord`` schema. What it hard-codes is
four module globals: which CSV to read, where to write, the release string
fed to ``derive_temperature_and_seed``, and the question list. This wrapper
imports the pilot module by path, rebinds exactly those four (plus
``RUNNER_VERSION``, so rows are attributable to this run), and calls its
``main()``. Every function the pilot uses reads those names as module
globals at call time, so rebinding is sufficient -- verified end-to-end with
``--engine fake`` (see Usage).

Why a wrapper rather than adding ``--dataset``/``--questions`` flags to the
pilot script: that file produced the committed pilot results, and editing it
now would put a post-hoc diff between the published rows' ``runner_version``
and the code that carries that label. The wrapper leaves it byte-identical.

Seeding: the pilot's rule, sha256(release, prompt_id, model_key,
sample_idx), with a NEW release string. The ``indifferent`` level therefore
re-elicits the pilot's original prompt texts on fresh seeds -- an
independent replication of the pilot's claim-9 cells, not a copy of them.

Usage (from the knobe repo root):
    # zero-GPU end-to-end check
    .venv/bin/python analysis/ngo_extensions/indifference_ablation/elicit.py \
        --engine fake --n-samples 2 --out /tmp/indiff_fake.jsonl

    # real run (cluster runner passes these)
    .venv/bin/python analysis/ngo_extensions/indifference_ablation/elicit.py \
        --engine vllm --n-samples 25 --model-keys llama-3.1-8b-instruct \
        --questions q_blame,q_praise,q_intentionality

Any flag not listed below is forwarded to the pilot script unchanged
(``--engine``, ``--n-samples``, ``--batch-size``, ``--model-keys``,
``--registry``).
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PILOT_ELICIT = HERE.parent / "nonmoral_pilot" / "elicit.py"

RELEASE = "ngo_extensions_indifference_ablation_v1"
RUNNER_VERSION = "ngo_extensions_indifference_ablation_elicit-0.1"
DEFAULT_DATASET = HERE / "outputs" / "indifference_ablation_dataset.csv"
DEFAULT_OUT = HERE / "outputs" / "elicit_results.jsonl"
ALL_QUESTIONS = ["q_intentionality", "q_blame", "q_praise"]


def main() -> None:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    p.add_argument("--questions", default=",".join(ALL_QUESTIONS),
                   help="comma-separated subset of q_intentionality,q_blame,q_praise")
    ours, passthrough = p.parse_known_args()

    questions = [q.strip() for q in ours.questions.split(",") if q.strip()]
    bad = sorted(set(questions) - set(ALL_QUESTIONS))
    if bad or not questions:
        print(f"invalid --questions {bad or questions}; valid: {ALL_QUESTIONS}", file=sys.stderr)
        sys.exit(2)

    spec = importlib.util.spec_from_file_location("nonmoral_pilot_elicit", PILOT_ELICIT)
    pilot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pilot)
    pilot.DATASET_PATH = ours.dataset
    pilot.OUT_PATH = ours.out
    pilot.RELEASE = RELEASE
    pilot.RUNNER_VERSION = RUNNER_VERSION
    pilot.QUESTION_TYPES = questions

    print(f"[indiff] dataset={ours.dataset} out={ours.out} questions={questions} release={RELEASE}")
    sys.argv = [str(PILOT_ELICIT), *passthrough]
    pilot.main()


if __name__ == "__main__":
    main()
