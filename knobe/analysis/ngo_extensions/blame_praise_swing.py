"""Gameplan section 5 item 2: is the blame-swing-vs-praise-swing comparison
(ALIGNMENT_DISCUSSION point 6) safe to make on a common scale?

Point 6 compares each family's blame swing against its own praise swing on
identical vignettes, and reads the result against the human negativity-bias
prior ("bad is stronger than good", Baumeister et al.). That comparison is
immune to everything that threatens the between-arm claims -- item
composition, severity, and the curation attrition in
`measurement_selection_audit.py` are all differenced out, since both
questions are asked of the same items. What it is NOT automatically immune
to is the two questions' response scales behaving differently, which is what
this script checks, three ways:

1. **Scoring method.** The same swings under `--score ev` and `--score
   parsed`. These are different scales by construction: EV is a
   logprob-weighted mean over 0-10 whose compression depends on the shape of
   the first-token logprob distribution, and that shape differs by question;
   parsed is the model's own raw integer on a 0-10 scale that is identical
   across questions. For a CROSS-QUESTION MAGNITUDE comparison -- which is
   exactly what point 6 is -- parsed is therefore the defensible score and EV
   is not, independent of which one any individual significance test prefers.
2. **Floor/ceiling structure.** Raw cell means per (family, arm, sign), the
   point-4a table generalized to praise. 4a found the moral-vs-nonmoral blame
   gap was driven by an elevated moral-good blame floor rather than by
   nonmoral items being blamed more; praise's own pattern was left open.
3. **Standardized swings.** Each swing divided by that question-cell's own
   pooled SD, so "blame swings more than praise" can be read without assuming
   the two questions have equal spread.

Machinery is REUSED: `load_frame` is imported from the nonmoral pilot's
`analyze_sign_wcb.py`, so the frame, merge, and sign coding are the same ones
the fits use; the swings themselves are read from that script's committed
output tables rather than refit here, so this script cannot drift from them.
No bootstrap and no seeding -- means and SDs only.

Finetuned cells only. Point 6 is a finetuned claim, and the pretrained
blame/praise cells parse at 25.5-29.9% (`measurement_audit.csv`), too thin to
carry a magnitude comparison.

Run from the knobe repo root (needs the nonmoral pilot's elicit_results.jsonl
unpacked, plus both --score runs of analyze_sign_wcb.py already written):
    .venv/bin/python analysis/ngo_extensions/blame_praise_swing.py

Writes two small committed summary tables under nonmoral_pilot/outputs/:
    blame_praise_swing.csv        -- swings per (score, family, arm) + verdict
    question_cell_means.csv       -- raw means/SDs per (question, family, arm, sign)
    domain_gap_decomposition.csv  -- the moral-vs-nonmoral gap split by sign
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
PILOT = HERE / "nonmoral_pilot"
sys.path.insert(0, str(PILOT))
from analyze_sign_wcb import load_frame  # noqa: E402

ARMS = {"moral": lambda d: d["category"] == "moral",
        "nonmoral_pooled": lambda d: d["category"] != "moral"}
FAMILIES = ["gemma", "llama", "mistral"]
SCORES = {"ev": "", "parsed": "_parsed"}


def cell_means(d: pd.DataFrame) -> pd.DataFrame:
    """Raw means/SDs per (question, score, family, arm, sign) -- point 4a's
    table, generalized to praise and to both scoring methods."""
    out = []
    for question in ["q_blame", "q_praise"]:
        for score, resp in [("ev", "ev_rating"), ("parsed", "parsed_rating")]:
            sub = d[d["question"] == question]
            if score == "parsed":
                sub = sub[sub["parse_ok"] & sub["parsed_rating"].notna()]
            for fam in FAMILIES:
                cell = sub[(sub["family"] == fam) & (sub["tuning_status"] == "finetuned")]
                for arm, mask in ARMS.items():
                    s = cell[mask(cell)]
                    for sign in ["good", "bad"]:
                        v = s[s["sign"] == sign][resp]
                        out.append(dict(question=question, score=score, family=fam,
                                        arm=arm, sign=sign, n=len(v),
                                        mean=round(v.mean(), 4), sd=round(v.std(), 4)))
    return pd.DataFrame(out)


def swings(means: pd.DataFrame) -> pd.DataFrame:
    """Blame vs. praise swing per (score, family, arm), in raw and SD units.

    Swings come from the committed WCB tables (beta_obs on sign_c) rather than
    from differencing the means above, so this table and the fits can't drift
    apart; the means supply only the pooled SD used to standardize them.
    """
    out = []
    for score, suffix in SCORES.items():
        b = pd.read_csv(PILOT / "outputs" / f"sign_wcb_blame{suffix}.csv")
        p = pd.read_csv(PILOT / "outputs" / f"sign_wcb_praise{suffix}.csv")
        for fam in FAMILIES:
            for arm in ARMS:
                pick = lambda t: t[(t.arm == arm) & (t.family == fam)
                                   & (t.tuning == "finetuned")].iloc[0]
                bb, pp = pick(b), pick(p)
                sd = lambda q: means[(means.question == q) & (means.score == score)
                                     & (means.family == fam) & (means.arm == arm)]["sd"].mean()
                bs, ps = abs(bb.beta_obs), abs(pp.beta_obs)
                out.append(dict(
                    score=score, family=fam, arm=arm,
                    blame_swing=round(bs, 4), blame_p_wcb=bb.p_wcb,
                    praise_swing=round(ps, 4), praise_p_wcb=pp.p_wcb,
                    blame_swing_sd=round(bs / sd("q_blame"), 4),
                    praise_swing_sd=round(ps / sd("q_praise"), 4),
                    bigger_raw="blame" if bs > ps else "praise",
                    bigger_sd="blame" if bs / sd("q_blame") > ps / sd("q_praise") else "praise",
                ))
    return pd.DataFrame(out)


def domain_gap_decomposition(means: pd.DataFrame) -> pd.DataFrame:
    """Where does the moral-vs-nonmoral difference actually live -- in the
    good-outcome cell or the bad-outcome one?

    Point 4a raised this for blame and answered it from three hand-read rows;
    point 5 left praise open entirely. Splitting the domain gap by sign
    answers both at once and is the table the interaction terms summarize.
    """
    out = []
    for question in ["q_blame", "q_praise"]:
        for score in ["ev", "parsed"]:
            for fam in FAMILIES:
                g = lambda arm, sign: means[
                    (means.question == question) & (means.score == score)
                    & (means.family == fam) & (means.arm == arm)
                    & (means.sign == sign)]["mean"].iloc[0]
                good_gap = g("moral", "good") - g("nonmoral_pooled", "good")
                bad_gap = g("moral", "bad") - g("nonmoral_pooled", "bad")
                out.append(dict(
                    question=question, score=score, family=fam,
                    moral_good=g("moral", "good"), nonmoral_good=g("nonmoral_pooled", "good"),
                    good_cell_gap=round(good_gap, 4),
                    moral_bad=g("moral", "bad"), nonmoral_bad=g("nonmoral_pooled", "bad"),
                    bad_cell_gap=round(bad_gap, 4),
                    gap_ratio_good_to_bad=(round(abs(good_gap) / abs(bad_gap), 2)
                                           if bad_gap else float("inf")),
                ))
    return pd.DataFrame(out)


def main() -> None:
    d = load_frame()
    means = cell_means(d)
    sw = swings(means)
    gaps = domain_gap_decomposition(means)

    print("=== raw cell means (finetuned) ===")
    print(means.to_string(index=False))
    print("\n=== blame vs praise swing ===")
    print(sw.to_string(index=False))
    print("\n=== negativity-bias prior (blame swings more) holds in ===")
    for score in SCORES:
        s = sw[sw.score == score]
        for col in ["bigger_raw", "bigger_sd"]:
            hit = s[s[col] == "blame"]
            print(f"  {score:<7} {col:<11}: {len(hit)}/{len(s)} cells, "
                  f"families {sorted(set(hit.family)) or '--'}")

    print("\n=== where the domain difference lives (parsed) ===")
    print(gaps[gaps.score == "parsed"].to_string(index=False))

    gaps.to_csv(PILOT / "outputs" / "domain_gap_decomposition.csv", index=False)
    means.to_csv(PILOT / "outputs" / "question_cell_means.csv", index=False)
    sw.to_csv(PILOT / "outputs" / "blame_praise_swing.csv", index=False)
    print(f"\nwrote {PILOT / 'outputs'}/question_cell_means.csv + blame_praise_swing.csv")


if __name__ == "__main__":
    main()
