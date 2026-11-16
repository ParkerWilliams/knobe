"""A small HTML report on the Knobe effect in Jev asked natively -> docs/JEV_NATIVE_REPORT.html.

Why (Parker, 2026-11-16): a short, shareable report on the Knobe evidence in Jev
itself (no wrapper), with verbatims: the scenarios and questions exactly as Jev
saw them, and Jev's answers.

No new fits. Every number is read from the tables tools/jev_native.py analyze and
retest wrote (outputs/first_look/jevnat_*, outputs/checks/jevnat_*); scenario and
question text come from the item files through kmp.jev_native.build_questions (the
same sheet the run asked); the verbatim answers come from the local answers
(outputs/elicit/jev_native_<set>.jsonl, gitignored). Jev writes no text: its
verbatim answer is the bubble it fills and the probability it puts on each.

The verbatim pairs are hand-picked (PAIRS, each with the reason); the retest
example is picked by rule (the Ngo question asked word for word in both runs
whose expected value moved most).

From the study folder:
    ../../.venv/bin/python tools/jev_native_report.py [--out docs/JEV_NATIVE_REPORT.html]
"""
from __future__ import annotations

import argparse
import html
from decimal import ROUND_HALF_UP, Decimal
import json
import subprocess
import sys
from pathlib import Path

STUDY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDY))

import pandas as pd  # noqa: E402

from kmp import jev_native  # noqa: E402
from kmp.items import load_items  # noqa: E402

SETS = {"ngo_verbatim": "stimuli/ngo_verbatim.csv",
        "pilot_nonmoral": "stimuli/pilot/pilot_nonmoral.csv",
        "pilot_foundations": "stimuli/pilot/pilot_foundations.csv"}
SET_LABEL = {"ngo_verbatim": "Ngo's items", "pilot_nonmoral": "Nonmoral pilot",
             "pilot_foundations": "Foundations pilot"}
ARM_LABEL = {"moral": "moral", "prudential": "prudential (own interest)", "procedural": "procedural (rules)",
             "harm": "harm", "authority": "authority", "fairness": "fairness", "loyalty": "loyalty",
             "purity": "purity"}
FIGURE_ROWS = [("ngo_verbatim", "moral"), ("pilot_nonmoral", "moral"), ("pilot_nonmoral", "prudential"),
               ("pilot_nonmoral", "procedural"), ("pilot_foundations", "harm"),
               ("pilot_foundations", "authority"), ("pilot_foundations", "fairness"),
               ("pilot_foundations", "loyalty"), ("pilot_foundations", "purity")]
# (set, storyline prefix of the item ids, why this pair is shown)
PAIRS = [
    ("ngo_verbatim", "kmp-nv-002-moral",
     "The textbook case: Knobe's CEO and the environment, in Ngo's wording."),
    ("pilot_nonmoral", "kmp-nm-005-procedural",
     "Nothing moral at stake, only an email font and the company's branding. Jev still splits the pair."),
    ("pilot_nonmoral", "kmp-nm-009-prudential",
     "The side effect falls on the agent's own health, not on anyone else."),
    ("pilot_foundations", "kmp-mf-001-authority",
     "Intentionality splits cleanly but blame does not: Jev blames both people. The authority pairs do this "
     "throughout, which is why the authority blame gap is the smallest."),
    ("ngo_verbatim", "kmp-nv-037-moral",
     "One of the three Ngo pairs (of 40) without the effect: Jev calls the good side effect intentional too."),
]
SHOWN_QKEYS = ("intentionality", "blame", "praise")   # each on its w1 wording (normal anchors)
QLABEL = {"intentionality": "Intentional?", "blame": "Blameworthy?", "praise": "Praiseworthy?"}


# --- data ---------------------------------------------------------------------------------

def _csv(rel: str) -> pd.DataFrame:
    return pd.read_csv(STUDY / "outputs" / rel)


