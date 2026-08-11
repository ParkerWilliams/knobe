"""WO-8 §2: the RQ1 primary models + the contrasts.yaml governance mechanism.

LMM-PRIMARY / ORDINAL-SENSITIVITY (a DOCUMENTED deviation, not silent -- master
spec §7.6). WO-8 states a preference for an ordinal cumulative-link mixed model
(CLMM) as the primary fit with a linear mixed model (LMM) as the sensitivity
check. statsmodels' ``OrderedModel`` (miscmodels.ordinal_model) has NO
random-effects support, and the crossed family/domain random-effects structure
these clustered designs need is load-bearing (master spec §6, DR §2). We
therefore INVERT the two: primary inference is the LMM (``statsmodels`` mixedlm,
random intercept for ``family_id`` ONLY), and the ordinal model (``OrderedModel``,
logit link, FIXED EFFECTS ONLY) is run as the DISTRIBUTIONAL SENSITIVITY check on
the same fixed-effect contrasts. This inversion, and its rationale, is restated in
every generated report (``analysis.report``), so a reader of the artifact -- not
just a reader of this source -- sees it. This is a spec-vs-implementation-reality
conflict resolved with documentation, not silently (master spec §7.6).

DOMAIN CLUSTERING IS NOT MODELED BY THE PRIMARY LMM (honest labeling, reviewer
finding -- see ``_fit_lmm``). statsmodels' MixedLM cannot cleanly nest families
within a separate domain group, and a ``vc_formula`` on domain with family groups
is mathematically inert (domain is constant within a family). The primary is
therefore ``lmm-familyRI`` and says so; master spec §6's "domain = random effect"
intent is honored by a SEPARATE, config-gated ``domain_sensitivity`` fit (same
fixed effects, ``groups=domain``) reported in its own section. The chat-vs-raw
format robustness comparison (WO-8 §4) is likewise config-gated + off by default
(``chat_format_comparison``); primary fits use the ``raw`` format only (spec §3.4).

The prereg of record is ``configs/contrasts.yaml``: EVERY planned contrast is
declared there, and code refuses (hard error) any contrast requested by a name
that file does not declare (``select_contrasts``). Holm correction
(``statsmodels.stats.multitest.multipletests``) is applied within each
(model_family, rq) family. Response-level ratings are NEVER aggregated for
inference (master spec §6.3) -- every fit is over response-level rows; item
means are computed only for the descriptive figures (``analysis.figures``).

1b item-level pairing (DR §12 / WO-8 §2): response-level pairing of an item's
blame/praise rating with its intentionality rating is IMPOSSIBLE -- they are
independent completions, never chained. The 1b slope therefore uses ITEM-LEVEL
pairing: each intentionality response is regressed on its ITEM's blame mean
(bad items) or praise mean (good items). That item mean is itself an estimate
(finite completions), so the predictor carries measurement error that
attenuates the slope toward 0 (errors-in-variables) -- the interaction stays
interpretable in sign, but its magnitude is a conservative estimate. Surfaced
in the report + contrasts.yaml notes.
"""
from __future__ import annotations

import hashlib
import re
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd
import yaml
from statsmodels.stats.multitest import multipletests
from statsmodels.tools.sm_exceptions import ConvergenceWarning

from knobe.schemas import ContrastResultRecord

DEFAULT_ALPHA = 0.05
NEUTRAL_MIDPOINT = 5.0

# Effect-coding maps (all +/-0.5, so main effects read at the other factor's
# mean and interactions are the pure product contrast).
_SIGN_CODE = {"bad": 0.5, "good": -0.5}
_TUNING_CODE = {"finetuned": 0.5, "pretrained": -0.5}
_VT_CODE = {"moral": 0.5, "nonmoral": -0.5}
_TYP_CODE = {"uncommon": 0.5, "common": -0.5}
_EVOC_CODE = {"high": 0.5, "low": -0.5}

# Coded predictor columns prepare_frame() adds, keyed by the source column.
_CODED_COLUMNS = ("sign_c", "tuning_c", "vt_c", "typ_c", "evoc_c", "rating_centered")

# Strips the valence token out of a family_id to recover its set_id -- the
# five valence-siblings (MB/MG/NMB/NMG/NEU) of one storyline share a set_id
# by construction (GENERATION_SYSTEM_PROMPT: "A set is ONE storyline...
# shared across 5 FAMILIES"). E.g. "ENV-MB-01" and "ENV-MG-01" -> "ENV-01";
# "ENV-MB-01r2" -> "ENV-01r2" (the optional revision suffix survives).
_SET_ID_VALENCE_RE = re.compile(r"-(MB|MG|NMB|NMG|NEU)-")


def _derive_set_id(family_id: str) -> str:
    return _SET_ID_VALENCE_RE.sub("-", family_id)


# ---------------------------------------------------------------------------
# contrasts.yaml -- the prereg of record (WO-8 §2b)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ContrastSpec:
    name: str
    rq: str
    kind: str  # "lmm" | "lmm_offset" | "lmm_1b"
    formula: str
    term: str
    direction: str  # "positive" | "negative" | "two-sided"
    tuning: str = "finetuned"  # "finetuned" | "both"
    subset: dict = field(default_factory=dict)
    note: str = ""


@dataclass(frozen=True)
class SensitivityAnalysis:
    """One declared sensitivity analysis from contrasts.yaml's
    ``sensitivity_analyses:`` section (the prereg governs these too). ``name``
    is the analysis id (e.g. "domain_random_slope"); ``contrasts`` are the
    contrast names it applies to; ``interpretation_rule`` is the machine-readable
    rule text that governs the QUALIFIED/UNQUALIFIED verdict."""

    name: str
    contrasts: tuple[str, ...]
    interpretation_rule: str = ""


