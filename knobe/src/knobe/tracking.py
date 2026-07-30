"""S1 generation tracking: set summaries, tracking-log text, and balance
math for the ``knobe generate`` CLI (WO-1; master spec §3.1, §7).

Port of ``repotentialexperiments/update_tracking_log.py``'s set-grouping
and subdomain-tally logic, generalized to work against the single combined
``ALL_DOMAINS_master_matrix.csv`` this project uses (the legacy script
assumed one CSV per domain).

Every function below is pure given already-loaded family-row dicts, except
``load_matrix_rows`` -- the one blessed way to read a master matrix CSV for
generation-tooling purposes (status/tracking/balance). Nothing here writes
to disk; ``generate.py`` owns all matrix mutation (ingest/approve) and
CLI-facing formatting, per the task brief's code-organization split.
"""
from __future__ import annotations

import csv
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from knobe import constants
from knobe.schemas import FamilyRow

# WO-1 provenance columns, added to master_matrix.csv on first `knobe
# generate ingest` (see generate.py's migration helpers). Order matters:
# this is the exact trailing column order ingest/approve write.
PROVENANCE_FIELDNAMES = ["generator_model", "ingest_date", "human_approved"]

# The full on-disk column order once a matrix has been migrated: the 12
# canonical assembly columns (FamilyRow.csv_fieldnames(), same order as
# master spec §3.1) followed by the 3 provenance columns above.
MATRIX_FIELDNAMES = FamilyRow.csv_fieldnames() + PROVENANCE_FIELDNAMES

# Canonical, deterministic iteration order for the four nonmoral
# subdomains. constants.VALID_SUBDOMAINS is a set (no defined order), but
# tally output and rarest-subdomain tie-breaking need a stable order.
SUBDOMAIN_ORDER = ("prudential", "procedural", "aesthetic", "etiquette")
assert set(SUBDOMAIN_ORDER) == constants.VALID_SUBDOMAINS

# Reverse of constants.DOMAIN_CODES ("Environment" -> "ENV"), used to map a
# matrix row's full-name `domain` column back to its family_id code prefix.
DOMAIN_CODE_BY_NAME = {full: code for code, full in constants.DOMAIN_CODES.items()}

# family_id's trailing set number, ignoring any -rN revision suffix (the
# WO-3 revision mechanism documented in constants.FAMILY_ID_RE).
_SET_NUM_RE = re.compile(r"-(\d{2})(?:r\d+)?$")


def _truthy(v) -> bool:
    """Same semantics as schemas._coerce_bool (true/1/yes, case-insensitive
    -> True; everything else -> False), duplicated locally as a tiny helper
    per the precedent already set in assemble.py's own ``_truthy`` (ordinary
    truthy-string parsing, not a frozen scientific instrument)."""
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("true", "1", "yes")


def extract_set_number(family_id: str) -> int:
    """The trailing NN of family_id, ignoring any -rN revision suffix
    (e.g. "ENV-MB-01" -> 1; "ENV-MB-01r2" -> 1, same set, a later
    revision)."""
    m = _SET_NUM_RE.search(family_id or "")
    if not m:
        raise ValueError(f"family_id {family_id!r} has no recognizable trailing set number (-NN[rM])")
    return int(m.group(1))