def _last_commit(rel: str) -> str:
    out = subprocess.run(["git", "log", "-1", "--format=%h", "--", str(STUDY / "outputs" / rel)],
                         capture_output=True, text=True, cwd=STUDY)
    return out.stdout.strip() or "uncommitted"


def load():
    data = {"items": {}, "questions": {}, "answers": {}}
    for s, path in SETS.items():
        items = load_items(STUDY / path)
        data["items"][s] = {i.item_id: i for i in items}
        data["questions"][s] = {q.job_id: q for q in jev_native.build_questions(items)}
        data["answers"][s] = jev_native.read_results(STUDY / "outputs" / "elicit" / f"jev_native_{s}.jsonl")
    old = STUDY / "outputs" / "elicit" / "jev_native_ngo_verbatim_pre1022.jsonl"
    data["answers_first_run"] = jev_native.read_results(old) if old.exists() else {}
    return data


def question(data, s: str, item_id: str, qkey: str, wording: str = "w1"):
    q = data["questions"][s][f"{item_id}::{qkey}::{wording}::{jev_native.FMT}"]
    return q, data["answers"][s][q.job_id]


# --- formatting ---------------------------------------------------------------------------

E = html.escape


def num(x: float, nd: int = 2) -> str:
    """Round half up, as the write-up does (0.975 -> 0.98; plain f-formatting gives 0.97 from the float)."""
    d = Decimal(repr(round(float(x), 9))).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)
    return f"{d:.{nd}f}"


def signed(x: float, nd: int = 1) -> str:
    s = num(x, nd)
    return (s if s.startswith("-") else "+" + s).replace("-", "−")


def pval(p: float) -> str:
    return "<&nbsp;.001" if p < 0.001 else f"{p:.3f}".lstrip("0")


def probs_of(answer: dict) -> list[float]:
    p = answer.get("probabilities") or {}
    total = sum(float(p.get(lv, 0.0)) for lv in jev_native.LEVELS) or 1.0
    return [float(p.get(lv, 0.0)) / total for lv in jev_native.LEVELS]


def mini_chart(answer: dict) -> str:
    """Jev's probability on each bubble 0..10: the filled bubble in the accent, EV as a marker."""
    probs, top, ev = probs_of(answer), int(answer["top"]), float(answer["ev"])
    peak = max(probs) or 1.0
    label = "Jev's probability on each bubble: " + ", ".join(f"{k}: {p:.0%}" for k, p in enumerate(probs)) + \
            f". Filled {top}; average {num(ev)}."
    bars = "".join(
        f'<span class="mb{" mb-top" if k == top else ""}" style="height:{max(p / peak, 0.02) * 100:.1f}%" '
        f'data-tip="Bubble {k}: {p:.0%}{" (filled)" if k == top else ""}"></span>'
        for k, p in enumerate(probs))
    return (f'<div class="mini" role="img" aria-label="{E(label)}"><div class="mini-plot">{bars}</div>'
            f'<div class="mini-axis">{"".join(f'<span style="left:{(k + 0.5) / 11 * 100:.1f}%">{k}</span>' for k in (0, 5, 10))}'
            f'<i class="ev" style="left:{(ev + 0.5) / 11 * 100:.1f}%" data-tip="Average (EV) {num(ev)}"></i></div></div>')


def answer_block(q, a: dict) -> str:
    return (f'<div class="qa"><p class="q">“{E(q.text)}”</p>{mini_chart(a)}'
            f'<p class="a">Filled <b>{a["top"]}</b> · average {num(a["ev"])}</p></div>')


# --- sections -----------------------------------------------------------------------------

