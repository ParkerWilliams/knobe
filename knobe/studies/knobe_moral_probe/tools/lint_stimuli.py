"""Mechanical checklist checks on an authored items file
(DEFINITIONS_AND_CHECKLIST.md section 6), on top of kmp.items.design_problems.

design_problems already covers: duplicate IDs, mixed experiments, pair
completeness, same agent within a pair (B1), gendered pronouns (R2) and the
foundations scaffold rules (decision A). This module adds only what those
leave out and code can check:

  A1   sentence count (3 nonmoral / ngo_verbatim, 4 foundations); no "?"
  A3   indifference clause: exact template for new items; prefix for adapted Ngo
  A4   last sentence is "<Agent> knew ..." (all but ngo_verbatim)
  A9   the action sentence opens with the agent, capitalised
  A10  effect form: starts lower case, no final punctuation, no leading "to "
  B2   new pairs: every sentence but the last identical in bad and good
  C2   one agent per storyline across arms
  C3   nonmoral prudential/procedural pairs reuse the adapted Ngo pair's
       action sentence, or the authoring log has a fresh_action entry (decision E)
  C4   foundations: one action-and-goal sentence per storyline
  D2   (--expect-complete) nonmoral: all three arms for storylines 1-40
  D3   no role noun used by two storylines in one file
  B8   adapted Ngo pairs differ from Ngo's text only by name and pronoun
       changes, or by changes listed in the authoring log
  B9   ngo_verbatim equals tools.ngo_source's parse of Ngo's text
  --   approved / rejected statuses are backed by a review decision on the
       current text (tools.review_record)

B8's automatic part: both texts are split into word and punctuation tokens
(curly apostrophes read as straight) and aligned with difflib. A changed
span passes if its old tokens are all the verbatim agent's name, gendered
pronouns, "the", "'" or "s", and its new tokens are all the role noun's
words, "the", "'" or "s". Any other span needs an authoring-log row for that
item and field whose "from" contains the old span and whose "to" contains
the new one. A log row whose "from" is not in Ngo's text or whose "to" is
not in the adapted text is stale and is flagged. A goal row's "to" must be
in the bad version's first sentence (decision B2: the bad version's goal).
This is permissive in one way: adding or dropping "the" always passes. The
reviewer still reads every B8 diff on the review sheet.

Run from the study folder:
    ../../.venv/bin/python -m tools.lint_stimuli stimuli/nonmoral.csv
Exit 0 clean, 1 problems found.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

from kmp.items import ARMS, GENDERED_PRONOUNS, Item, design_problems, load_items
from tools import ngo_source
from tools.review_record import REVIEW_DIR, approval_problems, decision_files, read_decisions

STIMULI = Path(__file__).resolve().parents[1] / "stimuli"
LOG = STIMULI / "nonmoral_log.csv"
VERBATIM = STIMULI / "ngo_verbatim.csv"
LOG_FIELDS = ["item_id", "field", "kind", "from", "to", "note"]
LOG_KINDS = ("goal", "typo", "other_name", "effect", "fresh_action")
N_SENTENCES = {"nonmoral": 3, "ngo_verbatim": 3, "foundations": 4}
ACTION_SENTENCE = {"nonmoral": 0, "ngo_verbatim": 0, "foundations": 1}
NGO_STORYLINES = range(1, 41)
NAMING_FILLER = frozenset({"the", "'", "s"})

# Storylines in Ngo's text where a gendered pronoun refers to someone other than the agent, so
# turning that pronoun into the agent's role noun would change who the sentence is about.
# Derived by reading all 80 verbatim texts (not by code; a parser cannot resolve reference).
# tests/test_lint_stimuli.py pins this set against the source: outside it, no object or
# reflexive pronoun (him, himself, herself, hers) appears at all; the his/her/he/she cases
# were read by hand and found to refer to the agent.
NON_AGENT_PRONOUNS = {
    10: "'avoid being his caretaker' / 'placing him' / 'make him extremely unhappy' (bad) and "
        "'make her extremely happy' (good) refer to the relative placed in the home, not the agent",
}

_SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+")
_TOKEN = re.compile(r"\w+|[^\w\s]")


def split_sentences(text: str) -> list[str]:
    return _SENTENCE_BREAK.split(text)


def capitalised(text: str) -> str:
    return text[:1].upper() + text[1:]


def read_log(path: str | Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != LOG_FIELDS:
            raise ValueError(f"{path}: header {reader.fieldnames} should be {LOG_FIELDS}")
        return list(reader)


def is_adapted_ngo(item: Item) -> bool:
    return item.experiment == "nonmoral" and item.source == "ngo"


# ---- per item ------------------------------------------------------------------

def item_problems(item: Item) -> list[str]:
    iid, out = item.item_id, []
    sentences = split_sentences(item.scenario)
    n = N_SENTENCES[item.experiment]
    if len(sentences) != n:
        out.append(f"{iid}: {len(sentences)} sentences, the template has {n} (A1)")
    if "?" in item.scenario:
        out.append(f"{iid}: the scenario contains '?'; the question line is not part of it (A1)")
    if not item.effect[:1].islower():
        out.append(f"{iid}: effect {item.effect!r} should start with a lower-case verb (A10)")
    if item.effect[-1] in ".?!,;:":
        out.append(f"{iid}: effect {item.effect!r} ends in punctuation (A10)")
    if item.effect.startswith("to "):
        out.append(f"{iid}: effect {item.effect!r} should be a bare verb phrase, without 'to' (A10)")
    if len(sentences) != n:
        return out
    agent = capitalised(item.agent)
    if not sentences[ACTION_SENTENCE[item.experiment]].startswith(agent + " "):
        out.append(f"{iid}: the action sentence should open with {agent!r} (A9)")
    if item.experiment == "ngo_verbatim":
        return out
    indifference, knew = sentences[-2], sentences[-1]
    if is_adapted_ngo(item):
        if not indifference.startswith(f"{agent} did not care at all about the effect"):
            out.append(f"{iid}: sentence {n - 1} should open '{agent} did not care at all about the effect' (A3)")
    elif not re.fullmatch(re.escape(agent) + r" did not care at all about the effect this would have on .+\.",
                          indifference):
        out.append(f"{iid}: sentence {n - 1} should read '{agent} did not care at all about the effect this "
                   f"would have on [X].' (A3)")
    if not knew.startswith(f"{agent} knew "):
        out.append(f"{iid}: the last sentence should open '{agent} knew ' (A4)")
    return out


# ---- per pair and storyline ---------------------------------------------------------

def _pairs(items: list[Item]) -> dict[tuple[int, str], dict[str, Item]]:
    pairs: dict[tuple[int, str], dict[str, Item]] = defaultdict(dict)
    for item in items:
        pairs[(item.storyline_id, item.arm)][item.sign] = item
    return pairs


def pair_problems(items: list[Item]) -> list[str]:
    out = []
    for key, pair in sorted(_pairs(items).items()):
        if set(pair) != {"bad", "good"}:
            continue
        if is_adapted_ngo(pair["bad"]):
            bad_action, good_action = (split_sentences(pair[s].scenario)[0] for s in ("bad", "good"))
            if bad_action != good_action:
                out.append(f"pair {key}: bad and good action sentences differ; the good version takes the bad "
                           f"version's goal (B8, decision B2)")
            continue
        if pair["bad"].source == "ngo":
            continue
        if split_sentences(pair["bad"].scenario)[:-1] != split_sentences(pair["good"].scenario)[:-1]:
            out.append(f"pair {key}: bad and good differ before the side-effect sentence (B2)")
    return out


def storyline_problems(items: list[Item], log_rows: list[dict[str, str]]) -> list[str]:
    out = []
    fresh = {row["item_id"] for row in log_rows if row["kind"] == "fresh_action"}
    storylines: dict[int, list[Item]] = defaultdict(list)
    for item in items:
        if item.experiment != "ngo_verbatim":
            storylines[item.storyline_id].append(item)
    for sid, members in sorted(storylines.items()):
        agents = sorted({m.agent for m in members})
        if len(agents) > 1:
            out.append(f"storyline {sid}: agents differ across arms {agents} (C2)")
        if members[0].experiment == "foundations":
            actions = {split_sentences(m.scenario)[1] for m in members if len(split_sentences(m.scenario)) == 4}
            if len(actions) > 1:
                out.append(f"storyline {sid}: the action-and-goal sentence differs across arms (C4)")
            continue
        reference = next((m for m in members if m.arm == "moral" and m.sign == "bad"), None)
        if reference is None:
            continue
        action = split_sentences(reference.scenario)[0]
        for m in members:
            if m.arm != "moral" and m.sign == "bad" and split_sentences(m.scenario)[0] != action:
                pair_ids = {m.item_id, m.item_id.replace("-bad", "-good")}
                if not pair_ids & fresh:
                    out.append(f"pair {(sid, m.arm)}: the action sentence differs from the adapted Ngo pair's and "
                               f"the authoring log has no fresh_action row for it (C3, decision E)")
    return out


def file_problems(items: list[Item], expect_complete: bool = False) -> list[str]:
    out = []
    by_agent: dict[str, set[int]] = defaultdict(set)
    for item in items:
        if item.experiment != "ngo_verbatim":
            by_agent[item.agent].add(item.storyline_id)
    for agent, sids in sorted(by_agent.items()):
        if len(sids) > 1:
            out.append(f"file: role noun {agent!r} is used by storylines {sorted(sids)} (D3)")
    if expect_complete and items and items[0].experiment == "nonmoral":
        complete = {key for key, pair in _pairs(items).items() if set(pair) == {"bad", "good"}}
        for sid in NGO_STORYLINES:
            for arm in ARMS["nonmoral"]:
                if (sid, arm) not in complete:
                    out.append(f"file: storyline {sid} has no complete {arm} pair (D2)")
    return out


# ---- Ngo adaptation (B8), authoring log, verbatim source (B9) ------------------------------

def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.replace("’", "'"))


def _within(span: list[str], text: str) -> bool:
    return not span or f" {' '.join(span)} " in f" {' '.join(_tokens(text))} "


def _covers(full: list[str], start: int, end: int, row_text: str) -> bool:
    """True if full[start:end] lies inside one occurrence of the row's tokens in full (an empty
    range, i.e. a pure insertion or deletion, may sit at either edge of the occurrence)."""
    sub = _tokens(row_text)
    return any(full[p:p + len(sub)] == sub and p <= start and end <= p + len(sub)
               for p in range(len(full) - len(sub) + 1)) if sub else False


def _naming_change(old: list[str], new: list[str], verbatim_agent: str, role_noun: str,
                   storyline_id: int | None = None) -> bool:
    if storyline_id in NON_AGENT_PRONOUNS and any(GENDERED_PRONOUNS.fullmatch(t) for t in old):
        return False
    before = {t.lower() for t in _tokens(verbatim_agent)} | NAMING_FILLER
    after = {t.lower() for t in _tokens(role_noun)} | NAMING_FILLER
    return (all(t.lower() in before or GENDERED_PRONOUNS.fullmatch(t) for t in old)
            and all(t.lower() in after for t in new))


def adaptation_problems(items: list[Item], verbatim: list[Item], log_rows: list[dict[str, str]]) -> list[str]:
    originals = {(v.storyline_id, v.sign): v for v in verbatim}
    by_id = {i.item_id: i for i in items}
    rows: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in log_rows:
        rows[(row["item_id"], row["field"])].append(row)
    out = []
    for item in sorted(filter(is_adapted_ngo, items), key=lambda i: i.item_id):
        original = originals.get((item.storyline_id, item.sign))
        if original is None:
            out.append(f"{item.item_id}: no ngo_verbatim item to compare it with (B8)")
            continue
        for field in ("scenario", "effect"):
            before, after = getattr(original, field), getattr(item, field)
            listed = rows[(item.item_id, field)]
            for row in listed:
                if not (_within(_tokens(row["from"]), before) and _within(_tokens(row["to"]), after)):
                    out.append(f"{item.item_id}: authoring-log row {row['from']!r} -> {row['to']!r} does not match "
                               f"the texts; it is stale (B8)")
                bad = by_id.get(item.item_id.replace("-good", "-bad"))
                if row["kind"] == "goal" and bad is not None and \
                        not _within(_tokens(row["to"]), split_sentences(bad.scenario)[0]):
                    out.append(f"{item.item_id}: goal row's new goal {row['to']!r} is not the bad version's goal "
                               f"(decision B2)")
            a, b = _tokens(before), _tokens(after)
            for tag, i1, i2, j1, j2 in SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
                old, new = a[i1:i2], b[j1:j2]
                if tag == "equal" or _naming_change(old, new, original.agent, item.agent, item.storyline_id):
                    continue
                if any(_covers(a, i1, i2, r["from"]) and _covers(b, j1, j2, r["to"]) for r in listed):
                    continue
                if item.storyline_id in NON_AGENT_PRONOUNS and any(GENDERED_PRONOUNS.fullmatch(t) for t in old):
                    why = (f"replaces a pronoun in a storyline where some pronouns do not refer to the agent "
                           f"({NON_AGENT_PRONOUNS[item.storyline_id]}) and is not in the authoring log (B8)")
                else:
                    why = "is not a name or pronoun change and not in the authoring log (B8)"
                out.append(f"{item.item_id}: {field} changes {' '.join(old)!r} to {' '.join(new)!r}, which {why}")
    return out


def log_problems(items: list[Item], log_rows: list[dict[str, str]]) -> list[str]:
    ids = {i.item_id for i in items}
    out = []
    for n, row in enumerate(log_rows, start=2):
        if row["item_id"] not in ids:
            out.append(f"authoring log line {n}: unknown item {row['item_id']!r}")
        if row["kind"] not in LOG_KINDS:
            out.append(f"authoring log line {n}: kind {row['kind']!r} not in {LOG_KINDS}")
        if row["field"] not in ("scenario", "effect"):
            out.append(f"authoring log line {n}: field {row['field']!r} should be scenario or effect")
        if row["kind"] != "fresh_action" and not (row["from"].strip() and row["to"].strip()):
            out.append(f"authoring log line {n}: from and to must both be non-empty for kind {row['kind']!r}")
        if not row["note"].strip():
            out.append(f"authoring log line {n}: note is empty")
    return out


def lint(items: list[Item], *, log_rows: list[dict[str, str]] = (), verbatim: list[Item] | None = None,
         decisions: list[dict[str, str]] = (), expect_complete: bool = False) -> list[str]:
    """Every lint problem for one items file. Empty = clean. Does not repeat design_problems."""
    log_rows, out = list(log_rows), []
    for item in sorted(items, key=lambda i: i.item_id):
        out += item_problems(item)
    out += pair_problems(items)
    out += storyline_problems(items, log_rows)
    out += file_problems(items, expect_complete)
    if items and items[0].experiment == "ngo_verbatim":
        out += ngo_source.differences(items, ngo_source.load_source())
    if items and items[0].experiment == "nonmoral":
        out += log_problems(items, log_rows)
        if any(map(is_adapted_ngo, items)):
            if verbatim is None:
                out.append("file: adapted Ngo items need --verbatim to check B8")
            else:
                out += adaptation_problems(items, verbatim, log_rows)
    out += approval_problems(items, list(decisions))
    return out


def pair_counts(items: list[Item]) -> dict[str, dict[str, int]]:
    """Complete pairs per arm and review status (a pair counts under its worse member's status)."""
    rank = {"rejected": 0, "draft": 1, "approved": 2}
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for (_, arm), pair in _pairs(items).items():
        if set(pair) == {"bad", "good"}:
            counts[arm][min((m.review_status for m in pair.values()), key=rank.__getitem__)] += 1
    return {arm: dict(c) for arm, c in sorted(counts.items())}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="lint an authored items file (DEFINITIONS_AND_CHECKLIST.md section 6)")
    p.add_argument("items", type=Path)
    p.add_argument("--verbatim", type=Path, default=VERBATIM, help="ngo_verbatim.csv, for B8")
    p.add_argument("--log", type=Path, default=LOG, help="the nonmoral authoring log")
    p.add_argument("--review-dir", type=Path, default=REVIEW_DIR)
    p.add_argument("--expect-complete", action="store_true", help="also require every nonmoral pair (D2)")
    args = p.parse_args(argv)
    items = load_items(args.items)
    problems = design_problems(items, stage="authoring")
    log_rows = read_log(args.log) if args.log.exists() else []
    verbatim = load_items(args.verbatim) if args.verbatim.exists() else None
    problems += lint(items, log_rows=log_rows, verbatim=verbatim,
                     decisions=read_decisions(decision_files(args.review_dir)), expect_complete=args.expect_complete)
    for arm, by_status in pair_counts(items).items():
        print(f"{arm}: " + ", ".join(f"{n} {status}" for status, n in sorted(by_status.items())) + " pairs")
    if problems:
        print(f"{len(problems)} problem(s):\n  " + "\n  ".join(problems), file=sys.stderr)
        return 1
    print(f"{args.items}: clean ({len(items)} items)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
