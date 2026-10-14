"""Read the rating a model wrote (DESIGN.md readout: "the number the model
writes, parsed from sampled text"), and nothing else.

Why not knobe.parsing.parse_rating: it takes the first whole number 0-10
anywhere in the reply, which is right for a bare "7" but wrong once replies
are longer -- "I cannot provide a number from 0 to 10" and "A score of 0 on
this scale would indicate..." both come back as 0. In the 2026-10-12/13
OpenRouter runs that misread 0.4% of Llama-3.1-8B-Instruct's replies, almost
all as 0. knobe.parsing stays unchanged, so the pilots' and main run's
published parsing is untouched; kmp uses this instead.

extract_rating(text) -> (value | None, ok, rule):
  1. normalize: drop markdown emphasis/heading marks, keep line breaks;
  2. mask scale restatements ("0 to 10", "0-10", "from 0 (not at all) to 10
     (extremely)", "scale of 0") so their numbers can't be read as answers;
  3. collect candidates:
       leading     the reply starts with the number (optionally "Answer:")
       phrase      an explicit answer: "the answer (to this question) is/would be N",
                   "Answer: N", a labelled line ("Praiseworthy: 3", "Rating: 4"),
                   "I would answer/rate/say/give ... N", "my rating is N",
                   "a level/degree of N", "N/10", "N out of 10"
       final_line  the last non-empty line is just the number (not a "1." list marker)
       first_number  fallback, only if nothing above matched: the first standalone
                   number on the first line, ended by punctuation, a bracket or the
                   line end ("the CEO deserves 0", "Stanley is 7 ("), not "5 people"
                   and not scale talk ("from 0 to...", "where 0 means...")
  4. one distinct value -> (value, True, first rule that found it);
     several values -> (None, False, "ambiguous");
     none -> (None, False, "blank" | "refusal" | "no_number");
     a reply opening a numbered list that answers the worked examples ("1. The child
     has...") or shows a second item ("2.") -> (None, False, "list"); a lone
     "1. Jared intentionally..." is an answer of 1 followed by an explanation.
Numbers 0-10 count, decimals included (8.5, which the schema stores as a float);
"15", "10.5" and "-1" are not ratings.
"""
from __future__ import annotations

import re

_N = r"(10(?:\.0+)?|[0-9](?:\.[0-9]{1,2})?)(?![0-9]|[.,][0-9])"   # 0-10, decimals allowed (8.5); not 15 or 10.5
_MARKDOWN = re.compile(r"[*_#`>]+")
_RANGE = r"(?:0|zero)\s*(?:\([^)]*\)?\s*)?(?:to|-|–|through)\s*(?:10|ten|1\b|$)(?:\s*\([^)]*\)?)?"
_SCALE = re.compile(
    rf"\bscale\s+(?:of|from)\s+{_RANGE}|\bscale\s+of\s+(?:0|zero)\b|\b(?:from\s+)?{_RANGE}",
    re.IGNORECASE,
)
_LEADING = re.compile(rf"^\W*(?:answer\s*[:\-]\s*)?{_N}(?!\w)(?![.)]\s+[A-Za-z])", re.IGNORECASE)
_END = r"(?=[\"'”]?\s*(?:$|[.,;:!?)(\]]|\n))"   # the number ends the clause: "is 0.", "as 10 (", not "3 people"
_LABELS = (r"(?:answer|rating|score|level|blame(?:worthy|worthiness)?|praise(?:worthy|worthiness)?"
           r"|intentional(?:ity)?|significance)")
