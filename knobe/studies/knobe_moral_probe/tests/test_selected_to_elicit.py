"""A foundations harm pair fails screening; selection keeps the storyline's
non-harm pairs (decision A), lists it in shared_without_harm, and elicitation
runs on the selected_items.csv that screening wrote."""
import json

from knobe.schemas import ResultRecord, read_jsonl

from conftest import make_items
from test_screen import ScriptedClient
from kmp import elicit, screen_run
from kmp.items import design_problems, load_items, write_items


class _HarmFailsFor1(ScriptedClient):
    async def complete(self, prompt, max_tokens):
        answer = await super().complete(prompt, max_tokens)
        item_id, qkey = self.lookup[prompt]
        return "2" if item_id.startswith("kmp-mf-001-harm-") and qkey == "fnd_harm" else answer


def test_elicit_runs_on_selection_that_lost_a_harm_pair(tmp_path, monkeypatch):
    items = make_items("foundations", 1)
    items_path = tmp_path / "items.csv"
    write_items(items, items_path)
    monkeypatch.setattr(screen_run, "MockClient", lambda **kw: _HarmFailsFor1(items))
    sdir = tmp_path / "screening"
    assert screen_run.main(["--items", str(items_path), "--out-dir", str(sdir), "--mock"]) == 0
    assert json.loads((sdir / "screening_meta.json").read_text())["shared_without_harm"] == [1]

    selected_path = sdir / "selected_items.csv"
    selected = load_items(selected_path)
    assert selected and not any(i.arm == "harm" for i in selected)
    assert design_problems(selected) != []                             # the strict authoring check refuses it
    out = tmp_path / "results.jsonl"
    assert elicit.main(["--items", str(selected_path), "--out", str(out), "--engine", "fake",
                        "--model-keys", "mistral-7b-v0.1-instruct"]) == 0
    assert {r.prompt_id.split("::")[0] for r in read_jsonl(out, ResultRecord)} == {i.item_id for i in selected}
