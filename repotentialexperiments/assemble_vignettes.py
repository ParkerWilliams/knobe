"""
General-purpose vignette assembler for the Knobe-effect extension study.

This replaces the old per-domain hardcoded scripts (build_env_set01.py,
generate_morally_bad.py) with ONE tool that reads a hand-authored
"master_matrix"-schema spreadsheet (one row per FAMILY: a single agent /
goal / action-pair / affected-entity / canonical side-effect), validates
it, and mechanically expands each family into its 4 variants
(typicality x evocativeness), per vignette_gameplan.md Sections 5-11.

Architecture (per the authoring/assembly/artifact split):
  SPREADSHEET (authoring layer, human-edited)
      -> this script (assembly layer, deterministic, no LLM calls)
      -> flat CSV / xlsx (pipeline artifact, consumed by elicitation code)

Usage:
    python assemble_vignettes.py input.xlsx output_prefix
    python assemble_vignettes.py input.csv output_prefix

Input schema (master_matrix sheet if xlsx, or the CSV itself), one row
per family:
    family_id, domain, valence, nonmoral_subdomain, agent, goal,
    common_action, uncommon_action, affected_entity,
    low_evocative_outcome, high_evocative_outcome, outcome_verb

valence must be one of: MB, MG, NMB, NMG, NEU
nonmoral_subdomain is REQUIRED for NMB/NMG (one of prudential/procedural/
    aesthetic/etiquette) and should be blank/empty for MB/MG/NEU.

Output: one row per variant (A/B/C/D = common x low, common x high,
uncommon x low, uncommon x high), matching the vignettes-sheet schema
already in ENV_set01.xlsx:
    variant_id, family_id, domain, valence, nonmoral_subdomain, sign,
    typicality, evocativeness, scenario, q_intentionality, q_blame,
    q_praise, q_moral_relevance, q_severity, q_vividness,
    q_typicality_perception
"""

import csv
import os
import re
import sys

try:
    import openpyxl
except ImportError:
    openpyxl = None


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = [
    "family_id", "domain", "valence", "agent", "goal",
    "common_action", "uncommon_action", "affected_entity",
    "low_evocative_outcome", "high_evocative_outcome", "outcome_verb",
]

VALID_VALENCES = {"MB", "MG", "NMB", "NMG", "NEU"}
NONMORAL_VALENCES = {"NMB", "NMG"}
VALID_SUBDOMAINS = {"prudential", "procedural", "aesthetic", "etiquette"}

SIGN_BY_VALENCE = {
    "MB": "bad", "NMB": "bad",
    "MG": "good", "NMG": "good",
    "NEU": "na",
}

# Column-name aliases, so minor header drift across spreadsheet versions
# (e.g. "Family ID" vs "family_id") doesn't silently break ingestion.
ALIASES = {
    "family_id": ["family_id", "family id", "familyid"],
    "domain": ["domain"],
    "valence": ["valence", "category", "outcome category", "outcome_category"],
    "nonmoral_subdomain": ["nonmoral_subdomain", "nonmoral subdomain", "subdomain"],
    "agent": ["agent"],
    "goal": ["goal", "self-interested goal", "self_interested_goal"],
    "common_action": ["common_action", "common action"],
    "uncommon_action": ["uncommon_action", "uncommon action"],
    "affected_entity": ["affected_entity", "affected entity"],
    "low_evocative_outcome": [
        "low_evocative_outcome", "low affect rendering", "low-evocative",
        "lower-evocative", "lower_evocative",
    ],
    "high_evocative_outcome": [
        "high_evocative_outcome", "high affect rendering", "high-evocative",
        "higher-evocative", "higher_evocative",
    ],
    "outcome_verb": ["outcome_verb", "outcome verb"],
}