def section_summary(data) -> str:
    top = _csv("first_look/jevnat_ngo_verbatim_normal_sign_effects.csv").set_index("qkey")
    ev = _csv("first_look/jevnat_ngo_verbatim_ev_normal_sign_effects.csv").set_index("qkey")
    pdir = _csv("checks/jevnat_ngo_verbatim/pair_direction.csv").query("wordings == 'normal'").set_index("qkey")

    def tile(qkey, label, note):
        b, e = top.loc[qkey, "beta_obs"], ev.loc[qkey, "beta_obs"]
        r = pdir.loc[qkey]
        count = (f"{r.bad_above} of {r.n_storylines} storylines harmful &gt; helpful" if qkey != "praise" else
                 f"{r.bad_below} of {r.n_storylines} storylines helpful &gt; harmful, {r.level} tied")
        return (f'<div class="tile"><div class="tile-label">{label}</div><div class="tile-value">{signed(b)}</div>'
                f'<div class="tile-note">average {signed(e)} · {count}</div><div class="tile-note">{note}</div></div>')

    tiles = "".join([
        tile("intentionality", "Intentionality gap", "harmful judged intentional, helpful not"),
        tile("blame", "Blame gap", "harmful blamed, helpful not"),
        tile("praise", "Praise gap", "almost no praise for either"),
    ])
    return f"""
<section>
  <p class="lede">Jev shows a strong Knobe effect. It judges a harmful side effect intentional and blameworthy, and the
  matching helpful one unintentional and barely praiseworthy. The intentionality gap is just as large when the side effect
  is not moral at all (the agent's own interests, or a company rule), so for Jev it follows <em>bad vs good</em>, not
  <em>moral vs not</em>. Blame is the exception: it is largest for harm.</p>
  <h3 class="tiles-title">Ngo's 80 items, harmful minus helpful, on the 0–10 scale</h3>
  <div class="tiles">{tiles}</div>
  <p class="note">Big number: the bubble Jev fills (its top choice). "Average": the mean over Jev's probabilities
  (expected value, EV). Normal wordings only; see <a href="#caveats">caveats</a> on the reversed ones.</p>
</section>"""


def section_method(data) -> str:
    q, _ = question(data, "ngo_verbatim", "kmp-nv-002-moral-bad", "intentionality")
    body = json.dumps(jev_native.request_body(q), indent=1)
    sizes = {s: len(a) for s, a in data["answers"].items()}
    return f"""
<section>
  <h2>How Jev was asked</h2>
  <p>Jev is a decision model: it does not write text, it picks one of the options it is given and reports how likely each
  one is. Each of the chat models' questions became one multiple-choice sheet: the scenario as Jev's state, the question as
  worded, and eleven bubbles, 0–10, with the scale's own end labels. There was no chat prompt, no worked examples, and one
  call per question. Here is one request, verbatim:</p>
  <pre><code>{E(body)}</code></pre>
  <p>Questions asked: {sizes["ngo_verbatim"]:,} on Ngo's 80 items, {sizes["pilot_nonmoral"]:,} on the nonmoral
  pilot (240 items) and {sizes["pilot_foundations"]:,} on the foundations pilot (152 items), all answered, by
  <code>typesafe/jev-1.14-20261014</code>, on 2026-11-12.</p>
</section>"""


