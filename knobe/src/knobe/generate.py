"""``knobe generate`` CLI logic (WO-1; master spec §3.1): next-prompt /
ingest / approve / status / qa.

Generation itself stays human-in-the-loop (DR §14) -- everything here
either emits a prompt for a human (or a supervised LLM session) to run
outside this tool, or validates/merges a CSV a human already has in hand.
**No network calls anywhere** (WO1_generation.md requirement 7).

Code-organization split (per task-3-brief.md): ``tracking.py`` owns pure
set-summary / tracking-log / balance-math functions plus the one matrix
reader; this module owns CLI-facing orchestration, ingest's set-level
checks (kept separate from ``assemble.py``'s row-level structural checks,
which are reused here verbatim, never re-derived), and all matrix writes
(ingest's append, approve's flip) -- the only place in this work order
that touches disk beyond reading.
"""
from __future__ import annotations

import csv
import datetime
import io
import re
from dataclasses import dataclass, field
from pathlib import Path

from knobe import assemble, constants, tracking
from knobe.schemas import FamilyRow


class DomainAtCapError(RuntimeError):
    """Raised by ``next_prompt_text`` when a domain already has 5 sets and
    ``--allow-extra`` wasn't passed (WO1_generation.md requirement 3's
    5-sets-per-domain end-state target)."""


def _repo_root() -> Path:
    """Repo root, derived from this source file's location -- same
    technique as ``assemble._repo_root`` (duplicated locally rather than
    importing that module's private helper, per the precedent its own
    ``_truthy`` docstring already sets: this is an ordinary path helper,
    not a frozen scientific instrument, so a small local copy is fine)."""
    return Path(__file__).resolve().parents[2]


def default_matrix_path() -> Path:
    """``data/authoring/ALL_DOMAINS_master_matrix.csv`` under the repo
    root -- NOT the caller's cwd, so ``knobe generate ...`` without
    ``--matrix`` works regardless of invocation directory."""
    return _repo_root() / "data" / "authoring" / "ALL_DOMAINS_master_matrix.csv"


def _domain_full_name(domain_code: str) -> str:
    domain_full = constants.DOMAIN_CODES.get(domain_code)
    if domain_full is None:
        raise ValueError(
            f"unknown domain code {domain_code!r}; must be one of {sorted(constants.DOMAIN_CODES)}"
        )
    return domain_full


# ---------------------------------------------------------------------------
# next-prompt (WO1_generation.md requirement 1 + balance enforcement in
# requirement 3)
# ---------------------------------------------------------------------------


def next_prompt_text(matrix_path: str | Path, domain_code: str, *, allow_extra: bool = False) -> str:
    """The full per-set prompt (PER_SET_PROMPT_TEMPLATE filled with the
    auto-built tracking log) plus, if the full-matrix nonmoral-subdomain
    balance is off by more than 2x, a hard INSTRUCTION line naming the
    subdomain this set's NMB/NMG families MUST use.

    Raises ``DomainAtCapError`` if ``domain_code`` already has 5 sets and
    ``allow_extra`` is False (the domain end-state target: 5 sets x 5
    valences per domain)."""
    domain_full = _domain_full_name(domain_code)
    rows = tracking.load_matrix_rows(matrix_path)
    domain_rows = [r for r in rows if r["domain"] == domain_full]

    n_sets = tracking.domain_set_count(domain_rows, domain_full)
    if n_sets >= 5 and not allow_extra:
        raise DomainAtCapError(
            f"{domain_full} ({domain_code}) already has {n_sets} set(s) -- target is 5 sets "
            f"x 5 valences per domain. Pass --allow-extra to generate beyond the target."
        )

    summaries = tracking.summarize_sets(domain_rows, domain_full)
    tracking_log = tracking.format_tracking_log(summaries)
    set_number = tracking.next_set_number(domain_rows, domain_full)

    prompt = constants.PER_SET_PROMPT_TEMPLATE.format(
        domain=domain_full, set_number=f"{set_number:02d}", tracking_log=tracking_log,
    )

    tally = tracking.subdomain_tally(rows, approved_only=True)
    target = tracking.rarest_subdomain(tally)
    if target is not None:
        tally_str = ", ".join(f"{s}={tally[s]}" for s in tracking.SUBDOMAIN_ORDER)
        prompt += (
            f"\n\nINSTRUCTION (required, not a suggestion): this set's NMB/NMG families "
            f"MUST use nonmoral_subdomain = {target}. Full-matrix approved subdomain tally: "
            f"{tally_str} (end-state target: within 2x of each other; {target} is currently "
            f"the rarest and must be steered toward until that holds)."
        )
    return prompt


# ---------------------------------------------------------------------------
# ingest (WO1_generation.md requirement 2)
# ---------------------------------------------------------------------------


