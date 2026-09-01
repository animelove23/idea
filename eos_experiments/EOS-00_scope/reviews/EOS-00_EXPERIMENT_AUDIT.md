# Experiment Audit Report: VISTA beam-5 EOS collapse

**Date**: 2026-08-30  
**Auditor**: fresh GPT-5.6-Sol ultra reviewer (same-family, provisional)  
**Project**: VISTA / LLaVA-1.5-7B CHAIR reproduction

## Overall verdict: WARN — mixed, primarily genuine VSV×SLA interaction

The artifacts support a real interaction between VSV and SLA under beam search, not a beam-cache or tensor-reordering implementation failure. The strongest evidence is the fixed ten-image ablation: VSV-only and SLA-only produce 0/10 empty captions, while their combination produces 8/10. Changing the code's six-state SLA window (`25,30`) to the paper-literal five-state window (`26,30`) leaves the rate at 8/10.

This is not a claim of exact paper reproduction. Several configuration and release discrepancies can affect the magnitude and portability of the effect.

## Checks

### A. Ground-truth provenance: PASS

CHAIR uses MSCOCO annotations through the project evaluation path; the observed empty-caption phenomenon is measured directly from generated captions before CHAIR scoring. The independent reviewer found no model-output-derived ground truth. Empty captions are nevertheless a metric confound: CHAIR counts them as captions with no unsupported objects, so they can mechanically improve hallucination metrics (`chair_ans.py:364`).

### B. Score normalization: PASS

No self-referential score normalization was found. The relevant evidence is the raw JSONL captions and the direct empty/length counts in `exp_results/new_observation/beam5_eos_collapse_ablation_20260830.md:10-78`.

### C. Result existence and scope: WARN

All cited replay JSONL files exist and reproduce the observation's counts. The original beam run contains 407/500 completed rows, not 500/500; therefore its 31.2% empty rate is conditional on completed rows. The ten-image module ablation and 32-image recheck complete successfully, but they are diagnostic samples rather than a full benchmark.

### D. Dead/misleading code: WARN

`chair_ans.py` is post-hoc scoring, not generation. The generation path is `chair_eval.py:60-142`. `return_dict=True` there is not `return_dict_in_generate=True`; several trace/position variables and `pos_emb` are unused. These do not explain the collapse but make the release harder to audit.

### E. Paper-to-code configuration: WARN

The paper specifies LLaVA-1.5 CHAIR with 500 COCO validation images, beam size 5, max 512 tokens, VSV lambda 0.17, and SLA gamma 0.3 with `w=5`. The local run has the following material differences:

| Setting | Paper/reported | Local release/run | Impact |
|---|---|---|---|
| SLA layers | `w=5`; 32-layer table corresponds to indices 26–30 | default `25,30` is inclusive, hence 6 states (`chair_eval.py:35`; `llava_llama.py:95-103`) | real drift; not dominant in ten-image ablation |
| Prompt | no final period | `Please help me describe the image in detail.` (`chair_eval.py:98`) | changes tokenization and VSV |
| VSV | raw positive-minus-negative residual direction with norm restoration | singleton PCA, normalization/cosine scaling, MLP wrapping (`steering_vector.py:113-129`; `llm_layers.py:15-32,132-150`) | not literal paper implementation |
| Stop criteria | not fully specified | inherited EOS=2/pad=0, `early_stopping=False`, `length_penalty=1.0`; no `min_new_tokens` (`chair_eval.py:123-135`) | allows first-token EOS to win |
| Sampling | 500 random images | seed 1994, but unsorted `os.listdir` before NumPy sampling (`eval_data_loader.py:14-16`; `chair_eval.py:81-85`) | image set is not portable |
| Environment | unspecified in paper | mixed CUDA/PyTorch/torchvision pins and foreign exported prefix (`environment.yml:21-27,170-171,243-254,288-299`) | portability risk |

### F. Beam control flow: PASS for structural correctness; WARN for behavior

The installed Transformers 4.37 path expands input/image tensors, reorders token sequences and KV cache, and safely broadcasts static VSV/SLA state. VSV hooks are active only during vector construction and are removed before generation. A synthetic exact-path cached five-beam test completed without shape/cache errors. No structural beam bug was found.

The behavioral mechanism is plausible and directly consistent with the code: SLA mixes raw logits as `0.3 * intermediate_average + 0.7 * final`; VSV changes the intermediate states used by SLA; beam search admits an EOS hypothesis once it is competitive among five beams, and length-penalized cumulative scoring can make an EOS-first hypothesis win. This is an interaction effect, not an EOS bonus guaranteed for every model.

### G. Quantitative evidence: WARN (strong diagnostic, limited scope)

Independent read-only recomputation of JSONL files:

| Condition | N | Empty | Rate | Mean decoded words |
|---|---:|---:|---:|---:|
| Combined VISTA beam, original | 407 | 127 | 31.2% | 131.25 |
| Combined VISTA greedy | 500 | 2 | 0.4% | 159.27 |
| Combined VISTA, `25,30` (w=6), ten-image replay | 10 | 8 | 80% | 50.6 |
| Combined VISTA, `26,30` (w=5), ten-image replay | 10 | 8 | 80% | 82.5 |
| VSV only, ten-image replay | 10 | 0 | 0% | 131.7 |
| SLA only, ten-image replay | 10 | 0 | 0% | 94.0 |
| Combined VISTA, `25,30`, 32-image recheck | 32 | 26 | 81.25% | 26.31 |

The 8/10 versus 0/10 gap is large enough to identify the joint configuration as the primary factor in this diagnostic, but not enough to establish a universal theorem about all beam settings or checkpoints.

### H. Evaluation type: real_gt with a decoding confound

The benchmark is `real_gt` for CHAIR annotations. The EOS/empty-caption analysis itself is a deterministic generation diagnostic. Because empty captions can score favorably under CHAIR, report empty rate and length distribution with CHAIR-S/I.

## Root-cause ranking

1. **Primary (high confidence):** VSV changes the intermediate hidden states that SLA reprojects into logits; their combination makes EOS competitive under beam scoring. Evidence: 8/10 combined versus 0/10 for either module alone, and 31.2% empty among 407 completed beam outputs versus 0.4% greedy.
2. **Secondary (medium confidence):** inherited EOS/stopping settings and beam length scoring expose the interaction; no `min_new_tokens` guard is used.
3. **Secondary (medium confidence):** released VSV implementation is not the paper equation (singleton PCA, MLP-only injection), so severity may be release-specific.
4. **Contributing (low-to-medium confidence):** six-layer default, prompt punctuation, nonportable image ordering, and environment drift.

## Minimal decisive follow-up

On the same ten fixed image IDs, hold checkpoint, prompt, seed, VSV and beam size fixed and sweep SLA gamma `{0, 0.05, 0.10, 0.20, 0.30}`. Log first-step EOS rank/logit/probability and empty rate for every image. Repeat the best gamma on a held-out 100-image COCO set. Run `min_new_tokens=16` only as a guardrail comparison; it prevents empty outputs but does not identify the causal logit interaction.

## Claim impact

- “The current VISTA implementation has a beam-5 EOS-collapse failure when VSV and SLA are combined”: **supported, qualified to this LLaVA-1.5-7B/checkpoint/configuration**.
- “The paper's exact configuration was reproduced”: **unsupported** until the layer window, prompt, VSV math, stopping settings, checkpoint revision, image IDs, and environment are aligned.
- “Beam search or KV-cache implementation is broken”: **not supported by current evidence**.
- “The interaction is universal across models/checkpoints”: **unsupported**; needs the gamma/EOS-rank/held-out follow-up.