def load_matrix_rows(path: str | Path) -> list[dict]:
    """Reads master_matrix.csv, one dict per row, with WO-1 provenance
    fields normalized:

    - If the CSV already has generator_model/ingest_date/human_approved
      columns, they're read as-is (human_approved coerced to bool via
      ``_truthy``).
    - If it doesn't (the pre-WO-1 105-family matrix, which predates these
      columns), every row is treated as generator_model="", ingest_date="",
      human_approved=True -- the backfill rule from WO1_generation.md
      requirement 3: the existing 105 families are already human-reviewed.

    This in-memory backfill default is deliberately the OPPOSITE of
    ``assemble.py``'s ``_check_family_approval``, which defaults a missing
    column to *unapproved* for release-gating safety. That's not a
    conflict: the two call sites serve different purposes (WO-1
    generation-tooling bookkeeping, where "no column yet" means "this is
    the already-reviewed legacy matrix", vs. WO-2's release gate, where
    "no column at all" must fail closed rather than silently ship an
    unreviewed matrix). Documented here per common-context.md's "flag
    conflicts, don't resolve silently" -- this is an intentional, narrow
    divergence between two modules' defaults, not an unresolved one.

    A missing file returns [] (an empty/nonexistent matrix means "this is
    set 01, nothing tracked yet" -- callers report that themselves,
    mirroring the legacy script's FileNotFoundError message).
    """
    path = Path(path)
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        has_provenance = all(c in fieldnames for c in PROVENANCE_FIELDNAMES)
        rows = []
        for raw in reader:
            row = dict(raw)
            if has_provenance:
                row["human_approved"] = _truthy(row.get("human_approved"))
                row["generator_model"] = row.get("generator_model") or ""
                row["ingest_date"] = row.get("ingest_date") or ""
            else:
                row["generator_model"] = ""
                row["ingest_date"] = ""
                row["human_approved"] = True
            rows.append(row)
    return rows


@dataclass(frozen=True)
class SetSummary:
    set_num: int
    agent: str
    goal: str
    subdomain: str


def summarize_sets(families: list[dict], domain: str) -> list[SetSummary]:
    """Groups ``domain``'s family rows by set number (trailing NN of
    family_id, ignoring any -rN suffix), sorted ascending. Port of
    ``update_tracking_log.py``'s ``load_sets``, generalized to filter by
    domain first (the legacy script assumed one domain per file)."""
    by_set: dict[int, list[dict]] = {}
    for r in families:
        if r.get("domain") != domain:
            continue
        set_num = extract_set_number(r["family_id"])
        by_set.setdefault(set_num, []).append(r)

    summaries = []
    for set_num in sorted(by_set):
        rows = by_set[set_num]
        agent = rows[0]["agent"]
        goal = rows[0]["goal"]
        subdomain = next((r["nonmoral_subdomain"] for r in rows if r.get("nonmoral_subdomain")), "")
        summaries.append(SetSummary(set_num=set_num, agent=agent, goal=goal, subdomain=subdomain))
    return summaries


def next_set_number(families: list[dict], domain: str) -> int:
    """The next unused set number for ``domain`` -- one past the highest
    set number currently present (approved or pending; a pending set
    already occupies that set-number slot and must not be overwritten)."""
    summaries = summarize_sets(families, domain)
    if not summaries:
        return 1
    return max(s.set_num for s in summaries) + 1


def domain_set_count(families: list[dict], domain: str) -> int:
    """Number of distinct sets present for ``domain`` (approved or
    pending) -- used for the "5 sets per domain" end-state cap."""
    return len(summarize_sets(families, domain))


def format_tracking_log(summaries: list[SetSummary]) -> str:
    """The exact "already used" block text that slots into
    ``PER_SET_PROMPT_TEMPLATE``'s ``{tracking_log}`` field (GS §8.2/§10.3).
    Port of ``update_tracking_log.py``'s per-set print loop, minus its
    "Already used in this domain (...)" header line -- that wording is
    already supplied by ``PER_SET_PROMPT_TEMPLATE`` itself, so repeating it
    here would double it up in the assembled prompt."""
    if not summaries:
        return "(none yet)"
    lines = []
    for s in summaries:
        subdomain_note = f" [subdomain: {s.subdomain}]" if s.subdomain else ""
        lines.append(f'  - Set {s.set_num:02d}: agent = "{s.agent}"; goal = "{s.goal}"{subdomain_note}')
    return "\n".join(lines)


