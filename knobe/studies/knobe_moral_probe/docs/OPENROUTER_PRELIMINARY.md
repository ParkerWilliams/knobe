# Preliminary analysis: OpenRouter runs on all vignettes (2026-10-13)

**Status: indicative, not the study's results.** Two of the three models are
stand-ins for the study's, there are no pretrained models, and the pilot
vignettes are the August texts, not the adapted items `DESIGN.md` specifies.
This is not the `FIRST_LOOK.md` go/no-go, which names the study's models.
Run by Parker (with Claude) while cluster access is pending.

## What was run

- **Models** (instruct only; OpenRouter, each pinned to one provider, no
  fallbacks): Llama-3.1-8B-Instruct (the study's own instruct checkpoint;
  DeepInfra, fp8), Gemma-3-4B-it (DeepInfra, bf16), Mistral-Nemo (Io Net,
  fp16). Llama-3.2-1B was tried first and dropped after a smoke test (34%
  numeric answers). OpenRouter serves none of the study's pretrained
  checkpoints, nor Gemma-2-9B or Mistral-7B-v0.1.
- **Protocol:** kmp unchanged, apart from swapping the engine for OpenRouter
  (`tools/openrouter_first_look.py`). That means kmp's prompts, worked
  examples, 168 samples per item, seed and temperature rule, chat format and
  `MAX_TOKENS=10`, with parsed ratings only (no logprobs).
- **Vignettes:**
  - Ngo's 80 originals word for word (`stimuli/ngo_verbatim.csv`), with and
    without worked examples: 80,640 answers.
  - The August pilots' 240 nonmoral items (Ngo's 80 moral plus Mer's 80
    prudential and 80 procedural) and 152 moral-foundations items, converted
    unchanged by `tools/pilot_items_to_kmp.py` into `stimuli/pilot/` as
    `draft` items: 182,304 answers, with worked examples only.
- **Totals:** 262,944 answers, about $3, about 12 hours of wall time (mostly
  provider rate limiting).

Notation: bad minus good mean rating; * means wild-cluster-bootstrap p < .05
(unadjusted unless stated, clustered by storyline). For praise the expected
sign is negative.

## 1. Ngo's 80 originals (the first-look question)

| model | intentionality | blame | praise | numeric answers |
|---|---:|---:|---:|---:|
| gemma-3-4b-instruct | +1.21* (p=0.000) | +0.50* | -0.39* | 100%–100% |
| llama-3.1-8b-instruct | +0.37 (p=0.475) | +2.62* | -1.05* | 9%–38% |
| mistral-nemo-instruct | +0.79* (p=0.016) | +1.39* | -0.50* | 34%–71% |

Go/no-go rule applied to these stand-ins: the intentionality effects, ordered
by Holm-adjusted p, are gemma-3-4b-instruct +1.21 (Holm p=0.000); mistral-nemo-instruct +0.79 (Holm p=0.032); llama-3.1-8b-instruct +0.37 (Holm p=0.475).
Two models are positive and significant, but Mistral-Nemo fails the
at-least-90% numeric-answer gate, so only Gemma counts. That is exactly 1 of 3:
**"discuss"**.

## 2. All pilot vignettes, pooled within each set

**Nonmoral set (240 items, 40 storylines)**

| model | intentionality | blame | praise | numeric (intent.) |
|---|---:|---:|---:|---:|
| gemma-3-4b-instruct | +0.38* | +0.96* | -0.58* | 100% |
| llama-3.1-8b-instruct | +1.08* | +1.99* | -1.65* | 24% |
| mistral-nemo-instruct | +1.04* | +2.17* | -1.45* | 53% |

**Moral-foundations set (152 items, 34 storylines)**

| model | intentionality | blame | praise | numeric (intent.) |
|---|---:|---:|---:|---:|
| gemma-3-4b-instruct | +1.21* | +0.62* | -0.54* | 100% |
| llama-3.1-8b-instruct | +1.34* | +0.79* | -2.01* | 26% |
| mistral-nemo-instruct | +1.28* | +1.05* | -1.69* | 53% |

Every model shows the Knobe pattern in both sets: bad side effects are rated
more intentional, more blameworthy and less praiseworthy.

## 3. By arm: the pilots' own questions

**Nonmoral, intentionality** (40 storylines per arm)

| model | moral | prudential | procedural | moral vs rest |
|---|---:|---:|---:|---:|
| gemma-3-4b-instruct | +1.26* | -1.27* | +1.14* | +1.32* |
| llama-3.1-8b-instruct | +1.38* | +1.58* | +0.08 | +0.45 |
| mistral-nemo-instruct | +1.72* | +1.18* | +0.42 | +0.96* |

**Nonmoral, blame**

| model | moral | prudential | procedural | moral vs rest |
|---|---:|---:|---:|---:|
| gemma-3-4b-instruct | +0.57* | +0.80* | +1.51* | -0.59* |
| llama-3.1-8b-instruct | +1.78* | +1.70* | +2.48* | -0.31 |
| mistral-nemo-instruct | +1.35* | +2.20* | +2.83* | -1.19* |

