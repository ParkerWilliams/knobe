"""First look on Ngo's 80 vignettes through OpenRouter, instead of the cluster.

Why this exists (2026-10-12): cluster submission now needs an AWS SSO login
the researcher doesn't have yet (weeks away), and OpenRouter serves only one of
the study's six checkpoints. Parker chose the cheapest instruct model of each
family instead (tools/openrouter_models.yaml). This is therefore an
INDICATIVE first look on substitute, instruct-only models -- not the
FIRST_LOOK.md go/no-go, which names the study's models.

What is reused unchanged: kmp's items, prompts (with and without worked
examples), sampling plan (168 samples per item), seed/temperature rule,
job IDs, ResultRecord rows, run manifest, resume, lock, and missing-response
handling -- by calling kmp.elicit.build_jobs and kmp.elicit._run_locked
directly. Only the engine differs: OpenRouterEngine below sends each chat
prompt (one user message, as kmp's "chat" format) to OpenRouter's
chat-completions API with that job's temperature and seed and kmp's
MAX_TOKENS. Each model is pinned to fixed providers (no fallbacks), and the
provider that answered each request is tallied in <out>.providers.json.
Rows record model_revision = "openrouter:<model id>" and the manifest
records engine = "openrouter", so these rows can't be mistaken for vLLM rows.
Readout is parse_rating on the text, as in kmp; there are no logprobs.

Analysis reuses kmp.checks and analysis/first_look.py unchanged, with
kmp.frame pointed at tools/openrouter_models.yaml instead of the repo
registry.

From the study folder, with OPENROUTER_API_KEY set:
    ../../.venv/bin/python tools/openrouter_first_look.py elicit --out outputs/elicit/or_ngo_verbatim.jsonl
    ../../.venv/bin/python tools/openrouter_first_look.py elicit --out outputs/elicit/or_ngo_verbatim_noex.jsonl --no-examples
    ../../.venv/bin/python tools/openrouter_first_look.py analyze
Add --limit N to elicit a smoke test on the first N storylines' items.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

STUDY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDY))

from knobe.elicit_vllm import EngineResponse  # noqa: E402
from knobe.registry import load_registry, model_key_for  # noqa: E402

from kmp import elicit, prompts, protocol  # noqa: E402
from kmp.items import design_problems, load_items  # noqa: E402

REGISTRY = STUDY / "tools" / "openrouter_models.yaml"
ITEMS = STUDY / "stimuli" / "ngo_verbatim.csv"
URL = "https://openrouter.ai/api/v1/chat/completions"
# Fixed providers per model, no fallbacks (endpoints listed 2026-10-12).
PROVIDERS = {
    "meta-llama/llama-3.1-8b-instruct": ["DeepInfra"],    # fp8; bf16 only at CoreWeave (~10x price)
    "google/gemma-3-4b-it": ["DeepInfra"],
    "mistralai/mistral-nemo": ["Mistral", "Io Net"],
}
RETRY_STATUS = {408, 409, 425, 429, 500, 502, 503, 504, 520, 522, 524}


class OpenRouterEngine:
    """knobe GenerationEngine over OpenRouter chat completions."""

    def __init__(self, api_key: str, concurrency: int = 32, max_retries: int = 8, timeout: float = 60.0):
        self.api_key, self.concurrency, self.max_retries, self.timeout = api_key, concurrency, max_retries, timeout
        self.model_id: str | None = None
        self.providers: Counter = Counter()
        self.errors: Counter = Counter()
        self._lock = threading.Lock()

    def load(self, model_id: str, *, revision: str = "main", **_: object) -> str:
        if model_id not in PROVIDERS:
            raise ValueError(f"{model_id} has no pinned provider in PROVIDERS")
        self.model_id = model_id
        return f"openrouter:{model_id}"

    def _one(self, req) -> EngineResponse | None:
        body = json.dumps({
            "model": self.model_id,
            "messages": req.messages if req.messages is not None else [{"role": "user", "content": req.text}],
            "temperature": req.temperature,
            "seed": req.seed,
            "max_tokens": req.max_tokens,
            "provider": {"order": PROVIDERS[self.model_id], "allow_fallbacks": False},
        }).encode()
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json",
                   "X-Title": "knobe_moral_probe first look"}
        for attempt in range(self.max_retries):
            try:
                with urllib.request.urlopen(urllib.request.Request(URL, body, headers), timeout=self.timeout) as r:
                    data = json.load(r)
                if "error" in data:
                    raise urllib.error.HTTPError(URL, int(data["error"].get("code") or 500), str(data["error"]), None, None)
                text = (data["choices"][0]["message"].get("content") or "")
                with self._lock:
                    self.providers[data.get("provider", "?")] += 1
                return EngineResponse(job_id=req.job_id, raw_response=text, logprobs_0_10=None)
            except urllib.error.HTTPError as e:
                with self._lock:
                    self.errors[e.code] += 1
                if e.code not in RETRY_STATUS:
                    print(f"[openrouter] {req.job_id}: HTTP {e.code} {str(e.reason)[:200]} (not retried)", file=sys.stderr)
                    return None
            except (urllib.error.URLError, TimeoutError, OSError, KeyError, IndexError, json.JSONDecodeError) as e:
                with self._lock:
                    self.errors[type(e).__name__] += 1
            time.sleep(min(60, 2 ** attempt))
        print(f"[openrouter] {req.job_id}: gave up after {self.max_retries} tries", file=sys.stderr)
        return None

    def generate(self, batch) -> list[EngineResponse]:
        with ThreadPoolExecutor(self.concurrency) as ex:
            return [r for r in ex.map(self._one, batch) if r is not None]


def cmd_elicit(a: argparse.Namespace) -> int:
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        print("OPENROUTER_API_KEY is not set", file=sys.stderr)
        return 2
    registry = load_registry(REGISTRY)
    model_keys = sorted(model_key_for(f, "finetuned") for f in registry) if not a.model_keys \
        else [k.strip() for k in a.model_keys.split(",")]
    items = load_items(a.items)
    if a.limit:
        keep = sorted({i.storyline_id for i in items})[: a.limit]
        items = [i for i in items if i.storyline_id in keep]
    if a.allow_draft:
        # Pilot texts (tools/pilot_items_to_kmp.py): drafts that predate the new
        # study's review and role-noun rule. Run as written, on purpose.
        drafts = sum(i.review_status == "draft" for i in items)
        print(f"[openrouter] --allow-draft: {drafts}/{len(items)} draft items, design checks skipped")
        problems = [f"{i.item_id} is {i.review_status}" for i in items if i.review_status == "rejected"]
    else:
        problems = ([] if a.limit else design_problems(items, stage="selected")) + \
            [f"{i.item_id} is {i.review_status}" for i in items if i.review_status != "approved"]
    if problems:
        print("refusing to run:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 2
    examples = () if a.no_examples else protocol.EXAMPLES
    jobs = elicit.build_jobs(prompts.build_subject_prompts(items, examples), model_keys)

    engine = OpenRouterEngine(api_key, concurrency=a.concurrency)
    elicit.build_engine = lambda name: engine          # the only swap: everything else is kmp's
    run_args = argparse.Namespace(out=a.out, engine="openrouter", registry=REGISTRY,
                                  batch_size=a.batch_size, max_tokens=elicit.max_tokens_by_format(a.max_tokens),
                                  no_examples=a.no_examples)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    print(f"[openrouter] {len(jobs)} jobs, models {model_keys}, examples={not a.no_examples} -> {a.out}")
    t0 = time.time()
    with open(elicit.lock_path(a.out), "a") as lock_fh:
        try:
            fcntl.flock(lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(f"another run holds {elicit.lock_path(a.out)}", file=sys.stderr)
            return 2
        rc = elicit._run_locked(run_args, jobs, model_keys)
    side = a.out.with_name(a.out.name + ".providers.json")
    prev = json.loads(side.read_text()) if side.exists() else {"providers": {}, "errors": {}}
    for k, v in engine.providers.items():
        prev["providers"][k] = prev["providers"].get(k, 0) + v
    for k, v in engine.errors.items():
        prev["errors"][str(k)] = prev["errors"].get(str(k), 0) + v
    side.write_text(json.dumps(prev, indent=2) + "\n")
    print(f"[openrouter] rc={rc} in {time.time() - t0:.0f}s; providers {dict(engine.providers)}; "
          f"retried errors {dict(engine.errors)}")
    return rc


def cmd_analyze(a: argparse.Namespace) -> int:
    import kmp.frame
    kmp.frame.default_registry_path = lambda: REGISTRY   # kmp.frame's registry lookup
    kmp.frame.REPARSE = a.reparse                        # re-read pre-0.2 rows with kmp.answer
    from kmp import checks
    sys.path.insert(0, str(STUDY / "analysis"))
    import first_look

    out = STUDY / "outputs"
    name = a.name or "or_ngo_verbatim"
    results = a.results or [out / "elicit" / "or_ngo_verbatim.jsonl"]
    rc = 0
    for res in ([] if a.no_checks else results):          # kmp.checks is per results file
        argv =["--results", str(res), "--items", str(a.items), "--out-dir",
                str(out / "checks" / res.name.removesuffix(".jsonl")), "--stage", "full"]
        noex = res.with_name(res.name.removesuffix(".jsonl") + "_noex.jsonl")
        if noex.exists():
            argv += ["--baseline", str(noex)]
        rc = checks.main(argv) or rc
    rc = first_look.main(["--results", *map(str, results), "--items", str(a.items),
                          "--out", str(out / "first_look" / f"{name}_sign_effects.csv")]) or rc
    return rc


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("elicit")
    e.add_argument("--out", required=True, type=Path)
    e.add_argument("--no-examples", action="store_true")
    e.add_argument("--model-keys")
    e.add_argument("--concurrency", type=int, default=32)
    e.add_argument("--batch-size", type=int, default=256)
    e.add_argument("--limit", type=int, default=0, help="smoke test: first N storylines only")
    e.add_argument("--items", type=Path, default=ITEMS, help="kmp items CSV (default: Ngo verbatim)")
    e.add_argument("--max-tokens", type=int, default=None,
                   help="answer budget for every format (default: protocol.MAX_TOKENS per format)")
    e.add_argument("--allow-draft", action="store_true",
                   help="run draft items as written (pilot texts), skipping the approval and design checks")
    an = sub.add_parser("analyze")
    an.add_argument("--results", type=Path, nargs="+", help="results files (default: the Ngo verbatim run)")
    an.add_argument("--items", type=Path, default=ITEMS)
    an.add_argument("--name", help="output name prefix (default or_ngo_verbatim)")
    an.add_argument("--reparse", action="store_true",
                    help="re-read raw_response with kmp.answer (for rows from runner 0.1)")
    an.add_argument("--no-checks", action="store_true",
                    help="sign-effect table only: kmp.checks writes outputs/checks/<results name>/, which "
                         "would overwrite that run's committed checks (e.g. a --reparse of an old run)")
    a = p.parse_args()
    return cmd_elicit(a) if a.cmd == "elicit" else cmd_analyze(a)


if __name__ == "__main__":
    raise SystemExit(main())
