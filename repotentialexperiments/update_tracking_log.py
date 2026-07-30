"""
Generates the "already used" tracking-log block for Section 8.2's
per-set prompt, straight from whatever's already in a domain's master
matrix CSV. Removes the one manual step (hand-maintaining a log) that's
most likely to get forgotten or mistyped across ~50 generation calls.

Usage:
    python update_tracking_log.py ENV_master_matrix.csv
"""

import argparse
import csv
import sys
from collections import Counter


def load_sets(path):
    """Groups rows by set number (the trailing number in family_id) and
    returns one summary dict per set."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    by_set = {}
    for r in rows:
        set_num = r["family_id"].split("-")[-1]
        by_set.setdefault(set_num, {}).setdefault("rows", []).append(r)

    summaries = []
    for set_num in sorted(by_set):
        set_rows = by_set[set_num]["rows"]
        agent = set_rows[0]["agent"]
        goal = set_rows[0]["goal"]
        subdomain = next((r["nonmoral_subdomain"] for r in set_rows if r["nonmoral_subdomain"]), "")
        summaries.append({"set_num": set_num, "agent": agent, "goal": goal, "subdomain": subdomain})
    return summaries


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("master_matrix_csv")
    args = parser.parse_args()

    try:
        summaries = load_sets(args.master_matrix_csv)
    except FileNotFoundError:
        sys.exit(f"No file at {args.master_matrix_csv} yet -- this is set 01, nothing to track. "
                 f"Paste 'Already used in this domain: (none yet)' into the per-set prompt.")

    if not summaries:
        print("No sets found yet -- this is set 01. Paste 'Already used in this domain: (none yet)'.")
        return

    print(f"Already used in this domain ({len(summaries)} set(s) so far):")
    for s in summaries:
        subdomain_note = f" [subdomain: {s['subdomain']}]" if s["subdomain"] else ""
        print(f"  - Set {s['set_num']}: agent = \"{s['agent']}\"; goal = \"{s['goal']}\"{subdomain_note}")

    subdomain_counts = Counter(s["subdomain"] for s in summaries if s["subdomain"])
    if subdomain_counts:
        print(f"\nNonmoral subdomain tally: {dict(subdomain_counts)}")
        if subdomain_counts:
            max_count = max(subdomain_counts.values())
            min_count = min(subdomain_counts.values())
            if max_count - min_count >= 2:
                least = min(subdomain_counts, key=subdomain_counts.get)
                print(f"  -> imbalanced. Next set should prefer subdomain: {least}")
            missing = {"prudential", "procedural", "aesthetic", "etiquette"} - subdomain_counts.keys()
            if missing:
                print(f"  -> not yet used at all: {sorted(missing)} -- prefer one of these next")

    print(f"\nNext set number: {int(summaries[-1]['set_num']) + 1:02d}")


if __name__ == "__main__":
    main()