# Merged banned-language list, per gameplan.md Section 5. Applied to the
# CONSEQUENCE fields only (low/high outcome text, outcome_verb) -- never to
# agent/goal/action fields, and the fixed template's own "knew...did not
# care" clause is exempt by construction (it's inserted by this script,
# not authored per-row).
BANNED_MENTAL_STATE = {
    "intentional", "intentionally", "motive", "believe", "desire", "want",
    "negligent", "reckless", "blame", "praise", "responsible", "fault",
    "cared", "caring", "careless", "uncaring", "indifferent",
}
# NOTE: bare "care" was on this list per vignette_gameplan.md Section 5's
# original banned-language spec, but it's genuinely ambiguous -- "care" as
# a noun (healthcare, patient care, childcare) is unavoidable ordinary
# vocabulary in entire domains (Healthcare being the obvious case), and is
# a completely different word from "care" the mental-state verb the rule
# actually means to exclude ("cared about," "didn't care"). No boundary-
# level regex fix distinguishes them (both sit at identical word
# boundaries) -- the fix is using the inflected forms above, which aren't
# ambiguous the same way. This is a refinement to the frozen protocol
# doc's banned list, not just a code change -- gameplan.md Section 5
# should be updated to match this narrower, more precise version.
BANNED_EPISTEMIC = {
    "accidentally", "deliberately", "unwittingly", "avoidably",
    "preventably", "unforeseeably", "foresaw", "foreseen", "knowingly",
}
BANNED_EVALUATIVE = {
    "wrong", "unethical", "cruel", "ugly", "elegant", "rude", "proper",
    "tacky", "sloppy", "polite", "immoral", "virtuous", "commendable",
    "kind", "evil", "wicked", "vicious", "noble", "heroic", "villainous",
    "classy", "uncouth", "impolite", "stylish", "chic", "gauche",
}
ALL_BANNED = BANNED_MENTAL_STATE | BANNED_EPISTEMIC | BANNED_EVALUATIVE

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "of",
    "for", "with", "would", "had", "was", "were", "later", "that", "this",
    "it", "its", "found", "showed", "measurable", "margin", "subsequent",
}

QUESTIONS = {
    "q_blame": "How blameworthy is {agent_lower} for this, on a scale from 0 (not at all) to 10 (extremely)?",
    "q_praise": "How praiseworthy is {agent_lower} for this, on a scale from 0 (not at all) to 10 (extremely)?",
}

# Fixed measurement instrument -- identical for every item, unlike QUESTIONS
# above (which vary by agent). Defined ONCE here and imported by
# curate_vignettes.py (`from assemble_vignettes import CURATION_QUESTIONS`)
# rather than also being stored as a repeated-constant column in every row
# of the output sheet. Storing an identical string on hundreds of rows adds
# no per-item information and isn't needed for single-source-of-truth --
# that only requires ONE definition existing somewhere, not one per row.
CURATION_QUESTIONS = {
    "moral_relevance": "Is this primarily a moral matter, or a matter of practicality/aesthetics/etiquette? (0=purely practical/aesthetic/etiquette, 10=purely moral)",
    "severity": "How severe or significant is this outcome, on a scale from 0 to 10?",
    "vividness": "How emotionally evocative or vivid is this description, on a scale from 0 to 10?",
    "typicality_perception": "How typical or expected is this action for someone in this role pursuing this goal, on a scale from 0 (highly atypical) to 10 (highly typical)?",
}

VARIANT_LETTER = {
    ("common", "low"): "A",
    ("common", "high"): "B",
    ("uncommon", "low"): "C",
    ("uncommon", "high"): "D",
}

OUTPUT_FIELDNAMES = [
    "variant_id", "family_id", "domain", "valence", "nonmoral_subdomain",
    "sign", "typicality", "evocativeness", "scenario",
    "q_intentionality", "q_blame", "q_praise",
]


# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------

def _normalize_header(raw_headers):
    """Map arbitrary spreadsheet headers onto the canonical field names via
    ALIASES (case-insensitive). Returns {col_index: canonical_name}."""
    lookup = {}
    for canonical, variants in ALIASES.items():
        for v in variants:
            lookup[v.lower().strip()] = canonical

    mapping = {}
    for i, h in enumerate(raw_headers):
        if h is None:
            continue
        key = str(h).lower().strip()
        if key in lookup:
            mapping[i] = lookup[key]
    return mapping