def section_figure() -> str:
    rows = []
    for qkey in ("intentionality", "blame"):
        for s, arm in FIGURE_ROWS:
            vals = {}
            for reader, suffix in (("top", ""), ("ev", "_ev")):
                p = _csv(f"checks/jevnat_{s}{suffix}/pair_direction.csv")
                r = p[(p.qkey == qkey) & (p.arm == arm) & (p.wordings == "normal")].iloc[0]
                vals[reader] = float(r.mean_bad_minus_good)
                vals["n"] = int(r.n_storylines)
            rows.append(dict(qkey=qkey, set=s, arm=arm, **vals))
    df = pd.DataFrame(rows)

    def panel(qkey, title):
        out = [f'<div class="panel"><h3>{title}</h3><div class="axis-top"><span>0</span><span>5</span>'
               f'<span>10</span></div>']
        last_set = None
        for r in df[df.qkey == qkey].itertuples():
            if r.set != last_set:
                out.append(f'<div class="group">{SET_LABEL[r.set]}</div>')
                last_set = r.set
            out.append(
                f'<div class="row"><div class="row-label">{ARM_LABEL[r.arm]}</div><div class="track">'
                f'<span class="hb hb-top" style="width:{max(r.top, 0) * 10:.1f}%" tabindex="0" '
                f'data-tip="{SET_LABEL[r.set]}, {r.arm}: filled bubble {signed(r.top, 2)} ({r.n} storylines)"></span>'
                f'<span class="hb hb-ev" style="width:{max(r.ev, 0) * 10:.1f}%" tabindex="0" '
                f'data-tip="{SET_LABEL[r.set]}, {r.arm}: average {signed(r.ev, 2)} ({r.n} storylines)"></span>'
                f'</div></div>')
        out.append("</div>")
        return "".join(out)

    table = "".join(f"<tr><td>{SET_LABEL[r.set]}</td><td>{r.arm}</td><td>{r.qkey}</td><td>{signed(r.top, 2)}</td>"
                    f"<td>{signed(r.ev, 2)}</td><td>{r.n}</td></tr>" for r in df.itertuples())
    return f"""
<section>
  <h2>Where the gap shows up</h2>
  <p>Harmful minus helpful, averaged over storylines, normal wordings. The intentionality gap is large in every kind of
  side effect. Blame is largest for harm and smallest for authority.</p>
  <div class="legend"><span><i class="sw sw-top"></i>filled bubble</span><span><i class="sw sw-ev"></i>average (EV)</span></div>
  <div class="panels">{panel("intentionality", "Intentionality gap")}{panel("blame", "Blame gap")}</div>
  <details><summary>Show as a table</summary><div class="scroll"><table><thead><tr><th>set</th><th>arm</th><th>question</th>
  <th>filled bubble</th><th>average</th><th>storylines</th></tr></thead><tbody>{table}</tbody></table></div></details>
</section>"""


def section_tests() -> str:
    top = _csv("first_look/jevnat_ngo_verbatim_normal_sign_effects.csv").set_index("qkey")
    ev = _csv("first_look/jevnat_ngo_verbatim_ev_normal_sign_effects.csv").set_index("qkey")
    ngo = "".join(
        f"<tr><td>{qk}</td><td>{num(top.loc[qk, 'mean_bad'])}</td><td>{num(top.loc[qk, 'mean_good'])}</td>"
        f"<td>{signed(top.loc[qk, 'beta_obs'], 2)}</td><td>{pval(top.loc[qk, 'p_wcb'])}</td>"
        f"<td>{signed(ev.loc[qk, 'beta_obs'], 2)}</td><td>{pval(ev.loc[qk, 'p_wcb'])}</td></tr>"
        for qk in SHOWN_QKEYS)
    arm_rows = []
    for s, contrast, label in (("pilot_nonmoral", "moral_vs_rest", "moral vs prudential + procedural"),
                               ("pilot_foundations", "harm_vs_rest", "harm vs the other four")):
        t = _csv(f"first_look/jevnat_{s}_arm_effects.csv")
        e = _csv(f"first_look/jevnat_{s}_ev_arm_effects.csv")
        for qk in ("intentionality", "blame"):
            rt = t[(t.qkey == qk) & (t.arm == contrast)].iloc[0]
            re_ = e[(e.qkey == qk) & (e.arm == contrast)].iloc[0]
            arm_rows.append(f"<tr><td>{SET_LABEL[s]}</td><td>{qk}, {label}</td><td>{signed(rt.beta_obs, 2)}</td>"
                            f"<td>{pval(rt.p_wcb)}</td><td>{signed(re_.beta_obs, 2)}</td><td>{pval(re_.p_wcb)}</td></tr>")
    return f"""
<section>
  <h2>The tests</h2>
  <h3>Ngo's 80 items (40 storylines), normal wordings</h3>
  <div class="scroll"><table><thead><tr><th>question</th><th>harmful</th><th>helpful</th><th>gap</th><th>p</th>
  <th>gap, average</th><th>p</th></tr></thead><tbody>{ngo}</tbody></table></div>
  <h3>Is the gap bigger for moral content? (all wordings)</h3>
  <p>Positive means a bigger harmful-vs-helpful gap in the moral (or harm) arm than in the others.</p>
  <div class="scroll"><table><thead><tr><th>set</th><th>contrast</th><th>filled bubble</th><th>p</th><th>average</th>
  <th>p</th></tr></thead><tbody>{"".join(arm_rows)}</tbody></table></div>
  <p class="note">Wild cluster bootstrap, B = 1999, clustered by storyline (lib.wild_cluster_bootstrap via
  analysis/first_look.sign_effects and analysis/arm_effects). p-values unadjusted. For intentionality the moral arm
  is not reliably bigger (and on the average the harm arm is smaller); blame is bigger for harm on both readouts.</p>
</section>"""