@dataclass
class IngestResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    appended_family_ids: list[str] = field(default_factory=list)


def _shared_scaffold_errors(rows: list[dict]) -> list[str]:
    """GS §1: "A set is ONE storyline: agent, goal, common_action,
    uncommon_action, shared across 5 FAMILIES." affected_entity is
    deliberately excluded -- the system prompt explicitly allows it to
    differ for NMB/NMG/NEU."""
    errors = []
    for fld in ("agent", "goal", "common_action", "uncommon_action"):
        values = {r.get(fld, "") for r in rows}
        if len(values) != 1:
            errors.append(
                f"'{fld}' must be identical across all 5 rows in a set (shared storyline "
                f"scaffold, GS §1); got {sorted(values)}"
            )
    return errors


def _goal_tokens(goal: str) -> set[str]:
    return set(re.findall(r"[a-z]+", goal.lower())) - constants.STOPWORDS


def _duplicate_storyline_checks(
    new_rows: list[dict], existing_domain_rows: list[dict], domain_full: str
) -> tuple[list[str], list[str]]:
    """Duplicate-storyline heuristics against the existing matrix, within
    the same domain, BEFORE merge (WO1_generation.md requirement 2):
      (a) agent-name reuse within domain -> error-level flag;
      (b) goal similarity: token-set Jaccard (lowercase, minus STOPWORDS)
          against every existing goal in the domain, flag > 0.6 -> warning.
    """
    errors: list[str] = []
    warnings: list[str] = []

    new_agent = new_rows[0].get("agent", "")
    existing_agents = {r["agent"].strip().lower() for r in existing_domain_rows if r.get("agent")}
    if new_agent.strip().lower() in existing_agents:
        errors.append(
            f"agent {new_agent!r} is already used in domain {domain_full!r} -- pick a "
            f"different agent (vary role-title vs. proper name, or the specific name/role) "
            f"for a new set"
        )

    new_goal = new_rows[0].get("goal", "")
    new_tokens = _goal_tokens(new_goal)
    existing_goals = {r["goal"] for r in existing_domain_rows if r.get("goal")}
    for existing_goal in sorted(existing_goals):
        existing_tokens = _goal_tokens(existing_goal)
        union = new_tokens | existing_tokens
        if not union:
            continue
        jaccard = len(new_tokens & existing_tokens) / len(union)
        if jaccard > 0.6:
            warnings.append(
                f"goal {new_goal!r} is {jaccard:.0%} token-similar to existing domain goal "
                f"{existing_goal!r} -- check for storyline duplication before accepting"
            )

    return errors, warnings


def ingest(
    set_csv_path: str | Path,
    matrix_path: str | Path,
    *,
    generator_model: str = "",
    date: str | None = None,
) -> IngestResult:
    """Validates a returned 5-family set CSV, then (only if it passes
    every check) appends it to the authoring matrix with provenance
    columns. Nothing is written on any error."""
    ingest_date = date or datetime.date.today().isoformat()
    errors: list[str] = []
    warnings: list[str] = []

    rows = assemble.load_families(set_csv_path)

    if len(rows) != 5:
        errors.append(f"expected exactly 5 rows (one set), got {len(rows)}")
        return IngestResult(ok=False, errors=errors, warnings=warnings)

    valences = [r.get("valence", "") for r in rows]
    if set(valences) != constants.VALID_VALENCES or len(set(valences)) != 5:
        errors.append(
            f"a set must contain exactly one row per valence {sorted(constants.VALID_VALENCES)}; "
            f"got {valences}"
        )

    domains = {r.get("domain", "") for r in rows}
    if len(domains) != 1:
        errors.append(f"all 5 rows must share the same domain; got {sorted(domains)}")
        return IngestResult(ok=False, errors=errors, warnings=warnings)
    domain_full = next(iter(domains))
    domain_code = tracking.DOMAIN_CODE_BY_NAME.get(domain_full)
    if domain_code is None:
        errors.append(f"unrecognized domain {domain_full!r} (not in constants.DOMAIN_CODES)")
        return IngestResult(ok=False, errors=errors, warnings=warnings)

    # Structural (S2) checks -- reuse assemble.validate_family verbatim, on
    # every row, never re-derived (common-context.md constraint 2 / the
    # task brief's "REUSE these -- never duplicate validation rules").
    for i, row in enumerate(rows, start=2):  # +2: header is row 1
        errs, warns = assemble.validate_family(row, i)
        errors.extend(errs)
        warnings.extend(warns)

    # Set-level checks (kept separate from assemble's row-level checks).
    existing_rows = tracking.load_matrix_rows(matrix_path)
    existing_domain_rows = [r for r in existing_rows if r["domain"] == domain_full]
    expected_set_num = tracking.next_set_number(existing_domain_rows, domain_full)

    set_nums: set[int] = set()
    for r in rows:
        fid = r.get("family_id", "")
        if not fid.startswith(f"{domain_code}-"):
            errors.append(f"family_id {fid!r} does not start with the expected domain code {domain_code!r}-")
            continue
        try:
            set_nums.add(tracking.extract_set_number(fid))
        except ValueError as exc:
            errors.append(str(exc))

    if len(set_nums) == 1:
        (set_num,) = set_nums
        if set_num != expected_set_num:
            errors.append(
                f"set number {set_num:02d} is not the next expected set for {domain_full} "
                f"(expected {expected_set_num:02d}) -- generate/ingest sets in order"
            )
    elif len(set_nums) > 1:
        errors.append(f"all 5 rows must share the same set number in family_id; got {sorted(set_nums)}")

    errors.extend(_shared_scaffold_errors(rows))

    dup_errors, dup_warnings = _duplicate_storyline_checks(rows, existing_domain_rows, domain_full)
    errors.extend(dup_errors)
    warnings.extend(dup_warnings)

    if errors:
        return IngestResult(ok=False, errors=errors, warnings=warnings)

    _append_rows(matrix_path, rows, generator_model=generator_model, ingest_date=ingest_date)
    return IngestResult(
        ok=True, errors=[], warnings=warnings, appended_family_ids=[r["family_id"] for r in rows],
    )


