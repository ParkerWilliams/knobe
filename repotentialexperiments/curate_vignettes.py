"""
Curation-stage elicitation for the vignette pipeline.

Runs the four curation checks (moral relevance, severity, vividness,
typicality-perception) on every vignette variant, BEFORE any item is
accepted into the dataset used for the actual RQ1 experiment.

Critical design constraints, both non-negotiable per the protocol:

1. INDEPENDENT COMPLETIONS. Each of the four checks is fired as its own
   fresh API call with no shared conversation history -- never chained,
   so C1's answer can't leak into C2's context, etc. This mirrors the
   between-subjects logic used for the main-experiment questions
   (knobe_vignette_protocol.md Section 8) and is just as important here:
   a curation reviewer that has already rated an item's severity should
   not carry that judgment into its vividness rating.

2. REVIEWER != SUBJECT. Curation must be run by a model that will NOT
   later serve as a test-subject model in the main experiment (e.g. if
   Llama/Gemma/Mistral are subjects per the Raimondi-comparison design,
   curation should run on a Claude model, or vice versa -- whatever
   guarantees no overlap). This script takes the reviewer model as a
   required argument and does not default it, so you can't accidentally
   run curation and the main experiment on the same model without
   explicitly choosing to.

This script makes network calls and will not run inside a sandboxed,
network-disabled shell -- run it in your own environment with
ANTHROPIC_API_KEY set (or adapt call_model() for a different provider's
SDK if your reviewer model isn't a Claude model).

Usage:
    python curate_vignettes.py vignettes.csv --reviewer-model claude-sonnet-4-6 --out curated.csv
"""

import argparse
import csv
import re
import sys
import time

try:
    import anthropic
except ImportError:
    anthropic = None


try:
    from assemble_vignettes import CURATION_QUESTIONS
except ImportError:
    sys.exit(
        "Could not import CURATION_QUESTIONS from assemble_vignettes.py -- "
        "run this script from the same directory, or copy that module alongside it."
    )

PROMPT_TEMPLATE = "Scenario: {scenario}\n\nQuestion: {question}\nAnswer:"

# Each field name here is what gets written to the output CSV.
CURATION_FIELDS = list(CURATION_QUESTIONS.keys())


def call_model(client, model, prompt, max_tokens=10, max_retries=3):
    """Fires ONE independent completion -- fresh context every time, no
    conversation history passed in. Retries on transient errors only."""
    for attempt in range(max_retries):
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return "".join(b.text for b in resp.content if b.type == "text").strip()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)


def parse_rating(raw_text):
    """Extracts the first integer 0-10 from the model's response. Returns
    (value, ok, raw). ok=False means the response didn't parse cleanly and
    needs manual inspection -- never silently coerce a bad parse to a
    default number."""
    match = re.search(r"\b(10|[0-9])\b", raw_text)
    if match:
        return int(match.group(1)), True, raw_text
    return None, False, raw_text


def curate_item(client, model, row):
    """Runs all four curation checks on one row, each as a fully
    independent call. Question wording comes from the imported
    CURATION_QUESTIONS constant (assemble_vignettes.py's single
    definition) -- fixed, identical for every item, so it's a code-level
    constant rather than something read per-row from the sheet. Returns a
    dict of {field: (value, ok, raw)}."""
    results = {}
    for field, question in CURATION_QUESTIONS.items():
        prompt = PROMPT_TEMPLATE.format(scenario=row["scenario"], question=question)
        raw = call_model(client, model, prompt)
        value, ok, raw_text = parse_rating(raw)
        results[field] = (value, ok, raw_text)
    return results


def flag_item(row, results):
    """Applies the manipulation-check logic from knobe_vignette_protocol.md
    Section 9 / gameplan Section 8: for a matched low/high evocativeness
    pair (same family_id, same typicality, opposite evocativeness),
    severity should NOT differ but vividness SHOULD. This function only
    flags parse failures at the single-item level; the actual pair-level
    severity/vividness match check needs both rows and is run separately
    in `check_pairs()` below, once the whole file is loaded.
    """
    flags = []
    for field, (value, ok, raw) in results.items():
        if not ok:
            flags.append(f"{field}: unparseable response ({raw!r})")
    return flags