def section_verbatims(data) -> str:
    cards = []
    for s, prefix, why in PAIRS:
        items = data["items"][s]
        bad, good = items[f"{prefix}-bad"], items[f"{prefix}-good"]
        cols = []
        for item, title in ((bad, "Harmful side effect"), (good, "Helpful side effect")):
            blocks = "".join(f'<div class="qrow"><div class="qlabel">{QLABEL[qk]}</div>'
                             f'{answer_block(*question(data, s, item.item_id, qk))}</div>' for qk in SHOWN_QKEYS)
            cols.append(f'<div class="col"><h4>{title}</h4><blockquote>{E(item.scenario)}</blockquote>{blocks}'
                        f'<p class="ids">{E(item.item_id)}</p></div>')
        cards.append(f'<article class="card"><header><span class="tag">{SET_LABEL[s]} · {ARM_LABEL[bad.arm]}</span>'
                     f'<p class="why">{E(why)}</p></header><div class="cols">{"".join(cols)}</div></article>')
    return f"""
<section>
  <h2>Verbatims</h2>
  <p>The scenarios and questions exactly as Jev saw them, with its answers. Each small chart is Jev's probability on the
  eleven bubbles: the highlighted bar is the bubble it filled, and the orange marker is the average over its probabilities. Pairs
  were picked by hand to show the pattern, a case without it, and a nuance; the reason is on each card.</p>
  <div class="legend"><span><i class="sw sw-top"></i>filled bubble</span><span><i class="sw sw-rest"></i>other bubbles</span>
  <span><i class="sw sw-ev sw-tri"></i>average (EV)</span></div>
  {"".join(cards)}
</section>"""


