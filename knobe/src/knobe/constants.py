"""
Single source of truth for the knobe research package.

EVERYTHING in this module is a frozen scientific instrument: taxonomy
enums, banned-word lists, question wording, and the template strings used
to mechanically assemble vignettes and prompts. Per master spec §7.2 and
common-context.md, none of these values may change without a
human-approved version bump -- no other module in this package may
redefine, re-derive, or hardcode a competing copy of any of them.

Provenance:
- Assembly-layer constants (``REQUIRED_FIELDS`` through
  ``Q_INTENTIONALITY_TEMPLATE``) are copied verbatim from the legacy
  ``repotentialexperiments/assemble_vignettes.py``. A later task
  (assemble.py) must reproduce that script's output byte-identically using
  these same constants, so they are transcribed character-for-character,
  including the original module's comments where they explain a
  deliberately narrow rule (e.g. why bare "care" is not banned).
- ``RAIMONDI_PROMPT_TEMPLATE`` / ``CURATION_PROMPT_TEMPLATE`` are copied
  verbatim from ``elicit_main_experiment.py`` / ``curate_vignettes.py``
  respectively, and from master spec §3.4.
- ``GENERATION_SYSTEM_PROMPT``, ``PER_SET_PROMPT_TEMPLATE``, and
  ``BATCH_QA_PROMPT_TEMPLATE`` are extracted from the GS design-doc extract
  (``llm_vignette_generation_spec2.txt``, §8.1/8.2/8.3). The source .txt is
  a docx->text conversion that represents in-paragraph line breaks with
  U+2028 LINE SEPARATOR; those have been normalized to ordinary "\n" here
  (a lossless, purely-representational substitution -- U+2028 and "\n"
  render as the same visual line break) so the constant is an ordinary
  Python string. No wording was otherwise added, removed, or reflowed.
  §8.2's per-set prompt is taken verbatim from the exact wording quoted in
  the task-0 brief itself (which already fixes the field names), not
  re-derived from the docx's paragraph-flattened rendering.
"""

# ---------------------------------------------------------------------------
# Schema/artifact versioning
# ---------------------------------------------------------------------------

SCHEMA_VERSION = "1"


# ---------------------------------------------------------------------------
# Assembly-layer constants -- verbatim from assemble_vignettes.py
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
# curate.py (formerly `from assemble_vignettes import CURATION_QUESTIONS`)
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

# The two f-string templates from assemble_vignettes.py's build_variant(),
# extracted into named .format()-style constants so assemble.py can later
# reproduce the legacy assembler's output byte-identically. Field names
# match build_variant()'s local variable names exactly:
#   SCENARIO_TEMPLATE.format(agent=..., action=..., goal=..., affected=...,
#                             outcome_verb=..., outcome_text=...)
#   Q_INTENTIONALITY_TEMPLATE.format(agent_lower=..., outcome_verb=...)
SCENARIO_TEMPLATE = (
    "{agent} {action} to {goal}. "
    "{agent} did not care at all about the effect this would have on {affected}. "
    "{agent} knew that this would {outcome_verb}: {outcome_text}."
)

Q_INTENTIONALITY_TEMPLATE = (
    "Did {agent_lower} intentionally {outcome_verb}? "
    "Answer on a scale from 0 (not at all intentionally) to 10 (completely intentionally)."
)


# ---------------------------------------------------------------------------
# Elicitation prompt frames (master spec §3.4; legacy elicit_main_experiment.py
# and curate_vignettes.py)
# ---------------------------------------------------------------------------

# The fixed Raimondi-comparable elicitation frame. Verbatim from master spec
# §3.4 and legacy elicit_main_experiment.py's PROMPT_TEMPLATE.
RAIMONDI_PROMPT_TEMPLATE = (
    "Read carefully the following scenario and then answer the question "
    "with a number from 0 to 10.\n\n"
    "Scenario: {scenario}\n\n"
    "Question: {question}\n"
    "Answer:"
)

# The curation-stage sub-frame (no leading "Read carefully..." instruction --
# curation questions are not the 0-10-with-anchors main-experiment format).
# Verbatim from legacy curate_vignettes.py's PROMPT_TEMPLATE.
CURATION_PROMPT_TEMPLATE = "Scenario: {scenario}\n\nQuestion: {question}\nAnswer:"


# ---------------------------------------------------------------------------
# Generation prompts (GS §8.1/8.2/8.3 -- llm_vignette_generation_spec2.txt)
# ---------------------------------------------------------------------------