def load_families(path, sheet_name="master_matrix"):
    """Load family rows from an .xlsx (preferring `sheet_name`, falling
    back to the first sheet) or a .csv. Returns a list of dicts keyed by
    canonical field names."""
    ext = os.path.splitext(path)[1].lower()

    if ext in (".xlsx", ".xlsm"):
        if openpyxl is None:
            raise RuntimeError("openpyxl is required to read .xlsx input")
        wb = openpyxl.load_workbook(path, data_only=True)
        ws = wb[sheet_name] if sheet_name in wb.sheetnames else wb[wb.sheetnames[0]]
        rows = list(ws.iter_rows(values_only=True))
        headers, data_rows = rows[0], rows[1:]
    elif ext == ".csv":
        with open(path, newline="", encoding="utf-8") as f:
            reader = list(csv.reader(f))
        headers, data_rows = reader[0], reader[1:]
    else:
        raise ValueError(f"Unsupported input file type: {ext}")

    mapping = _normalize_header(headers)
    unmapped = [h for i, h in enumerate(headers) if i not in mapping and h]
    if unmapped:
        print(f"NOTE: columns not recognized and ignored: {unmapped}")

    families = []
    for row in data_rows:
        if row is None or all(c is None or str(c).strip() == "" for c in row):
            continue  # skip blank rows
        d = {}
        for i, val in enumerate(row):
            if i in mapping:
                d[mapping[i]] = "" if val is None else str(val).strip()
        families.append(d)
    return families


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_family(fam, row_num):
    """Returns (errors, warnings). Errors block output (real problems:
    missing data, banned language, identical text). Warnings are printed
    but do not block (soft heuristics that can false-positive on
    legitimately-phrased human-authored content, e.g. low word overlap
    when a matched pair simply uses different vocabulary)."""
    errors = []
    warnings = []

    for field in REQUIRED_FIELDS:
        if not fam.get(field):
            errors.append(f"row {row_num} ({fam.get('family_id', '?')}): missing required field '{field}'")

    valence = fam.get("valence", "")
    if valence not in VALID_VALENCES:
        errors.append(f"row {row_num} ({fam.get('family_id', '?')}): invalid valence '{valence}' (must be one of {sorted(VALID_VALENCES)})")
        return errors, warnings  # can't validate further without a valid valence

    subdomain = fam.get("nonmoral_subdomain", "")
    if valence in NONMORAL_VALENCES:
        if not subdomain:
            errors.append(f"row {row_num} ({fam['family_id']}): {valence} requires a nonmoral_subdomain")
        elif subdomain not in VALID_SUBDOMAINS:
            errors.append(f"row {row_num} ({fam['family_id']}): nonmoral_subdomain '{subdomain}' not in {sorted(VALID_SUBDOMAINS)}")
    # NOTE (bug fix from prior session): an EMPTY nonmoral_subdomain on a
    # MB/MG/NEU row is valid (means "not applicable") and must NOT be
    # flagged as missing -- only NMB/NMG rows require it.

    # Banned-language check on consequence fields only.
    for field in ("low_evocative_outcome", "high_evocative_outcome", "outcome_verb"):
        text = fam.get(field, "").lower()
        hits = sorted({w for w in ALL_BANNED if re.search(rf"\b{w}\w*\b", text)})
        if hits:
            errors.append(f"row {row_num} ({fam['family_id']}): '{field}' contains banned evaluative/mental-state language: {hits}")

    # Low/high must differ (else evocativeness manipulation is inert).
    low = fam.get("low_evocative_outcome", "")
    high = fam.get("high_evocative_outcome", "")
    if low and high:
        if low.strip().lower() == high.strip().lower():
            errors.append(f"row {row_num} ({fam['family_id']}): low_evocative_outcome and high_evocative_outcome are identical")
        else:
            low_words = set(re.findall(r"[a-z]+", low.lower())) - STOPWORDS
            high_words = set(re.findall(r"[a-z]+", high.lower())) - STOPWORDS
            overlap = low_words & high_words
            if len(overlap) < 2:
                warnings.append(f"row {row_num} ({fam['family_id']}): low/high share few content words ({sorted(overlap)}) -- eyeball that both describe the same underlying event (this is often fine if they just use different vocabulary)")

    # Common/uncommon actions must differ.
    if fam.get("common_action", "").strip().lower() == fam.get("uncommon_action", "").strip().lower():
        errors.append(f"row {row_num} ({fam['family_id']}): common_action and uncommon_action are identical")

    errors.extend(check_grammatical_fit(fam, row_num))

    return errors, warnings