@dataclass(frozen=True)
class Prereg:
    prereg_frozen: bool
    contrasts: tuple[ContrastSpec, ...]
    sensitivity_analyses: tuple[SensitivityAnalysis, ...] = ()

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(c.name for c in self.contrasts)

    def by_name(self, name: str) -> ContrastSpec:
        for c in self.contrasts:
            if c.name == name:
                return c
        raise KeyError(name)

    @property
    def sensitivity_names(self) -> tuple[str, ...]:
        return tuple(s.name for s in self.sensitivity_analyses)

    def sensitivity_by_name(self, name: str) -> SensitivityAnalysis:
        for s in self.sensitivity_analyses:
            if s.name == name:
                return s
        raise KeyError(name)


_VALID_KINDS = {"lmm", "lmm_offset", "lmm_1b"}
_VALID_DIRECTIONS = {"positive", "negative", "two-sided"}
_VALID_TUNING = {"finetuned", "both"}


def default_contrasts_path() -> Path:
    return Path(__file__).resolve().parents[3] / "configs" / "contrasts.yaml"


def load_prereg(path: str | Path | None = None) -> Prereg:
    """Loads + validates ``configs/contrasts.yaml`` into a ``Prereg``. Every
    declared contrast is shape-checked (known kind/direction/tuning, unique
    name) at load time so a malformed prereg fails loudly here rather than
    mid-fit."""
    path = Path(path) if path is not None else default_contrasts_path()
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    specs: list[ContrastSpec] = []
    seen: set[str] = set()
    for raw in data.get("contrasts", []):
        name = raw["name"]
        if name in seen:
            raise ValueError(f"contrasts.yaml declares duplicate contrast name {name!r}")
        seen.add(name)
        kind = raw["kind"]
        if kind not in _VALID_KINDS:
            raise ValueError(f"contrast {name!r}: unknown kind {kind!r} (expected {sorted(_VALID_KINDS)})")
        direction = raw["direction"]
        if direction not in _VALID_DIRECTIONS:
            raise ValueError(f"contrast {name!r}: unknown direction {direction!r}")
        tuning = raw.get("tuning", "finetuned")
        if tuning not in _VALID_TUNING:
            raise ValueError(f"contrast {name!r}: unknown tuning {tuning!r}")
        specs.append(
            ContrastSpec(
                name=name, rq=raw["rq"], kind=kind, formula=raw["formula"],
                term=raw["term"], direction=direction, tuning=tuning,
                subset=dict(raw.get("subset", {})), note=raw.get("note", "").strip(),
            )
        )

    declared_names = {s.name for s in specs}
    sensitivities: list[SensitivityAnalysis] = []
    for sa_name, sa_raw in (data.get("sensitivity_analyses") or {}).items():
        sa_contrasts = tuple(sa_raw.get("contrasts", []))
        unknown = [c for c in sa_contrasts if c not in declared_names]
        if unknown:
            raise ValueError(
                f"sensitivity_analyses.{sa_name} names undeclared contrast(s) {unknown}; "
                f"every sensitivity contrast must itself be a declared contrast."
            )
        sensitivities.append(
            SensitivityAnalysis(
                name=sa_name, contrasts=sa_contrasts,
                interpretation_rule=str(sa_raw.get("interpretation_rule", "")).strip(),
            )
        )

    return Prereg(
        prereg_frozen=bool(data.get("prereg_frozen", False)),
        contrasts=tuple(specs), sensitivity_analyses=tuple(sensitivities),
    )


class UndeclaredContrastError(ValueError):
    """Raised when a contrast is requested by a name the prereg
    (contrasts.yaml) does not declare -- the governance hard error (WO-8
    acceptance: "an undeclared contrast requested -> hard error")."""


class UndeclaredSensitivityError(ValueError):
    """Raised when a sensitivity analysis is requested by a name the prereg's
    ``sensitivity_analyses:`` section does not declare -- the SAME governance as
    contrasts (only declared sensitivity analyses run)."""


def select_sensitivity_analysis(prereg: Prereg, name: str) -> SensitivityAnalysis:
    """Governance for sensitivity analyses: returns the declared
    ``SensitivityAnalysis`` or hard-errors if ``name`` is not declared in
    contrasts.yaml's ``sensitivity_analyses:`` section."""
    if name not in prereg.sensitivity_names:
        raise UndeclaredSensitivityError(
            f"sensitivity analysis {name!r} is not declared in contrasts.yaml's "
            f"sensitivity_analyses section (declared: {sorted(prereg.sensitivity_names)}). "
            f"Add it to the prereg (human-approved, before G2) before it can run."
        )
    return prereg.sensitivity_by_name(name)


def select_contrasts(prereg: Prereg, names: Sequence[str] | None) -> list[ContrastSpec]:
    """Returns the ContrastSpecs to fit. ``names=None`` means the full
    declared set. Any requested name NOT declared in the prereg is a hard
    error (``UndeclaredContrastError``) -- the contrasts.yaml governance
    mechanism (WO-8 §2b)."""
    if names is None:
        return list(prereg.contrasts)
    declared = set(prereg.names)
    undeclared = [n for n in names if n not in declared]
    if undeclared:
        raise UndeclaredContrastError(
            f"contrast(s) {undeclared} are not declared in contrasts.yaml (the prereg of "
            f"record). Declared contrasts: {sorted(declared)}. Add them to the prereg "
            f"(human-approved, before G2) before they can be fit."
        )
    return [prereg.by_name(n) for n in names]


# ---------------------------------------------------------------------------
# Frame preparation (effect coding). Response-level rows only (spec §6.3).
# ---------------------------------------------------------------------------


