"""Jev reads the replies of a finished run: a second reader beside kmp.answer.

Why (Parker, 2026-10-20): Jev returns a probability for each option it is
given, so asking it "which number from 0 to 10 does this reply give, or
none?" is the same question kmp.answer answers -- an independent check on the
reader, with no new subject-model calls. It is a cross-check: kmp.answer stays
the reader of record (DESIGN.md amendment 2026-10-13). The question, options
and reading rule are in kmp/jev.py.

Subcommands, from the study folder with OPENROUTER_API_KEY set:
    ../../.venv/bin/python tools/jev_read.py read --items <items.csv> --results <run.jsonl> [...] [--sample N]
    ../../.venv/bin/python tools/jev_read.py jitter --items <items.csv> --results <run.jsonl> [...]
    ../../.venv/bin/python tools/jev_read.py compare --name <name> --results <run.jsonl> [...]
    ../../.venv/bin/python tools/jev_read.py sign-compare --regex <a.csv> --jev <b.csv> --out <c.csv>

read: one Jev call per reply, written to <results>.jev.jsonl (resumes by
job_id; --sample N reads a fixed hash-ordered N rows per file first, and a
later full read completes the rest). Empty replies are not sent and read as
"none". The question Jev sees is rebuilt from the items file and must hash
to the run manifest's prompt text (kmp.jev.question_texts).
jitter: re-reads a fixed hash-chosen share of replies (--frac, default 5%)
--repeat times (default 3) into <results>.jev_jitter.jsonl.
compare: regex vs Jev agreement per file x question, and jitter, into
outputs/first_look/<name>_reader_agreement.csv and <name>_jev_jitter.csv;
disagreeing replies go to outputs/elicit/<name>_reader_disagreements.jsonl
(local, gitignored: it quotes replies).
sign-compare: a regex and a Jev sign/arm effect table side by side.

Analyses on Jev's readings: --reader jev (or jev_ev) on
tools/openrouter_first_look.py analyze, analysis/arm_effects.py and
analysis/parse_rate_by_sign.py.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
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

import pandas as pd  # noqa: E402
from knobe.schemas import ResultRecord, read_jsonl  # noqa: E402

from kmp import elicit, jev  # noqa: E402
from kmp.items import Item, load_items  # noqa: E402
from kmp.prompts import parse_prompt_id  # noqa: E402
from tools.openrouter_first_look import RETRY_STATUS  # noqa: E402

RETRY = RETRY_STATUS | {529}            # the Decisions API adds 529 (provider overloaded)
STOP = {401, 402, 403, 404}             # key, credit or model problems: every later call would fail too
AGREE_TOL = 0.5                         # a decimal regex reading (6.5) agrees with either neighbour


class DecisionsClient:
    """OpenRouter Decisions API, with the chat engine's retry rule (tools/openrouter_first_look.py)."""

    def __init__(self, api_key: str, max_retries: int = 8, timeout: float = 60.0, transport=None):
        self.api_key, self.max_retries, self.timeout = api_key, max_retries, timeout
        self.transport = transport or self._post
        self.errors: Counter = Counter()
        self.stopped = False
        self._lock = threading.Lock()

    def _post(self, body: dict) -> dict:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json",
                   "X-Title": "knobe_moral_probe jev reader"}
        req = urllib.request.Request(jev.URL, json.dumps(body).encode(), headers)
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            data = json.load(r)
        if "error" in data:
            raise urllib.error.HTTPError(jev.URL, int(data["error"].get("code") or 500), str(data["error"]), None, None)
        return data

    def decide(self, job_id: str, body: dict) -> dict | None:
        for attempt in range(self.max_retries):
            if self.stopped:
                return None
            try:
                data = self.transport(body)
                if not data["answers"][jev.QUESTION_KEY]["probabilities"]:
                    raise KeyError("probabilities")
                return data
            except urllib.error.HTTPError as e:
                with self._lock:
                    self.errors[e.code] += 1
                if e.code not in RETRY:
                    print(f"[jev] {job_id}: HTTP {e.code} {str(e.reason)[:200]} (not retried)", file=sys.stderr)
                    if e.code in STOP:
                        self.stopped = True
                    return None
            except (urllib.error.URLError, TimeoutError, OSError, KeyError, TypeError, json.JSONDecodeError) as e:
                with self._lock:
                    self.errors[type(e).__name__] += 1
            time.sleep(min(60, 2 ** attempt))
        print(f"[jev] {job_id}: gave up after {self.max_retries} tries", file=sys.stderr)
        return None


def _unit(job_id: str, salt: str = "") -> float:
    """A fixed number in [0, 1) per job_id, for hash-chosen samples."""
    return int(hashlib.sha256(f"{salt}{job_id}".encode()).hexdigest()[:12], 16) / 16 ** 12