# Fields that get slotted directly after a fixed template word, and would
# therefore double up or read wrong if the field itself repeats that word.
# This is a MECHANICAL check (does the string fit the fixed slot), not a
# content/style judgment -- added after a real bug where an elicitation
# script combined "cause" (a template word) with an outcome_verb field
# that was itself already a verb phrase, producing "intentionally cause
# contaminate the town's water supply." Catching the noun-phrase-vs-verb-
# phrase confusion here, at authoring time, is cheaper than catching it
# downstream in every script that later consumes these fields.
_LEADING_TO = re.compile(r"^\s*to\b", re.IGNORECASE)
_LEADING_ARTICLE = re.compile(r"^\s*(the|a|an)\b", re.IGNORECASE)


def check_grammatical_fit(fam, row_num):
    """Heuristic, not a grammar checker -- catches the specific class of
    slot-mismatch that has actually caused a bug in this project, not every
    possible grammatical error. Manual read-through (e.g. via the
    render_preview() function below) remains the real backstop for
    anything subtler than these mechanical signals."""
    errors = []
    fid = fam.get("family_id", "?")

    # goal and both actions slot in as "... to {goal}." / "{agent} {action}
    # to ..." -- a field starting with "to" would double the template's
    # own "to", e.g. "to to cut costs" or "{agent} to switch to...".
    for field in ("goal", "common_action", "uncommon_action"):
        val = fam.get(field, "")
        if val and _LEADING_TO.match(val):
            errors.append(
                f"row {row_num} ({fid}): '{field}' starts with \"to\" -- the template "
                f"already supplies \"to\", so this would double up (e.g. \"... to to {val}\"). "
                f"Rewrite '{field}' to start with the bare verb instead."
            )

    # outcome_verb slots in as "knew that this would {outcome_verb}: ..."
    # and reused verbatim in q_intentionality as "intentionally {outcome_verb}".
    # It must be a VERB phrase ("contaminate the water supply"), not a NOUN
    # phrase ("the contamination of the water supply") -- a leading
    # article is the clearest mechanical signal of the latter.
    outcome_verb = fam.get("outcome_verb", "")
    if outcome_verb and _LEADING_ARTICLE.match(outcome_verb):
        errors.append(
            f"row {row_num} ({fid}): 'outcome_verb' (\"{outcome_verb}\") looks like a noun "
            f"phrase (starts with the/a/an), but it needs to be a bare verb phrase -- it's "
            f"inserted directly after \"intentionally\" and after \"would\". "
            f"E.g. use \"contaminate the water supply\", not \"the contamination of the water supply\"."
        )

    # agent must start with "The " or be a capitalized proper name, since
    # _lower_agent()'s casing logic assumes one of those two shapes.
    agent = fam.get("agent", "")
    if agent and not (agent.startswith("The ") or agent[0].isupper()):
        errors.append(
            f"row {row_num} ({fid}): 'agent' (\"{agent}\") should start with \"The \" "
            f"(a role, e.g. \"The plant manager\") or be a capitalized proper name "
            f"(e.g. \"Maria\") -- lowercase-first-word agents will get mis-cased when "
            f"the template lowercases it for mid-sentence use."
        )

    return errors


# ---------------------------------------------------------------------------
# Assembly (deterministic template application -- gameplan Sections 10-11)
# ---------------------------------------------------------------------------

def _lower_agent(agent):
    if agent.startswith("The "):
        return "the " + agent[4:]
    return agent[0].lower() + agent[1:] if agent else agent


def build_variant(fam, typicality, evocativeness):
    agent = fam["agent"]
    action = fam["common_action"] if typicality == "common" else fam["uncommon_action"]
    outcome_text = fam["low_evocative_outcome"] if evocativeness == "low" else fam["high_evocative_outcome"]
    outcome_verb = fam["outcome_verb"]
    goal = fam["goal"]
    affected = fam["affected_entity"]

    scenario = (
        f"{agent} {action} to {goal}. "
        f"{agent} did not care at all about the effect this would have on {affected}. "
        f"{agent} knew that this would {outcome_verb}: {outcome_text}."
    )

    agent_lower = _lower_agent(agent)
    q_intentionality = (
        f"Did {agent_lower} intentionally {outcome_verb}? "
        f"Answer on a scale from 0 (not at all intentionally) to 10 (completely intentionally)."
    )

    letter = VARIANT_LETTER[(typicality, evocativeness)]
    row = {
        "variant_id": f"{fam['family_id']}-{letter}",
        "family_id": fam["family_id"],
        "domain": fam["domain"],
        "valence": fam["valence"],
        "nonmoral_subdomain": fam.get("nonmoral_subdomain", ""),
        "sign": SIGN_BY_VALENCE[fam["valence"]],
        "typicality": typicality,
        "evocativeness": evocativeness,
        "scenario": scenario,
        "q_intentionality": q_intentionality,
    }
    for qkey, template in QUESTIONS.items():
        row[qkey] = template.format(agent_lower=agent_lower)
    return row


