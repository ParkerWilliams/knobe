"""
Main-experiment elicitation for the vignette pipeline.

Fires Q1 (intentionality), Q2 (blame), Q3 (praise) at one or more SUBJECT
models, using the Raimondi-style prompt format, with the same independent-
completion discipline as curate_vignettes.py: every question is its own
fresh API call, never chained with another question about the same item.

Differences from curate_vignettes.py that make this a genuinely bigger job
(see chat discussion):

1. STOCHASTIC SAMPLING. Curation asked each question once, deterministically.
   The main experiment needs repeated samples at temperature > 0 per item
   per question, because the response-level variance across samples is
   itself part of what the analysis needs (not just each item's mean).
2. MULTIPLE MODEL FAMILIES, PLUGGABLE. Llama/Gemma/Mistral aren't Claude
   models, so "call the model" has no single SDK. This script defines a
   small ModelClient interface and a registry; you fill in the actual
   provider calls (Together/Fireworks/Replicate/HF/local vLLM/etc.) for
   whichever models you and your collaborator land on. One reference
   implementation (Claude via the anthropic SDK) is included, working out
   of the box, so you can test the whole pipeline's plumbing today even
   before the Llama/Gemma/Mistral question is settled -- just don't use it
   as an actual subject model in the real study, per the reviewer-vs-
   subject separation rule from curate_vignettes.py.
3. SCALE + CHECKPOINTING. 3 questions x N samples x many items x several
   models adds up fast, and can't be safely re-run from scratch if it dies
   partway through. This script writes each completed job to disk as soon
   as it's done and skips already-completed jobs on a re-run.

This script makes network calls and will not run inside a sandboxed,
network-disabled shell -- run it in your own environment.

Usage:
    python elicit_main_experiment.py vignettes_curated.csv \\
        --models claude-sonnet-4-6 \\
        --n-samples 10 \\
        --temperature 1.0 \\
        --out results.jsonl
"""

import argparse
import csv
import json
import os
import re
import sys
import time
from abc import ABC, abstractmethod

try:
    import anthropic
except ImportError:
    anthropic = None


# ---------------------------------------------------------------------------
# 1. Prompt construction (Raimondi-style, matches the confirmed-in-chat format)
# ---------------------------------------------------------------------------

MAIN_QUESTION_COLUMNS = {
    "intentionality": "q_intentionality",
    "blame": "q_blame",
    "praise": "q_praise",
}

PROMPT_TEMPLATE = (
    "Read carefully the following scenario and then answer the question "
    "with a number from 0 to 10.\n\n"
    "Scenario: {scenario}\n\n"
    "Question: {question}\n"
    "Answer:"
)


def build_prompt(scenario, question_type, row):
    """One independent prompt for one question type. Called fresh for every
    single API call -- never reused across a multi-turn context. Pulls the
    question text straight from the assembled CSV's own q_intentionality/
    q_blame/q_praise columns (already correctly worded by
    assemble_vignettes.py) rather than reconstructing it here, which is
    both simpler and avoids re-deriving grammar the assembler already got
    right once."""
    question = row[MAIN_QUESTION_COLUMNS[question_type]]
    return PROMPT_TEMPLATE.format(scenario=scenario, question=question)


# ---------------------------------------------------------------------------
# 2. Pluggable model-client interface
# ---------------------------------------------------------------------------

class ModelClient(ABC):
    """One implementation per model family/provider. Add a new subclass and
    register it in MODEL_REGISTRY below to support a new model -- nothing
    else in this file needs to change."""

    @abstractmethod
    def complete(self, prompt: str, temperature: float, max_tokens: int = 10) -> str:
        """Fire ONE completion. Must return the raw text response. Must NOT
        retain any state between calls -- every call is a fresh context."""
        raise NotImplementedError


class ClaudeClient(ModelClient):
    """Working reference implementation. Useful for testing the pipeline's
    plumbing end-to-end today. NOT intended as an actual subject model for
    the real study if Claude is also serving as the curation reviewer --
    see the reviewer/subject separation rule in curate_vignettes.py."""

    def __init__(self, model_name):
        if anthropic is None:
            raise RuntimeError("pip install anthropic")
        self.model_name = model_name
        self.client = anthropic.Anthropic()

    def complete(self, prompt, temperature, max_tokens=10):
        resp = self.client.messages.create(
            model=self.model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in resp.content if b.type == "text").strip()


class TogetherAIClient(ModelClient):
    """PLACEHOLDER, CHAT MODE. For instruct/finetuned models served via
    Together AI's OpenAI-compatible chat endpoint. Fill in with the
    `together` package or requests.post to /v1/chat/completions."""

    def __init__(self, model_name):
        self.model_name = model_name
        raise NotImplementedError(
            "Fill in TogetherAIClient.__init__ and .complete() with the "
            "`together` package (pip install together) or requests calls "
            "to https://api.together.xyz/v1/chat/completions"
        )

    def complete(self, prompt, temperature, max_tokens=10):
        raise NotImplementedError