# ---------------------------------------------------------------------------
# Matrix read/write helpers shared by ingest (append) and approve (flip) --
# the only place in this work order that writes to the authoring matrix.
# ---------------------------------------------------------------------------


def _read_raw_matrix(path: str | Path) -> tuple[list[str], list[dict]]:
    """Reads the matrix as raw string-valued rows, preserving exactly
    whatever columns/values are on disk (no bool coercion) -- the
    round-trip-safe counterpart to ``tracking.load_matrix_rows``, used
    only by writers below."""
    path = Path(path)
    if not path.exists():
        return [], []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = [dict(r) for r in reader]
    return fieldnames, rows


def _migrate_provenance(fieldnames: list[str], rows: list[dict]) -> list[dict]:
    """If ``rows`` already carry the 3 WO-1 provenance columns, returns
    them unchanged. Otherwise backfills every row per the documented rule
    (WO1_generation.md requirement 3): the pre-WO-1 matrix's families are
    already human-reviewed, so generator_model="", ingest_date="",
    human_approved="True" (string, matching schemas._csv_serialize_value's
    own bool-to-CSV convention)."""
    if all(c in fieldnames for c in tracking.PROVENANCE_FIELDNAMES):
        return rows
    migrated = []
    for r in rows:
        row = dict(r)
        row["generator_model"] = ""
        row["ingest_date"] = ""
        row["human_approved"] = "True"
        migrated.append(row)
    return migrated


def _write_raw_matrix(path: str | Path, rows: list[dict]) -> None:
    path = Path(path)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=tracking.MATRIX_FIELDNAMES)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in tracking.MATRIX_FIELDNAMES})


def _append_rows(
    matrix_path: str | Path, new_rows: list[dict], *, generator_model: str, ingest_date: str
) -> None:
    fieldnames, existing_rows = _read_raw_matrix(matrix_path)
    existing_rows = _migrate_provenance(fieldnames, existing_rows)

    for r in new_rows:
        row = {k: r.get(k, "") for k in FamilyRow.csv_fieldnames()}
        row["generator_model"] = generator_model or ""
        row["ingest_date"] = ingest_date
        row["human_approved"] = "False"
        existing_rows.append(row)

    _write_raw_matrix(matrix_path, existing_rows)


# ---------------------------------------------------------------------------
# approve (WO1_generation.md requirement 2's "human flips human_approved")
# ---------------------------------------------------------------------------


def approve(
    matrix_path: str | Path,
    *,
    family_ids: list[str] | None = None,
    set_selector: tuple[str, str] | None = None,
) -> tuple[set[str], set[str]]:
    """Flips human_approved=True for the named family_ids and/or a whole
    set (``set_selector = (domain_code, set_num_str)``). Returns (matched,
    missing) family_id sets. Raises ValueError if no targets were given at
    all, if ``set_selector``'s domain code is unrecognized, or if the matrix
    file does not exist (approving into a nonexistent matrix would otherwise
    silently write a header-only CSV)."""
    if not Path(matrix_path).exists():
        raise ValueError(f"matrix file does not exist: {matrix_path}")
    fieldnames, raw_rows = _read_raw_matrix(matrix_path)
    rows = _migrate_provenance(fieldnames, raw_rows)

    targets: set[str] = set(family_ids or [])
    if set_selector:
        domain_code, set_num_str = set_selector
        domain_full = _domain_full_name(domain_code)
        set_num = int(set_num_str)
        for r in rows:
            if r.get("domain") == domain_full and tracking.extract_set_number(r["family_id"]) == set_num:
                targets.add(r["family_id"])

    if not targets:
        raise ValueError("no family_ids to approve -- pass FAMILY_ID... and/or --set DOMAIN NN")

    matched: set[str] = set()
    for r in rows:
        if r.get("family_id") in targets:
            r["human_approved"] = "True"
            matched.add(r["family_id"])

    _write_raw_matrix(matrix_path, rows)
    return matched, targets - matched


