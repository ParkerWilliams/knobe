"""Applies moral_relevance_type2_patch.csv to the frozen master matrix,
producing a candidate revised matrix for re-curation. Does NOT touch the
original ALL_DOMAINS_master_matrix.csv -- writes a new file alongside it.

Usage: python data/authoring/v1.1_candidate/apply_patch.py

Only rewrites the fields listed per family_id in the patch (affected_entity,
outcome_verb, low_evocative_outcome, high_evocative_outcome). agent, goal,
common_action, uncommon_action are never touched, so set_id matching
(family_id with the valence token stripped) survives the revision.

Every patched family also gets human_approved reset to False (per the
provenance convention in generate.py's _append_rows -- a family with
revised content hasn't actually been reviewed in that revised form, and
assemble.py's --release mode hard-fails on any unapproved family, so this
is what makes Parker's existing `knobe approve` command the real gate for
this revision rather than silently inheriting approval of the old text).
generator_model/ingest_date are stamped to reflect this revision pass.

Rows with field == 'note' in the patch are not applied -- they're flagged
for manual attention instead (see the note text) and left as-is here,
including their original human_approved value.
"""
import csv
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # knobe/
MATRIX_PATH = ROOT / "data" / "authoring" / "ALL_DOMAINS_master_matrix.csv"
PATCH_PATH = Path(__file__).parent / "moral_relevance_type2_patch.csv"
OUT_PATH = Path(__file__).parent / "ALL_DOMAINS_master_matrix_v1.1_candidate.csv"
REVISION_GENERATOR_LABEL = "claude-sonnet-5 (manual revision draft, v1.1 moral-relevance patch, unreviewed)"


def main() -> None:
    patch_rows = [r for r in csv.DictReader(open(PATCH_PATH)) if r["field"] != "note"]
    notes = [r for r in csv.DictReader(open(PATCH_PATH)) if r["field"] == "note"]

    by_family: dict[str, list[dict]] = {}
    for r in patch_rows:
        by_family.setdefault(r["family_id"], []).append(r)

    matrix_rows = list(csv.DictReader(open(MATRIX_PATH)))
    fieldnames = list(matrix_rows[0].keys())

    touched = set()
    mismatches = []
    for row in matrix_rows:
        fam_id = row["family_id"]
        if fam_id not in by_family:
            continue
        touched.add(fam_id)
        for edit in by_family[fam_id]:
            field = edit["field"]
            if row.get(field, "") != edit["old_value"]:
                mismatches.append((fam_id, field, row.get(field, ""), edit["old_value"]))
            row[field] = edit["new_value"]
        row["human_approved"] = "False"
        row["generator_model"] = REVISION_GENERATOR_LABEL
        row["ingest_date"] = datetime.date.today().isoformat()

    missing = set(by_family) - touched
    if missing:
        raise SystemExit(f"family_ids in patch but not found in matrix: {missing}")
    if mismatches:
        print("WARNING: old_value in patch didn't match matrix content (matrix may have "
              "changed since the patch was drafted) -- review before trusting the output:")
        for fam_id, field, actual, expected in mismatches:
            print(f"  {fam_id}.{field}: matrix has {actual!r}, patch expected {expected!r}")

    with open(OUT_PATH, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(matrix_rows)

    print(f"Wrote {OUT_PATH} ({len(matrix_rows)} rows, {len(touched)} families patched)")
    if notes:
        print(f"\n{len(notes)} family(ies) flagged for manual attention, not auto-patched:")
        for n in notes:
            print(f"  {n['family_id']}: {n['old_value']}")


if __name__ == "__main__":
    main()