class TogetherAICompletionClient(ModelClient):
    """PLACEHOLDER, RAW COMPLETION MODE -- for BASE (pretrained, non-
    instruct) checkpoints. Base models generally aren't served through a
    chat template at all; they take plain text and continue it, so this
    hits Together's /v1/completions endpoint (not /v1/chat/completions).
    Our prompt format (plain text ending in "Answer:") already works
    as-is for this -- no prompt changes needed, just a different endpoint.
    Confirm your provider actually hosts the raw base checkpoint before
    committing to it; many providers only host the instruct-tuned version."""

    def __init__(self, model_name):
        self.model_name = model_name
        raise NotImplementedError(
            "Fill in TogetherAICompletionClient.__init__ and .complete() "
            "with requests calls to https://api.together.xyz/v1/completions "
            "(note: /v1/completions, NOT /v1/chat/completions)."
        )

    def complete(self, prompt, temperature, max_tokens=10):
        raise NotImplementedError


class HFInferenceClient(ModelClient):
    """PLACEHOLDER. For models served via Hugging Face Inference Endpoints
    (dedicated or serverless). Fill in with `huggingface_hub.InferenceClient`
    or a requests.post to your endpoint URL."""

    def __init__(self, model_name, endpoint_url=None):
        self.model_name = model_name
        self.endpoint_url = endpoint_url
        raise NotImplementedError(
            "Fill in HFInferenceClient with huggingface_hub.InferenceClient "
            "or requests calls to your endpoint URL."
        )

    def complete(self, prompt, temperature, max_tokens=10):
        raise NotImplementedError


class LocalVLLMClient(ModelClient):
    """PLACEHOLDER. For self-hosted inference via vLLM's OpenAI-compatible
    local server (vllm serve <model> --port 8000). Fill in with an
    `openai`-package client pointed at http://localhost:8000/v1."""

    def __init__(self, model_name, base_url="http://localhost:8000/v1"):
        self.model_name = model_name
        self.base_url = base_url
        raise NotImplementedError(
            "Fill in LocalVLLMClient with the `openai` package pointed at "
            "your local vLLM server's base_url."
        )

    def complete(self, prompt, temperature, max_tokens=10):
        raise NotImplementedError


# Each entry describes ONE model checkpoint: which client class to
# instantiate, and metadata the analysis needs downstream --
# specifically `family` (groups a base+instruct pair together) and
# `tuning_status` ("pretrained" or "finetuned"). RQ1 needs BOTH members of
# a family's pair to run the M_p vs M_f comparison -- registering one
# without the other is a silent way to end up unable to answer RQ1 even
# though the script runs without error, so check_family_pairs() below
# checks for this explicitly before any calls are fired.
MODEL_REGISTRY = {
    "claude-sonnet-4-6": {
        "client_factory": lambda: ClaudeClient("claude-sonnet-4-6"),
        "family": "claude-sonnet-4-6",
        "tuning_status": "finetuned",
        "completion_mode": "chat",
    },
    # TODO, once provider + exact checkpoints are decided, e.g.:
    # "llama-3.1-70b-base": {
    #     "client_factory": lambda: TogetherAICompletionClient("meta-llama/Llama-3.1-70B"),
    #     "family": "llama-3.1-70b", "tuning_status": "pretrained", "completion_mode": "raw",
    # },
    # "llama-3.1-70b-instruct": {
    #     "client_factory": lambda: TogetherAIClient("meta-llama/Llama-3.1-70B-Instruct"),
    #     "family": "llama-3.1-70b", "tuning_status": "finetuned", "completion_mode": "chat",
    # },
    # "gemma-2-27b-base": {
    #     "client_factory": lambda: HFInferenceClient("google/gemma-2-27b"),
    #     "family": "gemma-2-27b", "tuning_status": "pretrained", "completion_mode": "raw",
    # },
    # "gemma-2-27b-instruct": {
    #     "client_factory": lambda: HFInferenceClient("google/gemma-2-27b-it"),
    #     "family": "gemma-2-27b", "tuning_status": "finetuned", "completion_mode": "chat",
    # },
}


def get_client(model_key):
    if model_key not in MODEL_REGISTRY:
        sys.exit(
            f"Unknown model '{model_key}'. Registered models: {list(MODEL_REGISTRY.keys())}. "
            f"Add an entry to MODEL_REGISTRY in this file to support a new model."
        )
    return MODEL_REGISTRY[model_key]["client_factory"]()


def get_metadata(model_key):
    entry = MODEL_REGISTRY[model_key]
    return {"family": entry["family"], "tuning_status": entry["tuning_status"]}