**Foundations, intentionality** (storylines: harm 30, authority/fairness/loyalty 13 each, purity 7)

| model | harm | authority | fairness | loyalty | purity | harm vs rest |
|---|---:|---:|---:|---:|---:|---:|
| gemma-3-4b-instruct | +1.74* | +1.85* | +1.06 | -0.18 | +0.58 | +0.88* |
| llama-3.1-8b-instruct | +1.76* | +1.69 | +1.24 | +1.18 | +0.09 | +0.69 |
| mistral-nemo-instruct | +1.43* | +2.05* | +0.04 | +0.83 | +2.19* | +0.24 |

**Foundations, blame**

| model | harm | authority | fairness | loyalty | purity | harm vs rest |
|---|---:|---:|---:|---:|---:|---:|
| gemma-3-4b-instruct | +0.65* | +0.42* | +0.48* | +0.61* | +1.08* | +0.06 |
| llama-3.1-8b-instruct | +0.66 | +1.16* | +0.54 | +1.27* | +0.57 | -0.24 |
| mistral-nemo-instruct | +0.97* | +1.12* | +0.24 | +1.10* | +2.01* | -0.14 |

Reading (exploratory):
- **Nonmoral, intentionality:** the moral-vs-rest contrast is significant for
  Gemma and Mistral-Nemo but not Llama, and it means different things in the
  two models.
  - **Mistral-Nemo:** the moral effect really is the largest (+1.72, against
    +1.18 prudential and +0.42 procedural).
  - **Gemma:** the contrast comes from its *reversal* on prudential items
    (−1.27, rating the good self-regarding outcome as more intentional). Its
    moral and procedural effects are similar (+1.26 vs +1.14).
  - **Llama:** procedural is null (+0.08), with moral and prudential alike.
- **Nonmoral, blame:** the moral arm has a *smaller* bad-vs-good gap than the
  nonmoral arms for Gemma and Mistral-Nemo. That is the same direction as
  CLAIMS.md claim 9 from the August pilots (models and prompt format differ
  here).
- **Foundations:** harm gives the most consistent intentionality effect, and
  authority is also strong. Only Gemma's harm effect is significantly larger
  than the other foundations'. Fairness, loyalty and purity have 7–13
  storylines each, so those cells are imprecise.

## 4. Answer quality

- **Numeric answers:** at most 61% for Llama and Mistral-Nemo on the pilot
  items, 9–71% on the Ngo set. kmp's chat format with `MAX_TOKENS=10` lets
  them begin in words ("I cannot provide…", "Based on the scenario…") and run
  out of tokens before giving a number. Gemma gives a number 100% of the
  time. **The study's own Llama-3.1-8B-Instruct would likely fail the
  number-rate gate under the current protocol**; `MAX_TOKENS` is already
  marked "revisited in the pilot" in `kmp/protocol.py`.
- **Lopsided answer loss**, as numeric-answer rate on bad items minus good
  items (`outputs/first_look/or_parse_rate_by_sign.csv`):

  | model | range across runs and questions |
  |---|---:|
  | gemma-3-4b-instruct | +0.00 to +0.00 |
  | llama-3.1-8b-instruct | -0.00 to +0.08 |
  | mistral-nemo-instruct | +0.06 to +0.22 |

  Mistral-Nemo answers bad items more often than good ones, by up to 22
  points for praise, so its estimates (praise above all) may carry selection
  bias. Llama is close to balanced; Gemma loses nothing.
- **Validity and copying:** validity passes for every model on the Ngo set.
  Copying of the worked examples passes on the Ngo set (the only set with a
  no-examples baseline).

## 5. Implications

1. Before the real run, settle `MAX_TOKENS` and the instruct prompt format
   (Mer's call). Otherwise Llama and similar models fail the number-rate
   gate regardless of their judgments.
2. The pattern is robust enough across substitute models and vignette sets
   to be worth running the study's six models, on the cluster once access
   lands or on a rented GPU.
3. This run used the pilot texts as they were. Mer's adaptation (role nouns,
   aligned goals, rewriting failed pairs, more foundation storylines) is
   still the plan for the real stimuli.

## Provenance

- Code: `tools/openrouter_first_look.py`, `tools/openrouter_models.yaml`,
  `tools/pilot_items_to_kmp.py`, `analysis/arm_effects.py`, plus
  `analysis/first_look.py` and `kmp.checks` unchanged.
- Tables: `outputs/first_look/or_*.csv`, `outputs/checks/or_*/`.
- Run records: `outputs/elicit/or_*.manifest.json` and `*.providers.json`.
- Raw answers: `results_dist/results_knobe_moral_probe_openrouter.tar.gz`.
- Commands: see `ANALYSIS_LOG.md` entries dated 2026-10-12/13.