def section_caveats(data) -> str:
    agree = pd.concat([_csv(f"checks/jevnat_{s}/anchor_agreement.csv") for s in SETS])
    rng = {qk: (agree[agree.qkey == qk]["r"].min(), agree[agree.qkey == qk]["r"].max()) for qk in SHOWN_QKEYS}
    fmt = lambda lo, hi: f"{lo:.2f} to {hi:.2f}".replace("-", "−")  # noqa: E731
    q1, a1 = question(data, "ngo_verbatim", "kmp-nv-002-moral-bad", "praise", "w1")
    q3, a3 = question(data, "ngo_verbatim", "kmp-nv-002-moral-bad", "praise", "w3r")
    retest = pd.concat([_csv(f"checks/jevnat_retest_{s}.csv").query("qkey == 'all'") for s in SETS])
    repeat = f'{retest["top_same"].min():.1%}–{retest["top_same"].max():.1%}'
    evr = retest["ev_r"].min()
    flip = ""
    first = data["answers_first_run"]
    if first:
        now = data["answers"]["ngo_verbatim"]
        same = [j for j in now if j in first and first[j]["body_sha256"] == now[j]["body_sha256"]]
        j = max(same, key=lambda j: abs(first[j]["ev"] - now[j]["ev"]))
        q = data["questions"]["ngo_verbatim"][j]
        flip = f"""
  <div class="pair2">
    <div><h4>First run</h4>{answer_block(q, first[j])}</div>
    <div><h4>Second run, same request</h4>{answer_block(q, now[j])}</div>
  </div>
  <p class="note">The Ngo question whose average moved most between the two runs (the worst case, not a typical
  one{", on a reversed wording" if q.reversed else ""}), from
  <span class="ids">{E(q.item_id)}</span>: “{E(data["items"]["ngo_verbatim"][q.item_id].scenario)}”</p>"""
    return f"""
<section id="caveats">
  <h2>Caveats</h2>
  <h3>Jev reads reversed praise scales backwards</h3>
  <p>Each question also had a reversed wording, with 0 at the strong end. Jev follows reversed intentionality scales
  (agreement with the normal wording r = {fmt(*rng["intentionality"])}) and partly follows reversed blame
  (r = {fmt(*rng["blame"])}). It reads reversed praise backwards (r = {fmt(*rng["praise"])}): it fills 0 meaning
  "none", where 0 now means "extremely". That is why the headline numbers use the normal wordings. The same harmful
  CEO, both praise wordings:</p>
  <div class="pair2"><div><h4>Normal wording: 0 means "not at all"</h4>{answer_block(q1, a1)}</div>
  <div><h4>Reversed wording: 0 means "extremely"</h4>{answer_block(q3, a3)}</div></div>
  <p class="note">On the reversed sheet Jev again fills 0, which as written says the CEO is extremely praiseworthy.</p>
  <h3>Jev is not deterministic</h3>
  <p>5,426 questions were asked word for word in two runs. Jev filled the same bubble {repeat} of
  the time, and its average barely moved (r ≥ {evr:.3f}). Big effects are unaffected, but a small effect's filled-bubble
  p-value can cross .05 between runs, so the average is the readout to quote for small effects.</p>{flip}
  <h3>Other limits</h3>
  <ul>
    <li>The filled bubble snaps to the ends of the scale, which is why its gaps (about 9) are bigger than the averages'
    (about 5–6). The average is the closer match to a chat model's mean answer.</li>
    <li>The pilot items were run as drafted, not yet reviewed.</li>
    <li>This report does not compare Jev with the chat models or with people.</li>
  </ul>
</section>"""


def section_provenance() -> str:
    ref = _last_commit("first_look/jevnat_ngo_verbatim_sign_effects.csv")
    return f"""
<section class="prov">
  <h2>Where the numbers come from</h2>
  <ul>
    <li>Tables: <code>outputs/first_look/jevnat_*</code> and <code>outputs/checks/jevnat_*</code>, as of commit
    <code>{E(ref)}</code>, written by <code>tools/jev_native.py analyze</code> and <code>retest</code>.</li>
    <li>Question sheet: <code>kmp/jev_native.py</code>; answers: <code>outputs/elicit/jev_native_&lt;set&gt;.jsonl</code>
    (local; their manifests, with every request's hash, are committed).</li>
    <li>This page: <code>tools/jev_native_report.py</code>. Full write-up: <code>docs/JEV_NATIVE.md</code>.</li>
  </ul>
</section>"""


# --- page ---------------------------------------------------------------------------------

