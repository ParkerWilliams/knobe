"""Does a 0-10 scale on Ngo's yes/no intentionality question fix Llama-3.1-8B-Instruct's number rate?

Llama-3.1-8B-Instruct (a study model; also served on OpenRouter) answers intentionality w1,
"Did {agent} intentionally {effect}?", with a bare "Yes" or "No" about half the time (DESIGN.md
amendment 2026-10-13, "still open"). This compares w1 with two candidates that keep Ngo's question
and append a scale:
  w1a  "... Answer on a scale from 0 (definitely not) to 10 (definitely yes)."
  w1b  "... Answer with a number from 0 (no) to 10 (yes)."
on Ngo's 80 verbatim items, with everything else as in the real run: the worked examples, the chat
format, kmp.elicit's job IDs and its seed/temperature rule (knobe.jobs.derive_temperature_and_seed:
sha256 of RELEASE, prompt_id, model_key, sample_idx), protocol.MAX_TOKENS (chat 512), and kmp.answer
as the reader. Only sample_idx < --samples is run (default 20, above kmp's 8 per intentionality
wording, so every sample runs).

Reuses tools/openrouter_first_look.OpenRouterEngine (the DeepInfra pin, no fallbacks) and
kmp.elicit.build_jobs / to_request / to_result; nothing about the prompt differs from kmp's except the
wording. Raw replies go to --out (gitignored outputs/elicit/), their finish reasons to the
kmp.elicit sidecar, and the summary table to --summary.

From the study folder, with OPENROUTER_API_KEY set:
    ../../.venv/bin/python -m analysis.intentionality_wording_test
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import pandas as pd
from knobe.schemas import append_jsonl, read_jsonl, ResultRecord

from kmp import elicit, prompts, protocol
from kmp.items import load_items
from tools.openrouter_first_look import OpenRouterEngine

STUDY = Path(__file__).resolve().parents[1]
# Ngo's question, as w1 read before the 2026-10-22 change (protocol's w1 is now the w1a below).
NGO_W1 = "Did {agent} intentionally {effect}?"
CANDIDATES = {
    "w1": NGO_W1,
    "w1a": NGO_W1 + " Answer on a scale from 0 (definitely not) to 10 (definitely yes).",
    "w1b": NGO_W1 + " Answer with a number from 0 (no) to 10 (yes).",
}
MODEL_KEY, MODEL_ID = "llama-3.1-8b-instruct", "meta-llama/llama-3.1-8b-instruct"


def build(items, samples: int) -> list[elicit.Job]:
    specs = []
    for key, template in CANDIDATES.items():
        for item in items:
            text = prompts.render_text(item.scenario, prompts.render_question(item, template))
            specs.append(prompts.PromptSpec(stem=f"{item.item_id}::intentionality::{key}", item_id=item.item_id,
                                            qkey="intentionality", wording_key=key, reversed=False, text=text,
                                            n_samples=protocol.n_samples("intentionality"),
                                            text_sha256=prompts.sha256_for_text(text)))
    jobs = elicit.build_jobs(specs, [MODEL_KEY])
    return [j for j in jobs if j.sample_idx < samples]


def summarize(rows: list[ResultRecord], finish: dict, items) -> pd.DataFrame:
    sign = {i.item_id: i.sign for i in items}
    df = pd.DataFrame([{"wording": r.prompt_id.split("::")[2], "sign": sign[r.prompt_id.split("::")[0]],
                        "ok": r.parse_ok, "rating": r.parsed_rating, "raw": r.raw_response,
                        "finish": (finish.get(r.job_id) or {}).get("finish_reason")} for r in rows])
    out = []
    for w, g in df.groupby("wording"):
        rated = g[g["ok"]]
        yes_no = g["raw"].str.strip().str.match(r"(?i)^(yes|no)\b")
        means = rated.groupby("sign")["rating"].mean()
        out.append({"wording": w, "template": CANDIDATES[w], "n": len(g), "number_rate": g["ok"].mean(),
                    "yes_no_share": yes_no.mean(), "cut_off_share": (g["finish"] == "length").mean(),
                    "not_recorded": int(g["finish"].isna().sum()),
                    "number_rate_bad": g.loc[g["sign"] == "bad", "ok"].mean(),
                    "number_rate_good": g.loc[g["sign"] == "good", "ok"].mean(),
                    "mean_bad": means.get("bad"), "mean_good": means.get("good"),
                    "bad_minus_good": means.get("bad", float("nan")) - means.get("good", float("nan"))})
    return pd.DataFrame(out)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--items", type=Path, default=STUDY / "stimuli" / "ngo_verbatim.csv")
    p.add_argument("--samples", type=int, default=20)
    p.add_argument("--out", type=Path, default=STUDY / "outputs" / "elicit" / "wording_test_llama.jsonl")
    p.add_argument("--summary", type=Path, default=STUDY / "outputs" / "first_look" / "intentionality_wording_test.csv")
    p.add_argument("--concurrency", type=int, default=16)
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args(argv)
    items = load_items(a.items)
    jobs = build(items, a.samples)
    per = min(a.samples, protocol.n_samples("intentionality"))
    print(f"{len(jobs)} jobs ({len(CANDIDATES)} wordings x {len(items)} items x {per} samples)")
    if a.dry_run:
        print(jobs[0].text[-400:])
        return 0
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        print("OPENROUTER_API_KEY is not set", file=sys.stderr)
        return 2
    done = {r.job_id for r in read_jsonl(a.out, ResultRecord)} if a.out.exists() else set()
    todo = [j for j in jobs if j.job_id not in done]
    engine = OpenRouterEngine(api_key, concurrency=a.concurrency)
    revision = engine.load(MODEL_ID)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    budgets = elicit.max_tokens_by_format()
    with open(a.out, "a", encoding="utf-8") as fh, open(elicit.finish_path(a.out), "a", encoding="utf-8") as ffh:
        for start in range(0, len(todo), 256):
            batch = todo[start:start + 256]
            requests = [elicit.to_request(j, budgets) for j in batch]
            responses = {r.job_id: r for r in engine.generate(requests)}
            for job, req in zip(batch, requests):
                resp = responses.get(job.job_id)
                if resp is None:
                    continue
                append_jsonl(elicit.to_result(job, req, resp, revision), fh)
                ffh.write(json.dumps(elicit.finish_row(resp)) + "\n")
            print(f"  {min(start + 256, len(todo))}/{len(todo)}", flush=True)
    rows = read_jsonl(a.out, ResultRecord)
    table = summarize(rows, elicit.read_finish(a.out), items)
    a.summary.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(a.summary, index=False)
    print(table.drop(columns="template").to_string(index=False))
    print(f"providers {dict(engine.providers)}; errors {dict(engine.errors)}; missing {len(jobs) - len(rows)}")
    return 0 if len(rows) == len(jobs) else 1


if __name__ == "__main__":
    raise SystemExit(main())
