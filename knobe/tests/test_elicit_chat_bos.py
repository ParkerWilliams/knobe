"""render_chat_prompt: chat-format prompts must reach the model with
exactly one BOS (double-BOS defect found 2026-09-25, before the first
chat-format run; see render_chat_prompt's docstring)."""
from __future__ import annotations

from knobe import elicit_vllm


class _TemplatedTokenizer:
    """Mimics an HF tokenizer whose chat template writes BOS text and
    whose encode() may or may not prepend BOS itself."""

    bos_token = "<s>"
    bos_token_id = 1

    def __init__(self, auto_bos: bool):
        self.auto_bos = auto_bos

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        assert not tokenize and add_generation_prompt
        return "<s>[INST] " + messages[0]["content"] + " [/INST]"

    def encode(self, text, add_special_tokens=True):
        ids = [1] if (add_special_tokens and self.auto_bos) else []
        pieces = text.split("<s>")
        for i, piece in enumerate(pieces):
            if i:
                ids.append(1)  # literal "<s>" text parses to the BOS special token
            ids.extend(2 for _ in piece.split())
        return ids


MESSAGES = [{"role": "user", "content": "Scenario... Answer:"}]


def test_strips_template_bos_when_tokenizer_adds_its_own():
    tok = _TemplatedTokenizer(auto_bos=True)
    text = elicit_vllm.render_chat_prompt(tok, MESSAGES)
    assert not text.startswith("<s>")
    assert tok.encode(text, add_special_tokens=True).count(1) == 1


def test_keeps_template_bos_when_tokenizer_does_not_add_one():
    tok = _TemplatedTokenizer(auto_bos=False)
    text = elicit_vllm.render_chat_prompt(tok, MESSAGES)
    assert text.startswith("<s>")
    assert tok.encode(text, add_special_tokens=True).count(1) == 1


def test_unpatched_path_would_double_bos():
    """Documents the defect itself: the raw template string, tokenized the
    way vLLM generate() tokenizes a text prompt, carries two BOS ids."""
    tok = _TemplatedTokenizer(auto_bos=True)
    raw = tok.apply_chat_template(MESSAGES, tokenize=False, add_generation_prompt=True)
    assert tok.encode(raw, add_special_tokens=True)[:2] == [1, 1]