def read_file(path: Path, items: list[Item], client: DecisionsClient, concurrency: int = 32,
              sample: int | None = None, jitter: tuple[float, int] | None = None, batch_size: int = 512) -> int:
    """Read one results file into its sidecar (or its jitter file). 0 = every
    selected row has a reading; 1 = some calls failed (re-run to resume)."""
    path = Path(path)
    manifest = json.loads(elicit.manifest_path(path).read_text(encoding="utf-8"))
    questions = jev.question_texts(items, manifest)
    records = read_jsonl(path, ResultRecord)
    unknown = sorted({r.prompt_id for r in records} - set(questions))
    if unknown:
        raise ValueError(f"{path}: {len(unknown)} prompt_id(s) not in its manifest, e.g. {unknown[:5]}")
    if jitter:
        frac, repeat = jitter
        out = jev.jitter_path(path)
        done = {(r["job_id"], r["read_idx"]) for r in jev.read_rows(out)}
        todo = [(r, k) for r in records if (r.raw_response or "").strip() and _unit(r.job_id, "jitter:") < frac
                for k in range(1, repeat + 1) if (r.job_id, k) not in done]
    else:
        out = jev.sidecar_path(path)
        done = set(jev.read_sidecar(out))
        chosen = records if sample is None else sorted(records, key=lambda r: _unit(r.job_id))[:sample]
        todo = [(r, 0) for r in chosen if r.job_id not in done]
    print(f"[jev] {path.name}: {len(todo)} reading(s) to do -> {out.name}")
    if not todo:
        return 0

    def call(rk):
        rec, _ = rk
        return client.decide(rec.job_id, jev.request_body(questions[rec.prompt_id], rec.raw_response))

    missing, cost, t0 = 0, 0.0, time.time()
    with open(out.with_name(out.name + ".lock"), "a") as lock_fh:
        try:
            fcntl.flock(lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(f"another run holds {out.name}.lock", file=sys.stderr)
            return 2
        with open(out, "a", encoding="utf-8") as fh, ThreadPoolExecutor(concurrency) as ex:
            for start in range(0, len(todo), batch_size):
                chunk = todo[start:start + batch_size]
                empty = [(r, k) for r, k in chunk if not (r.raw_response or "").strip()]
                sent = [(r, k) for r, k in chunk if (r.raw_response or "").strip()]
                rows = [jev.reading_row(r.job_id, None, read_idx=k, note="empty reply") for r, k in empty]
                failed = 0
                for (rec, k), data in zip(sent, ex.map(call, sent)):
                    if data is None:
                        failed += 1
                        continue
                    rows.append(jev.reading_row(rec.job_id, data["answers"][jev.QUESTION_KEY], read_idx=k,
                                                model=data.get("model"), usage=data.get("usage")))
                for row in rows:
                    cost += row["cost"] or 0.0
                    fh.write(json.dumps(row) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
                missing += failed
                print(f"[jev] {path.name}: {min(start + batch_size, len(todo))}/{len(todo)} "
                      f"({time.time() - t0:.0f}s, ${cost:.4f}, missing {missing}, errors {dict(client.errors)})")
                if client.stopped or (sent and failed == len(sent)):
                    print("[jev] stopped: " + ("a key, credit or model error" if client.stopped else
                                               "no call in this batch succeeded") + ", so later calls would fail too",
                          file=sys.stderr)
                    client.stopped = True
                    missing += len(todo) - start - len(chunk)
                    break
    return 1 if missing else 0


def _agreement(rec: dict, reading: dict) -> str:
    regex_ok, jev_ok = bool(rec["parse_ok"]), bool(reading["ok"])
    if regex_ok and jev_ok:
        return "agree" if abs(float(rec["parsed_rating"]) - reading["rating"]) <= AGREE_TOL else "differ"
    return {(True, False): "regex_only", (False, True): "jev_only"}.get((regex_ok, jev_ok), "neither")


def compare(results: list[Path], name: str, out_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    agree_rows, jitter_rows, disagreements = [], [], []
    for path in results:
        recs = pd.DataFrame([r.model_dump() for r in read_jsonl(path, ResultRecord)])
        readings = jev.read_sidecar(jev.sidecar_path(path))
        recs = recs[recs["job_id"].isin(readings)]
        recs["qkey"] = [parse_prompt_id(p)[1] for p in recs["prompt_id"]]
        recs["status"] = [_agreement(r, readings[r["job_id"]]) for r in recs.to_dict("records")]
        for col in ("rating", "ev", "confidence", "p_none", "cost"):
            recs[f"jev_{col}"] = [readings[j][col] for j in recs["job_id"]]
        recs["ev_minus_top"] = (recs["jev_ev"] - recs["jev_rating"]).abs()
        for qkey, g in [*recs.groupby("qkey"), ("ALL", recs)]:
            n = Counter(g["status"])
            both = n["agree"] + n["differ"]
            agree_rows.append({
                "results": path.name.removesuffix(".jsonl"), "model_key": g["model_key"].iloc[0], "qkey": qkey,
                "n_read": len(g), "regex_ok": int(g["parse_ok"].sum()),
                "jev_ok": int(n["agree"] + n["differ"] + n["jev_only"]), "both_ok": both,
                "agree": n["agree"], "agree_rate": n["agree"] / both if both else None, "differ": n["differ"],
                "regex_only": n["regex_only"], "jev_only": n["jev_only"], "neither": n["neither"],
                "mean_confidence": g["jev_confidence"].mean(), "mean_p_none": g["jev_p_none"].mean(),
                "mean_abs_ev_minus_top": g["ev_minus_top"].mean(), "cost_usd": g["jev_cost"].fillna(0).sum(),
            })
        bad = recs[recs["status"].isin(["differ", "regex_only", "jev_only"])]
        disagreements += [{"results": path.name, "job_id": r["job_id"], "qkey": r["qkey"], "status": r["status"],
                           "regex": r["parsed_rating"], "jev": r["jev_rating"], "jev_ev": r["jev_ev"],
                           "jev_p_none": r["jev_p_none"], "reply": r["raw_response"]}
                          for r in bad.to_dict("records")]

        first = {j: r for j, r in readings.items()}
        again = [r for r in jev.read_rows(jev.jitter_path(path)) if r["job_id"] in first]
        if again:
            by_job: dict[str, list[dict]] = {}
            for r in again:
                by_job.setdefault(r["job_id"], []).append(r)
            devs = [abs(r["ev"] - first[j]["ev"]) for j, rs in by_job.items() for r in rs
                    if r["ev"] is not None and first[j]["ev"] is not None]
            jitter_rows.append({
                "results": path.name.removesuffix(".jsonl"), "n_replies": len(by_job), "n_rereads": len(again),
                "top_flip_rate": sum(any(r["rating"] != first[j]["rating"] for r in rs) for j, rs in by_job.items())
                / len(by_job),
                "ok_flip_rate": sum(any(r["ok"] != first[j]["ok"] for r in rs) for j, rs in by_job.items())
                / len(by_job),
                "mean_abs_ev_change": sum(devs) / len(devs) if devs else None,
                "max_abs_ev_change": max(devs) if devs else None,
                "cost_usd": sum(r["cost"] or 0.0 for r in again),
            })
    agreement, jitter = pd.DataFrame(agree_rows), pd.DataFrame(jitter_rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    agreement.to_csv(out_dir / f"{name}_reader_agreement.csv", index=False)
    if not jitter.empty:
        jitter.to_csv(out_dir / f"{name}_jev_jitter.csv", index=False)
    local = STUDY / "outputs" / "elicit" / f"{name}_reader_disagreements.jsonl"
    with open(local, "w", encoding="utf-8") as fh:
        for d in disagreements:
            fh.write(json.dumps(d) + "\n")
    print(f"[jev] {len(disagreements)} disagreeing replies -> {local}")
    return agreement, jitter


SIGN_KEYS = ("level", "cell", "family", "tuning_status", "model_key", "qkey", "arm", "term")
SIGN_VALUES = ("n_rows", "number_rate", "mean_bad", "mean_good", "beta_obs", "p_wcb")


def sign_compare(regex_csv: Path, jev_csv: Path) -> pd.DataFrame:
    a, b = pd.read_csv(regex_csv), pd.read_csv(jev_csv)
    keys = [k for k in SIGN_KEYS if k in a.columns and k in b.columns]
    vals = [v for v in SIGN_VALUES if v in a.columns and v in b.columns]
    m = a[keys + vals].merge(b[keys + vals], on=keys, how="outer", suffixes=("_regex", "_jev"), validate="one_to_one")
    m["beta_jev_minus_regex"] = m["beta_obs_jev"] - m["beta_obs_regex"]
    return m


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    for cmd in ("read", "jitter"):
        s = sub.add_parser(cmd)
        s.add_argument("--results", type=Path, nargs="+", required=True)
        s.add_argument("--items", type=Path, required=True, help="the kmp items CSV the run was elicited from")
        s.add_argument("--concurrency", type=int, default=32)
        if cmd == "read":
            s.add_argument("--sample", type=int, help="read only a fixed hash-ordered N rows per file")
        else:
            s.add_argument("--frac", type=float, default=0.05)
            s.add_argument("--repeat", type=int, default=3)
    c = sub.add_parser("compare")
    c.add_argument("--results", type=Path, nargs="+", required=True)
    c.add_argument("--name", required=True, help="output name prefix, e.g. or_v2jev_ngo_verbatim")
    sc = sub.add_parser("sign-compare")
    sc.add_argument("--regex", type=Path, required=True)
    sc.add_argument("--jev", type=Path, required=True)
    sc.add_argument("--out", type=Path, required=True)
    a = p.parse_args()

    if a.cmd == "compare":
        compare(a.results, a.name, STUDY / "outputs" / "first_look")
        return 0
    if a.cmd == "sign-compare":
        sign_compare(a.regex, a.jev).to_csv(a.out, index=False)
        return 0
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        print("OPENROUTER_API_KEY is not set", file=sys.stderr)
        return 2
    items = load_items(a.items)
    client = DecisionsClient(api_key)
    rc = 0
    for res in a.results:
        jitter = (a.frac, a.repeat) if a.cmd == "jitter" else None
        rc = read_file(res, items, client, a.concurrency, sample=getattr(a, "sample", None), jitter=jitter) or rc
        if client.stopped:
            return 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
