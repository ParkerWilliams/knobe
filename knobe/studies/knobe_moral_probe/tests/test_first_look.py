import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

STUDY_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def first_look():
    spec = importlib.util.spec_from_file_location("first_look", STUDY_DIR / "analysis" / "first_look.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.B = 99
    return mod


def _frame(effect_instruct: float, effect_pretrained: float, n_storylines: int = 12) -> pd.DataFrame:
    """Synthetic frame in kmp.frame's column contract: one family, both tunings."""
    rng = np.random.default_rng(0)
    rows = []
    for mk, tuning, effect in [("llama-3.1-8b-instruct", "finetuned", effect_instruct),
                               ("llama-3.1-8b-pretrained", "pretrained", effect_pretrained)]:
        for sid in range(1, n_storylines + 1):
            for sign, sc in [("bad", 0.5), ("good", -0.5)]:
                for q in ["intentionality", "blame", "praise", "significance"]:
                    for _ in range(6):
                        rows.append(dict(model_key=mk, qkey=q, sign=sign, sign_c=sc,
                                         rating=5 + effect * sc + rng.normal(0, 1),
                                         cluster_id=f"ngo_verbatim-{sid:03d}", family="llama",
                                         tuning_status=tuning, tuning_c=0.5 if tuning == "finetuned" else -0.5))
    return pd.DataFrame(rows)


def test_recovers_planted_sign_effect_and_tuning_interaction(first_look):
    out = first_look.sign_effects(_frame(effect_instruct=3.0, effect_pretrained=0.0))
    inst = out[(out.cell == "llama-3.1-8b-instruct") & (out.qkey == "intentionality")].iloc[0]
    pre = out[(out.cell == "llama-3.1-8b-pretrained") & (out.qkey == "intentionality")].iloc[0]
    tun = out[(out.level == "family") & (out.qkey == "intentionality")].iloc[0]
    assert inst.beta_obs == pytest.approx(3.0, abs=0.5) and inst.p_wcb < 0.05
    assert abs(pre.beta_obs) < 0.5
    assert tun.term == "sign_c:tuning_c" and tun.beta_obs == pytest.approx(3.0, abs=0.7)
    assert inst.mean_bad > inst.mean_good and inst.number_rate == 1.0


def test_number_rate_counts_unparsed_rows(first_look):
    f = _frame(1.0, 1.0)
    cell = (f.model_key == "llama-3.1-8b-instruct") & (f.qkey == "blame")
    f.loc[f.index[cell][:36], "rating"] = np.nan          # 36 of the cell's 144 rows
    out = first_look.sign_effects(f)
    low = out[(out.level == "model") & (out.number_rate < 1)]
    assert list(low.qkey) == ["blame"] and low.number_rate.iloc[0] == pytest.approx(0.75)


def test_seed_is_order_independent(first_look):
    assert first_look.seed_for("a", "b") == first_look.seed_for("a", "b") != first_look.seed_for("b", "a")