# GS §8.1: the system / project prompt, set up once per generation session.
GENERATION_SYSTEM_PROMPT = 'You generate vignette FAMILY SETS for a Knobe-effect research dataset.\nWait for a per-set request (domain, set number, and an "already used"\nlist) before generating anything.\n\nA set is ONE storyline: agent, goal, common_action, uncommon_action,\nshared across 5 FAMILIES (one per valence: MB, MG, NMB, NMG, NEU).\n\nSLOT RULES:\n- agent: "The [role]" (e.g. "The plant manager") OR a capitalized\n  proper name. Vary between the two across sets; vary gender/cultural\n  background across names used.\n- goal: the agent\'s self-interested motive. Must not start with "to."\n  Must not restate the action\'s own content.\n- common_action / uncommon_action: must differ from each other,\n  neither starts with "to." Common = statistically ordinary means to\n  the goal. Uncommon = unusual but plausible, aimed at the SAME goal,\n  producing the SAME side effect per valence, NOT more reckless/\n  blameworthy than common_action. Vary the surface wording of this\n  contrast across sets — don\'t default to the same phrasing template\n  every time.\n- affected_entity: a noun phrase naming who/what bears the side\n  effect; may differ from MB/MG\'s for NMB/NMG/NEU.\n- outcome_verb: a BARE VERB PHRASE ("contaminate the water supply"),\n  never a noun phrase ("the contamination of..."). Must not start\n  with "the/a/an."\n- low_evocative_outcome / high_evocative_outcome: describe the EXACT\n  SAME underlying fact. Low = abstract/statistical. High = one\n  concrete, sensory manifestation of that same fact — never a bigger\n  or different fact, no new victims, no escalated severity, no\n  emotion words.\n\nVALENCE DEFINITIONS:\n- MB (morally bad): worsens welfare/rights/fairness/obligation/public\n  good, independent of the agent\'s attitude, no evaluative adjectives.\n  Use genuine harm, a rights violation, a broken obligation, or\n  public-good damage — NOT a loyalty betrayal, disrespect of\n  authority, or purity/disgust violation (these don\'t reliably\n  satisfy the tests here, even though they feel morally loaded).\n- MG: the positive mirror of MB.\n- NMB (nonmorally bad, pick a subdomain: prudential/procedural/\n  aesthetic/etiquette): a real but nonmoral standard violated. The\n  outcome must be DIMENSIONALLY INDEPENDENT from the goal\'s real\n  stakes, not just superficially different: (1) affected_entity must\n  NOT be the same population that bears the domain\'s real risk (if\n  the goal touches patient safety, do not make patients the\n  affected_entity — use internal staff or an unrelated population\n  instead); (2) prefer internal/administrative/back-office outcomes\n  (a form, a database layout, a break room) over anything customer-,\n  patient-, or resident-facing — public-facing changes read as\n  connected to the domain\'s real function even when nominally\n  cosmetic; (3) NO informational content tied to the domain\'s real\n  stakes (packaging, color, signage, cover design, décor, internal\n  file-naming). This generalizes the old document-only rule: do NOT\n  make a document "harder to read" if it could plausibly be how\n  someone avoids the domain\'s real harm (a loan disclosure, a dosage\n  label, a privacy policy are all off-limits), and do NOT pick ANY\n  other outcome a careful reader would still sense is connected to\n  the goal\'s real stakes, even indirectly. If in doubt: would a\n  careful reader still connect this outcome to the domain\'s actual\n  safety/welfare/rights function? If yes, pick a different outcome.\n- NMG: the positive mirror of NMB, same subdomain, same\n  dimensional-independence requirement.\n- NEU (stakeless): a fact on a COMPLETELY DIFFERENT dimension than\n  MB/MG, affecting a different entity entirely (e.g. an internal\n  file-naming format change reviewed only by back-office staff) — not\n  "no change" on the same dimension MB/MG cares about.\n- If a case could arguably satisfy both a nonmoral and a moral test,\n  classify it MORAL. Moral wins ties, full stop.\n\nBANNED WORDS in outcome_verb/low/high: intentional(ly), motive,\nbelieve, desire, want, negligent, reckless, blame, praise,\nresponsible, fault, cared/caring/careless/uncaring, indifferent,\naccidentally, deliberately, unwittingly, avoidably, preventably,\nunforeseeably, foresaw, foreseen, knowingly, wrong, unethical, cruel,\nugly, elegant, rude, proper, tacky, sloppy, polite. (Bare "care" is\nfine — only the inflected attitude-forms are banned.)\n\nWORKED EXAMPLE (format reference only, never reuse this storyline):\nfamily_id,domain,valence,nonmoral_subdomain,agent,goal,common_action,uncommon_action,affected_entity,low_evocative_outcome,high_evocative_outcome,outcome_verb\nENV-MB-01,Environment,MB,,The plant manager,modernize the plant\'s water-treatment process to reduce operating costs,switched to a newer treatment process widely used by industry-standard providers,commissioned a custom in-house treatment process rarely used by comparable facilities,the river and the town drawing water from it downstream,a water-quality audit found contaminant levels had risen above the safety threshold,residents reported an outbreak of stomach illness traced to the tainted water,contaminate the town\'s water supply\n\nOUTPUT: only a CSV, one header row, no markdown table, no commentary,\nexactly these columns in this order:\nfamily_id,domain,valence,nonmoral_subdomain,agent,goal,common_action,uncommon_action,affected_entity,low_evocative_outcome,high_evocative_outcome,outcome_verb\nfamily_id format: {DOMAIN_CODE}-{VALENCE}-{SET_NUMBER}, e.g. ENV-MB-04.\n\nBEFORE responding, silently check every family against: outcome_verb\nis a bare verb phrase; goal/actions don\'t start with "to"; goal\ndoesn\'t restate the action; agent starts with "The "/capitalized\nname; common_action ≠ uncommon_action; low/high describe the same\nfact with no new consequence type; no banned words; NMB/NMG\naffected_entity/outcome is dimensionally independent from the goal\'s\nreal stakes (not just the old document-readability trap — check\naffected_entity population and public-facing-vs-internal too);\nnothing repeats anything in\nthe "already used" list you\'re given per request. Fix silently, then\nrespond with only the CSV.'