def check_pairs(rows):
    """Post-hoc pair-level check across the whole curated set: for every
    (family_id, typicality) pair, compare the low- and high-evocativeness
    rows' severity and vividness ratings. Adds a 'pair_flag' column.
    Threshold of 2 points is a starting heuristic -- inspect the actual
    distribution before treating it as a hard cutoff."""
    by_key = {}
    for r in rows:
        key = (r["family_id"], r["typicality"])
        by_key.setdefault(key, {})[r["evocativeness"]] = r

    SEVERITY_MATCH_MAX_DIFF = 2
    VIVIDNESS_MIN_GAP = 2

    for key, pair in by_key.items():
        low, high = pair.get("low"), pair.get("high")
        if not low or not high:
            continue
        try:
            sev_low, sev_high = int(low["severity"]), int(high["severity"])
            viv_low, viv_high = int(low["vividness"]), int(high["vividness"])
        except (ValueError, TypeError):
            continue  # unparseable ratings already flagged individually

        pair_flags = []
        if abs(sev_high - sev_low) > SEVERITY_MATCH_MAX_DIFF:
            pair_flags.append(
                f"severity mismatch: low={sev_low} high={sev_high} (should be matched)"
            )
        if (viv_high - viv_low) < VIVIDNESS_MIN_GAP:
            pair_flags.append(
                f"vividness gap too small: low={viv_low} high={viv_high} (should differ)"
            )
        flag_text = "; ".join(pair_flags) if pair_flags else ""
        low["pair_flag"] = flag_text
        high["pair_flag"] = flag_text

    # Rows with no evocativeness pairing at all (shouldn't happen given
    # the assembler's 4-variant structure, but don't silently drop them).
    for r in rows:
        r.setdefault("pair_flag", r.get("pair_flag", ""))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input_csv", help="Output of assemble_vignettes.py")
    parser.add_argument("--reviewer-model", required=True,
                         help="Model string for the CURATION reviewer -- must not be a model you plan to test as a subject in the main experiment.")
    parser.add_argument("--out", default="vignettes_curated.csv")
    parser.add_argument("--subject-models", nargs="*", default=[],
                         help="Optional: list the model(s) you intend to use as test subjects. "
                              "If --reviewer-model appears in this list, the script refuses to run.")
    args = parser.parse_args()

    if args.reviewer_model in args.subject_models:
        sys.exit(
            f"Refusing to run: reviewer model '{args.reviewer_model}' also appears in "
            f"--subject-models. Curation must be run by a model that is NOT a test subject."
        )

    if anthropic is None:
        sys.exit("The 'anthropic' package is required. pip install anthropic")

    with open(args.input_csv, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"Loaded {len(rows)} vignette variants from {args.input_csv}")

    required_cols = {"scenario"}
    missing_cols = required_cols - set(rows[0].keys()) if rows else required_cols
    if missing_cols:
        sys.exit(f"Input CSV is missing required column(s): {missing_cols}.")

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    out_rows = []
    n_flagged_individual = 0

    for i, row in enumerate(rows, start=1):
        results = curate_item(client, args.reviewer_model, row)
        flags = flag_item(row, results)
        if flags:
            n_flagged_individual += 1

        out_row = dict(row)
        for field, (value, ok, raw) in results.items():
            out_row[field] = value if ok else ""
            out_row[f"{field}_raw"] = raw
        out_row["individual_flags"] = "; ".join(flags)
        out_rows.append(out_row)
        print(f"  [{i}/{len(rows)}] {row['variant_id']}: "
              f"moral_rel={out_row['moral_relevance']} sev={out_row['severity']} "
              f"viv={out_row['vividness']} typ={out_row['typicality_perception']}"
              + (f"  FLAGGED: {flags}" if flags else ""))

    out_rows = check_pairs(out_rows)
    n_pair_flagged = sum(1 for r in out_rows if r.get("pair_flag"))

    fieldnames = list(rows[0].keys()) + [
        f for field in CURATION_FIELDS for f in (field, f"{field}_raw")
    ] + ["individual_flags", "pair_flag"]

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"\nCurated {len(out_rows)} items.")
    print(f"{n_flagged_individual} item(s) had an unparseable curation response -- inspect manually.")
    print(f"{n_pair_flagged} item(s) failed the pair-level severity-match / vividness-gap check -- inspect before using in the main experiment.")
    print(f"Written to {args.out}")


if __name__ == "__main__":
    main()
