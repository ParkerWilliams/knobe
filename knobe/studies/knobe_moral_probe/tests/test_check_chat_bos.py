"""tools/check_chat_bos.py must judge the prompt the engine actually sends
(render_chat_prompt), not the raw template recipe the engine no longer uses."""
from tools import check_chat_bos


class _Tok:
    """HF-like tokenizer whose chat template writes BOS text and whose
    string tokenization also prepends BOS -- the doubled-BOS setup."""

    bos_token, bos_token_id = "<s>", 1

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        return "<s>[INST] " + messages[0]["content"] + " [/INST]"

    def encode(self, text, add_special_tokens=True):
        ids = [1] if add_special_tokens else []
        for i, piece in enumerate(text.split("<s>")):
            if i:
                ids.append(1)
            ids.extend(2 for _ in piece.split())
        return ids

    def __call__(self, text):
        return {"input_ids": self.encode(text)}


def test_engine_rendering_has_one_bos_while_template_recipe_has_two():
    tok = _Tok()
    engine_ids = tok(check_chat_bos.render_chat_prompt(tok, check_chat_bos.MESSAGES))["input_ids"]
    assert check_chat_bos.count_leading_bos(engine_ids, 1) == 1
    assert check_chat_bos.count_leading_bos(check_chat_bos.template_only_ids(tok), 1) == 2