# ---------------------------------------------------------------------------
# status (WO1_generation.md requirement 4)
# ---------------------------------------------------------------------------


def status(matrix_path: str | Path) -> dict:
    rows = tracking.load_matrix_rows(matrix_path)
    pending_rows = [r for r in rows if not r["human_approved"]]
    domains = sorted({r["domain"] for r in rows})

    return {
        "total_families": len(rows),
        "grid": tracking.domain_valence_grid(rows),
        "subdomain_tally_approved": tracking.subdomain_tally(rows, approved_only=True),
        "subdomain_tally_pending": tracking.subdomain_tally(pending_rows),
        "approval_backlog": tracking.approval_backlog(rows),
        "agent_diversity": tracking.agent_diversity(rows),
        "domain_set_counts": {
            d: tracking.domain_set_count([r for r in rows if r["domain"] == d], d) for d in domains
        },
    }


_VALENCE_ORDER = ("MB", "MG", "NMB", "NMG", "NEU")


def format_status(s: dict) -> str:
    lines = ["=== knobe generate status ===", ""]

    lines.append(f"Total families: {s['total_families']}")
    lines.append("")
    lines.append("Families per domain x valence (sets completed / 5 target):")
    header = "  {:<16}".format("Domain") + "".join(f"{v:>6}" for v in _VALENCE_ORDER) + "   Sets"
    lines.append(header)
    for domain in sorted(s["grid"]):
        row = s["grid"][domain]
        sets = s["domain_set_counts"].get(domain, 0)
        line = "  {:<16}".format(domain) + "".join(f"{row.get(v, 0):>6}" for v in _VALENCE_ORDER)
        line += f"   {sets}/5"
        lines.append(line)

    lines.append("")
    lines.append("Nonmoral subdomain tally (APPROVED families only -- counts toward targets):")
    for sd in tracking.SUBDOMAIN_ORDER:
        lines.append(f"  {sd}: {s['subdomain_tally_approved'][sd]}")
    target = tracking.rarest_subdomain(s["subdomain_tally_approved"])
    if target:
        lines.append(f"  -> imbalanced (>2x): steer new NMB/NMG sets toward {target}")

    lines.append("")
    lines.append("Nonmoral subdomain tally (PENDING / not yet approved):")
    for sd in tracking.SUBDOMAIN_ORDER:
        lines.append(f"  {sd}: {s['subdomain_tally_pending'][sd]}")

    lines.append("")
    backlog = s["approval_backlog"]
    lines.append(f"Approval backlog (human_approved == False): {len(backlog)} families")
    if backlog:
        lines.append(f"  {backlog}")

    lines.append("")
    diversity = s["agent_diversity"]
    lines.append(
        f"Agent-name diversity: {diversity['role_title_count']} role-title set(s), "
        f"{diversity['proper_name_count']} proper-name set(s)"
    )
    if diversity["repeated_agents_by_domain"]:
        lines.append("  Repeated agents within a domain (same agent used in >1 set):")
        for domain in sorted(diversity["repeated_agents_by_domain"]):
            for agent, n in diversity["repeated_agents_by_domain"][domain].items():
                lines.append(f'    {domain}: "{agent}" used in {n} sets')
    else:
        lines.append("  (no agent reused within a domain across sets)")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# qa (WO1_generation.md requirement 5)
# ---------------------------------------------------------------------------


def qa_prompt(matrix_path: str | Path, domain_code: str) -> str:
    domain_full = _domain_full_name(domain_code)
    rows = tracking.load_matrix_rows(matrix_path)
    domain_rows = [r for r in rows if r["domain"] == domain_full]
    n_sets = tracking.domain_set_count(domain_rows, domain_full)

    buf = io.StringIO()
    fieldnames = FamilyRow.csv_fieldnames()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in domain_rows:
        writer.writerow({k: r.get(k, "") for k in fieldnames})
    matrix_csv = buf.getvalue()

    return constants.BATCH_QA_PROMPT_TEMPLATE.format(
        domain=domain_full, n_sets=n_sets, n_families=len(domain_rows), matrix_csv=matrix_csv,
    )
