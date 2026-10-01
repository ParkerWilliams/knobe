# knobe_moral_probe stimuli: authoring plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Write the study's three stimulus files (`stimuli/ngo_verbatim.csv`, `stimuli/nonmoral.csv`, `stimuli/foundations.csv`), get every item through the researcher's review, then screen them with the pinned reviewer model so that `selected_items.csv` exists for each experiment.

**Architecture:** First, three small authoring tools under `tools/`, built test-first: a parser that turns Ngo's text file into the verbatim set, a lint for the mechanical checklist items that `kmp.items.design_problems` does not cover, and a review tool. The review tool writes markdown review sheets and lets the researcher, and only the researcher, apply decisions. Each decision is tied to a hash of the exact text reviewed. After that, the items are drafted in batches of about 40 (one arm or one group of scaffolds per batch). Each batch is linted, committed as a draft, and stopped for review. Screening uses the existing `kmp.screen` CLI unchanged, with the reviewer already pinned to `claude-sonnet-4-6` (DESIGN.md amendment 2026-10-01, reviewer pin): a dry run first, then one real run per experiment.

**Tech Stack:** Python 3.13, pydantic (via `kmp.items`), stdlib `csv`/`difflib`/`hashlib`, pytest; the `anthropic` SDK for screening only.

**Scope:** DESIGN.md §3 (stimuli), §3.4 (authoring process) and §4 (screening and pair selection). The pilot and the full run (§8–§9) are outside this plan. It reuses `kmp.items` (schema, IDs, CSV I/O, `design_problems`), `kmp.screen`/`kmp.screen_run` (screening) and `kmp.protocol` (the reviewer pin). Nothing in `kmp/` is reimplemented (CLAUDE.md §7). The one overlap, `tools.lint_stimuli` reading sentences, adds checks that `design_problems` does not make, and its docstring lists which checks belong to which module.