CSS = """
:root{--page:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#6f6e69;--grid:#e1e0d9;--base:#c3c2b7;
--ring:rgba(11,11,11,.10);--top:#2a78d6;--rest:#b7d3f6;--ev:#eb6834;--code:#f0efec;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--page:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;
--ink2:#c3c2b7;--muted:#9a9890;--grid:#2c2c2a;--base:#383835;--ring:rgba(255,255,255,.10);--top:#3987e5;--rest:#184f95;
--ev:#d95926;--code:#232321;color-scheme:dark}}
:root[data-theme="dark"]{--page:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--muted:#9a9890;--grid:#2c2c2a;
--base:#383835;--ring:rgba(255,255,255,.10);--top:#3987e5;--rest:#184f95;--ev:#d95926;--code:#232321;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:920px;margin:0 auto;padding:32px 16px 64px}
h1{font-size:1.9rem;line-height:1.2;margin:0 0 6px}h2{font-size:1.3rem;margin:44px 0 10px}
h3{font-size:1rem;margin:24px 0 8px}h4{font-size:.9rem;margin:0 0 8px;color:var(--ink2)}
p{margin:0 0 12px}.meta{color:var(--ink2);font-size:.9rem;margin-bottom:24px}.lede{font-size:1.08rem}
.note{color:var(--ink2);font-size:.88rem}a{color:var(--top)}
code,pre{font:13px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace}code{background:var(--code);padding:1px 4px;border-radius:4px}
pre{background:var(--code);padding:12px;border-radius:8px;white-space:pre-wrap;overflow-wrap:anywhere}pre code{padding:0;background:none}
.tiles-title{color:var(--ink2);font-weight:600}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin:8px 0 10px}
.tile{background:var(--surface);border:1px solid var(--ring);border-radius:10px;padding:14px 16px}
.tile-label{color:var(--ink2);font-size:.88rem}.tile-value{font-size:2rem;font-weight:600;line-height:1.2}
.tile-note{color:var(--ink2);font-size:.84rem}
table{border-collapse:collapse;width:100%;font-size:.9rem;font-variant-numeric:tabular-nums;margin:6px 0 10px}
th,td{text-align:left;padding:6px 10px 6px 0;border-bottom:1px solid var(--grid)}th{color:var(--ink2);font-weight:600}
.scroll{overflow-x:auto}details{margin:10px 0}summary{cursor:pointer;color:var(--ink2);font-size:.9rem}
.legend{display:flex;flex-wrap:wrap;gap:16px;font-size:.85rem;color:var(--ink2);margin:6px 0 10px}
.legend span{display:inline-flex;align-items:center;gap:6px}
.sw{display:inline-block;width:12px;height:12px;border-radius:3px}.sw-top{background:var(--top)}
.sw-ev{background:var(--ev)}.sw-rest{background:var(--rest)}
.sw-tri{width:0;height:0;border-radius:0;background:none;border-left:6px solid transparent;border-right:6px solid transparent;
border-bottom:9px solid var(--ev)}
.panels{display:grid;grid-template-columns:1fr 1fr;gap:28px}.panels>*,.cols>*,.pair2>*,.tiles>*{min-width:0}
code{overflow-wrap:anywhere}
.panel{background:var(--surface);border:1px solid var(--ring);border-radius:10px;padding:14px 16px}
.panel h3{margin:0 0 6px}
.axis-top{display:flex;justify-content:space-between;margin-left:42%;font-size:.75rem;color:var(--muted)}
.group{font-size:.78rem;color:var(--muted);margin:10px 0 2px;text-transform:uppercase;letter-spacing:.04em}
.row{display:flex;align-items:center;gap:8px;margin:3px 0}
.row-label{width:42%;font-size:.84rem;color:var(--ink2);flex:none}
.track{flex:1;display:flex;flex-direction:column;gap:2px;padding:2px 0;border-left:1px solid var(--base);
background:linear-gradient(to right,transparent calc(50% - .5px),var(--grid) calc(50% - .5px),var(--grid) calc(50% + .5px),transparent calc(50% + .5px))}
.hb{display:block;height:9px;border-radius:0 4px 4px 0;outline-offset:2px}.hb-top{background:var(--top)}
.hb-ev{background:var(--ev)}
.card{background:var(--surface);border:1px solid var(--ring);border-radius:12px;padding:16px;margin:18px 0}
.card header{margin-bottom:12px}.tag{font-size:.78rem;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.why{margin:4px 0 0}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:20px}
blockquote{margin:0 0 12px;padding:8px 12px;border-left:3px solid var(--base);color:var(--ink);font-size:.93rem;background:var(--page);
border-radius:0 6px 6px 0}
.qrow{display:grid;grid-template-columns:92px 1fr;gap:8px;margin:10px 0}.qlabel{font-size:.84rem;font-weight:600;padding-top:2px}
.q{font-size:.82rem;color:var(--ink2);margin:0 0 6px}.a{font-size:.84rem;margin:4px 0 0}
.mini{max-width:240px}.mini-plot{display:flex;align-items:flex-end;gap:2px;height:44px;border-bottom:1px solid var(--base)}
.mb{flex:1;max-width:24px;background:var(--rest);border-radius:4px 4px 0 0}.mb-top{background:var(--top)}
.mini-axis{position:relative;font-size:.7rem;color:var(--muted);height:24px}
.ev{position:absolute;top:0;width:0;height:0;margin-left:-6px;border-left:6px solid transparent;border-right:6px solid transparent;
border-bottom:9px solid var(--ev)}
.mini-axis span{position:absolute;top:9px;transform:translateX(-50%)}
.ids{font:12px ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--muted)}
.pair2{display:grid;grid-template-columns:1fr 1fr;gap:20px;background:var(--surface);border:1px solid var(--ring);
border-radius:10px;padding:14px 16px;margin:8px 0 12px}
ul{padding-left:20px}li{margin:4px 0}
.prov{font-size:.9rem;color:var(--ink2)}
#tip{position:fixed;pointer-events:none;background:var(--ink);color:var(--page);font-size:.8rem;padding:4px 8px;border-radius:6px;
opacity:0;transition:opacity .08s;z-index:10;white-space:nowrap}
@media (max-width:680px){.panels,.cols,.pair2{grid-template-columns:1fr}.qrow{grid-template-columns:1fr}h1{font-size:1.6rem}}
"""

