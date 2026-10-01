"""Pre-pilot check: do chat prompts reach the instruct models with two BOS tokens?

Why: knobe's VllmEngine (src/knobe/elicit_vllm.py, `_prompt_text` and
`generate`) renders chat prompts with `apply_chat_template(tokenize=False)`,
then passes the string to `LLM.generate`, which tokenizes it again. The chat
templates of Llama-3.1-Instruct, gemma-2-9b-it and Mistral-Instruct-v0.1
already emit the BOS text, so if the second tokenization also adds BOS
(the default for string prompts), every chat prompt starts with BOS BOS.
Gemma in particular degrades on that. This script measures it; it changes
nothing.

Two modes, both read the instruct checkpoints from the knobe registry:

  tokenizer (default, CPU only; needs HF access to the gated repos):
      reproduces the engine's two steps with the model's own tokenizer.
  --vllm (GPU; ground truth):
      runs one real `LLM.generate` per model and reads
      `outputs[0].prompt_token_ids`, i.e. what vLLM actually fed the model.

Run from the repo root on the cluster, e.g.
    .venv/bin/python studies/knobe_moral_probe/tools/check_chat_bos.py
    .venv/bin/python studies/knobe_moral_probe/tools/check_chat_bos.py --vllm --families gemma-2-9b

Exit code 0 if no model shows a doubled BOS, 1 if any does.
"""
from __future__ import annotations

import argparse
import sys

from knobe.elicit_vllm import default_registry_path
from knobe.registry import load_registry

FAMILIES = ("llama-3.1-8b", "mistral-7b-v0.1", "gemma-2-9b")  # the study's six models
MESSAGES = [{"role": "user", "content": "How many legs does a spider have? Answer with a number."}]


def count_leading_bos(ids: list[int], bos_id: int | None) -> int:
    n = 0
    for tok in ids:
        if tok != bos_id:
            break
        n += 1
    return n


def check_tokenizer(model_id: str, revision: str) -> tuple[list[int], int | None, object]:
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(model_id, revision=revision)
    text = tok.apply_chat_template(MESSAGES, tokenize=False, add_generation_prompt=True)
    ids = tok(text)["input_ids"]  # add_special_tokens=True, as for a string prompt
    return ids, tok.bos_token_id, tok


def check_vllm(model_id: str, revision: str) -> tuple[list[int], int | None, object]:
    from vllm import LLM, SamplingParams

    llm = LLM(model=model_id, revision=revision, dtype="bfloat16")
    tok = llm.get_tokenizer()
    text = tok.apply_chat_template(MESSAGES, tokenize=False, add_generation_prompt=True)
    out = llm.generate([text], SamplingParams(temperature=0.0, max_tokens=1))
    return list(out[0].prompt_token_ids), tok.bos_token_id, tok


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--vllm", action="store_true", help="ground truth via a real LLM.generate (GPU)")
    p.add_argument("--families", default=",".join(FAMILIES))
    p.add_argument("--registry", default=str(default_registry_path()))
    args = p.parse_args(argv)

    registry = load_registry(args.registry)
    check = check_vllm if args.vllm else check_tokenizer
    doubled = []
    for fam in args.families.split(","):
        family = registry[fam]
        ids, bos_id, tok = check(family.finetuned, family.revision)
        n = count_leading_bos(ids, bos_id)
        head = tok.convert_ids_to_tokens(ids[:4])
        verdict = "DOUBLE BOS" if n > 1 else ("ok" if n == 1 else "no BOS")
        print(f"{fam:18s} {family.finetuned:40s} leading BOS={n}  first tokens={head}  -> {verdict}")
        if n > 1:
            doubled.append(fam)
    mode = "vllm" if args.vllm else "tokenizer"
    print(f"\n[{mode}] doubled BOS: {', '.join(doubled) if doubled else 'none'}")
    return 1 if doubled else 0


if __name__ == "__main__":
    sys.exit(main())