_PHRASES = [
    re.compile(rf"\banswer\b(?:[^0-9\n]{{0,25}}?\b(?:is|would\s+be|will\s+be))?\s*[:=]?\s*[\"'“]?{_N}(?!\w)",
               re.IGNORECASE),
    re.compile(rf"^\W*{_LABELS}[^:\n0-9]{{0,20}}:\s*{_N}(?!\w)", re.IGNORECASE | re.MULTILINE),
    re.compile(rf"\b(?:level|degree|extent)\s+of\s+{_N}(?!\w)", re.IGNORECASE),
    re.compile(rf"\bI(?:'d|\s+would|\s+will|'ll)?\s+(?:answer|rate|say|give|score|choose|pick|go\s+with)\b"
               rf"[^0-9\n]{{0,60}}?(?<![\w.]){_N}(?!\w)", re.IGNORECASE),
    re.compile(rf"\b(?:rate|rated|rating|score|scored)\b[^0-9\n]{{0,120}}?\bas\s+(?:an?\s+)?[\"'“]?{_N}{_END}",
               re.IGNORECASE),
    # "The extent to which this side effect is ..., on a <scale>, is 0." / '... is "0" (not at all)'
    re.compile(rf"\b(?:extent|degree|level|rating|score)\b[^0-9\n]{{0,160}}?\bis\s*:?\s*(?:an?\s+)?[\"'“]?{_N}{_END}",
               re.IGNORECASE),
    re.compile(rf"\bmy\s+(?:rating|score|answer)\s*(?:is|would\s+be|:)?\s*{_N}(?!\w)", re.IGNORECASE),
    re.compile(rf"(?<![\w.]){_N}\s*/\s*1(?:0\b|$)"),
    re.compile(rf"(?<![\w.]){_N}\s+out\s+of\s+1(?:0\b|$)", re.IGNORECASE),
]
_FINAL_LINE = re.compile(rf"^\W*{_N}\W*$")
_LIST_MARKER = re.compile(r"^\s*1[.)]\s*$")      # "Here's why:\n\n1." starts a list, it isn't a rating
# A reply that opens a numbered list is answering the worked examples one by one, not the question.
_LIST_START = re.compile(r"^\W*1[.)](?:\s|$)")
_LIST_EVIDENCE = re.compile(r"(?m)^\s*2(?:[.)](?:\s|$)|\s*$)|\b(?:apples?|dots?|die|dice|players?|practice|counting)\b",
                            re.IGNORECASE)
# Fallback: the first standalone number on the first line, ended by punctuation, a bracket or the line end
# ("the CEO deserves 0", "Stanley is 7 (", 'answer "0"'), but not "5 people" or a cut-off "from 0 to...".
_ANY = re.compile(rf"(?<![\w.]){_N}(?!\w)")
_FIRST = re.compile(rf"(?<![\w.]){_N}(?=\s*(?:$|[.,;:!?)(\"\'\]]))")
_REFUSAL = re.compile(r"^\W*(?:I\s+(?:cannot|can'?t|am\s+unable|'m\s+unable|won'?t|will\s+not|do\s+not|don'?t)"
                      r"|unfortunately|sorry)", re.IGNORECASE)


def _num(s: str) -> int | float:
    return float(s) if "." in s else int(s)


def extract_rating(text: str) -> tuple[int | float | None, bool, str]:
    raw = text or ""
    if not raw.strip():
        return None, False, "blank"
    norm = _MARKDOWN.sub("", raw).strip()
    if _LIST_START.match(norm) and _LIST_EVIDENCE.search(norm):
        return None, False, "list"
    found: list[tuple[str, float]] = []
    # "N/10" and "N out of 10" are answers, so read them before scale masking.
    for pat in _PHRASES[-2:]:
        for m in pat.finditer(norm):
            found.append(("phrase", _num(m.group(1))))
    masked = _SCALE.sub(" <scale> ", norm)
    m = _LEADING.match(masked)
    if m:
        found.append(("leading", _num(m.group(1))))
    elif _LIST_START.match(masked):
        found.append(("leading", 1))      # "1. Jared intentionally..." = 1; conflicts with any later answer
    for pat in _PHRASES[:-2]:
        for m in pat.finditer(masked):
            found.append(("phrase", _num(m.group(1))))
    lines = [ln for ln in masked.splitlines() if ln.strip()]
    if lines:
        m = _FINAL_LINE.match(lines[-1])
        opens_list = len(lines) > 1 and lines[-2].rstrip().endswith(":") and m and _num(m.group(1)) == 1
        if m and not _LIST_MARKER.match(lines[-1]) and not opens_list:
            found.append(("final_line", _num(m.group(1))))
    if not found:
        first_line = masked.splitlines()[0] if masked else ""
        # Two standalone 0-10 numbers on the line ("A 9 or 10.", "formats (1-3") is a range, not an answer.
        if len({x for x in _ANY.findall(first_line)}) > 1:
            return None, False, "ambiguous"
        for m in _FIRST.finditer(first_line):
            if not re.search(r"\b(?:from|where|between|out\s+of)\s*$", first_line[: m.start()], re.IGNORECASE):
                found.append(("first_number", _num(m.group(1))))
                break
    values = {v for _, v in found}
    if len(values) == 1:
        return values.pop(), True, found[0][0]
    if len(values) > 1:
        return None, False, "ambiguous"
    return None, False, "refusal" if _REFUSAL.search(norm) else "no_number"