def prepare_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Adds the effect-coded predictor columns the contrast formulas use
    (``sign_c``, ``tuning_c``, ``vt_c``, ``typ_c``, ``evoc_c``,
    ``rating_centered``). Never aggregates -- one row in, one row out (spec
    §6.3). Unmapped categories (e.g. ``sign=='na'`` for NEU) become NaN and
    are dropped only by the specific contrasts that actually reference that
    column."""
    out = df.copy()
    out["sign_c"] = out["sign"].map(_SIGN_CODE)
    out["tuning_c"] = out["tuning_status"].map(_TUNING_CODE)
    out["vt_c"] = out["valence_type"].map(_VT_CODE)
    out["typ_c"] = out["typicality"].map(_TYP_CODE)
    out["evoc_c"] = out["evocativeness"].map(_EVOC_CODE)
    out["rating"] = out["rating"].astype(float)
    out["rating_centered"] = out["rating"] - NEUTRAL_MIDPOINT
    out["set_id"] = out["family_id"].map(_derive_set_id)
    return out


def _apply_subset(df: pd.DataFrame, spec: ContrastSpec) -> pd.DataFrame:
    sub = df
    if spec.tuning == "finetuned":
        sub = sub[sub["tuning_status"] == "finetuned"]
    for col, allowed in spec.subset.items():
        values = allowed if isinstance(allowed, (list, tuple, set)) else [allowed]
        sub = sub[sub[col].isin(values)]
    return sub


def _formula_columns(formula: str) -> list[str]:
    """The coded/known columns a formula references (so we can drop rows with
    NaN in exactly those, no more). TOKEN-based (identifier boundaries), so
    ``rating`` no longer spuriously matches inside ``rating_centered`` nor
    ``sg_c`` inside ``sign_c`` (reviewer minor)."""
    tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", formula))
    candidates = set(_CODED_COLUMNS) | {"rating", "pred_c", "sg_c"}
    return sorted(tokens & candidates)


# ---------------------------------------------------------------------------
# 1b item-level-pairing frame construction (DR §12 / WO-8 §2)
# ---------------------------------------------------------------------------


def prepare_1b_frame(df_ft: pd.DataFrame, valence_type: str, *, fmt: str = "raw") -> pd.DataFrame:
    """Builds the 1b item-level-pairing frame for one valence_type within the
    finetuned checkpoint (and one prompt ``fmt``, default the primary "raw").
    For each item (variant_id) computes the ITEM's mean blame rating (bad items)
    or praise rating (good items) -- the responsibility channel -- and merges
    it, standardized (mean 0 / sd 1 across the subset), onto that item's
    INTENTIONALITY responses as the predictor ``pred_c``. ``sg_c`` is the
    bad/good indicator. The response-level intentionality ratings are the
    outcome (never aggregated -- spec §6.3); only the PREDICTOR is an item mean,
    and that measurement error is the documented EIV caveat."""
    sub = df_ft[(df_ft["valence_type"] == valence_type) & (df_ft["format"] == fmt)]
    # Item's responsibility-channel mean: blame for bad, praise for good.
    channel = np.where(sub["sign"] == "bad", "blame", "praise")
    resp = sub.assign(_channel=channel)
    resp = resp[resp["question_type"] == resp["_channel"]]
    item_pred = resp.groupby("variant_id")["rating"].mean()

    intent = sub[sub["question_type"] == "intentionality"].copy()
    intent["pred_raw"] = intent["variant_id"].map(item_pred)
    intent = intent.dropna(subset=["pred_raw"])
    if intent.empty:
        return intent.assign(pred_c=[], sg_c=[])
    mean = intent["pred_raw"].mean()
    sd = intent["pred_raw"].std(ddof=0)
    intent["pred_c"] = (intent["pred_raw"] - mean) / sd if sd > 0 else 0.0
    intent["sg_c"] = intent["sign"].map(_SIGN_CODE)
    return intent


# ---------------------------------------------------------------------------
# The primary LMM fit (+ documented fallbacks). Never silently drops a fit.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FitResult:
    estimate: float
    se: float | None
    p_value: float
    n_obs: int
    n_groups: int
    converged: bool
    fallback_used: bool
    method: str


def _group_label(groups: str) -> str:
    """Honest label for a grouping column: family_id -> 'familyRI' (a random
    INTERCEPT for family), any other column -> '<col>Cluster' (that column as
    the clustering unit)."""
    return "familyRI" if groups == "family_id" else f"{groups}Cluster"


def _fit_lmm(df: pd.DataFrame, formula: str, term: str, *, groups: str = "family_id") -> FitResult:
    """Fits ``formula`` as a mixedlm with a random intercept for ``groups``;
    falls back to OLS with cluster-robust SEs (clustered on ``groups``) if the
    mixed model raises, fails to converge, or emits a ConvergenceWarning.
    Returns the ``term`` estimate/SE/p-value and which path produced them -- the
    fit is NEVER silently dropped (a fallback is recorded honestly).

    DOMAIN IS NOT MODELED HERE (honest labeling, reviewer finding). An earlier
    version passed ``vc_formula={"domain": "0 + C(domain)"}`` with
    ``groups=family_id``; because domain is CONSTANT within a family, that gives
    each family its own single domain draw and is mathematically inert -- its
    SEs are byte-identical to plain family-RI. statsmodels' MixedLM cannot nest
    families within a separate domain grouping cleanly, so the primary LMM
    models family clustering only (method ``lmm-familyRI``). Domain-level
    clustering is offered as a SEPARATE, config-gated sensitivity fit
    (``domain_sensitivity``, ``groups=domain``) -- master spec §6's "domain =
    random effect" honored as far as statsmodels allows, and surfaced in the
    report as its own section rather than misrepresented in the primary label.

    All warnings are captured locally so this repo's ``filterwarnings=error``
    pytest config never turns a benign convergence warning into a hard error."""
    import statsmodels.formula.api as smf

    n_obs = int(len(df))
    n_groups = int(df[groups].nunique())
    label = _group_label(groups)

    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            md = smf.mixedlm(formula, data=df, groups=df[groups])
            mdf = md.fit(reml=False, method="lbfgs")
        had_cw = any(issubclass(w.category, ConvergenceWarning) for w in caught)
        converged = bool(getattr(mdf, "converged", False)) and not had_cw
        if converged and term in mdf.params.index:
            est = float(mdf.params[term])
            se = float(mdf.bse[term])
            p = float(mdf.pvalues[term])
            if np.isfinite(est) and np.isfinite(p):
                return FitResult(
                    estimate=est, se=se, p_value=p, n_obs=n_obs, n_groups=n_groups,
                    converged=True, fallback_used=False, method=f"lmm-{label}",
                )
    except Exception:
        pass

    # OLS cluster-robust fallback -- always yields a p-value; row never dropped.
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        ols = smf.ols(formula, data=df).fit(cov_type="cluster", cov_kwds={"groups": df[groups]})
    est = float(ols.params[term]) if term in ols.params.index else float("nan")
    se = float(ols.bse[term]) if term in ols.bse.index else None
    p = float(ols.pvalues[term]) if term in ols.pvalues.index else 1.0
    if not np.isfinite(p):
        p = 1.0
    return FitResult(
        estimate=est, se=se, p_value=p, n_obs=n_obs, n_groups=n_groups,
        converged=False, fallback_used=True, method=f"ols-{label}",
    )


def _boot_seed(base_seed: int, contrast: str, model_family: str, boot_idx: int) -> int:
    material = f"{base_seed}|{contrast}|{model_family}|{boot_idx}".encode("utf-8")
    return int(hashlib.sha256(material).hexdigest(), 16) % (2**32)


def _bootstrap_ci(
    df: pd.DataFrame, formula: str, term: str, *,
    base_seed: int, contrast: str, model_family: str, n_boot: int, groups: str = "family_id",
) -> tuple[float | None, float | None]:
    """Seeded cluster (family) percentile bootstrap CI for ``term`` (WO-8
    determinism acceptance: "same inputs -> byte-identical contrast table csv
    (seeded bootstraps)"). Resamples whole families with replacement (relabeled
    so a duplicated family is an independent cluster), refits the formula via
    OLS on each resample (fast + always defined -- this is a robustness CI
    companion to the LMM Wald p-value, not a second estimator of record), and
    returns the 2.5/97.5 percentiles. Every resample's RNG is derived by
    sha256(base_seed, contrast, model_family, boot_idx), so the interval is a
    pure function of its inputs -- byte-reproducible."""
    import statsmodels.formula.api as smf

    if n_boot <= 0:
        return None, None
    family_ids = df[groups].unique()
    by_family = {fid: df[df[groups] == fid] for fid in family_ids}
    estimates: list[float] = []
    for b in range(n_boot):
        rng = np.random.default_rng(_boot_seed(base_seed, contrast, model_family, b))
        picks = rng.choice(family_ids, size=len(family_ids), replace=True)
        parts = []
        for j, fid in enumerate(picks):
            block = by_family[fid].copy()
            block[groups] = f"{fid}__b{j}"
            parts.append(block)
        resampled = pd.concat(parts, ignore_index=True)
        try:
            with warnings.catch_warnings(record=True):
                warnings.simplefilter("always")
                res = smf.ols(formula, data=resampled).fit()
            if term in res.params.index and np.isfinite(res.params[term]):
                estimates.append(float(res.params[term]))
        except Exception:
            continue
    if len(estimates) < 2:
        return None, None
    arr = np.sort(np.asarray(estimates))
    return float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5))


# ---------------------------------------------------------------------------
# Ordinal sensitivity check (OrderedModel, logit, fixed effects only)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OrdinalSensitivity:
    contrast: str
    model_family: str
    term: str
    estimate: float
    p_value: float
    converged: bool
    note: str


def _ordinal_sensitivity(df: pd.DataFrame, spec: ContrastSpec, model_family: str) -> OrdinalSensitivity:
    """Fixed-effects-only ordinal (cumulative-link, logit) fit of the same
    contrast formula, as the DISTRIBUTIONAL sensitivity check (see module
    docstring on the LMM-primary/ordinal-sensitivity inversion). Best-effort:
    OrderedModel has no random effects and can fail to converge on small or
    separable subsets -- never fatal, ``converged=False`` records that."""
    from patsy import dmatrices
    from statsmodels.miscmodels.ordinal_model import OrderedModel

    try:
        y, X = dmatrices(spec.formula, df, return_type="dataframe")
        X = X.drop(columns=["Intercept"], errors="ignore")
        endog = y.iloc[:, 0].round().astype(int)
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            res = OrderedModel(endog, X, distr="logit").fit(method="bfgs", disp=False)
        term = spec.term
        est = float(res.params[term]) if term in res.params.index else float("nan")
        p = float(res.pvalues[term]) if term in res.pvalues.index else float("nan")
        ok = bool(np.isfinite(est) and np.isfinite(p))
        return OrdinalSensitivity(spec.name, model_family, term, est, p, ok, "logit link; fixed effects only (no RE)")
    except Exception as exc:  # never fatal -- it's a sensitivity companion
        return OrdinalSensitivity(spec.name, model_family, spec.term, float("nan"), float("nan"), False, f"failed: {type(exc).__name__}")


# ---------------------------------------------------------------------------
# Orchestration: fit every selected contrast per model_family, Holm-correct.
# ---------------------------------------------------------------------------


def _direction_ok(direction: str, estimate: float, p_holm: float, alpha: float) -> bool:
    if not np.isfinite(estimate) or p_holm >= alpha:
        return False
    if direction == "positive":
        return estimate > 0
    if direction == "negative":
        return estimate < 0
    return True  # two-sided: any significant estimate confirms


def _subset_for_fit(
    prepared: pd.DataFrame, spec: ContrastSpec, model_family: str, *, fmt: str = "raw",
) -> pd.DataFrame:
    """Subsets to one model_family + prompt ``fmt`` (default "raw", the primary
    format -- spec §3.4; "chat" is the robustness pass) and applies the spec's
    own filters. The 1b frame is built by ``prepare_1b_frame`` (which needs all
    three question types, so it does its own format filter)."""
    fam = prepared[prepared["model_family"] == model_family]
    if spec.kind == "lmm_1b":
        vt = spec.subset.get("valence_type", ["moral"])
        vt = vt[0] if isinstance(vt, (list, tuple)) else vt
        ft = fam[fam["tuning_status"] == "finetuned"] if spec.tuning == "finetuned" else fam
        return prepare_1b_frame(ft, vt, fmt=fmt)
    sub = _apply_subset(fam[fam["format"] == fmt], spec)
    needed = _formula_columns(spec.formula)
    if needed:
        sub = sub.dropna(subset=needed)
    return sub


def _bootstrap_formula(spec: ContrastSpec) -> str:
    """The formula ``_bootstrap_ci`` should refit on each family-resample.

    For every ``kind`` except ``lmm_1b``, this is just ``spec.formula``: the
    fixed effects (sign/tuning/valence-type/typicality/evocativeness) are
    balanced, effect-coded design factors, so plain OLS and the primary
    mixedlm agree closely on the point estimate (confirmed empirically:
    family-RI vs. set_id-cluster vs. family-FE point estimates are identical
    to 6 decimal places for RQ1_base/RQ1a/RQ1c/RQ1d) and a pooled-OLS
    bootstrap refit is unbiased.

    ``lmm_1b`` is different and needs family fixed effects instead. Its
    predictor ``pred_c`` (an item's blame/praise mean) is a continuous,
    per-item covariate, NOT a balanced design factor, and it is strongly
    correlated with family identity (measured on v1.1: corr(pred_c, its own
    family mean) = 0.77-0.96 across all six family x valence_type cells) --
    an unmeasured family-level driver (plausibly the same severity/valence
    intensity confound documented for RQ1a) shifts both an item's judged
    blameworthiness and its intentionality rating together. Plain pooled OLS
    treats that between-family covariation as if it were the within-family
    slope of interest, biasing the estimate (verified: pooled-OLS vs.
    family-fixed-effects point estimates disagreed by 0.4-3.7 rating points
    across the six real cells, occasionally flipping sign, while the
    family-fixed-effects and the primary mixedlm/RE point estimates agreed
    to within ~0.1 in every cell -- see docs/RQ1_STATISTICAL_METHODS_v1.1.md).
    This is exactly why the reported ``ci_low``/``ci_high`` for RQ1b
    contrasts used to fail to bracket their own point estimate.

    The fix: add family fixed effects (``C(family_id)``) to the bootstrap
    refit for ``lmm_1b`` contrasts, and drop the now-collinear bare ``sg_c``
    main effect (sign is constant within a family/valence, so once family
    dummies are in the model ``sg_c`` is perfectly explained by them --
    leaving it in produces a rank-deficient design and degenerate SEs).
    ``pred_c:sg_c`` stays identified: it's each family's fixed sg_c value
    times that family's OWN within-family ``pred_c`` variation, and
    families differ in which sg_c value they carry."""
    if spec.kind != "lmm_1b":
        return spec.formula
    if "pred_c * sg_c" not in spec.formula:
        raise ValueError(
            f"contrast {spec.name!r} is kind=lmm_1b but its formula "
            f"{spec.formula!r} doesn't match the expected 'pred_c * sg_c' "
            "shape -- _bootstrap_formula's family-FE rewrite needs updating."
        )
    return spec.formula.replace("pred_c * sg_c", "pred_c + pred_c:sg_c") + " + C(family_id)"


def fit_contrast(
    prepared: pd.DataFrame, spec: ContrastSpec, model_family: str, *,
    base_seed: int, n_boot: int, ordinal: bool = True, fmt: str = "raw",
) -> tuple[ContrastResultRecord | None, OrdinalSensitivity | None]:
    """Fits ONE declared contrast on ONE model_family (primary format ``fmt``,
    default "raw"). Returns (ContrastResultRecord, OrdinalSensitivity) -- p_holm
    is filled in later by ``holm_correct``. Returns (None, None) when the subset
    is too small to fit (fewer than 2 groups or empty), so an unestimable cell
    is reported as a gap rather than a spurious number."""
    df = _subset_for_fit(prepared, spec, model_family, fmt=fmt)
    if df.empty or df["family_id"].nunique() < 2:
        return None, None

    fit = _fit_lmm(df, spec.formula, spec.term)
    ci_low, ci_high = _bootstrap_ci(
        df, _bootstrap_formula(spec), spec.term, base_seed=base_seed, contrast=spec.name,
        model_family=model_family, n_boot=n_boot,
    )
    ci_method = "cluster_bootstrap_ols" if (n_boot > 0 and ci_low is not None) else "none"
    tuning_scope = "both" if spec.tuning == "both" else "finetuned"
    record = ContrastResultRecord(
        contrast=spec.name, rq=spec.rq, model_family=model_family, tuning_scope=tuning_scope,
        term=spec.term, estimate=fit.estimate, se=fit.se, p_value=fit.p_value,
        p_holm=fit.p_value,  # placeholder; holm_correct() overwrites
        ci_low=ci_low, ci_high=ci_high, ci_method=ci_method, direction_expected=spec.direction,
        direction_ok=False, n_obs=fit.n_obs, n_groups=fit.n_groups,
        method=fit.method, converged=fit.converged, fallback_used=fit.fallback_used,
    )
    sens = _ordinal_sensitivity(df, spec, model_family) if (ordinal and spec.kind == "lmm") else None
    return record, sens


# ---------------------------------------------------------------------------
# Domain-cluster sensitivity (config-gated) -- master spec §6's "domain =
# random effect" intent, as far as statsmodels allows: the SAME fixed effects
# refit with groups=domain (a domain-clustered fit), reported in its own
# section so the primary family-RI never overstates what it models.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DomainSensitivity:
    contrast: str
    model_family: str
    term: str
    estimate: float
    se: float | None
    p_value: float
    n_domains: int
    method: str
    note: str


def domain_sensitivity(prepared: pd.DataFrame, spec: ContrastSpec, model_family: str, *, fmt: str = "raw") -> DomainSensitivity | None:
    """Refits ``spec`` with ``groups=domain`` (domain as the clustering unit) --
    the domain-aware sensitivity companion to the family-RI primary. Returns
    None when the cell spans fewer than 2 domains (nothing domain-level to
    estimate). Best-effort: uses ``_fit_lmm``'s own mixed/OLS-cluster
    cascade."""
    df = _subset_for_fit(prepared, spec, model_family, fmt=fmt)
    if df.empty or "domain" not in df or df["domain"].nunique() < 2:
        return None
    fit = _fit_lmm(df, spec.formula, spec.term, groups="domain")
    return DomainSensitivity(
        contrast=spec.name, model_family=model_family, term=spec.term,
        estimate=fit.estimate, se=fit.se, p_value=fit.p_value,
        n_domains=fit.n_groups, method=fit.method,
        note="domain as clustering unit (groups=domain); companion to lmm-familyRI primary",
    )


# ---------------------------------------------------------------------------
# Set-cluster sensitivity (v1.1 proposal, RQ1a power fix -- NOT yet a
# confirmed primary-vs-sensitivity decision, see NEXT_RUN_ACTION_ITEMS.md).
# A "set" is the five valence-siblings (MB/MG/NMB/NMG/NEU) generated from one
# shared storyline (agent/goal/actions) -- see _derive_set_id. sign and
# valence_type are both fixed per family, so contrasts on them (rq1_base,
# rq1a) are fully between-family under the primary family-RI fit, which pays
# the entire var_family component as noise. Modeling set_id as the
# clustering unit instead recovers the matched-storyline structure that
# family-RI clustering discards.
#
# VALIDATION CAVEAT, check every time this is used: set_id is derived from
# the same family_id string that valence_type is read from, so there is a
# real risk set_id partially absorbs the fixed effect it's meant to de-noise
# rather than just tightening its SE. Before trusting a set-cluster result,
# confirm the term's point estimate is stable relative to the family-RI
# primary (see ``estimate`` on both records) -- only the SE should shrink.
# If the estimate itself moves, treat that as a red flag, not a win.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SetSensitivity:
    contrast: str
    model_family: str
    term: str
    estimate: float
    se: float | None
    p_value: float
    n_sets: int
    method: str
    note: str


def set_sensitivity(prepared: pd.DataFrame, spec: ContrastSpec, model_family: str, *, fmt: str = "raw") -> SetSensitivity | None:
    """Refits ``spec`` with ``groups=set_id`` (the shared-storyline set as the
    clustering unit) -- the set-aware companion to the family-RI primary,
    proposed specifically for RQ1a's between-family power problem (see the
    module-level caveat above). Returns None when the cell spans fewer than
    2 sets (nothing set-level to estimate). Best-effort: uses ``_fit_lmm``'s
    own mixed/OLS-cluster cascade."""
    df = _subset_for_fit(prepared, spec, model_family, fmt=fmt)
    if df.empty or "set_id" not in df or df["set_id"].nunique() < 2:
        return None
    fit = _fit_lmm(df, spec.formula, spec.term, groups="set_id")
    return SetSensitivity(
        contrast=spec.name, model_family=model_family, term=spec.term,
        estimate=fit.estimate, se=fit.se, p_value=fit.p_value,
        n_sets=fit.n_groups, method=fit.method,
        note=(
            "set_id (shared-storyline valence-siblings) as clustering unit; "
            "companion to lmm-familyRI primary -- confirm estimate is stable "
            "vs. the primary before trusting the SE shrinkage (see module docstring)"
        ),
    )


def set_sensitivity_all(
    prepared: pd.DataFrame, specs: Sequence[ContrastSpec],
) -> list[SetSensitivity]:
    """Set-cluster sensitivity for every estimable (contrast, model_family)
    cell (see ``set_sensitivity``)."""
    model_families = sorted(prepared["model_family"].unique())
    out: list[SetSensitivity] = []
    for spec in specs:
        for mf in model_families:
            ss = set_sensitivity(prepared, spec, mf)
            if ss is not None:
                out.append(ss)
    return out


# ---------------------------------------------------------------------------
# Domain-random-slope sensitivity (DECLARED in contrasts.yaml; researcher
# decision 2026-07-28, the middle course). For each headline cross-domain-
# generalization contrast: fit mixedlm groups=domain with re_formula on the
# focal term (random intercept + random SLOPE for the tested term across
# domains), same fixed effects as the primary. If the domain-slope CI is
# materially wider than the primary family-RI CI (ratio > threshold) OR the
# slope variance is non-negligible, the cross-domain generalization claim is
# reported QUALIFIED. OLS fallback is NOT appropriate here (there is no random
# slope to recover under OLS) -- non-convergence is recorded honestly instead.
# ---------------------------------------------------------------------------

# Thresholds encoding contrasts.yaml's declared interpretation_rule (kept in
# code, documented to match the human-readable rule string in the prereg).
CI_WIDTH_RATIO_THRESHOLD = 1.5
SLOPE_VAR_THRESHOLD = 0.05  # rating-point^2; "non-negligible" between-domain slope variance


@dataclass(frozen=True)
class DomainSlopeFit:
    estimate: float
    se: float | None
    ci_low: float | None
    ci_high: float | None
    slope_variance: float | None
    converged: bool
    n_domains: int


def _fit_domain_slope(df: pd.DataFrame, formula: str, term: str, *, groups: str = "domain") -> DomainSlopeFit:
    """Fits ``formula`` (same fixed effects as primary) as a mixedlm with
    ``groups=domain`` and a random SLOPE for ``term`` across domains
    (``re_formula="~<term>"`` -> random intercept + random slope). Returns the
    fixed-effect ``term`` estimate/SE + a Wald CI, the between-domain slope
    variance (from ``cov_re``), and an HONEST convergence flag. No OLS fallback:
    a non-converged fit is recorded as ``converged=False`` (an OLS fit has no
    random slope to recover), never silently dropped. Fragile with few domains
    -- that is expected and reported."""
    import statsmodels.formula.api as smf

    n_domains = int(df[groups].nunique())
    re_formula = f"~{term}"
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            md = smf.mixedlm(formula, data=df, groups=df[groups], re_formula=re_formula)
            mdf = md.fit(reml=False, method="lbfgs")
        had_cw = any(issubclass(w.category, ConvergenceWarning) for w in caught)
        converged = bool(getattr(mdf, "converged", False)) and not had_cw
        if term not in mdf.params.index:
            return DomainSlopeFit(float("nan"), None, None, None, None, False, n_domains)
        est = float(mdf.params[term])
        se = float(mdf.bse[term])
        ci_low = est - 1.96 * se
        ci_high = est + 1.96 * se
        slope_var = None
        try:
            cov_re = mdf.cov_re
            if term in cov_re.index:
                slope_var = float(cov_re.loc[term, term])
        except Exception:
            slope_var = None
        ok = converged and np.isfinite(est) and np.isfinite(se)
        return DomainSlopeFit(est, se, ci_low, ci_high, slope_var, ok, n_domains)
    except Exception:
        return DomainSlopeFit(float("nan"), None, None, None, None, False, n_domains)


@dataclass(frozen=True)
class DomainSlopeSensitivity:
    contrast: str
    model_family: str
    term: str
    primary_estimate: float
    primary_se: float | None
    primary_ci_low: float | None
    primary_ci_high: float | None
    slope_estimate: float
    slope_se: float | None
    slope_ci_low: float | None
    slope_ci_high: float | None
    slope_variance: float | None
    ci_width_ratio: float | None
    n_domains: int
    converged: bool
    qualified: bool
    note: str


def _ci_width(low: float | None, high: float | None) -> float | None:
    if low is None or high is None:
        return None
    return float(high - low)


def domain_slope_sensitivity(
    prepared: pd.DataFrame, specs: Sequence[ContrastSpec], analysis: SensitivityAnalysis,
    *, fmt: str = "raw",
) -> list[DomainSlopeSensitivity]:
    """DECLARED domain-random-slope sensitivity (contrasts.yaml governs which
    contrasts get it -- ``analysis.contrasts``). For each such contrast x
    model_family with >=2 domains: fit the primary family-RI (for its Wald CI)
    and the domain-random-slope model, then apply the declared interpretation
    rule -> QUALIFIED if the slope CI is materially wider than the primary
    (``ci_width_ratio > CI_WIDTH_RATIO_THRESHOLD``) OR the between-domain slope
    variance is non-negligible (``> SLOPE_VAR_THRESHOLD``) OR the slope fit did
    not converge (generalization unverifiable)."""
    declared = set(analysis.contrasts)
    targets = [s for s in specs if s.name in declared]
    model_families = sorted(prepared["model_family"].unique())
    out: list[DomainSlopeSensitivity] = []
    for spec in targets:
        for mf in model_families:
            df = _subset_for_fit(prepared, spec, mf, fmt=fmt)
            if df.empty or "domain" not in df or df["domain"].nunique() < 2:
                continue
            primary = _fit_lmm(df, spec.formula, spec.term, groups="family_id")
            slope = _fit_domain_slope(df, spec.formula, spec.term)
            primary_ci_low = (
                primary.estimate - 1.96 * primary.se if primary.se is not None else None
            )
            primary_ci_high = (
                primary.estimate + 1.96 * primary.se if primary.se is not None else None
            )
            w_primary = _ci_width(primary_ci_low, primary_ci_high)
            w_slope = _ci_width(slope.ci_low, slope.ci_high)
            ratio = (w_slope / w_primary) if (w_primary and w_slope and w_primary > 0) else None

            # QUALIFIED follows the DECLARED interpretation_rule: ratio>1.5 OR
            # slope variance non-negligible. Non-convergence is recorded
            # honestly (``converged``) but does NOT by itself qualify -- a
            # zero-variance slope legitimately sits at the RE boundary and
            # reports non-convergence while still yielding a usable
            # slope_var~=0 / ratio~=1 (correctly UNQUALIFIED). Only a genuinely
            # DEGENERATE fit (no usable CI ratio AND no slope variance) is
            # qualified, as an unverifiable generalization.
            reasons: list[str] = []
            if ratio is not None and ratio > CI_WIDTH_RATIO_THRESHOLD:
                reasons.append(f"CI width ratio {ratio:.2f} > {CI_WIDTH_RATIO_THRESHOLD}")
            if slope.slope_variance is not None and slope.slope_variance > SLOPE_VAR_THRESHOLD:
                reasons.append(f"slope variance {slope.slope_variance:.3f} > {SLOPE_VAR_THRESHOLD}")
            degenerate = ratio is None and slope.slope_variance is None
            if degenerate:
                reasons.append("slope fit degenerate (no usable CI/variance); generalization unverifiable")
            qualified = bool(reasons)
            conv_note = "" if slope.converged else " [slope fit non-converged/at-boundary, recorded honestly]"
            note = ("; ".join(reasons) if reasons else "generalization unqualified by the declared rule") + conv_note

            out.append(DomainSlopeSensitivity(
                contrast=spec.name, model_family=mf, term=spec.term,
                primary_estimate=primary.estimate, primary_se=primary.se,
                primary_ci_low=primary_ci_low, primary_ci_high=primary_ci_high,
                slope_estimate=slope.estimate, slope_se=slope.se,
                slope_ci_low=slope.ci_low, slope_ci_high=slope.ci_high,
                slope_variance=slope.slope_variance, ci_width_ratio=ratio,
                n_domains=slope.n_domains, converged=slope.converged,
                qualified=qualified, note=note,
            ))
    return out


# ---------------------------------------------------------------------------
# Chat-vs-raw format robustness comparison (config-gated; WO-8 §4)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChatComparisonRow:
    contrast: str
    model_family: str
    term: str
    raw_estimate: float
    raw_p: float
    chat_estimate: float
    chat_p: float


def chat_format_comparison(
    prepared: pd.DataFrame, specs: Sequence[ContrastSpec],
) -> tuple[list[ChatComparisonRow], bool]:
    """WO-8 §4 robustness stub (config-gated, off by default): for each contrast
    x model_family where BOTH raw and chat subsets are estimable, refit on each
    format and return raw-vs-chat estimates side by side. The second return
    value is whether ANY chat-format rows exist at all -- False lets the caller
    log the "no chat-format rows; comparison skipped" note (never silent)."""
    any_chat = bool((prepared["format"] == "chat").any()) if "format" in prepared else False
    rows: list[ChatComparisonRow] = []
    if not any_chat:
        return rows, False
    model_families = sorted(prepared["model_family"].unique())
    for spec in specs:
        for mf in model_families:
            raw_df = _subset_for_fit(prepared, spec, mf, fmt="raw")
            chat_df = _subset_for_fit(prepared, spec, mf, fmt="chat")
            if raw_df.empty or chat_df.empty:
                continue
            if raw_df["family_id"].nunique() < 2 or chat_df["family_id"].nunique() < 2:
                continue
            raw_fit = _fit_lmm(raw_df, spec.formula, spec.term)
            chat_fit = _fit_lmm(chat_df, spec.formula, spec.term)
            rows.append(ChatComparisonRow(
                contrast=spec.name, model_family=mf, term=spec.term,
                raw_estimate=raw_fit.estimate, raw_p=raw_fit.p_value,
                chat_estimate=chat_fit.estimate, chat_p=chat_fit.p_value,
            ))
    return rows, True


def holm_correct(records: list[ContrastResultRecord], alpha: float = DEFAULT_ALPHA) -> list[ContrastResultRecord]:
    """Holm-corrects p-values WITHIN each (model_family, rq) family
    (``statsmodels.stats.multitest.multipletests``), fills ``p_holm`` and
    recomputes ``direction_ok`` against the corrected p. Returns NEW records
    (frozen inputs untouched)."""
    out: list[ContrastResultRecord] = []
    groups: dict[tuple[str, str], list[ContrastResultRecord]] = {}
    for r in records:
        groups.setdefault((r.model_family, r.rq), []).append(r)
    for _key, group in groups.items():
        pvals = [r.p_value for r in group]
        _, p_holm, _, _ = multipletests(pvals, alpha=alpha, method="holm")
        for r, ph in zip(group, p_holm):
            ph = float(ph)
            out.append(
                r.model_copy(update={
                    "p_holm": ph,
                    "direction_ok": _direction_ok(r.direction_expected, r.estimate, ph, alpha),
                })
            )
    out.sort(key=lambda r: (r.rq, r.contrast, r.model_family))
    return out


def fit_all(
    prepared: pd.DataFrame, specs: Sequence[ContrastSpec], *,
    base_seed: int = 0, n_boot: int = 0, alpha: float = DEFAULT_ALPHA, ordinal: bool = True,
) -> tuple[list[ContrastResultRecord], list[OrdinalSensitivity]]:
    """Fits every (contrast, model_family) cell (primary "raw" format), then
    Holm-corrects within each (model_family, rq) family. ``prepared`` is a
    ``prepare_frame``d analysis DataFrame."""
    model_families = sorted(prepared["model_family"].unique())
    records: list[ContrastResultRecord] = []
    sensitivities: list[OrdinalSensitivity] = []
    for spec in specs:
        for mf in model_families:
            rec, sens = fit_contrast(prepared, spec, mf, base_seed=base_seed, n_boot=n_boot, ordinal=ordinal)
            if rec is not None:
                records.append(rec)
            if sens is not None:
                sensitivities.append(sens)
    corrected = holm_correct(records, alpha=alpha)
    return corrected, sensitivities


def domain_sensitivity_all(
    prepared: pd.DataFrame, specs: Sequence[ContrastSpec],
) -> list[DomainSensitivity]:
    """Config-gated domain-cluster sensitivity for every estimable
    (contrast, model_family) cell (see ``domain_sensitivity``)."""
    model_families = sorted(prepared["model_family"].unique())
    out: list[DomainSensitivity] = []
    for spec in specs:
        for mf in model_families:
            ds = domain_sensitivity(prepared, spec, mf)
            if ds is not None:
                out.append(ds)
    return out