def subdomain_tally(families: list[dict], *, approved_only: bool = False) -> dict[str, int]:
    """Nonmoral-subdomain counts over ``families`` (caller decides whether
    that's the full matrix or an already domain-filtered subset). Always
    returns all four canonical subdomains (0 if unused), not a sparse
    Counter, so "not yet used at all" is reportable rather than merely
    absent (WO1_generation.md's acceptance criterion pins etiquette=0 on
    the real matrix -- that must be a visible 0, not a missing key).

    ``approved_only=True`` implements WO1_generation.md requirement 3:
    "only approved rows count toward balance/status targets" -- used by
    ``generate.next_prompt_text``'s balance enforcement and by
    ``generate.status``'s target-facing tally."""
    rows = families
    if approved_only:
        rows = [r for r in rows if r.get("human_approved")]
    counts = Counter(r["nonmoral_subdomain"] for r in rows if r.get("nonmoral_subdomain"))
    return {s: counts.get(s, 0) for s in SUBDOMAIN_ORDER}


def rarest_subdomain(tally: dict[str, int]) -> str | None:
    """The subdomain new NMB/NMG generation MUST steer toward, per the
    within-2x full-matrix balance target (WO1_generation.md requirement 3):
    returns the rarest of the four canonical subdomains if the current
    max:min ratio violates 2x (a deficit exists), else None (already
    balanced, or nothing generated in any subdomain yet). Ties broken by
    SUBDOMAIN_ORDER for determinism."""
    counts = {s: tally.get(s, 0) for s in SUBDOMAIN_ORDER}
    max_count = max(counts.values())
    min_count = min(counts.values())
    if max_count == 0:
        return None  # nothing generated yet in any subdomain -- no basis to steer
    if max_count <= 2 * min_count:
        return None  # within 2x already
    return min(SUBDOMAIN_ORDER, key=lambda s: (counts[s], SUBDOMAIN_ORDER.index(s)))


def domain_valence_grid(families: list[dict]) -> dict[str, dict[str, int]]:
    """{domain: {valence: count}} over every row passed in (caller decides
    approved-only vs. all, same convention as ``subdomain_tally``)."""
    grid: dict[str, dict[str, int]] = {}
    for r in families:
        d = grid.setdefault(r.get("domain", "?"), {v: 0 for v in constants.VALID_VALENCES})
        v = r.get("valence")
        if v in d:
            d[v] += 1
    return grid


def approval_backlog(families: list[dict]) -> list[str]:
    """family_ids still awaiting human review (human_approved == False)."""
    return [r["family_id"] for r in families if not r.get("human_approved")]


def agent_diversity(families: list[dict]) -> dict:
    """GS §10.4 agent-naming diversity summary: role-title vs. proper-name
    counts (one count per SET, since agent is shared across a set's 5
    rows -- counting every row would 5x-inflate this), plus, per domain,
    any agent used in more than one set (repetition the tracking log's
    per-set view alone doesn't surface at a glance across a whole
    domain)."""
    role_title = 0
    proper_name = 0
    seen_sets: set[tuple[str, int | None, str]] = set()
    per_domain_agents: dict[str, Counter] = {}

    for r in families:
        agent = r.get("agent", "")
        domain = r.get("domain", "?")
        try:
            set_num = extract_set_number(r.get("family_id", ""))
        except ValueError:
            set_num = None
        key = (domain, set_num, agent)
        if key in seen_sets:
            continue
        seen_sets.add(key)

        if agent.startswith("The "):
            role_title += 1
        elif agent:
            proper_name += 1
        per_domain_agents.setdefault(domain, Counter())[agent] += 1

    repeated_agents_by_domain = {
        domain: {agent: n for agent, n in counter.items() if n > 1}
        for domain, counter in per_domain_agents.items()
    }
    repeated_agents_by_domain = {d: r for d, r in repeated_agents_by_domain.items() if r}

    return {
        "role_title_count": role_title,
        "proper_name_count": proper_name,
        "repeated_agents_by_domain": repeated_agents_by_domain,
    }
