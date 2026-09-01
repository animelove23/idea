# Observation: beam5 EOS collapse under VISTA on LLaVA-1.5

Date: 2026-08-30  
Model: LLaVA-1.5-7B (`llava-v1.5-7b`)  
Dataset: MSCOCO 2014 validation images  
Prompt: `Please help me describe the image in detail.`

## Scope

The original VISTA beam5 CHAIR run exhibited frequent empty captions. An empty caption means the first generated token was EOS (token id 2); it is not a JSON-writing or post-processing failure.

The initial result file contains 407/500 completed images, of which 127 are empty captions (31.2%). The corresponding VISTA greedy run contains 2 empty captions among 500 images (0.4%).

To isolate the cause, the first ten image IDs with empty captions in the original beam5 output were replayed individually and in fixed order:

`220182, 449485, 104893, 116521, 553698, 153445, 150320, 142483, 414501, 457584`.

All replays use `num_beams=5`, `max_new_tokens=512`, seed 1994, and the same model/checkpoint/data/prompt. Each row reports decoded word count; zero denotes an empty caption.

## Raw data

| Image ID | Original beam5 | VISTA w=6 (`25,30`) | VISTA w=5 (`26,30`) | VSV only (lambda=0.17) | SLA only (gamma=0.3, w=5) |
|---:|---:|---:|---:|---:|---:|
| 220182 | 0 | 0 | 0 | 49 | 58 |
| 449485 | 0 | 0 | 0 | 1 | 91 |
| 104893 | 0 | 45 | 0 | 64 | 94 |
| 116521 | 0 | 0 | 364 | 346 | 67 |
| 553698 | 0 | 461 | 461 | 39 | 119 |
| 153445 | 0 | 0 | 0 | 7 | 122 |
| 150320 | 0 | 0 | 0 | 398 | 113 |
| 142483 | 0 | 0 | 0 | 7 | 48 |
| 414501 | 0 | 0 | 0 | 21 | 134 |
| 457584 | 0 | 0 | 0 | 385 | 81 |

| Configuration | Empty captions | Mean decoded words |
|---|---:|---:|
| Original beam5 selection | 10 / 10 | 0.0 |
| VISTA, default code window `25,30` (six states) | 8 / 10 | 50.6 |
| VISTA, paper-literal `w=5` window `26,30` | 8 / 10 | 82.5 |
| VSV only | 0 / 10 | 131.7 |
| SLA only | 0 / 10 | 92.7 |

## Findings

1. **Observation:** Correcting the SLA window from the code default `25,30` (inclusive: six hidden states) to the paper-literal five-state window `26,30` did not reduce the empty-caption rate: both runs produced 8/10 empty captions. The two settings differ only on boundary samples (`104893` versus `116521`).

   **Interpretation:** The window off-by-one discrepancy is real, but it is not the dominant explanation for the EOS collapse in this sample.

   **Implication:** A paper-faithful `w=5` setting alone is insufficient to make beam5 usable.

2. **Observation:** VSV only produced 0/10 empty captions, and SLA only produced 0/10 empty captions. Their combination at lambda=0.17 and gamma=0.3 produced 8/10 empty captions under beam5.

   **Interpretation:** The EOS collapse is an interaction effect between VSV-induced residual-stream changes and SLA logits mixing, rather than an independent failure of either module.

   **Implication:** The joint hyperparameter configuration is not calibrated for beam5 on this checkpoint, even though it matches the paper's reported nominal values.

3. **Observation:** The full VISTA output is sensitive near the decision boundary: separate replays of the same image can switch between EOS and a long caption. However, the 8/10 versus 0/10 ablation gap is large enough to establish the interaction as the primary factor in this diagnostic.

   **Interpretation:** Beam candidate ordering is sensitive to small logit changes, while the VSV+SLA combination systematically moves EOS into competitive first-step ranks.

   **Implication:** Subsequent evaluations must report empty-caption rate and decoded-length distribution alongside CHAIR, otherwise an EOS collapse can look deceptively favorable on hallucination metrics.

## Suggested next experiments

1. Sweep SLA gamma with VSV fixed: gamma in `{0.00, 0.05, 0.10, 0.20, 0.30}` on the same ten image IDs, then validate the best setting on a held-out 100-image COCO set.
2. At each gamma, log the first-step EOS rank, logit, and probability for every image; this directly tests the proposed beam-EOS mechanism.
3. Run `min_new_tokens=16` only as a guardrail comparison. It prevents empty outputs but does not identify or correct the underlying logits interaction.

## Source artifacts

- Original beam5: `../chair_three_decode/llava-1.5/seed1994_vsv_lambda_0.17_logaug_loglayer_25,30_logalpha_0.3_beam5_max_new_tokens_512.jsonl`
- Original greedy: `../chair_three_decode/llava-1.5/seed1994_vsv_lambda_0.17_logaug_loglayer_25,30_logalpha_0.3_greedy_max_new_tokens_512.jsonl`
- VISTA w=6 replay: `../chair_beam_empty32_recheck/llava-1.5/seed1994_vsv_lambda_0.17_logaug_loglayer_25,30_logalpha_0.3_beam5_max_new_tokens_512.jsonl`
- VISTA w=5 replay: `../chair_beam_empty10_w5/llava-1.5/seed1994_vsv_lambda_0.17_logaug_loglayer_26,30_logalpha_0.3_beam5_max_new_tokens_512.jsonl`
- VSV only: `../chair_beam_empty10_vsv_only/llava-1.5/seed1994_vsv_lambda_0.17_beam5_max_new_tokens_512.jsonl`
- SLA only: `../chair_beam_empty10_sla_only/llava-1.5/seed1994_org_logaug_loglayer_26,30_logalpha_0.3_beam5_max_new_tokens_512.jsonl`
