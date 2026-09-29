# knobe_moral_probe: references (2026-09-28)

BibTeX for all of these is in this study's `references.bib`, taken from each
publisher's official record (ACL Anthology, arXiv, doi.org), not typed
from memory. Each entry below gives a stable link, what the work shows,
and what it supports or changes in this project. PDFs are not stored in
the repo; every link below is open access.

## The human effect and the stimuli

**Knobe (2003).** *Intentional action and side effects in ordinary
language.* Analysis 63(3):190–194.
[doi:10.1093/analys/63.3.190](https://doi.org/10.1093/analys/63.3.190).
The original finding: people judge a harmful foreseen side effect as
intentional far more often than a helpful one. Key: `Knobe_2003`.

**Ngo et al. (2015).** *Two Distinct Moral Mechanisms for Ascribing and
Denying Intentionality.* Scientific Reports 5:17390.
[doi:10.1038/srep17390](https://doi.org/10.1038/srep17390).
Source of the 40 paired scenarios (80 items) both experiments build on;
local copy of the items at
`analysis/ngo_extensions/nonmoral_pilot/ngo_2015_original_80.txt`. The
human result the models are compared against. Key: `Ngo_2015`.

## The LLM study this paper extends

**Raimondi, Dalbagno & Gabbrielli (2026).** *Analysing Moral Bias in
Finetuned LLMs through Mechanistic Interpretability.*
[arXiv:2510.12229](https://arxiv.org/abs/2510.12229).
Reports the Knobe effect emerging in finetuned LLMs, using Ngo's items.
What their paper specifies about elicitation (checked 2026-09-28):
- A fixed prompt, "Read carefully the following scenario and then answer
  the question with a number from 0 to 10", held constant across
  conditions.
- Temperature drawn from U(0.85, 1.15), 283 generations per model.

What it does **not** specify: whether chat templates or system prompts
were used, how ratings were extracted (text vs token probabilities), how
unparseable answers were handled, or parse rates. No public code found.
So this repo's statement that raw completion "matches how Raimondi
queried their models" (`nonmoral_pilot/elicit.py` docstring) is our
inference, and the paper should say so. Key:
`raimondi2026analysingmoralbiasfinetuned`.

## Eliciting ratings and judgments from LLMs

**Wang et al. (2024).** *"My Answer is C": First-Token Probabilities Do
Not Match Text Answers in Instruction-Tuned Language Models.* Findings of
ACL 2024, 7407–7416.
[aclanthology.org/2024.findings-acl.441](https://aclanthology.org/2024.findings-acl.441/).
For instruction-tuned models, the answer implied by first-token
probabilities often differs from the answer the model writes. Mismatch
exceeds 60%, is worst for models heavily tuned on conversational or safety
data, and persists under constrained prompts.
- **Supports:** reading the written number, not token probabilities
  (design choice A, `DESIGN.md` §6).
- **Changes:** CLAIMS.md claim 1 (logprob-EV scoring is
  question-dependent) is an instance of this known problem, not a new one.
  It has to be cited and framed as extending it to rating scales and the
  question axis. Key: `wang-etal-2024-answer-c`.

**Röttger et al. (2024).** *Political Compass or Spinning Arrow? Towards
More Meaningful Evaluations for Values and Opinions in Large Language
Models.* ACL 2024, 15295–15311.
[aclanthology.org/2024.acl-long.816](https://aclanthology.org/2024.acl-long.816/).
Answers forced into a fixed format differ from unforced ones, change with
how they're forced, and aren't robust to paraphrase.
- **Supports:** testing more than one question wording.
- **A vulnerability** in the single fixed wording used so far. Key:
  `rottger-etal-2024-political`.

**Scherrer et al. (2023).** *Evaluating the Moral Beliefs Encoded in
LLMs.* NeurIPS 2023. [arXiv:2307.14324](https://arxiv.org/abs/2307.14324).
Moral-judgment elicitation with six question forms per scenario (three
templates × two answer orders), sampled at temperature 1, text mapped to
answers, and consistency across forms reported.
- **The model for** adding paraphrased wordings plus reversed scale
  anchors, and reporting agreement across them. Key:
  `scherrer2023evaluatingmoralbeliefsencoded`.

**Dominguez-Olmedo, Hardt & Mendler-Dünner (2024).** *Questioning the
Survey Responses of Large Language Models.* NeurIPS 2024.
[arXiv:2306.07951](https://arxiv.org/abs/2306.07951).
Across 43 models, survey-style answers were governed by ordering and
labeling biases, and trended toward uniformly random once those were
controlled.
- **Supports:** validity checks for pretrained models before their
  ratings are compared with instruct models (for example, blame higher
  for harmful than helpful side effects), not just a parse-rate check.
- **Also supports:** reversing scale anchors. Key:
  `dominguezolmedo2024questioningsurveyresponseslarge`.