def check_family_pairs(model_keys):
    """Warns (doesn't block -- you might legitimately want to run just one
    side for a quick test) if any requested model's family is missing its
    pretrained/finetuned partner. This is the check that catches the
    'script ran fine but can't answer RQ1' failure mode."""
    families = {}
    for key in model_keys:
        meta = get_metadata(key)
        families.setdefault(meta["family"], set()).add(meta["tuning_status"])

    for family, statuses in families.items():
        missing = {"pretrained", "finetuned"} - statuses
        if missing:
            print(
                f"WARNING: family '{family}' is missing its {sorted(missing)} "
                f"variant among --models. RQ1's M_p vs M_f comparison needs both "
                f"halves of the pair present in the same run (or a matching run) "
                f"to be answerable for this family."
            )


# ---------------------------------------------------------------------------
# 3. Rating parsing (same logic as curate_vignettes.py)
# ---------------------------------------------------------------------------

def parse_rating(raw_text):
    match = re.search(r"\b(10|[0-9])\b", raw_text)
    if match:
        return int(match.group(1)), True
    return None, False


def call_with_retries(client, prompt, temperature, max_tokens=10, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.complete(prompt, temperature, max_tokens)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)


# ---------------------------------------------------------------------------
# 4. Job list construction + checkpointing
# ---------------------------------------------------------------------------

def build_job_list(rows, models, n_samples):
    """One 'job' = one (item, question_type, model, sample_index) tuple --
    the smallest unit of independent-completion work. Fully enumerating
    this up front (rather than nesting loops at call time) is what makes
    checkpointing simple: a job's identity is just these four fields."""
    jobs = []
    for row in rows:
        for question_type in MAIN_QUESTION_COLUMNS:
            for model_key in models:
                for sample_idx in range(n_samples):
                    jobs.append({
                        "variant_id": row["variant_id"],
                        "question_type": question_type,
                        "model": model_key,
                        "sample_idx": sample_idx,
                    })
    return jobs


def load_completed_job_keys(out_path):
    """Reads whatever's already in the output file (from a prior partial
    run) and returns the set of job identities already done, so main()
    can skip them rather than re-spending API calls and re-charging cost."""
    completed = set()
    if not os.path.exists(out_path):
        return completed
    with open(out_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = (rec["variant_id"], rec["question_type"], rec["model"], rec["sample_idx"])
            completed.add(key)
    return completed


def job_key(job):
    return (job["variant_id"], job["question_type"], job["model"], job["sample_idx"])


# ---------------------------------------------------------------------------
# 5. CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input_csv", help="Curated vignette CSV (output of curate_vignettes.py, or assemble_vignettes.py if you're skipping curation for a quick test)")
    parser.add_argument("--models", nargs="+", required=True, help="Model keys from MODEL_REGISTRY, e.g. --models llama-3.1-70b gemma-2-27b mistral-large")
    parser.add_argument("--n-samples", type=int, default=10, help="Stochastic samples per item per question per model")
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--max-tokens", type=int, default=10)
    parser.add_argument("--out", default="main_experiment_results.jsonl")
    args = parser.parse_args()

    with open(args.input_csv, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    row_by_id = {r["variant_id"]: r for r in rows}
    print(f"Loaded {len(rows)} vignette variants from {args.input_csv}")

    clients = {model_key: get_client(model_key) for model_key in args.models}
    check_family_pairs(args.models)

    jobs = build_job_list(rows, args.models, args.n_samples)
    completed = load_completed_job_keys(args.out)
    remaining = [j for j in jobs if job_key(j) not in completed]

    print(f"Total jobs: {len(jobs)}. Already completed (resuming): {len(completed)}. Remaining: {len(remaining)}.")

    with open(args.out, "a", encoding="utf-8") as f:
        for i, job in enumerate(remaining, start=1):
            row = row_by_id[job["variant_id"]]
            prompt = build_prompt(row["scenario"], job["question_type"], row)
            client = clients[job["model"]]

            raw = call_with_retries(client, prompt, args.temperature, args.max_tokens)
            value, ok = parse_rating(raw)
            meta = get_metadata(job["model"])

            record = {
                **job,
                "model_family": meta["family"],
                "tuning_status": meta["tuning_status"],
                "family_id": row.get("family_id", ""),
                "valence": row.get("valence", ""),
                "typicality": row.get("typicality", ""),
                "evocativeness": row.get("evocativeness", ""),
                "temperature": args.temperature,
                "raw_response": raw,
                "parsed_rating": value,
                "parse_ok": ok,
                "timestamp": time.time(),
            }
            f.write(json.dumps(record) + "\n")
            f.flush()

            if i % 50 == 0 or i == len(remaining):
                print(f"  [{i}/{len(remaining)}] done")

    print(f"\nWrote results to {args.out}")


if __name__ == "__main__":
    main()