def assemble(families):
    rows = []
    for fam in families:
        for typicality in ("common", "uncommon"):
            for evocativeness in ("low", "high"):
                rows.append(build_variant(fam, typicality, evocativeness))
    return rows


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def write_xlsx(families, rows, path):
    if openpyxl is None:
        return
    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "master_matrix"
    mm_fields = REQUIRED_FIELDS[:2] + ["valence", "nonmoral_subdomain"] + REQUIRED_FIELDS[4:]
    # Preserve original column order used in ENV_set01.xlsx:
    mm_fields = [
        "family_id", "domain", "valence", "nonmoral_subdomain", "agent",
        "goal", "common_action", "uncommon_action", "affected_entity",
        "low_evocative_outcome", "high_evocative_outcome", "outcome_verb",
    ]
    ws1.append(mm_fields)
    for fam in families:
        ws1.append([fam.get(f, "") for f in mm_fields])

    ws2 = wb.create_sheet("vignettes")
    ws2.append(OUTPUT_FIELDNAMES)
    for r in rows:
        ws2.append([r.get(f, "") for f in OUTPUT_FIELDNAMES])

    wb.save(path)


def render_preview(families, rows, path):
    """Writes one fully-composed variant per family (the 'A' variant) to a
    plain-text file for manual read-through -- the backstop for anything
    the mechanical checks in check_grammatical_fit() can't catch (awkward
    phrasing, subtly wrong verb forms, tone). Automated checks catch
    whether a string FITS the slot; a human still has to judge whether it
    READS WELL once it does."""
    by_family = {}
    for r in rows:
        by_family.setdefault(r["family_id"], []).append(r)

    with open(path, "w", encoding="utf-8") as f:
        for fam in families:
            fid = fam.get("family_id", "?")
            variant_a = next((r for r in by_family.get(fid, []) if r["variant_id"].endswith("-A")), None)
            if not variant_a:
                continue
            f.write(f"=== {fid} ({fam.get('valence', '?')}) ===\n")
            f.write(variant_a["scenario"] + "\n")
            f.write(f"  Q1: {variant_a['q_intentionality']}\n")
            f.write(f"  Q2: {variant_a['q_blame']}\n\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 3:
        print("Usage: python assemble_vignettes.py <input.xlsx|input.csv> <output_prefix>")
        sys.exit(1)

    input_path, out_prefix = sys.argv[1], sys.argv[2]
    families = load_families(input_path)
    print(f"Loaded {len(families)} family rows from {input_path}")

    all_errors, all_warnings = [], []
    for i, fam in enumerate(families, start=2):  # +2: header is row 1
        errs, warns = validate_family(fam, i)
        all_errors.extend(errs)
        all_warnings.extend(warns)

    if all_warnings:
        print(f"\n{len(all_warnings)} WARNING(S) -- worth a human eyeball, but not blocking:")
        for w in all_warnings:
            print(" -", w)

    if all_errors:
        print(f"\n{len(all_errors)} VALIDATION ERROR(S) -- fix these in the spreadsheet before re-running:")
        for e in all_errors:
            print(" -", e)
        print("\nNo output written. (Pass --force to write anyway, if you want to inspect partial output.)")
        if "--force" not in sys.argv:
            sys.exit(1)

    rows = assemble(families)
    print(f"Assembled {len(rows)} vignette variants from {len(families)} families.")

    csv_path = f"{out_prefix}.csv"
    write_csv(rows, csv_path)
    print(f"Wrote {csv_path}")

    xlsx_path = f"{out_prefix}.xlsx"
    write_xlsx(families, rows, xlsx_path)
    print(f"Wrote {xlsx_path}")

    preview_path = f"{out_prefix}_preview.txt"
    render_preview(families, rows, preview_path)
    print(f"Wrote {preview_path} -- one example variant per family, for manual read-through "
          f"(automated checks only catch structural fit, not whether it reads well)")


if __name__ == "__main__":
    main()
