# knobe_moral_probe analysis log

One line per completed analysis run of this study, per the repo's CLAUDE.md
§5 format. This study keeps its own log so its record stays separate from
the pilots' and the main run's (`results/ANALYSIS_LOG.md`, which carries a
pointer here).

    YYYY-MM-DD | script/command | key params | one-line outcome | commit hash

2026-10-01 | `analysis/power_basis.py` | MF pilot finetuned sign_c cells, parsed scoring; script 15's required_sets/mde, 80% power, |beta| > 0.2 | Storylines per foundation for 80% power: Gemma loyalty 13, fairness 17, purity 10, authority already powered; Mistral fairness 11, purity 10, loyalty 66, authority 357 (effect ≈ 0) — matches DESIGN.md §9. Llama: fairness no effect (|beta| < 0.2), but authority 14, purity 58, loyalty 99 (§9 says "no effect to power"). Basis for the 20-per-foundation target | a67a29a