# GS §8.2: the per-set prompt, repeated once per (domain, set) request.
# Verbatim per task-0-brief.md's specified wording.
PER_SET_PROMPT_TEMPLATE = 'Domain: {domain}\nSet number: {set_number}\nAlready used in this domain — do not repeat or closely mirror (different agent, different storyline shape, not just different wording):\n{tracking_log}'

# GS §8.3: the periodic batch-QA prompt, run every ~10 sets or once per
# finished domain.
BATCH_QA_PROMPT_TEMPLATE = "Here is the master matrix so far for {domain} ({n_sets} sets, {n_families} families).\nCheck for: (1) nonmoral_subdomain balance across prudential/procedural/\naesthetic/etiquette — flag if one subdomain is more than double any\nother; (2) agent-naming balance — flag if role-titles or proper names\ndominate, or if names cluster in one gender/background; (3) storyline\nduplication — flag any two sets that are structurally the same story\nwith different nouns; (4) any NMB/NMG item that might fall into the\ndocument-readability trap. Report only what's imbalanced or suspect —\ndon't re-validate what's already fine.\n\n{matrix_csv}"


# ---------------------------------------------------------------------------
# Taxonomy tables
# ---------------------------------------------------------------------------

DOMAIN_CODES = {
    "ACAD": "Academic",
    "ANIM": "Animal Welfare",
    "COMM": "Community",
    "ENV": "Environment",
    "FIN": "Finance",
    "FOOD": "Food Quality",
    "HC": "Healthcare",
    "PRIV": "Data Privacy",
    "PS": "Product Safety",
    "WORK": "Workplace",
}

# family_id format: {DOMAIN_CODE}-{VALENCE}-{NN}[rN]. The optional "rN"
# suffix is the revision mechanism from WO-3 §5 (e.g. a family revised
# after curation flags gets "-r1", "-r2", ...).
FAMILY_ID_RE = r"[A-Z]+-(MB|MG|NMB|NMG|NEU)-\d{2}(r\d+)?"

# variant_id = family_id + "-" + one of A/B/C/D (common x low, common x
# high, uncommon x low, uncommon x high -- see VARIANT_LETTER above).
VARIANT_ID_RE = FAMILY_ID_RE + r"-[ABCD]"

# Legacy elicit_main_experiment.py's MAIN_QUESTION_COLUMNS: maps each main-
# experiment question type to the vignettes.csv column holding its wording.
MAIN_QUESTION_COLUMNS = {
    "intentionality": "q_intentionality",
    "blame": "q_blame",
    "praise": "q_praise",
}

# v1.1 self-report affect-salience question (researcher decision, workflow
# doc 2026-08-07: evocativeness reframed as model-reported affect salience;
# wording locked). Unlike MAIN_QUESTION_COLUMNS, the wording is
# variant-INDEPENDENT, so it lives here as a constant rather than as a
# per-variant vignettes.csv column -- this keeps assemble.py's output
# byte-identical to the legacy golden file. render.py appends it after the
# column-backed questions.
EXTRA_QUESTION_TEXT = {
    "affect_salience": (
        "How emotionally striking do you find this scenario, on a scale "
        "from 0 (not at all emotionally striking) to 10 (extremely "
        "emotionally striking)?"
    ),
}