JS = """
(function(){var t=document.getElementById('tip');function show(el,x,y){t.textContent=el.getAttribute('data-tip');
t.style.opacity=1;var w=t.offsetWidth,h=t.offsetHeight;t.style.left=Math.max(8,Math.min(innerWidth-w-8,x-w/2))+'px';
t.style.top=Math.max(8,y-h-10)+'px'}function hide(){t.style.opacity=0}
document.addEventListener('pointerover',function(e){var el=e.target.closest('[data-tip]');if(el)show(el,e.clientX,e.clientY)});
document.addEventListener('pointermove',function(e){var el=e.target.closest('[data-tip]');if(el)show(el,e.clientX,e.clientY);else hide()});
document.addEventListener('pointerout',function(e){if(!e.relatedTarget||!e.relatedTarget.closest||!e.relatedTarget.closest('[data-tip]'))hide()});
document.addEventListener('focusin',function(e){var el=e.target.closest('[data-tip]');if(el){var r=el.getBoundingClientRect();
show(el,r.left+r.width,r.top)}});document.addEventListener('focusout',hide)})();
"""


def build() -> str:
    data = load()
    body = "".join([section_summary(data), section_method(data), section_figure(), section_tests(),
                    section_verbatims(data), section_caveats(data), section_provenance()])
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Knobe Effect in Jev</title><style>{CSS}</style></head>
<body><main>
<h1>The Knobe effect in Jev</h1>
<p class="meta">Jev (<code>typesafe/jev-1.14-20261014</code>) answering the study's questions itself, with no wrapper ·
run 2026-11-12 · knobe_moral_probe study</p>
{body}
</main><div id="tip" role="tooltip"></div><script>{JS}</script></body></html>
"""


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--out", type=Path, default=STUDY / "docs" / "JEV_NATIVE_REPORT.html")
    a = p.parse_args(argv)
    a.out.write_text(build(), encoding="utf-8")
    print(f"wrote {a.out} ({a.out.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
