"""Jev as the subject model, asked natively (kmp/jev_native.py): run, analyze, compare.

Why (Parker, 2026-11-12): is the Knobe effect present in Jev itself, with no
wrapper? Each scenario is Jev's state and each of the chat models' questions is
Jev's own Choice question over labelled 0..10 bubbles -- no chat prompt, no reply
text, no answer reader. kmp/jev_native.py has the sheet and the reasoning.

Subcommands, from the study folder (elicit needs OPENROUTER_API_KEY):
    ../../.venv/bin/python tools/jev_native.py elicit --items <items.csv> --out <run.jsonl> [--allow-draft] [--limit N]
    ../../.venv/bin/python tools/jev_native.py analyze --items <items.csv> --results <run.jsonl> --name <name> \\
        [--experiment nonmoral|foundations]
    ../../.venv/bin/python tools/jev_native.py compare --native <a.csv> --wrapped <b.csv> --out <c.csv>

elicit: one Decisions API call per question, appended to <run.jsonl> as it
arrives (resumes by job_id; one writer per file, <run.jsonl>.lock). The manifest
<run.jsonl>.manifest.json holds the sheet's spec and every question's request
hash; a later run whose sheet differs is refused. --limit N asks only the first
N storylines' questions (a smoke test; a later full run completes the rest).
Exit 0 when every question has an answer, 1 when some calls failed (re-run).

analyze: for each reader (top bubble -> <name>, expected value -> <name>_ev),
reusing the existing code, not reimplementing it:
  outputs/first_look/<name>_sign_effects.csv   analysis/first_look.sign_effects
  outputs/first_look/<name>_arm_effects.csv    analysis/arm_effects.arm_effects (--experiment)
  outputs/checks/<name>/{coverage,anchor_agreement,validity,wording_means}.csv
                                               kmp.checks + tools/jev_subject.wording_means
(B=1999 wild cluster bootstrap by storyline, first_look's seeds.) kmp.checks'
number rates, example copying, example effect and throughput don't apply: every
answer is a bubble, and there are no worked examples.

compare: two sign-effect (or wording_means) tables side by side, e.g. native vs
the 2026-10-22 wrapped run (tools/jev_subject.py).
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

STUDY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDY))
sys.path.insert(0, str(STUDY / "analysis"))

import pandas as pd  # noqa: E402

from kmp import checks, jev_native  # noqa: E402
from kmp.frame import analysis_rows  # noqa: E402
from kmp.items import design_problems, load_items  # noqa: E402
from tools.jev_read import DecisionsClient  # noqa: E402


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _refusals(items, allow_draft: bool) -> list[str]:
    """As tools/jev_subject.py: --allow-draft runs pilot texts as written."""
    if allow_draft:
        return [f"{i.item_id} is {i.review_status}" for i in items if i.review_status == "rejected"]
    return design_problems(items, stage="selected") + \
        [f"{i.item_id} is {i.review_status}" for i in items if i.review_status != "approved"]


def cmd_elicit(a: argparse.Namespace, transport=None) -> int:
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        print("OPENROUTER_API_KEY is not set", file=sys.stderr)
        return 2
    items = load_items(a.items)
    problems = _refusals(items, a.allow_draft)
    if problems:
        print("refusing to run:\n  " + "\n  ".join(problems[:20]), file=sys.stderr)
        return 2
    questions = jev_native.build_questions(items)
    bodies = {q.job_id: jev_native.body_sha256(jev_native.request_body(q)) for q in questions}
    if a.limit:
        keep = {i.item_id for i in items if i.storyline_id in sorted({i.storyline_id for i in items})[:a.limit]}
        asked = [q for q in questions if q.item_id in keep]
    else:
        asked = questions

    a.out.parent.mkdir(parents=True, exist_ok=True)
    with open(jev_native.lock_path(a.out), "a") as lock_fh:
        try:
            fcntl.flock(lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(f"another run holds {jev_native.lock_path(a.out)}", file=sys.stderr)
            return 2
        mpath = jev_native.manifest_path(a.out)
        if mpath.exists():
            old = json.loads(mpath.read_text(encoding="utf-8"))
            changed = sorted(j for j in set(old["bodies"]) & set(bodies) if old["bodies"][j] != bodies[j])
            if old["spec"] != jev_native.SPEC or changed:
                print(f"refusing to run: {a.out} was asked a different sheet (spec {old['spec'][:12]} vs "
                      f"{jev_native.SPEC[:12]}; {len(changed)} question(s) changed, e.g. {changed[:3]})",
                      file=sys.stderr)
                return 2
        mpath.write_text(json.dumps({
            "spec": jev_native.SPEC, "sheet_version": jev_native.SHEET_VERSION, "model": jev_native.MODEL,
            "items": str(a.items), "items_sha256": _sha256(a.items), "n_questions": len(questions),
            "bodies": bodies}, indent=1) + "\n", encoding="utf-8")

        done = jev_native.read_results(a.out)
        todo = [q for q in asked if q.job_id not in done]
        print(f"[jev native] {len(asked)} question(s) asked, {len(todo)} to do -> {a.out}")
        client = DecisionsClient(api_key, transport=transport)
        cost, empty, t0 = 0.0, 0, time.time()
        with ThreadPoolExecutor(a.concurrency) as ex, open(a.out, "a", encoding="utf-8") as fh:
            futures = {ex.submit(client.decide, q.job_id, jev_native.request_body(q)): q for q in todo}
            for n, fut in enumerate(as_completed(futures), 1):
                q, data = futures[fut], fut.result()
                row = jev_native.answer_row(q, data) if data is not None else None
                if row is None:
                    empty += data is not None
                    continue
                fh.write(json.dumps(row) + "\n")
                fh.flush()
                cost += row.get("cost") or 0.0
                if n % 500 == 0:
                    print(f"[jev native] {n}/{len(todo)} ({time.time() - t0:.0f}s, ${cost:.4f})")
    answered = jev_native.read_results(a.out)
    missing = [q.job_id for q in asked if q.job_id not in answered]
    models = Counter(r.get("model") for r in answered.values())
    print(f"[jev native] {len(asked) - len(missing)}/{len(asked)} answered in {time.time() - t0:.0f}s; "
          f"this run ${cost:.4f}; no-probability answers {empty}; retried errors {dict(client.errors)}; "
          f"served by {dict(models)}")
    if missing:
        print(f"[jev native] {len(missing)} missing, e.g. {missing[:3]} (re-run to resume)", file=sys.stderr)
    return 1 if missing else 0


def cmd_analyze(a: argparse.Namespace) -> int:
    import first_look
    from arm_effects import arm_effects
    from tools.jev_subject import wording_means
    items = load_items(a.items)
    outputs = a.outputs
    (outputs / "first_look").mkdir(parents=True, exist_ok=True)
    for reader in jev_native.READERS:
        name = a.name if reader == "top" else f"{a.name}_ev"
        frame = jev_native.native_frame(a.results, items, reader=reader)
        tables = {
            outputs / "first_look" / f"{name}_sign_effects.csv": first_look.sign_effects(frame)}
        if a.experiment:
            tables[outputs / "first_look" / f"{name}_arm_effects.csv"] = arm_effects(analysis_rows(frame),
                                                                                      a.experiment)
        cdir = outputs / "checks" / name
        cdir.mkdir(parents=True, exist_ok=True)
        tables.update({cdir / "coverage.csv": checks.coverage(frame, items, [jev_native.MODEL_KEY]),
                       cdir / "anchor_agreement.csv": checks.anchor_agreement(frame),
                       cdir / "validity.csv": checks.validity(frame),
                       cdir / "wording_means.csv": wording_means(frame)})
        for path, table in tables.items():
            table.to_csv(path, index=False)
        sign = tables[outputs / "first_look" / f"{name}_sign_effects.csv"]
        cols = ["qkey", "n_rows", "mean_bad", "mean_good", "beta_obs", "p_wcb"]
        with pd.option_context("display.width", 200, "display.float_format", "{:.3f}".format):
            print(f"\n== {name}: sign effects ({len(frame)} answers)\n{sign[cols].to_string(index=False)}")
            print(f"== {name}: wording means\n{tables[cdir / 'wording_means.csv'].to_string(index=False)}")
            missing = tables[cdir / "coverage.csv"].query("n_rows == 0")
            print(f"== {name}: {len(missing)} empty coverage cell(s)")
    print(f"\nwrote {outputs / 'first_look'}/{a.name}[_ev]_*.csv and {outputs / 'checks'}/{a.name}[_ev]/")
    return 0


def cmd_compare(a: argparse.Namespace) -> int:
    nat, wrp = pd.read_csv(a.native), pd.read_csv(a.wrapped)
    if "level" in nat.columns:
        nat, wrp = nat[nat["level"] == "model"], wrp[wrp["level"] == "model"]
        keys, vals = ["qkey"], ["mean_bad", "mean_good", "beta_obs", "p_wcb"]
    else:
        keys, vals = ["qkey", "wording_key", "reversed"], ["bad", "good", "bad_minus_good"]
    out = wrp[keys + vals].merge(nat[keys + vals], on=keys, how="outer", suffixes=("_wrapped", "_native"))
    if "beta_obs_native" in out.columns:
        out["beta_change"] = out["beta_obs_native"] - out["beta_obs_wrapped"]
    a.out.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(a.out, index=False)
    with pd.option_context("display.width", 200, "display.float_format", "{:.3f}".format):
        print(out.to_string(index=False))
    print(f"\nwrote {a.out}")
    return 0


def main(argv: list[str] | None = None, transport=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("elicit")
    e.add_argument("--items", required=True, type=Path)
    e.add_argument("--out", required=True, type=Path)
    e.add_argument("--concurrency", type=int, default=32)
    e.add_argument("--limit", type=int, default=0, help="smoke test: the first N storylines only")
    e.add_argument("--allow-draft", action="store_true",
                   help="run draft items as written (pilot texts), skipping the approval and design checks")
    an = sub.add_parser("analyze")
    an.add_argument("--items", required=True, type=Path)
    an.add_argument("--results", required=True, type=Path)
    an.add_argument("--name", required=True)
    an.add_argument("--experiment", choices=("nonmoral", "foundations"),
                    help="also the per-arm sign effects and the arm contrast (analysis/arm_effects.py)")
    an.add_argument("--outputs", type=Path, default=STUDY / "outputs")
    c = sub.add_parser("compare")
    c.add_argument("--native", required=True, type=Path)
    c.add_argument("--wrapped", required=True, type=Path)
    c.add_argument("--out", required=True, type=Path)
    a = p.parse_args(argv)
    if a.cmd == "elicit":
        return cmd_elicit(a, transport)
    return cmd_analyze(a) if a.cmd == "analyze" else cmd_compare(a)


if __name__ == "__main__":
    raise SystemExit(main())