**Conventions for every task:**
- Work on branch `knobe_moral_probe`. The repo CLAUDE.md §1 says to commit to `main`, but this study's README and every commit so far use the study branch. Follow the study.
- Prefix commit messages with `[knobe_moral_probe]`. Add no AI co-author or attribution trailer (user's global CLAUDE.md).
- Commit incrementally: each tool is its own commit, each batch's CSV plus log rows is its own commit, and the researcher's applied decisions are their own commit.
- Run tests from the repo root:
  `.venv/bin/python -m pytest studies/knobe_moral_probe/tests -q`.
  `pyproject.toml` sets `filterwarnings = ["error"]`, so any warning fails a test.
- Run CLIs from the study folder:
  `cd studies/knobe_moral_probe && ../../.venv/bin/python -m <module> ...`.
- **STOP** marks a researcher gate. Stop there, report what is ready and where, and do nothing past it until the researcher replies.
- **The drafting agent never sets `review_status` to `approved` or `rejected`.** Only `tools.review apply`, run by the researcher on a decisions file the researcher filled in, does that. The agent may set an item back to `draft`, and only when it edits that item's text after a "revise" or "rejected" decision.
- Batch numbers: 01 verbatim; 02–03 moral; 04–05 prudential; 06–07 procedural; 08–13 foundations shared scaffolds; 14 purity purpose-written. A fix or top-up batch takes the next free number when it is created, and the planned batches after it shift up by one. `tools.review_record.decision_files` reads decisions in file-name order, so numbers must increase with time. Never reuse a number.
- Every item is LLM-drafted. Record the drafting model ID and date for each batch in the batch table in `stimuli/NOTES.md` (Task 9). The no-attribution rule keeps this out of the commits, so NOTES.md is the disclosure record (DESIGN.md §3.4).

## Decisions this plan needs before Task 1 (recorded in Task 0)

These gaps were found while writing the plan. Each has a recommendation. Task 0 recorded the researcher's answers (all recommendations accepted, 2026-10-01) in `docs/DEFINITIONS_AND_CHECKLIST.md` §7 as decisions M–S and U. Decision T is already resolved (below).

- **M. Verbatim agent where Ngo's question names the agent differently** RESOLVED 2026-10-01 (recommendation accepted). (items 12 "the CEO" vs scenario "The company owner"; 53 "Phillip" vs "Philip"; 57 "he"; 69, 70 "the director" vs "The financial officer" / "The treasurer"). *Recommendation:* use the scenario's subject, since the question line is not used. This is `tools.ngo_source.AGENT_OVERRIDES`.
- **N. Typography in the verbatim set.** RESOLVED 2026-10-01 (recommendation accepted). The file pads lines with spaces, U+00A0 and U+2028, and uses curly apostrophes in 9 places (item 17 mixes ’ and '). *Recommendation:* strip only the surrounding whitespace on each line, join the three clauses with one space, and keep every character inside a line, curly apostrophes included. The adapted pairs use the straight `'`. This is recorded once in NOTES.md as a file-wide convention rather than as 9 log rows. The B8 lint treats ’ and ' as equal.
- **O. Role nouns for Ngo pairs that already use role nouns.** RESOLVED 2026-10-01 (recommendation accepted). The amendment covers names and pronouns, but R3 (no loaded or gendered roles) and D3 (no role noun reused across storylines) also hit Ngo's own roles. Pairs 2, 6 and 36 are all "the CEO"; pair 2's good version is "the chairman"; pair 5's is "the councilwoman"; several pairs use two different roles (CEO / chairman, Surgeon General / Defense Secretary, financial officer / treasurer, university president / athletic director). *Recommendation:* use the bad version's role noun (the same rule as the goal, decision B2), with three exceptions. Gendered roles are made neutral (chairman → chair, councilwoman → council member). Roles R3 names ("the CEO") are replaced with a plain role. A D3 collision gets a distinct plain role. Keep roles that are the story itself ("the terrorist", "the cult leader", "the bomber pilot") and list them in NOTES.md as R3 exceptions. Every choice goes in the role-noun table (Task 9).
- **P. Loaded roles carried into the nonmoral arms.** RESOLVED 2026-10-01 (recommendation accepted). C2 fixes one role noun per storyline, so a procedural item in storyline 34 would be about "the terrorist". *Recommendation:* accept this, since holding the role constant across arms is the reason for the rule. Flag the storylines with loaded roles in NOTES.md. The analysis plan should add a sensitivity fit that excludes them.
- **Q. `source` values for rewritten text.** RESOLVED 2026-10-01 (recommendation accepted). The vocabulary is `ngo` / `pilot` / `new`. *Recommendation:* `ngo` only for Ngo's own pairs (adapted or verbatim). `pilot` when a pilot variant's text was the starting draft, even if rewritten for role nouns and the template. `new` for everything written fresh, including rewrites of pilot failures and foundations items built on an Ngo storyline. Record the Ngo-storyline origin in the scaffold roster (Task 14).
- **R. DESIGN.md §3.2's list of failed pilot variants disagrees with the pilot report.** RESOLVED 2026-10-01 (recommendation accepted). DESIGN lists prudential 2, 5, 8, 23, 29, 30, 31; procedural 23, 37; and 27 for both. `nonmoral_pilot/outputs/selection_report.md` shows prudential 23 **passing**. The prudential failures there are 2, 5, 8, 27, 29, 30, 31 and the procedural ones 23, 27, 37. *Recommendation:* go by the report, and correct DESIGN.md §3.2 in Task 0. Prudential 23 still gets rewritten for role nouns like every other variant.
- **S. Who commits applied decisions.** RESOLVED 2026-10-01 (recommendation accepted). *Recommendation:* the researcher runs `tools.review apply`. The agent then commits the resulting CSV and decisions file unchanged, on the researcher's word, after lint is clean. The commit message says the decisions are the researcher's.
- **T. Reviewer model for screening. RESOLVED 2026-10-01: `claude-sonnet-4-6`** (DESIGN.md amendment "reviewer pin", commits d35b59b and 534738d; already set as `protocol.REVIEWER_MODEL`). It differs from the drafting model, which keeps the screen from being the drafter grading its own work. It is not an open decision; it is listed here only so the letters stay continuous. Record both IDs in NOTES.md.
- **U. Purpose-written storyline numbering.** RESOLVED 2026-10-01 (recommendation accepted). *Recommendation:* shared scaffolds use storyline IDs 1–36 and purpose-written purity storylines 101–120. This is for readability only; the `scaffold` field stays authoritative (decision A).

## File structure

```
studies/knobe_moral_probe/
├── tools/
│   ├── __init__.py            package marker (tools run as `python -m tools.<module>`)
│   ├── check_chat_bos.py      (exists, unchanged)
│   ├── ngo_source.py          Ngo's .txt → ngo_verbatim items; compare-only once the CSV exists (B9)
│   ├── review_record.py       text_sha256, decisions files, approval check
│   ├── lint_stimuli.py        mechanical checklist checks beyond design_problems (A1 A3 A4 A9 A10 B2 B8 B9 C2 C3 C4 D2 D3)
│   └── review.py              `sheet` (drafting agent) and `apply` (researcher only)
├── stimuli/
│   ├── ngo_verbatim.csv       80 items, Ngo word for word (generated by tools.ngo_source)
│   ├── nonmoral.csv           240 items: 40 adapted Ngo moral pairs + 40 prudential + 40 procedural
│   ├── foundations.csv        ~280 drafted items: 36 shared scaffolds (harm + foundation pairs) + 20 purpose-written purity storylines
│   ├── nonmoral_log.csv       machine-readable log of every change from Ngo, and every fresh action (decisions C, E, K, L)
│   ├── NOTES.md               conventions, role-noun table, scaffold roster, batch table (drafting model, dates), disclosure
│   └── review/
│       ├── NN_<batch>.md                review sheet (generated)
│       └── NN_<batch>_decisions.csv     the researcher's decisions (the review record)
├── outputs/screening/<experiment>/      kmp.screen outputs (committed, see .gitignore comment)
└── tests/
    ├── test_ngo_source.py
    ├── test_review_record.py
    ├── test_lint_stimuli.py
    └── test_review.py
```

Why there is a CSV log next to NOTES.md: the B8 lint needs a machine-readable allow-list. A markdown table in NOTES.md would be fragile to parse. So `nonmoral_log.csv` is the single record of every Ngo change and every fresh action. NOTES.md holds the prose and points to the log. The review sheet shows each item's log rows next to it.

`nonmoral_log.csv` columns: `item_id,field,kind,from,to,note`.
- `field` is `scenario` or `effect`.
- `kind` is one of `goal` (decision B2), `typo` (C), `other_name` (L), `effect` (C: effect phrase differs from Ngo's question phrase beyond naming), `fresh_action` (E).
- `from` / `to` are the old and new text, with enough context to be unique. Leave them empty for `fresh_action`.
- `note` says why, and is required.

Name and pronoun changes to the agent need no row; the lint recognises them.

---

### Task 0: Researcher sign-off on the checklist and on decisions M–S, U

**Files:**
- Modify: `studies/knobe_moral_probe/docs/DEFINITIONS_AND_CHECKLIST.md` (status line 3; §7, append M–U, with T recorded as already resolved)
- Modify: `studies/knobe_moral_probe/docs/DESIGN.md` §3.2 (failed-variant list, per decision R)

The definitions doc still says "Status: DRAFT for researcher review" in its header, although commit 9bd3072 says it was reviewed and §7's decisions A–L are resolved. Several rules are still marked **(proposed)**: rule 7 for nonmoral domains, the role-noun lists, the background clause being identical in both versions, A4's "side effect last", and D3. The lint and the review sheet implement them, so they must be accepted or struck first.

- [x] **Step 1: STOP.** Send the researcher this plan's "Decisions this plan needs" section and the list of (proposed) items in DEFINITIONS_AND_CHECKLIST.md: §2 rule 7, §2.1 lists, §3.2 background and harm background, §6 A4 and D3. Ask for accept, change or strike on each, and for decisions M–S and U. T is resolved (`claude-sonnet-4-6`).
- [x] **Step 2: Record the answers.** Change line 3 of DEFINITIONS_AND_CHECKLIST.md to `**Status: approved by the researcher (YYYY-MM-DD), revision 3.**` and replace every accepted "(proposed)" marker with nothing. Rewrite or delete the struck ones. Append to §7, one entry per decision, in the existing format:

```markdown
**M. Verbatim agent where Ngo's question differs from the scenario. RESOLVED YYYY-MM-DD:**
the scenario's subject (items 12, 53, 57, 69, 70; `tools/ngo_source.py` AGENT_OVERRIDES).
```

  If the researcher strikes D3, delete `file_problems`'s D3 loop and `test_d3_role_noun_reused_across_storylines` from Task 4 before building it. If the researcher strikes A4's "last clause" rule, delete the A4 check from `item_problems` and `test_side_effect_sentence_opens_with_agent_knew`.
- [x] **Step 3: Correct DESIGN.md §3.2.** Replace "(pairs 2, 5, 8, 23, 29, 30 and 31 prudential; 23 and 37 procedural; 27 both, per `nonmoral_pilot/outputs/selection_report.md`)" with "(pairs 2, 5, 8, 29, 30 and 31 prudential; 23 and 37 procedural; 27 both, per `nonmoral_pilot/outputs/selection_report.md`)". Make this change only if the researcher accepted decision R.
- [x] **Step 4: Commit**

```bash
git add studies/knobe_moral_probe/docs/DEFINITIONS_AND_CHECKLIST.md studies/knobe_moral_probe/docs/DESIGN.md
git commit -m "[knobe_moral_probe] definitions: researcher approval, decisions M-U; design §3.2 failed-variant list per the pilot report"
```

---

### Task 1: Ngo source parser (`tools/ngo_source.py`)

**Files:**
- Create: `studies/knobe_moral_probe/tools/__init__.py`
- Create: `studies/knobe_moral_probe/tools/ngo_source.py`
- Test: `studies/knobe_moral_probe/tests/test_ngo_source.py`

How the source file works: `analysis/ngo_extensions/nonmoral_pilot/ngo_2015_original_80.txt` has a 9-line preamble, then 80 blocks. Each block is a header line `N.` (sometimes padded with spaces or U+00A0), then exactly four non-blank lines: three scenario clauses and the question. Lines carry trailing spaces, U+00A0 and, at the end of item 80, U+2028.

**Signs are not labelled in the file.** They come from Ngo's ordering: each pair is printed harm-first, so item 2N−1 is `bad` and item 2N is `good`, both in pair N. The pilots used the same convention (`prudential_variants.py`: "pair_id N -> source items 2N-1 [bad], 2N [good]"), and so does DEFINITIONS §3.4. The tests pin it on content: item 1 "kill babies" (bad), item 2 "help toddlers" (good), items 7/8, 79/80.

Field rules, from DEFINITIONS §3.4 and §3.5, decision C, and decision M:
- `agent` is the question's subject ("Did Bill intentionally ..." gives "Bill"), unless overridden by decision M.
- `effect` is the rest of Ngo's question, verbatim, minus the "?".
- Questions 73 and 79 lack "intentionally".
- `source=ngo`, `experiment=ngo_verbatim`, `arm=moral`, `review_status=draft`.

- [ ] **Step 1: Create the package marker**

`studies/knobe_moral_probe/tools/__init__.py`:
```python
"""Authoring tools for the study's stimuli (docs/AUTHORING_PLAN.md). Run from the
study folder as modules: ../../.venv/bin/python -m tools.<module> ..."""
```

- [ ] **Step 2: Write the failing tests**

`studies/knobe_moral_probe/tests/test_ngo_source.py`:
```python
"""tools.ngo_source: Ngo et al.'s 80 vignettes, parsed word for word (B9)."""
import pytest

from kmp.items import design_problems, load_items, write_items
from tools import ngo_source


@pytest.fixture(scope="module")
def parsed():
    return {i.item_id: i for i in ngo_source.load_source()}


def test_eighty_items_forty_pairs(parsed):
    assert len(parsed) == 80
    assert {i.storyline_id for i in parsed.values()} == set(range(1, 41))
    for sid in range(1, 41):
        assert {i.sign for i in parsed.values() if i.storyline_id == sid} == {"bad", "good"}


def test_odd_items_are_bad_even_items_are_good(parsed):
    # Ngo lists the harm version first: item 2N-1 bad, item 2N good, pair N.
    assert parsed["kmp-nv-001-moral-bad"].effect == "cause the death of babies"        # item 1
    assert parsed["kmp-nv-001-moral-good"].effect == "help toddlers"                   # item 2
    assert parsed["kmp-nv-004-moral-bad"].effect == "increase membership costs"        # item 7
    assert parsed["kmp-nv-004-moral-good"].effect == "increase customer satisfaction"  # item 8
    assert parsed["kmp-nv-040-moral-bad"].scenario.endswith("would cause fatal bleeding for her patient.")  # 79
    assert parsed["kmp-nv-040-moral-good"].effect == "cure his patient"                # item 80


def test_item_1_word_for_word(parsed):
    item = parsed["kmp-nv-001-moral-bad"]
    assert item.agent == "Bill"
    assert item.scenario == ("Bill released a gadget to make a deadline. Bill did not care at all about the "
                             "effect the gadget would have on babies. Bill knew his gadget would kill babies.")
    assert (item.experiment, item.arm, item.source, item.review_status, item.scaffold) == \
        ("ngo_verbatim", "moral", "ngo", "draft", None)


def test_typos_and_typography_are_kept(parsed):
    assert "the effect the drug would have rates of cancer" in parsed["kmp-nv-012-moral-bad"].scenario   # item 23
    assert "diverting the water for his town" in parsed["kmp-nv-005-moral-good"].scenario               # item 10
    assert "enemy’s steel production" in parsed["kmp-nv-007-moral-bad"].scenario                        # item 13
    assert parsed["kmp-nv-036-moral-good"].effect == "make the tablet accessible for the blind"          # item 72


def test_no_padding_characters_survive(parsed):
    for item in parsed.values():
        for text in (item.agent, item.effect, item.scenario):
            assert "\xa0" not in text and " " not in text and "  " not in text


def test_agent_overrides_use_the_scenarios_name(parsed):
    assert parsed["kmp-nv-006-moral-good"].agent == "the company owner"     # item 12; question says "the CEO"
    assert parsed["kmp-nv-027-moral-bad"].agent == "Philip"                # item 53
    assert parsed["kmp-nv-029-moral-bad"].agent == "the cop"               # item 57; question says "he"
    assert parsed["kmp-nv-035-moral-bad"].agent == "the financial officer" # item 69
    assert parsed["kmp-nv-035-moral-good"].agent == "the treasurer"        # item 70


def test_questions_without_intentionally(parsed):
    assert parsed["kmp-nv-037-moral-bad"].effect == "cause his followers to commit mass suicide"  # item 73
    assert parsed["kmp-nv-040-moral-bad"].effect == "cause the patient to have fatal bleeding"    # item 79


def test_parsed_items_pass_the_design_checks(parsed):
    assert design_problems(list(parsed.values())) == []


def _block(n, lines):
    return f"{n}.\n" + "\n".join(lines) + "\n\n"


GOOD_BLOCK = ["Ann ran.", "Ann did not care.", "Ann knew.", "Did Ann intentionally run?"]


def test_wrong_line_count_raises(monkeypatch):
    monkeypatch.setattr(ngo_source, "N_ITEMS", 1)
    with pytest.raises(ValueError, match="item 1: expected three scenario lines"):
        ngo_source.parse_items(_block(1, GOOD_BLOCK[:3]))


def test_agent_not_opening_the_scenario_raises(monkeypatch):
    monkeypatch.setattr(ngo_source, "N_ITEMS", 1)
    with pytest.raises(ValueError, match="AGENT_OVERRIDES"):
        ngo_source.parse_items(_block(1, ["Bob ran.", *GOOD_BLOCK[1:]]))


def test_missing_item_raises(monkeypatch):
    monkeypatch.setattr(ngo_source, "N_ITEMS", 2)
    with pytest.raises(ValueError, match="expected items 1..2"):
        ngo_source.parse_items(_block(1, GOOD_BLOCK))


def test_cli_writes_then_only_compares(tmp_path, capsys):
    out = tmp_path / "ngo_verbatim.csv"
    assert ngo_source.main(["--out", str(out)]) == 0
    items = load_items(out)
    assert len(items) == 80 and ngo_source.differences(items, ngo_source.load_source()) == []
    assert ngo_source.main(["--out", str(out)]) == 0
    assert "matches" in capsys.readouterr().out
    out.write_text(out.read_text(encoding="utf-8").replace("kill babies.", "kill infants."), encoding="utf-8")
    assert ngo_source.main(["--out", str(out)]) == 1
    assert "kmp-nv-001-moral-bad: scenario" in capsys.readouterr().err
    assert "kill infants." in out.read_text(encoding="utf-8")       # not overwritten


def test_cli_update_keeps_statuses_of_unchanged_items(tmp_path, capsys):
    out = tmp_path / "ngo_verbatim.csv"
    parsed = ngo_source.load_source()
    approved = [i.model_copy(update={"review_status": "approved"}) for i in parsed]
    broken = approved[0].model_copy(update={"effect": "wrong effect"})
    write_items([broken, *approved[1:]], out)
    assert ngo_source.main(["--out", str(out), "--update"]) == 0
    items = {i.item_id: i for i in load_items(out)}
    assert ngo_source.differences(list(items.values()), parsed) == []
    assert items["kmp-nv-001-moral-bad"].review_status == "draft"
    assert {i.review_status for k, i in items.items() if k != "kmp-nv-001-moral-bad"} == {"approved"}
```

- [ ] **Step 3: Run them to verify they fail**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests/test_ngo_source.py -q`
Expected: collection error, `ImportError: cannot import name 'ngo_source' from 'tools'`.

- [ ] **Step 4: Write the implementation**

`studies/knobe_moral_probe/tools/ngo_source.py`:
```python
"""Ngo et al. (2015)'s 80 vignettes as the ngo_verbatim items (DESIGN.md
2026-10-01 amendment "Ngo goals and verbatim set"; DEFINITIONS_AND_CHECKLIST.md
sections 3.4, 3.5 and check B9).

Source: analysis/ngo_extensions/nonmoral_pilot/ngo_2015_original_80.txt, the
pilots' copy of Ngo's stimulus appendix. Each vignette is a header line "N."
followed by four non-blank lines: three scenario clauses, then the question
("Did X intentionally ...?").

Signs: the file does not label them. Ngo lists every pair as the harm
version, then the help version, so item 2N-1 is bad, item 2N is good, and
both belong to pair N = storyline N. The pilots used the same convention
(nonmoral_pilot/prudential_variants.py: "pair_id N -> source items 2N-1
[bad], 2N [good]"), and DEFINITIONS section 3.4 numbers storylines this way.
tests/test_ngo_source.py pins it on the content of several pairs.

Word for word: each line loses only its surrounding whitespace (the file
pads lines with spaces, U+00A0 and U+2028), and the three clauses are joined
with one space. Nothing inside a line changes: typos, curly apostrophes and
Ngo's names and pronouns all stay.

agent: the question's subject ("Did Bill intentionally ..." gives "Bill"),
which must open the scenario. Where Ngo's question names the agent
differently from the scenario, AGENT_OVERRIDES gives the scenario's name.
effect: the rest of Ngo's question, verbatim, without the "?". Two questions
(73, 79) have no "intentionally"; NO_INTENT_SUBJECT names their subjects.

CLI: writes stimuli/ngo_verbatim.csv if it does not exist. If it exists, it
only compares (review statuses live in that file), exit 1 if the file
differs from the source. --update rewrites it from the source after a
parser fix, keeping review_status for items whose text is unchanged and
resetting changed items to draft, so they go back for review.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from kmp.items import Item, design_problems, load_items, make_item_id, write_items

STUDY_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = STUDY_DIR.parents[1]
SOURCE = REPO_ROOT / "analysis" / "ngo_extensions" / "nonmoral_pilot" / "ngo_2015_original_80.txt"
OUT = STUDY_DIR / "stimuli" / "ngo_verbatim.csv"
N_ITEMS = 80

# Where Ngo's question names the agent differently from the scenario, the
# scenario's name is the agent (the question line is not used; protocol.py
# asks its own questions).
AGENT_OVERRIDES: dict[int, str] = {
    12: "the company owner",       # question: "the CEO"
    53: "Philip",                  # question and clauses 2-3: "Phillip"
    57: "the cop",                 # question: "he"
    69: "the financial officer",   # question: "the director"
    70: "the treasurer",           # question: "the director"
}
# Questions without "intentionally": their subject, so the effect can be cut off.
NO_INTENT_SUBJECT: dict[int, str] = {73: "the cult leader", 79: "the doctor"}
# Fields that must match the source exactly (everything but review_status).
TEXT_FIELDS = ("experiment", "storyline_id", "arm", "sign", "agent", "effect", "scenario", "source", "scaffold")

_HEADER = re.compile(r"(\d+)\.")
_QUESTION = re.compile(r"Did (.+?) intentionally (.+)\?")


def read_blocks(text: str) -> dict[int, list[str]]:
    """Item number -> its non-blank lines, each stripped. Lines before the first header are skipped."""
    blocks: dict[int, list[str]] = {}
    current: int | None = None
    for line in text.split("\n"):
        stripped = line.strip()
        header = _HEADER.fullmatch(stripped)
        if header:
            current = int(header.group(1))
            if current in blocks:
                raise ValueError(f"item {current} appears twice")
            blocks[current] = []
        elif stripped and current is not None:
            blocks[current].append(stripped)
    return blocks


def question_parts(n: int, question: str) -> tuple[str, str]:
    """(subject, effect) of Ngo's question for item n."""
    m = _QUESTION.fullmatch(question)
    if m:
        return m.group(1), m.group(2)
    subject = NO_INTENT_SUBJECT.get(n)
    if subject is not None:
        prefix = f"Did {subject} "
        if question.startswith(prefix) and question.endswith("?"):
            return subject, question[len(prefix):-1]
    raise ValueError(f"item {n}: cannot parse the question {question!r}")


def _capitalised(text: str) -> str:
    return text[:1].upper() + text[1:]


def parse_items(text: str) -> list[Item]:
    """All 80 vignettes as ngo_verbatim items, review_status draft."""
    blocks = read_blocks(text)
    if sorted(blocks) != list(range(1, N_ITEMS + 1)):
        raise ValueError(f"expected items 1..{N_ITEMS}, found {sorted(blocks)}")
    items = []
    for n, lines in sorted(blocks.items()):
        if len(lines) != 4 or not lines[3].startswith("Did "):
            raise ValueError(f"item {n}: expected three scenario lines and a question, got {lines!r}")
        subject, effect = question_parts(n, lines[3])
        agent = AGENT_OVERRIDES.get(n, subject)
        if not lines[0].startswith(_capitalised(agent) + " "):
            raise ValueError(f"item {n}: the scenario does not open with the agent {agent!r}: {lines[0]!r}; "
                             f"add the scenario's name to AGENT_OVERRIDES")
        storyline, sign = (n + 1) // 2, ("bad" if n % 2 else "good")
        items.append(Item(
            item_id=make_item_id("ngo_verbatim", storyline, "moral", sign),
            experiment="ngo_verbatim", storyline_id=storyline, arm="moral", sign=sign,
            agent=agent, effect=effect, scenario=" ".join(lines[:3]),
            source="ngo", review_status="draft",
        ))
    return items


def load_source(path: str | Path = SOURCE) -> list[Item]:
    return parse_items(Path(path).read_text(encoding="utf-8"))


def differences(items: list[Item], parsed: list[Item]) -> list[str]:
    """How items differ from the parsed source, ignoring review_status. Empty = identical (B9)."""
    have = {i.item_id: i for i in items}
    want = {i.item_id: i for i in parsed}
    problems = [f"{k}: in Ngo's source but missing from the file (B9)" for k in sorted(want.keys() - have.keys())]
    problems += [f"{k}: not in Ngo's source (B9)" for k in sorted(have.keys() - want.keys())]
    for k in sorted(want.keys() & have.keys()):
        for field in TEXT_FIELDS:
            got, expected = getattr(have[k], field), getattr(want[k], field)
            if got != expected:
                problems.append(f"{k}: {field} is {got!r}, Ngo's source gives {expected!r} (B9)")
    return problems


def changed_ids(items: list[Item], parsed: list[Item]) -> set[str]:
    """IDs of parsed items that are missing from items or differ in a text field."""
    have = {i.item_id: i for i in items}
    return {i.item_id for i in parsed if i.item_id not in have
            or any(getattr(have[i.item_id], f) != getattr(i, f) for f in TEXT_FIELDS)}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Ngo et al. (2015)'s 80 vignettes -> stimuli/ngo_verbatim.csv")
    p.add_argument("--source", type=Path, default=SOURCE)
    p.add_argument("--out", type=Path, default=OUT)
    p.add_argument("--update", action="store_true",
                   help="rewrite an existing file from the source; changed items are reset to draft")
    args = p.parse_args(argv)
    parsed = load_source(args.source)
    problems = design_problems(parsed)
    if problems:
        print("parsed items fail the design checks:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 1
    if args.out.exists():
        current = load_items(args.out)
        diffs = differences(current, parsed)
        if diffs and args.update:
            changed = changed_ids(current, parsed)
            status = {i.item_id: i.review_status for i in current}
            write_items([i if i.item_id in changed else i.model_copy(update={"review_status": status[i.item_id]})
                         for i in parsed], args.out)
            print(f"updated {args.out}: {len(changed)} item(s) changed and reset to draft: {sorted(changed)}")
            return 0
        if diffs:
            print(f"{args.out} differs from {args.source}; not overwriting it (it holds the review statuses; "
                  f"--update rewrites it and resets changed items to draft):\n  "
                  + "\n  ".join(diffs), file=sys.stderr)
            return 1
        print(f"{args.out} matches {args.source} ({len(parsed)} items)")
        return 0
    write_items(parsed, args.out)
    print(f"wrote {len(parsed)} items to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests/test_ngo_source.py -q`
Expected: `13 passed`.

- [ ] **Step 6: Run the full suite**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests -q`
Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add studies/knobe_moral_probe/tools/__init__.py studies/knobe_moral_probe/tools/ngo_source.py studies/knobe_moral_probe/tests/test_ngo_source.py
git commit -m "[knobe_moral_probe] tools: parse Ngo's 80 vignettes word for word (signs from Ngo's harm-first ordering)"
```

---

### Task 2: Review record (`tools/review_record.py`)

**Files:**
- Create: `studies/knobe_moral_probe/tools/review_record.py`
- Test: `studies/knobe_moral_probe/tests/test_review_record.py`

Each decision is tied to the exact text it was made on: `text_sha256` hashes every field except `review_status`. Lint (Task 4) then fails any `approved` or `rejected` item whose current text no longer matches its last decision. This is how "approved" keeps meaning "the researcher saw exactly this".

- [ ] **Step 1: Write the failing tests**

`studies/knobe_moral_probe/tests/test_review_record.py`:
```python
"""tools.review_record: decisions are tied to the exact text reviewed."""
import csv

import pytest

from conftest import make_items
from tools.review_record import DECISION_FIELDS, approval_problems, read_decisions, text_sha256


def _write(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=DECISION_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def _row(item, decision, **kw):
    return {"item_id": item.item_id, "text_sha256": text_sha256(item), "decision": decision,
            "reviewer": "MM", "date": "2026-10-02", "note": "", **kw}


def test_hash_ignores_review_status_only():
    item = make_items("nonmoral", 1, status="draft")[0]
    assert text_sha256(item) == text_sha256(item.model_copy(update={"review_status": "approved"}))
    assert text_sha256(item) != text_sha256(item.model_copy(update={"effect": "something else"}))


def test_read_decisions_skips_blank_rows_and_checks_header(tmp_path):
    item = make_items("nonmoral", 1)[0]
    path = _write(tmp_path / "01_x_decisions.csv", [_row(item, "approved"), _row(item, "")])
    rows = read_decisions([path])
    assert [r["decision"] for r in rows] == ["approved"]
    (tmp_path / "02_bad_decisions.csv").write_text("item_id,decision\n", encoding="utf-8")
    with pytest.raises(ValueError, match="header"):
        read_decisions([tmp_path / "02_bad_decisions.csv"])


def test_approval_needs_a_matching_decision():
    items = make_items("nonmoral", 1, status="approved")[:2]
    assert approval_problems(items, [_row(i, "approved", file="f") for i in items]) == []
    assert "no review decision" in approval_problems(items, [_row(items[0], "approved", file="f")])[0]


def test_last_decision_wins_and_must_match_status():
    item = make_items("nonmoral", 1, status="approved")[0]
    rows = [_row(item, "approved", file="01"), _row(item, "revise", file="02")]
    assert "last decision (02) is revise" in approval_problems([item], rows)[0]


def test_text_edited_after_approval_is_flagged():
    item = make_items("nonmoral", 1, status="approved")[0]
    row = _row(item, "approved", file="f")
    edited = item.model_copy(update={"scenario": item.scenario + " Extra."})
    assert "text changed after it was approved" in approval_problems([edited], [row])[0]


def test_drafts_need_nothing():
    assert approval_problems(make_items("nonmoral", 1, status="draft"), []) == []
```

- [ ] **Step 2: Run them to verify they fail**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests/test_review_record.py -q`
Expected: collection error, `ModuleNotFoundError: No module named 'tools.review_record'`.

- [ ] **Step 3: Write the implementation**

`studies/knobe_moral_probe/tools/review_record.py`:
```python
"""The review record: which exact text the researcher approved or rejected
(DESIGN.md section 3.4 step 2; DEFINITIONS_AND_CHECKLIST.md section 1).

A decisions file (stimuli/review/NN_<batch>_decisions.csv) has one row per
reviewed item. text_sha256 is the hash of every item field except
review_status, so a decision belongs to the exact text it was made on: edit
the text and the decision no longer applies. Files are read in name order
(NN = batch number), and an item's last row is its current decision.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from kmp.items import Item

DECISION_FIELDS = ["item_id", "text_sha256", "decision", "reviewer", "date", "note"]
DECISIONS = ("approved", "rejected", "revise")
REVIEW_DIR = Path(__file__).resolve().parents[1] / "stimuli" / "review"


def text_sha256(item: Item) -> str:
    fields = {k: v for k, v in item.model_dump().items() if k != "review_status"}
    return hashlib.sha256(json.dumps(fields, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def decision_files(review_dir: str | Path = REVIEW_DIR) -> list[Path]:
    return sorted(Path(review_dir).glob("*_decisions.csv"))


def read_decisions(paths: list[Path]) -> list[dict[str, str]]:
    """Filled-in rows of the given decisions files, in order. Rows with an empty decision are skipped."""
    rows = []
    for path in paths:
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames != DECISION_FIELDS:
                raise ValueError(f"{path}: header {reader.fieldnames} should be {DECISION_FIELDS}")
            rows += [{**row, "file": str(path)} for row in reader if row["decision"].strip()]
    return rows


def approval_problems(items: list[Item], rows: list[dict[str, str]]) -> list[str]:
    """Approved or rejected items whose status is not backed by a decision on their current text."""
    last = {row["item_id"]: row for row in rows}
    problems = []
    for item in sorted(items, key=lambda i: i.item_id):
        if item.review_status == "draft":
            continue
        row = last.get(item.item_id)
        if row is None:
            problems.append(f"{item.item_id}: {item.review_status} but no review decision is on file")
        elif row["decision"] != item.review_status:
            problems.append(f"{item.item_id}: {item.review_status} but the last decision ({row['file']}) "
                            f"is {row['decision']}")
        elif row["text_sha256"] != text_sha256(item):
            problems.append(f"{item.item_id}: text changed after it was {item.review_status}; "
                            f"set it back to draft and send it for review again")
    return problems
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests/test_review_record.py -q`
Expected: `6 passed`.

- [ ] **Step 5: Commit**

```bash
git add studies/knobe_moral_probe/tools/review_record.py studies/knobe_moral_probe/tests/test_review_record.py
git commit -m "[knobe_moral_probe] tools: review decisions tied to the hash of the text reviewed"
```

---

### Task 3: Generate `stimuli/ngo_verbatim.csv`

**Files:**
- Create: `studies/knobe_moral_probe/stimuli/ngo_verbatim.csv` (generated)
- Modify: `studies/knobe_moral_probe/ANALYSIS_LOG.md`

- [ ] **Step 1: Generate**

Run: `cd studies/knobe_moral_probe && ../../.venv/bin/python -m tools.ngo_source`
Expected: `wrote 80 items to .../stimuli/ngo_verbatim.csv`

- [ ] **Step 2: Check it**

Run: `../../.venv/bin/python -c "from kmp.items import load_items, design_problems; i = load_items('stimuli/ngo_verbatim.csv'); print(len(i), design_problems(i, stage='authoring'))"`
Expected: `80 []`

Run again: `../../.venv/bin/python -m tools.ngo_source`
Expected: `... matches ... (80 items)` (compare-only once the file exists; `--update` is for parser fixes, Task 7).

- [ ] **Step 3: Commit**

```bash
git add studies/knobe_moral_probe/stimuli/ngo_verbatim.csv
git commit -m "[knobe_moral_probe] stimuli: ngo_verbatim.csv, Ngo's 80 items word for word (draft)"
```

- [ ] **Step 4: Log it**, using the hash of the Step 3 commit (`git rev-parse --short HEAD`). Append to `ANALYSIS_LOG.md`:

```
2026-MM-DD | `python -m tools.ngo_source` | source analysis/ngo_extensions/nonmoral_pilot/ngo_2015_original_80.txt; signs from Ngo's order (2N-1 bad, 2N good); agent overrides 12, 53, 57, 69, 70 | stimuli/ngo_verbatim.csv: 80 items, 40 pairs, design checks clean | <hash>
```

```bash
git add studies/knobe_moral_probe/ANALYSIS_LOG.md
git commit -m "[knobe_moral_probe] log the ngo_verbatim build"
```

---

### Task 4: Stimulus lint (`tools/lint_stimuli.py`)

**Files:**
- Create: `studies/knobe_moral_probe/tools/lint_stimuli.py`
- Test: `studies/knobe_moral_probe/tests/test_lint_stimuli.py`

The lint covers checklist items that code can check but `design_problems` does not. It does not repeat `design_problems`' checks (duplicates, pair completeness, B1, R2, the scaffold rules); the CLI runs `design_problems` first and then adds these. B8 is only partly automatable: the lint passes name and pronoun changes and changes listed in `nonmoral_log.csv`, and flags everything else. The researcher still reads the Ngo-vs-adapted text on the review sheet.

- [ ] **Step 1: Write the failing tests**

`studies/knobe_moral_probe/tests/test_lint_stimuli.py`:
```python
"""tools.lint_stimuli: mechanical checklist checks beyond design_problems."""
import csv

import pytest

from kmp.items import Item, make_item_id
from tools import lint_stimuli as lint
from tools import ngo_source
from tools.review_record import DECISION_FIELDS, text_sha256

CLERK_BAD = ("The clerk moved to a new apartment to be closer to the gym. The clerk did not care at all about "
             "the effect this would have on the clerk's savings. The clerk knew the move would drain the "
             "clerk's savings.")
CLERK_GOOD = CLERK_BAD.replace("would drain", "would grow")
GARDEN = "The coordinator rearranged the community garden's plots to shorten the watering route."
INDIFF = "The coordinator did not care at all about the effect this would have on {x}."


def make(experiment="nonmoral", sid=1, arm="prudential", sign="bad", agent="the clerk", effect=None,
         scenario=None, source="new", status="draft", scaffold=None):
    if scenario is None:
        scenario = CLERK_BAD if sign == "bad" else CLERK_GOOD
    if effect is None:
        effect = "drain the clerk's savings" if sign == "bad" else "grow the clerk's savings"
    if experiment == "foundations" and scaffold is None:
        scaffold = "shared"
    return Item(item_id=make_item_id(experiment, sid, arm, sign), experiment=experiment, storyline_id=sid,
                arm=arm, sign=sign, agent=agent, effect=effect, scenario=scenario, source=source,
                review_status=status, scaffold=scaffold)


def pair(**kw):
    return [make(sign="bad", **kw), make(sign="good", **kw)]


def fnd(sid, arm, sign, background, x, last, effect):
    return make(experiment="foundations", sid=sid, arm=arm, sign=sign, agent="the coordinator", effect=effect,
                scenario=" ".join([background, GARDEN, INDIFF.format(x=x), last]))


@pytest.fixture(scope="module")
def verbatim():
    return ngo_source.load_source()


# ---- per item ------------------------------------------------------------------------

def test_definitions_example_is_clean():
    assert lint.lint(pair()) == []


def test_sentence_count_and_question_line():
    item = make(scenario=CLERK_BAD + " Did the clerk intentionally drain the clerk's savings?")
    problems = lint.item_problems(item)
    assert any("4 sentences, the template has 3 (A1)" in p for p in problems)
    assert any("contains '?'" in p for p in problems)


def test_effect_form():
    assert any("(A10)" in p for p in lint.item_problems(make(effect="Drain the clerk's savings")))
    assert any("punctuation (A10)" in p for p in lint.item_problems(make(effect="drain the clerk's savings.")))
    assert any("without 'to'" in p for p in lint.item_problems(make(effect="to drain the clerk's savings")))


def test_agent_must_open_the_action_sentence():
    item = make(scenario=CLERK_BAD.replace("The clerk moved", "A clerk moved", 1))
    assert any("(A9)" in p for p in lint.item_problems(item))


def test_indifference_clause_template_for_new_items():
    item = make(scenario=CLERK_BAD.replace("the effect this would have", "the effect the move would have"))
    assert any("(A3)" in p for p in lint.item_problems(item))


def test_side_effect_sentence_opens_with_agent_knew():
    item = make(scenario=CLERK_BAD.replace("The clerk knew the move", "Everyone knew the move"))
    assert any("(A4)" in p for p in lint.item_problems(item))


def test_verbatim_items_get_only_a1_a9_a10(verbatim):
    assert [p for i in verbatim for p in lint.item_problems(i)] == []


# ---- pairs, storylines, file -----------------------------------------------------------------

def test_b2_flags_a_pair_differing_before_the_side_effect():
    good = make(sign="good", scenario=CLERK_GOOD.replace("closer to the gym", "closer to the park"))
    assert lint.pair_problems([make(sign="bad"), good]) == ["pair (1, 'prudential'): bad and good differ "
                                                           "before the side-effect sentence (B2)"]


def test_c2_one_agent_per_storyline():
    items = pair() + [make(arm="procedural", sign=s, agent="the engineer",
                           scenario=(CLERK_BAD if s == "bad" else CLERK_GOOD).replace("clerk", "engineer"))
                      for s in ("bad", "good")]
    assert any("agents differ across arms" in p for p in lint.storyline_problems(items, []))


def test_c3_fresh_action_needs_a_log_row():
    moral = [make(arm="moral", sign=s, source="ngo",
                  scenario=(CLERK_BAD if s == "bad" else CLERK_GOOD).replace("to be closer to the gym",
                                                                            "to be closer to work"))
             for s in ("bad", "good")]
    items = moral + pair()
    assert any("(C3, decision E)" in p for p in lint.storyline_problems(items, []))
    row = {"item_id": "kmp-nm-001-prudential-bad", "kind": "fresh_action"}
    assert lint.storyline_problems(items, [row]) == []


def test_c4_foundations_share_the_action_sentence():
    items = [fnd(1, "harm", "bad", "One older member has a bad knee.", "the older member",
                 "The coordinator knew the new layout would hurt the older member's knee.", "hurt the older member's knee"),
             fnd(1, "harm", "good", "One older member has a bad knee.", "the older member",
                 "The coordinator knew the new layout would ease the older member's knee pain.",
                 "ease the older member's knee pain")]
    assert lint.lint(items) == []
    changed = items[1].model_copy(update={"scenario": items[1].scenario.replace("watering route", "mowing route")})
    assert any("(C4)" in p for p in lint.storyline_problems([items[0], changed], []))


def test_d3_role_noun_reused_across_storylines():
    items = pair() + pair(sid=2)
    assert lint.file_problems(items) == ["file: role noun 'the clerk' is used by storylines [1, 2] (D3)"]


def test_d2_expect_complete_lists_missing_pairs():
    problems = lint.file_problems(pair(), expect_complete=True)
    assert "file: storyline 1 has no complete moral pair (D2)" in problems
    assert len(problems) == 40 * 3 - 1


# ---- B8: adapted Ngo pairs against the verbatim text ---------------------------------------------------

MANAGER_BAD = ("The manager enacted the plan to increase earnings. The manager did not care at all about the "
               "effect the plan would have on the manager's employees. The manager knew the plan would make "
               "employees unhappy.")


def adapted(sid, sign, scenario, effect, agent="the manager"):
    return make(sid=sid, arm="moral", sign=sign, agent=agent, effect=effect, scenario=scenario, source="ngo")


def test_b8_name_and_pronoun_changes_pass(verbatim):
    items = [adapted(19, "bad", MANAGER_BAD, "make employees unhappy"),
             adapted(19, "good", MANAGER_BAD.replace("unhappy.", "happy."), "make employees happy")]
    assert lint.adaptation_problems(items, verbatim, []) == []


def test_b8_other_changes_need_a_log_row(verbatim):
    item = adapted(19, "bad", MANAGER_BAD.replace("make employees unhappy", "make staff unhappy"),
                   "make employees unhappy")
    problems = lint.adaptation_problems([item], verbatim, [])
    assert problems == ["kmp-nm-019-moral-bad: scenario changes 'employees' to 'staff', which is not a name or "
                        "pronoun change and not in the authoring log (B8)"]
    row = {"item_id": item.item_id, "field": "scenario", "kind": "typo", "from": "make employees unhappy",
           "to": "make staff unhappy", "note": "test"}
    assert lint.adaptation_problems([item], verbatim, [row]) == []


def test_b8_goal_alignment_and_stale_rows(verbatim):
    bad = ("The investor enacted a financial scheme to buy a house. The investor did not care at all about the "
           "effect the scheme would have on old retirees. The investor knew the plan would bankrupt old retirees.")
    good = ("The investor enacted a financial scheme to buy a house. The investor did not care at all about the "
            "effect the scheme would have on old retirees. The investor knew the plan would help old retirees.")
    items = [adapted(3, "bad", bad, "bankrupt old retirees", "the investor"),
             adapted(3, "good", good, "help old retirees", "the investor")]
    goal = {"item_id": "kmp-nm-003-moral-good", "field": "scenario", "kind": "goal", "from": "to buy a car",
            "to": "to buy a house", "note": "decision B2"}
    assert any("to 'house'" in p for p in lint.adaptation_problems(items, verbatim, []))
    assert lint.adaptation_problems(items, verbatim, [goal]) == []
    stale = {**goal, "from": "to buy a boat"}
    assert any("stale" in p for p in lint.adaptation_problems(items, verbatim, [stale]))
    boat = [items[0], items[1].model_copy(update={"scenario": good.replace("buy a house", "buy a boat")})]
    wrong_goal = {**goal, "to": "to buy a boat"}
    assert any("not the bad version's goal" in p for p in lint.adaptation_problems(boat, verbatim, [wrong_goal]))


def test_b8_checks_the_effect_too(verbatim):
    item = adapted(19, "bad", MANAGER_BAD, "upset employees")
    assert any("effect changes" in p for p in lint.adaptation_problems([item], verbatim, []))


def test_lint_requires_verbatim_for_adapted_items():
    item = adapted(19, "bad", MANAGER_BAD, "make employees unhappy")
    assert "file: adapted Ngo items need --verbatim to check B8" in lint.lint([item])


# ---- B9, authoring log, approvals, CLI -------------------------------------------------------------------

def test_b9_verbatim_must_equal_the_source(verbatim):
    assert lint.lint(verbatim) == []
    edited = [verbatim[0].model_copy(update={"scenario": verbatim[0].scenario.replace("babies.", "infants.")}),
              *verbatim[1:]]
    assert any("(B9)" in p for p in lint.lint(edited))


def test_log_rows_are_checked():
    rows = [{"item_id": "kmp-nm-099-moral-bad", "field": "question", "kind": "whim", "from": "", "to": "", "note": ""}]
    problems = lint.log_problems(pair(), rows)
    assert len(problems) == 4


def test_approved_items_need_a_decision():
    items = pair(status="approved")
    assert any("no review decision" in p for p in lint.lint(items))
    rows = [{"item_id": i.item_id, "text_sha256": text_sha256(i), "decision": "approved", "file": "f"} for i in items]
    assert lint.lint(items, decisions=rows) == []


def test_cli(tmp_path, capsys):
    from kmp.items import write_items
    path = tmp_path / "nonmoral.csv"
    write_items(pair(), path)
    review = tmp_path / "review"
    review.mkdir()
    args = [str(path), "--log", str(tmp_path / "none.csv"), "--verbatim", str(tmp_path / "none.csv"),
            "--review-dir", str(review)]
    assert lint.main(args) == 0
    assert "prudential: 1 draft pairs" in capsys.readouterr().out
    write_items(pair() + pair(sid=2), path)
    assert lint.main(args) == 1
    assert "(D3)" in capsys.readouterr().err
```

- [ ] **Step 2: Run them to verify they fail**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests/test_lint_stimuli.py -q`
Expected: collection error, `ImportError: cannot import name 'lint_stimuli' from 'tools'`.

- [ ] **Step 3: Write the implementation**

`studies/knobe_moral_probe/tools/lint_stimuli.py`:
```python
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
        if set(pair) != {"bad", "good"} or pair["bad"].source == "ngo":
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


def _naming_change(old: list[str], new: list[str], verbatim_agent: str, role_noun: str) -> bool:
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
                if tag == "equal" or _naming_change(old, new, original.agent, item.agent):
                    continue
                if any(_within(old, r["from"]) and _within(new, r["to"]) for r in listed):
                    continue
                out.append(f"{item.item_id}: {field} changes {' '.join(old)!r} to {' '.join(new)!r}, which is "
                           f"not a name or pronoun change and not in the authoring log (B8)")
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests/test_lint_stimuli.py -q`
Expected: `22 passed`.

- [ ] **Step 5: Lint the verbatim file**

Run: `cd studies/knobe_moral_probe && ../../.venv/bin/python -m tools.lint_stimuli stimuli/ngo_verbatim.csv`
Expected: `moral: 40 draft pairs` then `stimuli/ngo_verbatim.csv: clean (80 items)`, exit 0.

- [ ] **Step 6: Commit**

```bash
git add studies/knobe_moral_probe/tools/lint_stimuli.py studies/knobe_moral_probe/tests/test_lint_stimuli.py
git commit -m "[knobe_moral_probe] tools: stimulus lint for checklist items design_problems leaves out (incl. B8 diff, B9)"
```

---

### Task 5: Review sheets and decisions (`tools/review.py`)

**Files:**
- Create: `studies/knobe_moral_probe/tools/review.py`
- Test: `studies/knobe_moral_probe/tests/test_review.py`

`sheet` is the drafting agent's command. It refuses unless the whole file passes `design_problems` and the lint. It writes `stimuli/review/<batch>.md` with the batch's draft items grouped by storyline: the checks that apply to each pair (DEFINITIONS §6 "Which checks apply"), Ngo's original text next to adapted Ngo items, log rows, and capitalised mid-sentence words as R1 name candidates. It also writes `<batch>_decisions.csv`, prefilled with `item_id` and `text_sha256`. `apply` is the researcher's command.

- [ ] **Step 1: Write the failing tests**

`studies/knobe_moral_probe/tests/test_review.py`:
```python
"""tools.review: review sheets for the drafting agent, decisions applied by the researcher."""
import csv

from kmp.items import load_items, write_items
from tools import ngo_source, review
from tools.review_record import DECISION_FIELDS, text_sha256

from test_lint_stimuli import pair


def _fill(path, decision="approved", note=""):
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for row in rows:
        row.update(decision=decision, reviewer="MM", date="2026-10-02", note=note)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=DECISION_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _setup(tmp_path, items):
    path = tmp_path / "nonmoral.csv"
    write_items(items, path)
    (tmp_path / "review").mkdir()
    common = ["--items", str(path)]
    sheet_args = ["sheet", *common, "--review-dir", str(tmp_path / "review"),
                  "--log", str(tmp_path / "none.csv"), "--verbatim", str(tmp_path / "none.csv")]
    return path, sheet_args


def test_checks_follow_the_checklist_applicability():
    assert review.PAIR_CHECKS["ngo_verbatim"] == ["A1", "A10", "A13", "B9"]
    assert "B8" in review.PAIR_CHECKS["ngo_adapted"] and "B2" not in review.PAIR_CHECKS["ngo_adapted"]
    assert "B8" not in review.PAIR_CHECKS["new"] and "A13" in review.PAIR_CHECKS["new"]


def test_name_candidates_flag_mid_sentence_capitals():
    item = ngo_source.load_source()[8]   # item 9: "The mayor diverted water to Oldtown ..."
    assert review.name_candidates(item) == ["Newtown", "Oldtown"]
    assert review.name_candidates(pair()[0]) == []


def test_parse_range():
    assert review.parse_range("1-3,7") == {1, 2, 3, 7}


def test_sheet_then_apply_round_trip(tmp_path, capsys):
    path, sheet_args = _setup(tmp_path, pair() + pair(arm="procedural"))
    assert review.main([*sheet_args, "--batch", "01_test", "--arms", "prudential"]) == 0
    sheet = (tmp_path / "review" / "01_test.md").read_text(encoding="utf-8")
    assert "## Storyline 1: the clerk" in sheet and "### prudential" in sheet and "procedural" not in sheet
    assert "B2 B3 B4 B5 B6 B7" in sheet
    decisions = tmp_path / "review" / "01_test_decisions.csv"
    _fill(decisions)
    assert review.main(["apply", "--items", str(path), "--decisions", str(decisions)]) == 0
    statuses = {i.item_id: i.review_status for i in load_items(path)}
    assert statuses == {"kmp-nm-001-prudential-bad": "approved", "kmp-nm-001-prudential-good": "approved",
                        "kmp-nm-001-procedural-bad": "draft", "kmp-nm-001-procedural-good": "draft"}
    # The approved items now leave the next sheet, and their approvals pass lint.
    assert review.main([*sheet_args, "--batch", "02_test"]) == 0
    assert "prudential" not in (tmp_path / "review" / "02_test.md").read_text(encoding="utf-8")


def test_sheet_refuses_an_existing_batch_and_unclean_files(tmp_path, capsys):
    path, sheet_args = _setup(tmp_path, pair())
    assert review.main([*sheet_args, "--batch", "01_test"]) == 0
    assert review.main([*sheet_args, "--batch", "01_test"]) == 2
    write_items(pair() + pair(sid=2), path)                       # D3 problem
    assert review.main([*sheet_args, "--batch", "02_test"]) == 1
    assert not (tmp_path / "review" / "02_test.md").exists()


def test_apply_refuses_incomplete_rows_and_changed_text(tmp_path, capsys):
    path, sheet_args = _setup(tmp_path, pair())
    assert review.main([*sheet_args, "--batch", "01_test"]) == 0
    decisions = tmp_path / "review" / "01_test_decisions.csv"
    assert review.main(["apply", "--items", str(path), "--decisions", str(decisions)]) == 2   # blank decisions
    _fill(decisions, decision="rejected")                                                     # no note
    assert review.main(["apply", "--items", str(path), "--decisions", str(decisions)]) == 2
    assert "needs a note" in capsys.readouterr().err
    edited = [i.model_copy(update={"effect": "lose the clerk's savings"}) if i.sign == "bad" else i for i in pair()]
    write_items(edited, path)
    _fill(decisions, decision="approved")
    assert review.main(["apply", "--items", str(path), "--decisions", str(decisions)]) == 2
    assert "changed since the sheet was made" in capsys.readouterr().err
    assert {i.review_status for i in load_items(path)} == {"draft"}


def test_revise_keeps_the_item_a_draft():
    item = pair()[0]
    row = {"item_id": item.item_id, "text_sha256": text_sha256(item), "decision": "revise", "reviewer": "MM",
           "date": "2026-10-02", "note": "B4: bigger"}
    updated, problems = review.apply_decisions([item], [row])
    assert problems == [] and updated[0].review_status == "draft"
```

- [ ] **Step 2: Run them to verify they fail**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests/test_review.py -q`
Expected: collection error, `ImportError: cannot import name 'review' from 'tools'`.

- [ ] **Step 3: Write the implementation**

`studies/knobe_moral_probe/tools/review.py`:
```python
"""Review sheets and review decisions (DESIGN.md section 3.4 step 2;
DEFINITIONS_AND_CHECKLIST.md sections 1 and 6).

  sheet  (run by the drafting agent) writes a markdown review sheet for one
         batch of draft items, grouped by storyline, with the checklist IDs
         that apply to each pair, any authoring-log rows, Ngo's
         original text for adapted Ngo items, and capitalised words that may
         be personal names (R1). Next to it, a decisions template: one row
         per item with its text_sha256 and the decision columns empty.
         Refuses (writes nothing) unless design_problems and lint are clean.
  apply  (run by the researcher only) reads filled-in decisions and sets
         review_status: approved, rejected, or draft for "revise". It
         refuses the whole file if any row is incomplete or if an item's
         text changed since the sheet was made. The drafting agent never
         runs apply and never edits review_status.

Run from the study folder:
    ../../.venv/bin/python -m tools.review sheet --items stimuli/nonmoral.csv --batch 02_nm_moral_01-20 --arms moral --storylines 1-20
    ../../.venv/bin/python -m tools.review apply --items stimuli/nonmoral.csv --decisions stimuli/review/02_nm_moral_01-20_decisions.csv
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

from kmp.items import Item, design_problems, load_items, write_items
from tools import lint_stimuli
from tools.review_record import (DECISION_FIELDS, DECISIONS, REVIEW_DIR, decision_files, read_decisions,
                                 text_sha256)

_A = [f"A{i}" for i in range(1, 14)]
_R = ["R1", "R2", "R3", "R4"]
PAIR_CHECKS = {   # DEFINITIONS_AND_CHECKLIST.md section 6, "Which checks apply"
    "ngo_verbatim": ["A1", "A10", "A13", "B9"],
    "ngo_adapted": ["A1", "A9", "A10", "A13", *_R, "B1", "B8"],
    "new": [*_A, *_R, "B1", "B2", "B3", "B4", "B5", "B6", "B7"],
}
STORYLINE_CHECKS = {"ngo_verbatim": ["C1"], "nonmoral": ["C1", "C2", "C3"],
                    "shared": ["C2", "C4", "C5", "C6"], "purpose": ["C2", "C7"]}


def pair_kind(item: Item) -> str:
    if item.experiment == "ngo_verbatim":
        return "ngo_verbatim"
    return "ngo_adapted" if lint_stimuli.is_adapted_ngo(item) else "new"


def storyline_kind(item: Item) -> str:
    return item.scaffold if item.experiment == "foundations" else item.experiment


def name_candidates(item: Item) -> list[str]:
    """Capitalised words that do not open a sentence and are not the agent: possible names (R1)."""
    agent_words = {w for word in item.agent.split() for w in (word, word.capitalize())}
    words = [w for s in lint_stimuli.split_sentences(item.scenario) for w in s.split()[1:]] + item.effect.split()
    stripped = (w.strip(".,;:!?\"()") for w in words)
    return sorted({w for w in stripped if w[:1].isupper() and w not in agent_words})


def parse_range(text: str) -> set[int]:
    """'1-20,25' -> {1..20, 25}."""
    out: set[int] = set()
    for part in text.split(","):
        lo, _, hi = part.partition("-")
        out |= set(range(int(lo), int(hi or lo) + 1))
    return out


def select(items: list[Item], storylines: set[int] | None, arms: set[str] | None) -> list[Item]:
    """Draft items in the batch."""
    return [i for i in items if i.review_status == "draft"
            and (storylines is None or i.storyline_id in storylines) and (arms is None or i.arm in arms)]


def render_sheet(batch: str, selected: list[Item], log_rows: list[dict[str, str]],
                 originals: dict[str, Item], items_path: str) -> str:
    log_by_item: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in log_rows:
        log_by_item[row["item_id"]].append(row)
    lines = [f"# Review sheet: {batch}", "",
             f"Items: `{items_path}`, {len(selected)} draft items. Checklist: "
             f"`docs/DEFINITIONS_AND_CHECKLIST.md` section 6.", "",
             f"Record one decision per item in `stimuli/review/{batch}_decisions.csv`: `approved`, `rejected` or "
             f"`revise`, your initials as reviewer, the date (YYYY-MM-DD), and a note for every rejected or "
             f"revise row naming the failed check (e.g. \"B4: good version is bigger\"). Then run "
             f"`../../.venv/bin/python -m tools.review apply --items {items_path} --decisions "
             f"stimuli/review/{batch}_decisions.csv` yourself.", "",
             "Automated checks (design_problems and tools.lint_stimuli) were clean when this sheet was made.", ""]
    by_storyline: dict[int, list[Item]] = defaultdict(list)
    for item in selected:
        by_storyline[item.storyline_id].append(item)
    for sid, members in sorted(by_storyline.items()):
        kind = storyline_kind(members[0])
        lines += [f"## Storyline {sid}: {members[0].agent} ({kind}; storyline checks "
                  f"{' '.join(STORYLINE_CHECKS[kind])})", ""]
        arms: dict[str, list[Item]] = defaultdict(list)
        for m in members:
            arms[m.arm].append(m)
        for arm, versions in sorted(arms.items()):
            kind = pair_kind(versions[0])
            lines += [f"### {arm} (source {versions[0].source}; checks {' '.join(PAIR_CHECKS[kind])})", ""]
            for item in sorted(versions, key=lambda i: i.sign):
                lines += [f"**{item.sign}** `{item.item_id}`", "", f"> {item.scenario}", "",
                          f"- agent: `{item.agent}`", f"- effect: `{item.effect}`"]
                if item.item_id in originals:
                    lines += [f"- Ngo's original: {originals[item.item_id].scenario}",
                              f"- Ngo's effect: `{originals[item.item_id].effect}`"]
                lines += [f"- log ({r['kind']}, {r['field']}): {r['from']!r} -> {r['to']!r}. {r['note']}"
                          for r in log_by_item[item.item_id]]
                names = name_candidates(item)
                if names:
                    lines.append(f"- capitalised words (R1: names?): {', '.join(names)}")
                lines.append("")
    return "\n".join(lines) + "\n"


def write_template(selected: list[Item], path: Path) -> None:
    if path.exists():
        raise FileExistsError(f"{path} exists; it may hold decisions. Use a new batch name.")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=DECISION_FIELDS)
        writer.writeheader()
        for item in sorted(selected, key=lambda i: i.item_id):
            writer.writerow({"item_id": item.item_id, "text_sha256": text_sha256(item)})


def apply_decisions(items: list[Item], rows: list[dict[str, str]]) -> tuple[list[Item], list[str]]:
    """(updated items, problems). If problems is non-empty, nothing should be written."""
    by_id = {i.item_id: i for i in items}
    updated, problems = dict(by_id), []
    for n, row in enumerate(rows, start=2):
        where = f"{row.get('file', 'decisions')} line {n}"
        item = by_id.get(row["item_id"])
        if item is None:
            problems.append(f"{where}: unknown item {row['item_id']!r}")
            continue
        if row["decision"] not in DECISIONS:
            problems.append(f"{where}: decision {row['decision']!r} not in {DECISIONS}")
            continue
        if not row["reviewer"].strip():
            problems.append(f"{where}: reviewer is empty")
        try:
            date.fromisoformat(row["date"])
        except ValueError:
            problems.append(f"{where}: date {row['date']!r} is not YYYY-MM-DD")
        if row["decision"] != "approved" and not row["note"].strip():
            problems.append(f"{where}: a {row['decision']} decision needs a note naming the failed check")
        if row["text_sha256"] != text_sha256(item):
            problems.append(f"{where}: {item.item_id} changed since the sheet was made; review it again")
        status = "draft" if row["decision"] == "revise" else row["decision"]
        updated[item.item_id] = item.model_copy(update={"review_status": status})
    return list(updated.values()), problems


def _read_filled(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as fh:
        return [{**row, "file": str(path)} for row in csv.DictReader(fh)]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="review sheets and decisions for authored items")
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("sheet", help="write a review sheet and a decisions template (drafting agent)")
    s.add_argument("--items", required=True, type=Path)
    s.add_argument("--batch", required=True, help="NN_<name>, e.g. 02_nm_moral_01-20")
    s.add_argument("--storylines", help="e.g. 1-20 (default: all)")
    s.add_argument("--arms", help="comma-separated (default: all)")
    s.add_argument("--review-dir", type=Path, default=REVIEW_DIR)
    s.add_argument("--verbatim", type=Path, default=lint_stimuli.VERBATIM)
    s.add_argument("--log", type=Path, default=lint_stimuli.LOG)
    a = sub.add_parser("apply", help="apply filled-in decisions (researcher only)")
    a.add_argument("--items", required=True, type=Path)
    a.add_argument("--decisions", required=True, type=Path)
    args = p.parse_args(argv)
    items = load_items(args.items)

    if args.command == "apply":
        rows = _read_filled(args.decisions)
        missing = [r["item_id"] for r in rows if not r["decision"].strip()]
        if missing:
            print(f"refusing: {len(missing)} row(s) have no decision: {missing}", file=sys.stderr)
            return 2
        updated, problems = apply_decisions(items, rows)
        if problems:
            print("refusing; nothing written:\n  " + "\n  ".join(problems), file=sys.stderr)
            return 2
        write_items(updated, args.items)
        counts = defaultdict(int)
        for r in rows:
            counts[r["decision"]] += 1
        print(f"applied {len(rows)} decisions to {args.items}: {dict(sorted(counts.items()))}")
        return 0

    log_rows = lint_stimuli.read_log(args.log) if args.log.exists() else []
    verbatim = load_items(args.verbatim) if args.verbatim.exists() else None
    problems = design_problems(items, stage="authoring") + lint_stimuli.lint(
        items, log_rows=log_rows, verbatim=verbatim, decisions=read_decisions(decision_files(args.review_dir)))
    if problems:
        print(f"automated checks are not clean; no sheet written ({len(problems)} problem(s)):\n  "
              + "\n  ".join(problems), file=sys.stderr)
        return 1
    selected = select(items, parse_range(args.storylines) if args.storylines else None,
                      set(args.arms.split(",")) if args.arms else None)
    if not selected:
        print("no draft items match; nothing written", file=sys.stderr)
        return 2
    originals = {}
    if verbatim is not None:
        by_key = {(v.storyline_id, v.sign): v for v in verbatim}
        originals = {i.item_id: by_key[(i.storyline_id, i.sign)] for i in selected
                     if lint_stimuli.is_adapted_ngo(i) and (i.storyline_id, i.sign) in by_key}
    sheet = args.review_dir / f"{args.batch}.md"
    try:
        write_template(selected, args.review_dir / f"{args.batch}_decisions.csv")
    except FileExistsError as exc:
        print(f"refusing: {exc}", file=sys.stderr)
        return 2
    sheet.write_text(render_sheet(args.batch, selected, log_rows, originals, str(args.items)), encoding="utf-8")
    print(f"wrote {sheet} and its decisions template ({len(selected)} items)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests/test_review.py -q`
Expected: `7 passed`.

- [ ] **Step 5: Run the full suite**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests -q`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add studies/knobe_moral_probe/tools/review.py studies/knobe_moral_probe/tests/test_review.py
git commit -m "[knobe_moral_probe] tools: review sheets for the drafting agent; decisions applied by the researcher only"
```

---

### Task 6: README

**Files:**
- Modify: `studies/knobe_moral_probe/README.md`

- [ ] **Step 1: Add the authoring tools to the Contents table**, after the `tools/check_chat_bos.py` row:

```markdown
| `tools/ngo_source.py` | Ngo's 80 vignettes → `stimuli/ngo_verbatim.csv`; compare-only once it exists |
| `tools/lint_stimuli.py` | checklist checks beyond `design_problems` (A1 A3 A4 A9 A10 B2 B8 B9 C2 C3 C4 D2 D3, approvals) |
| `tools/review.py` | `sheet`: review sheet + decisions template (drafting agent); `apply`: decisions → review_status (researcher only) |
| `docs/AUTHORING_PLAN.md` | the stimuli authoring plan |
```

  Change the `stimuli/` row to:

```markdown
| `stimuli/` | one items file per experiment (`nonmoral.csv`, `foundations.csv`, `ngo_verbatim.csv`); `nonmoral_log.csv` (every change from Ngo, every fresh action); `NOTES.md` (conventions, role nouns, scaffolds, batches, disclosure); `review/` (sheets and the researcher's decisions) |
```

- [ ] **Step 2: Add the exception under "Relation to earlier work".** Replace "and reads none of their outputs except one: `analysis/power_basis.py`, the design-stage power check, reads the MF pilot's committed `sign_wcb_parsed.csv`." with:

```markdown
and reads none of their outputs except one: `analysis/power_basis.py`, the
design-stage power check, reads the MF pilot's committed
`sign_wcb_parsed.csv`. It also reads one pilot *input*:
`tools/ngo_source.py` parses the pilots' copy of Ngo et al.'s stimuli,
`nonmoral_pilot/ngo_2015_original_80.txt`. The pilot variant files are read
by the authors as drafting material, never by code.
```

- [ ] **Step 3: Add an "Authoring" block under Commands**, before "Screening":

```markdown
**Authoring** (`docs/AUTHORING_PLAN.md`). Lint every items file after each
edit; the review sheet refuses files that aren't clean. Only the researcher
runs `apply`.

    ../../.venv/bin/python -m tools.lint_stimuli stimuli/<experiment>.csv
    ../../.venv/bin/python -m tools.review sheet --items stimuli/<experiment>.csv --batch NN_<name> [--storylines 1-20] [--arms moral]
    ../../.venv/bin/python -m tools.review apply --items stimuli/<experiment>.csv --decisions stimuli/review/NN_<name>_decisions.csv
```

- [ ] **Step 4: Commit**

```bash
git add studies/knobe_moral_probe/README.md
git commit -m "[knobe_moral_probe] README: authoring tools and the Ngo source exception"
```

---

### Task 7: Review batch 01, the verbatim set (80 items)

**Files:**
- Create: `studies/knobe_moral_probe/stimuli/review/01_nv_all.md`, `01_nv_all_decisions.csv` (generated)
- Modify (by the researcher's `apply`): `studies/knobe_moral_probe/stimuli/ngo_verbatim.csv`

Checks the researcher applies: A1, A10, A13, B9 (DEFINITIONS §6). In practice: does `effect` read correctly in "Did {agent} intentionally {effect}?" and "it would {effect}", with Ngo's own typos (e.g. item 72 "make the tablet accessible")? And is `agent` right (decision M)? The text itself cannot change, because it is Ngo's.

- [ ] **Step 1: Make the sheet**

Run: `cd studies/knobe_moral_probe && ../../.venv/bin/python -m tools.review sheet --items stimuli/ngo_verbatim.csv --batch 01_nv_all`
Expected: `wrote stimuli/review/01_nv_all.md and its decisions template (80 items)`

- [ ] **Step 2: Commit the sheet and the empty template**

```bash
git add studies/knobe_moral_probe/stimuli/review/01_nv_all.md studies/knobe_moral_probe/stimuli/review/01_nv_all_decisions.csv
git commit -m "[knobe_moral_probe] review sheet 01: ngo_verbatim (80 items)"
```

- [ ] **Step 3: STOP.** Tell the researcher that `stimuli/review/01_nv_all.md` is ready. They fill in `01_nv_all_decisions.csv` and run `tools.review apply --items stimuli/ngo_verbatim.csv --decisions stimuli/review/01_nv_all_decisions.csv` themselves.
- [ ] **Step 4: If any item is marked `revise`**, the fix is in the parser, not the CSV. Change `AGENT_OVERRIDES` or `NO_INTENT_SUBJECT` with a test (as in Task 1), commit, then run `../../.venv/bin/python -m tools.ngo_source --update`. That rewrites the file from the source, keeps the researcher's statuses on unchanged items, and resets changed items to `draft`. Re-sheet them as the next free batch number (for example `02_nv_fix`; later batch numbers shift by one), commit, and STOP again.
- [ ] **Step 5: Verify and commit the researcher's decisions**

Run: `../../.venv/bin/python -m tools.lint_stimuli stimuli/ngo_verbatim.csv`
Expected: `moral: 40 approved pairs`, clean.

```bash
git add studies/knobe_moral_probe/stimuli/ngo_verbatim.csv studies/knobe_moral_probe/stimuli/review/01_nv_all_decisions.csv
git commit -m "[knobe_moral_probe] review 01: researcher's decisions on ngo_verbatim applied"
```

---

### Task 8: How to add draft items (used by every content batch)

This is not a separate commit; it is the method Tasks 10–15 use. Never type an `item_id`. Build items with `make_item_id`, merge them into the file, and write with `write_items`, which sorts and quotes consistently. Run this from the study folder with a scratch script in the session scratchpad. It is not committed, because the CSV is the record:

```python
from kmp.items import Item, load_items, make_item_id, write_items
from pathlib import Path

PATH = Path("stimuli/nonmoral.csv")
existing = load_items(PATH) if PATH.exists() else []
new = [
    # One dict per version; ids are generated. Example from DEFINITIONS §4.2 (illustrative, not a real item):
    dict(experiment="nonmoral", storyline_id=99, arm="prudential", sign="bad", agent="the clerk",
         effect="drain the clerk's savings",
         scenario=("The clerk moved to a new apartment to be closer to the gym. The clerk did not care at all "
                   "about the effect this would have on the clerk's savings. The clerk knew the move would "
                   "drain the clerk's savings."),
         source="new"),
]
items = [Item(item_id=make_item_id(d["experiment"], d["storyline_id"], d["arm"], d["sign"]),
              review_status="draft", scaffold=d.pop("scaffold", None), **d) for d in new]
clash = {i.item_id for i in items} & {i.item_id for i in existing}
assert not clash, f"already in the file: {sorted(clash)}"
write_items(existing + items, PATH)
```

To revise an item after a "revise" or "rejected" decision, replace it with `item.model_copy(update={...text fields..., "review_status": "draft"})` and write the file. The lint then accepts it, because drafts need no decision.

---

### Task 9: `stimuli/NOTES.md`, `nonmoral_log.csv` and the role-noun table (gate)

**Files:**
- Create: `studies/knobe_moral_probe/stimuli/NOTES.md`
- Create: `studies/knobe_moral_probe/stimuli/nonmoral_log.csv`

C2 fixes the role noun for every arm of a storyline, and D3 requires it to be unique in the file. So the 40 role nouns are chosen and reviewed before any nonmoral item is drafted.

- [ ] **Step 1: Create `nonmoral_log.csv`** with just the header line:

```
item_id,field,kind,from,to,note
```

- [ ] **Step 2: Create `NOTES.md`** with these sections, filled in:

```markdown
# Stimuli notes

How the three items files were written. The machine-readable record of
every change from Ngo et al. (2015) and every fresh action is
`nonmoral_log.csv`; the review record is `review/*_decisions.csv`.

## Authorship and disclosure (DESIGN.md §3.4)

Every item except the `ngo_verbatim` set was drafted by an LLM (Claude;
model ID and date per batch below) and reviewed item by item by the
researcher against `docs/DEFINITIONS_AND_CHECKLIST.md` §6. `approved` is
set only by `tools.review apply` from the researcher's decisions file, and
`tools.lint_stimuli` checks that every approval matches the current text.
The paper's methods disclose this; suggested wording: "Items were drafted
with an LLM (Claude) and every item was reviewed by the authors against a
written checklist before screening."

Screening reviewer: `claude-sonnet-4-6` (`protocol.REVIEWER_MODEL`; DESIGN.md amendment 2026-10-01, reviewer pin).
Drafting model: <ID, per batch below>. It differs from the reviewer, so the screen is not the drafter (decision T).

## File-wide conventions

- Straight apostrophes (') in all authored items; `ngo_verbatim` keeps Ngo's
  curly ones (decision N). The B8 lint reads ’ and ' as equal.
- Role nouns: lower case mid-sentence in `agent` ("the manager"),
  capitalised at the start of a sentence (DEFINITIONS §3.4).
- Self-referring side effects repeat the role noun (decision J).

## Role nouns, one per storyline (C2, D3, decisions O and P)

| storyline | Ngo bad / good agent | role noun | why (kept / neutralised / replaced / R3 exception) | loaded role (decision P) |
|---|---|---|---|---|
| 1 | Bill / Robyn | (chosen in Step 3) | name → role | no |

## Batches

| batch | file | storylines / arms | items | drafting model | drafted | sheet commit | decisions applied |
|---|---|---|---|---|---|---|---|

## Foundations scaffold roster (Task 14)
```

- [ ] **Step 3: Fill in the role-noun table, all 40 rows.**
  - Rules: DEFINITIONS §2.1, R3, D3, decisions O and P.
  - Each role must fit the adapted Ngo action, and also work for a prudential and a procedural story (C3).
  - Sources: the agents in `stimuli/ngo_verbatim.csv` and the roles in `nonmoral_pilot/prudential_variants.py` and `procedural_variants.py`. The pilot roles are names; take only role ideas from them.
- [ ] **Step 4: Commit**

```bash
git add studies/knobe_moral_probe/stimuli/NOTES.md studies/knobe_moral_probe/stimuli/nonmoral_log.csv
git commit -m "[knobe_moral_probe] stimuli: notes, change log, role nouns for the 40 Ngo storylines (for review)"
```

- [ ] **Step 5: STOP.** Ask the researcher to review the role-noun table (R3, D3, decisions O and P). Make the changes they ask for, commit them as "[knobe_moral_probe] stimuli: role nouns as reviewed", and continue only once they say the table stands.

---

### Task 10: Batches 02–03, adapted Ngo moral pairs (2 × 40 items)

**Files:**
- Create/modify: `studies/knobe_moral_probe/stimuli/nonmoral.csv`
- Modify: `studies/knobe_moral_probe/stimuli/nonmoral_log.csv`, `stimuli/NOTES.md` (batch table)
- Create: `stimuli/review/02_nm_moral_01-20.md` and `_decisions.csv`; `03_nm_moral_21-40.md` and `_decisions.csv`

| batch | storylines | items |
|---|---|---|
| `02_nm_moral_01-20` | 1–20 | 40 |
| `03_nm_moral_21-40` | 21–40 | 40 |

Rules: DEFINITIONS §3.5, §2.1, decisions B2, C, K, L, O. Columns: `experiment=nonmoral`, `arm=moral`, `source=ngo`, `storyline_id` = Ngo pair N, `sign` as in `ngo_verbatim`, `agent` = the storyline's role noun from NOTES.md, `review_status=draft`, `scaffold` empty. Start every item from its `ngo_verbatim` twin. Change only these things:
1. The agent's names and pronouns become the role noun, or a restructure ("her plan" → "the plan", "her employees" → "the manager's employees"). No log row is needed.
2. Non-agent names become roles, with their pronouns replaced (decision L). Each gets an `other_name` row.
3. The good version's goal becomes the bad version's, where they differ (decision B2): a `goal` row on the good item, `from` = Ngo's goal phrase and `to` = the bad version's.
4. Typo fixes (decision C): a `typo` row each. Known ones: item 23 "would have rates of cancer", item 40 "his new road", item 58 "the effect would have on". The adaptation itself removes items 10 and 53. Look for more and list each one.
5. `effect` is Ngo's question phrase with the role noun (decision C). Where it disagrees with the scenario (items 17, 72, and any others found), choose case by case and add an `effect` row.
Nothing else changes (decision K). Differences in action, object or affected party stay.

Run Steps 1–7 once per row of the table, in order:

- [ ] **Step 1: Draft the batch's pairs** with the Task 8 method, and add their log rows to `nonmoral_log.csv`.
- [ ] **Step 2: Lint until clean**

Run: `cd studies/knobe_moral_probe && ../../.venv/bin/python -m tools.lint_stimuli stimuli/nonmoral.csv`
Expected: exit 0. Every B8 complaint is either fixed (the change was not allowed) or logged (it was allowed and needs a row).

- [ ] **Step 3: Make the sheet**

Run (batch 02): `../../.venv/bin/python -m tools.review sheet --items stimuli/nonmoral.csv --batch 02_nm_moral_01-20 --arms moral --storylines 1-20`
Run (batch 03): `../../.venv/bin/python -m tools.review sheet --items stimuli/nonmoral.csv --batch 03_nm_moral_21-40 --arms moral --storylines 21-40`
Expected: `wrote ... (40 items)`.

- [ ] **Step 4: Add the batch row to NOTES.md** (drafting model ID, date, sheet name).
- [ ] **Step 5: Commit the batch**

```bash
git add studies/knobe_moral_probe/stimuli/nonmoral.csv studies/knobe_moral_probe/stimuli/nonmoral_log.csv studies/knobe_moral_probe/stimuli/NOTES.md studies/knobe_moral_probe/stimuli/review/
git commit -m "[knobe_moral_probe] stimuli: adapted Ngo moral pairs <storylines> (draft, batch <NN>), per AUTHORING_PLAN Task 10"
```

- [ ] **Step 6: STOP.** Tell the researcher which sheet is ready. Checks: A1, A9, A10, A13, R1–R4, B1, B8, plus C1/C2 per storyline. They fill in the decisions file and run `apply`.
- [ ] **Step 7: Handle the decisions.**
  - For `revise` and `rejected` items: fix the text with the Task 8 revise method (status back to `draft`), lint, and re-sheet the fixed items as the next free batch number (for example `04_nm_moral_fix`; later batch numbers shift by one). Commit and STOP again.
  - A `rejected` Ngo moral pair that cannot be fixed within the adaptation rules stays `rejected` and is left out (decision G, by analogy).
  - When the batch's last decisions are in, lint until clean and commit: `git commit -m "[knobe_moral_probe] review <NN>: researcher's decisions applied"`.

---

### Task 11: Batches 04–05, prudential pairs (2 × 40 items)

**Files:**
- Modify: `studies/knobe_moral_probe/stimuli/nonmoral.csv`, `stimuli/nonmoral_log.csv`, `stimuli/NOTES.md`
- Create: `stimuli/review/04_nm_prudential_01-20.md` and `_decisions.csv`; `05_nm_prudential_21-40.md` and `_decisions.csv`

| batch | storylines | items |
|---|---|---|
| `04_nm_prudential_01-20` | 1–20 | 40 |
| `05_nm_prudential_21-40` | 21–40 | 40 |

Rules: DEFINITIONS §2 (rules 1–7), §3.1 template, §4.2 (definition, every "Out" case), §5, decisions E, F, J, Q.
- Columns: `experiment=nonmoral`, `arm=prudential`, the storyline's role noun, `source` per decision Q, `scaffold` empty.
- Clause 1 reuses the adapted moral pair's bad-version first sentence word for word where it reads naturally (decision E, C3). Otherwise write a fresh action and goal in the same register, with the same role noun, and add a `fresh_action` row with the reason. The pilot used fresh domains for storylines 7, 34 and 37.
- Clause 2 is exactly "The [role] did not care at all about the effect this would have on [X]." with a neutral X (A3).
- Clause 3 is "The [role] knew ... would [side effect]." Only the side effect differs between bad and good (B2–B7).
- Starting drafts: `analysis/ngo_extensions/nonmoral_pilot/prudential_variants.py`, `PRUDENTIAL_PAIRS[N]`. Every pilot variant uses names and pronouns, and many use different actions in bad and good, so take the side-effect idea and rewrite it to these rules. Write from scratch (`source=new`) for the pilot failures 2, 5, 8, 27, 29, 30, 31 (decision R), with the failure reasons in DEFINITIONS §4.2 ("Out" cases) in mind.

Run Steps 1–7 once per row of the table, in order:

- [ ] **Step 1: Draft the batch's pairs** with the Task 8 method, and add `fresh_action` rows where clause 1 is not reused.
- [ ] **Step 2: Lint until clean**

Run: `cd studies/knobe_moral_probe && ../../.venv/bin/python -m tools.lint_stimuli stimuli/nonmoral.csv`
Expected: exit 0.

- [ ] **Step 3: Make the sheet**

Run (batch 04): `../../.venv/bin/python -m tools.review sheet --items stimuli/nonmoral.csv --batch 04_nm_prudential_01-20 --arms prudential --storylines 1-20`
Run (batch 05): `../../.venv/bin/python -m tools.review sheet --items stimuli/nonmoral.csv --batch 05_nm_prudential_21-40 --arms prudential --storylines 21-40`
Expected: `wrote ... (40 items)`.

- [ ] **Step 4: Add the batch row to NOTES.md.**
- [ ] **Step 5: Commit the batch**

```bash
git add studies/knobe_moral_probe/stimuli/nonmoral.csv studies/knobe_moral_probe/stimuli/nonmoral_log.csv studies/knobe_moral_probe/stimuli/NOTES.md studies/knobe_moral_probe/stimuli/review/
git commit -m "[knobe_moral_probe] stimuli: prudential pairs <storylines> (draft, batch <NN>), per AUTHORING_PLAN Task 11"
```

- [ ] **Step 6: STOP** for review. Checks: A1–A13, R1–R4, B1–B7, plus C1–C3 per storyline.
- [ ] **Step 7: Handle the decisions** as in Task 10 Step 7. Revised items are re-sheeted under the next free batch number. Commit the applied decisions.

---

### Task 12: Batches 06–07, procedural pairs (2 × 40 items)

**Files:**
- Modify: `studies/knobe_moral_probe/stimuli/nonmoral.csv`, `stimuli/nonmoral_log.csv`, `stimuli/NOTES.md`
- Create: `stimuli/review/06_nm_procedural_01-20.md` and `_decisions.csv`; `07_nm_procedural_21-40.md` and `_decisions.csv`

| batch | storylines | items |
|---|---|---|
| `06_nm_procedural_01-20` | 1–20 | 40 |
| `07_nm_procedural_21-40` | 21–40 | 40 |

Rules: DEFINITIONS §2, §3.1, §4.3 (definition, every "Out" case: no shared-resource conventions, no "tradition" or "the manager's rule", no trouble for the agent), §5 (mistake 1: the good version must actively fit the convention), decisions E, F, Q.
- Columns: `experiment=nonmoral`, `arm=procedural`, the storyline's role noun, `source` per decision Q.
- Clause 1 is reused or logged as `fresh_action`, as in Task 11.
- Starting drafts: `nonmoral_pilot/procedural_variants.py`, `PROCEDURAL_PAIRS[N]`, rewritten to the rules. Write from scratch for pilot failures 23, 27, 37.
- Decision F: write to the definition, not to the valence threshold. Do not add welfare stakes to make a procedural item read as good or bad.

Run Steps 1–7 once per row of the table, in order:

- [ ] **Step 1: Draft the batch's pairs** with the Task 8 method; add `fresh_action` rows as needed.
- [ ] **Step 2: Lint until clean**

Run: `cd studies/knobe_moral_probe && ../../.venv/bin/python -m tools.lint_stimuli stimuli/nonmoral.csv`
Expected: exit 0.

- [ ] **Step 3: Make the sheet**

Run (batch 06): `../../.venv/bin/python -m tools.review sheet --items stimuli/nonmoral.csv --batch 06_nm_procedural_01-20 --arms procedural --storylines 1-20`
Run (batch 07): `../../.venv/bin/python -m tools.review sheet --items stimuli/nonmoral.csv --batch 07_nm_procedural_21-40 --arms procedural --storylines 21-40`
Expected: `wrote ... (40 items)`.

- [ ] **Step 4: Add the batch row to NOTES.md.**
- [ ] **Step 5: Commit the batch**

```bash
git add studies/knobe_moral_probe/stimuli/nonmoral.csv studies/knobe_moral_probe/stimuli/nonmoral_log.csv studies/knobe_moral_probe/stimuli/NOTES.md studies/knobe_moral_probe/stimuli/review/
git commit -m "[knobe_moral_probe] stimuli: procedural pairs <storylines> (draft, batch <NN>), per AUTHORING_PLAN Task 12"
```

- [ ] **Step 6: STOP** for review. Checks: A1–A13, R1–R4, B1–B7, plus C1–C3 per storyline.
- [ ] **Step 7: Handle the decisions** as in Task 10 Step 7. Commit the applied decisions.

---

### Task 13: Nonmoral completeness

- [ ] **Step 1: Check counts and the file**

Run: `cd studies/knobe_moral_probe && ../../.venv/bin/python -m tools.lint_stimuli stimuli/nonmoral.csv --expect-complete`
Expected: exit 0, with `moral: 40 ...`, `procedural: 40 ...`, `prudential: 40 ...` pairs, and no `draft` count. Every pair is approved or rejected.

Rejected moral pairs are dropped (decision G). A missing or rejected prudential or procedural pair goes back through Task 11 or 12 under a new batch number until each storyline has one, or the researcher accepts the gap (record it in NOTES.md).

- [ ] **Step 2: Commit** any NOTES.md update: `git commit -m "[knobe_moral_probe] stimuli: nonmoral complete (240 items)"`.

---

### Task 14: Foundations scaffold roster (gate)

**Files:**
- Modify: `studies/knobe_moral_probe/stimuli/NOTES.md` ("Foundations scaffold roster")

Targets (DESIGN §3.3, DEFINITIONS D2):
- 20 passing pairs per foundation, floor 15, drafted with about 30% extra, so about 26 per foundation.
- 30–40 harm pairs on shared scaffolds.

Plan: 36 shared scaffolds (storylines 1–36, decision U), each with one harm pair and 2–3 foundation pairs. That gives 26 fairness, 26 loyalty and 26 authority pairs, plus about 6 purity pairs where a scaffold fits purity naturally. Add 20 purpose-written purity storylines (101–120, `scaffold=purpose`, no harm pair). Total: 36 harm + 84 foundation + 20 purity = 140 pairs = 280 items.

- [ ] **Step 1: Write the roster table** in NOTES.md, one row per storyline:

```markdown
| storyline | scaffold | role noun | action-and-goal sentence (verbatim) | pairs planned | origin (decision H) | batch |
|---|---|---|---|---|---|---|
```

  Rules:
  - C5: the action and goal must be harm-neutral. Do not use Ngo storylines whose main action harms (bombing, the shelter cut, the smacking, the bomb threat, the jail bombing, prescribing for a vendor); prefer new scaffolds (decision H).
  - C6: no near-duplicate foundation pairs on one scaffold.
  - D3: role nouns are unique within the file. They may repeat role nouns used in `nonmoral.csv`, which D3 does not check across files, but prefer not to.
  - A per-foundation count line under the table must show ≥ 26 for each of fairness, loyalty, authority and purity, and 30–40 for harm.
  - Ideas may come from `moral_foundations_pilot/*_variants.py`. They use Ngo names, pronouns and, often, different actions in bad and good, so their text can't be kept. Use `source=pilot` only where a pilot item really is the starting draft (decision Q).
- [ ] **Step 2: Commit**: `git commit -m "[knobe_moral_probe] stimuli: foundations scaffold roster (for review)"`.
- [ ] **Step 3: STOP.** The researcher reviews the roster (C4–C7, decision H, allocation). Apply their changes, commit, and continue only on their word.

---

### Task 15: Batches 08–14, foundations items

**Files:**
- Create/modify: `studies/knobe_moral_probe/stimuli/foundations.csv`, `stimuli/NOTES.md`
- Create: `stimuli/review/<batch>.md` and `_decisions.csv` for each batch below

| batch | storylines | content | items (about) |
|---|---|---|---|
| `08_mf_shared_01-06` | 1–6 | harm pair + 2–3 foundation pairs each | 40 |
| `09_mf_shared_07-12` | 7–12 | same | 40 |
| `10_mf_shared_13-18` | 13–18 | same | 40 |
| `11_mf_shared_19-24` | 19–24 | same | 40 |
| `12_mf_shared_25-30` | 25–30 | same | 40 |
| `13_mf_shared_31-36` | 31–36 | same | 40 |
| `14_mf_purity_101-120` | 101–120 | one purity pair each, `scaffold=purpose` | 40 |

Batches go by scaffold, not by foundation. `design_problems(stage="authoring")` refuses any shared storyline that lacks its harm pair or all its non-harm pairs, so a file holding a harm-only batch would not pass.

Rules:
- DEFINITIONS §2, §3.2 (4-clause template), §3.3 (scaffolds), §4.4–§4.8 (each foundation's definition and "Out" cases), §5, decisions A, D (the harm background is a neutral fact that sets up who could be hurt or helped, never a moral rule), F, H, I, Q.
- Columns: `experiment=foundations`, `arm` from the roster, `scaffold` = `shared` or `purpose`, the roster's role noun, `source` per decision Q.
- Sentence 1 is the background, identical in bad and good.
- Sentence 2 is the roster's action-and-goal sentence, word for word, in every arm (C4; the lint checks it).
- Sentence 3 is the A3 indifference clause with that arm's X.
- Sentence 4 is the side effect.

Illustrative row, copied from DEFINITIONS §4.5 (scaffold S, fairness). It is not an item to keep:

```
experiment=foundations, storyline_id=<S>, arm=fairness, sign=bad, agent=the coordinator, scaffold=shared,
effect=give some members twice as much space as others,
scenario=The members had agreed that plots would be shared out equally. The coordinator rearranged the community garden's plots to shorten the watering route. The coordinator did not care at all about the effect this would have on the members' agreement. The coordinator knew the new layout would give some members twice as much space as others.
```

Run Steps 1–7 once per row of the table, in order:

- [ ] **Step 1: Draft the batch** with the Task 8 method (`PATH = Path("stimuli/foundations.csv")`, `scaffold` given in each dict).
- [ ] **Step 2: Lint until clean**

Run: `cd studies/knobe_moral_probe && ../../.venv/bin/python -m tools.lint_stimuli stimuli/foundations.csv`
Expected: exit 0.

- [ ] **Step 3: Make the sheet**, e.g. for batch 08:

Run: `../../.venv/bin/python -m tools.review sheet --items stimuli/foundations.csv --batch 08_mf_shared_01-06 --storylines 1-6`
(batch 14: `--batch 14_mf_purity_101-120 --storylines 101-120`)
Expected: `wrote ... (~40 items)`.

- [ ] **Step 4: Add the batch row to NOTES.md.**
- [ ] **Step 5: Commit the batch**

```bash
git add studies/knobe_moral_probe/stimuli/foundations.csv studies/knobe_moral_probe/stimuli/NOTES.md studies/knobe_moral_probe/stimuli/review/
git commit -m "[knobe_moral_probe] stimuli: foundations storylines <range> (draft, batch <NN>), per AUTHORING_PLAN Task 15"
```

- [ ] **Step 6: STOP** for review. Checks: A1–A13, R1–R4, B1–B7; shared storylines C2, C4–C6; purpose storylines C2, C7.
- [ ] **Step 7: Handle the decisions** as in Task 10 Step 7. A shared scaffold whose harm pair is rejected and can't be fixed stays in the file. Its rejected harm items keep `design_problems` satisfied, and screening's `shared_without_harm` reports it (decision A). Commit the applied decisions.

- [ ] **Step 8 (after batch 14): Counts**

Run: `../../.venv/bin/python -m tools.lint_stimuli stimuli/foundations.csv`
Expected: exit 0, no `draft` counts, and approved pairs per arm ≥ 26 for fairness, loyalty, authority and purity, and 30–40 for harm. Any shortfall gets a top-up batch (next free number), drafted, linted, sheeted and reviewed the same way.

---

### Task 16: Screening dry run and cost estimate (gate, CLAUDE.md §4)

`kmp.screen` screens only `approved` items, and its dry run counts only those. So the estimate is only meaningful now, after review.

- [ ] **Step 1: All three files clean, no drafts left**

Run (from the study folder):
```bash
for e in ngo_verbatim nonmoral foundations; do ../../.venv/bin/python -m tools.lint_stimuli stimuli/$e.csv || echo "FAIL $e"; done
```
Expected: three `clean` lines and no `draft` counts.

- [ ] **Step 2: Dry runs**

```bash
for e in ngo_verbatim nonmoral foundations; do ../../.venv/bin/python -m kmp.screen --items stimuli/$e.csv --out-dir outputs/screening/$e --dry-run; done
```

  Expected for ngo_verbatim if all 80 are approved: `320 screening prompts; worst case 640 calls`, `~45000 input tokens + <= 2560 output tokens per pass`. Nonmoral: about 960 prompts. Foundations: about 6 × the approved item count. In total about 3,000 prompts, roughly 0.4M input tokens.
- [ ] **Step 3: STOP.** Report the three dry-run outputs to the researcher. Include a dollar estimate at `claude-sonnet-4-6`'s current price per million input and output tokens, checked against DESIGN.md's figure (worst case about 6,200 calls, about $3.50), and the expected wall-clock time at `--concurrency 8`. Ask for go-ahead.

---

### Task 17: Install `anthropic` and confirm the pin

**Files:**
- Modify: `studies/knobe_moral_probe/stimuli/NOTES.md` (SDK version line)
- Modify, only under option (a) below: `pyproject.toml` (repo root, `[project.optional-dependencies]`)

The reviewer is already pinned: `kmp/protocol.py` has `REVIEWER_MODEL: str | None = "claude-sonnet-4-6"` (commit 534738d). That is an exact model ID, and `pin_problems` refuses `-latest` aliases. Nothing is edited here. The `anthropic` SDK is not installed, and nothing declares it. The `.venv` is managed by uv and has no `pip`.

**Choice for the researcher: option (a), chosen 2026-10-01.**
- **(a) Declare it. CHOSEN by the researcher (2026-10-01).** Add a `screen = ["anthropic"]` extra under `[project.optional-dependencies]` in the repo's `pyproject.toml`, then run `uv pip install --python .venv/bin/python -e ".[screen]"`. Anyone rebuilding the venv can see the dependency. The cost is a repo-wide file change outside the study folder.
- **(b) Install only.** Run `uv pip install --python .venv/bin/python anthropic` and record the version in NOTES.md and in the screening log lines. The study folder is untouched, but the dependency lives only in the docs.

  *Recommendation (adopted):* (a), pinned to the installed major version (e.g. `anthropic>=X,<X+1`), because screening is a committed, reproducible step. Use (b) if the researcher wants no changes outside `studies/knobe_moral_probe/`.

- [ ] **Step 1: Confirm the pin**

Run: `cd studies/knobe_moral_probe && ../../.venv/bin/python -c "from kmp import protocol, screen_run; print(protocol.REVIEWER_MODEL, screen_run.pin_problems(protocol.REVIEWER_MODEL))"`
Expected: `claude-sonnet-4-6 []`

- [ ] **Step 2: Install the SDK**, using option (a) or (b) above, from the repo root.
Then run: `.venv/bin/python -c "import anthropic; print(anthropic.__version__)"`, and record the version in NOTES.md.

- [ ] **Step 3: Run the suite**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests -q`
Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add studies/knobe_moral_probe/stimuli/NOTES.md   # plus pyproject.toml under option (a)
git commit -m "[knobe_moral_probe] screening: anthropic SDK installed (<version>); reviewer pin confirmed"
```

---

### Task 18: First real screening run, ngo_verbatim (the cheap first pass)

This is the smallest set, so it is the first real run. It also checks on real calls what plan amendment 2 left open: whether the pinned model, `claude-sonnet-4-6`, accepts `temperature=0` with thinking disabled. DESIGN.md's reviewer-pin amendment expects it to, unlike the current generation.

- [ ] **Step 1: Run** (needs `ANTHROPIC_API_KEY` in the environment)

Run: `cd studies/knobe_moral_probe && ../../.venv/bin/python -m kmp.screen --items stimuli/ngo_verbatim.csv --out-dir outputs/screening/ngo_verbatim --reviewer-model claude-sonnet-4-6`
Expected: a per-arm `pairs  pairs_passed` table. If the API rejects `temperature` or `thinking`, the run aborts before writing any rows. STOP and report; do not change `ScreeningClient` without the researcher.
- [ ] **Step 2: Check the meta.** `outputs/screening/ngo_verbatim/screening_meta.json` must show `git_dirty: false`, `served_models` equal to the pin, and `reviewer_temperature: 0.0`. If `git_dirty` is true, commit or stash first and re-run; the re-run resumes for free.
- [ ] **Step 3: Commit the outputs**

```bash
git add studies/knobe_moral_probe/outputs/screening/ngo_verbatim/
git commit -m "[knobe_moral_probe] screening: ngo_verbatim with the pinned reviewer"
```

- [ ] **Step 4: Log it** in `ANALYSIS_LOG.md`, with the hash of the Step 3 commit:

```
2026-MM-DD | `python -m kmp.screen --items stimuli/ngo_verbatim.csv --out-dir outputs/screening/ngo_verbatim --reviewer-model claude-sonnet-4-6` | reviewer claude-sonnet-4-6, T=0, valence bad<=3/good>=7, target>=6; <n> prompts, <calls> calls, <in>/<out> tokens | <k>/40 pairs pass; unparsed: <list or none> | <hash>
```

  Commit: `git commit -m "[knobe_moral_probe] log the ngo_verbatim screening run"`.
- [ ] **Step 5: STOP.** Show the researcher the pass counts and `selection_report.csv` failures. Continue to the other experiments only on their go-ahead.

---

### Task 19: Screening nonmoral and foundations

- [ ] **Step 1: Run nonmoral**

Run: `../../.venv/bin/python -m kmp.screen --items stimuli/nonmoral.csv --out-dir outputs/screening/nonmoral --reviewer-model claude-sonnet-4-6`

- [ ] **Step 2: Commit the outputs and log**, as in Task 18 Steps 2–4 (outputs commit, then a log line with that hash, then the log commit). Outcome field: passing pairs per arm out of 40.
- [ ] **Step 3: Run foundations**

Run: `../../.venv/bin/python -m kmp.screen --items stimuli/foundations.csv --out-dir outputs/screening/foundations --reviewer-model claude-sonnet-4-6`
The command prints `shared storylines without a surviving harm pair` / `non-harm pair` to stderr when any exist. Copy them into the log line.

- [ ] **Step 4: Commit the outputs and log**, as in Task 18 Steps 2–4. Outcome field: passing pairs per foundation, with the `shared_without_harm` / `shared_without_nonharm` lists.

---

### Task 20: Selection review and threshold revisits (gate; decisions F, G, I)

- [ ] **Step 1: Summarise for the researcher**, per experiment:
  - passing pairs per arm against the targets (nonmoral 40 per arm; foundations ≥ 20, floor 15);
  - failure reasons from `selection_report.csv`;
  - the distribution of valence scores per arm. Count bad versions in 4–5 and good versions in 5–6 (near misses), especially for procedural, fairness and purity (decision F);
  - foundation profiles for cross-foundation bleed (decision I, descriptive only);
  - unparsed answers by name.

  Write this as a summary table in `outputs/screening/SELECTION_REVIEW.md`. It is small, so commit it.
- [ ] **Step 2: STOP.** The researcher decides:
  - Threshold revisit (decision F), only against these real distributions. If thresholds change: amend DESIGN.md (a dated amendment at the top, giving old value, new value and the evidence), change `kmp/screen.py`'s `VALENCE_BAD_MAX` / `VALENCE_GOOD_MIN` / `TARGET_MIN` with a test, and commit. Then re-run the same `kmp.screen` command per experiment. Raw answers are reused, because the prompts are unchanged, so no calls are made and only selection is redone. Commit the outputs and add one log line per re-run.
  - Which failing non-Ngo pairs to rewrite. Ngo moral pairs are never rewritten (decision G).
- [ ] **Step 3: Commit the summary**: `git add studies/knobe_moral_probe/outputs/screening/SELECTION_REVIEW.md && git commit -m "[knobe_moral_probe] screening: selection review for the researcher"`.

---

### Task 21: Revisit round (only if Task 20 asks for rewrites)

A rewritten item's prompt text changes. `kmp.screen_run` then refuses to resume in the same `--out-dir` (`text_sha256 changed`), so every revisit round screens into a fresh directory, and the final round's `selected_items.csv` is the one elicitation uses.

- [ ] **Step 1: Rewrite** the failing pairs the researcher chose, with the Task 8 revise method (status back to `draft`). Lint, sheet as the next free batch number (`NN_<exp>_revisit_r2`), commit, and **STOP** for review, exactly as in Tasks 10–15.
- [ ] **Step 2: Dry run into the new directory** and report the call count (CLAUDE.md §4):

Run: `../../.venv/bin/python -m kmp.screen --items stimuli/<experiment>.csv --out-dir outputs/screening/<experiment>/round_2 --dry-run`

- [ ] **Step 3: Run, commit, log**, as in Task 18 Steps 1–4, with `--out-dir outputs/screening/<experiment>/round_2`.
- [ ] **Step 4: STOP.** Report against targets. A third round needs the researcher's explicit go-ahead. Below the foundation floor of 15 after the agreed rounds, the researcher decides whether to proceed with fewer, as §3.3 allows.

---

### Task 22: Close out

- [ ] **Step 1: Fill in NOTES.md**: the batch table complete, the screening reviewer ID, the `anthropic` version, and the final `--out-dir` per experiment.
- [ ] **Step 2: Full suite and lints**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests -q` (all pass), then the Task 16 Step 1 loop (three `clean`).

- [ ] **Step 3: Commit**: `git commit -m "[knobe_moral_probe] stimuli: notes complete; screening done"`.
- [ ] **Step 4: Session summary (CLAUDE.md §6):** list every file created, modified or deleted, including scratch scripts in the scratchpad, and flag anything uncommitted.

---

## Self-review against the spec

- DESIGN §3.1 rules → lint A1, A3, A4, A9, B2 plus `design_problems` B1 and R2; the rest are review-only checklist items shown on each sheet.
- §3.2 nonmoral (240 items; the pilot rewrites) → Tasks 9–13; the failed-pair list is corrected per the pilot report (decision R).
- §3.3 foundations (shared scaffolds, purpose-written purity, 20/15/+30%) → Tasks 14–15; harm background per decision D; sources per decision H.
- §3.4 (definitions first; Claude drafts; the researcher reviews every item; disclosure) → Task 0, the review gates, `tools.review apply` (researcher only), and the NOTES.md disclosure section.
- §4 screening (reviewer pinned to claude-sonnet-4-6, T=0, pass rule, unparsed reported, thresholds revisited only on real data) → Tasks 16–21, reusing `kmp.screen` unchanged.
- The ngo_verbatim amendment → Tasks 1, 3, 7.
- CLAUDE.md §2 incremental commits, §3 commit small outputs, §4 cost gate, §5 log lines with hashes, §6 session summary, §7 reuse → covered in the conventions and in Tasks 3, 16, 18–22.
