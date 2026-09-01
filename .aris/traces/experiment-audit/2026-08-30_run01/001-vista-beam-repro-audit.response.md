Independent reviewer findings (read-only):

Paper-faithful LLaVA-1.5 CHAIR setup: 500 randomly sampled MSCOCO-2014 validation images; prompt “Please help me describe the image in detail” without a terminal period; max_new_tokens=512; beam size 5; temperature 1.0; VSV all layers lambda=0.17; SLA gamma=0.3 and w=5. The published LLaVA-1.5 beam target is vanilla CHAIR-S/I 49.0/12.5 and VISTA 17.4/6.3. The paper does not specify seed/image IDs, exact checkpoint hashes, EOS/pad IDs, early stopping, length penalty, or software versions.

Material configuration differences: chair_eval.py defaults logits-layers='25,30'; the patch interprets endpoints inclusively, so indices 25–30 are six states. A literal five-state window for a 32-layer model is 26–30. The prompt in chair_eval.py has a terminal period. Image enumeration uses unsorted os.listdir, so seeded sampling is not portable without a released image-ID list. The release VSV implementation fits PCA to a singleton pair, normalizes activation/VSV, applies cosine-dependent lambda_sim, preserves MLP-output norm, and wraps layer.mlp; this is not the literal paper residual-stream equation. generate() passes no explicit EOS/pad/min_new_tokens/early_stopping/length_penalty settings; local Transformers 4.37.0 and checkpoint defaults supply eos=2, pad=0, early_stopping=False, length_penalty=1.0.

Beam-control audit: no structural beam/cache mismatch was found. Transformers 4.37 expands input_ids, image tensors and masks; reorders token sequences and KV cache; VSV is static model state and broadcasts safely; SLA ranges/scalars are static and preserve the leading beam dimension; VSV hooks are only active during the two VSV-forward passes and are removed before generation. A CPU synthetic exact-path test completed five-beam cached generation without shape/cache errors. The behavior is therefore not explained by a beam reorder or JSON/post-processing bug.

Mechanism: SLA mixes raw logits as 0.3*intermediate-average + 0.7*final. VSV changes the intermediate states used by SLA, so the combined effect is nonlinear with respect to the final decoded distribution. Beam search admits EOS when it enters the top five, and length-penalized cumulative scores can let a first-token EOS hypothesis win. No explicit EOS bonus exists, so the effect is model/data dependent, but it is systematic in these artifacts.

Quantitative evidence: combined VISTA beam produced 127 empty captions among 407 completed outputs (31.2%), while combined VISTA greedy produced 2/500 (0.4%). On the fixed ten-image ablation, original beam5 was 10/10 empty; VISTA with code window 25,30 was 8/10 empty; paper-literal 26,30 was also 8/10 empty; VSV-only was 0/10; SLA-only was 0/10. Mean decoded words were 0.0, 50.6, 82.5, 131.7, and 92.7 respectively. The 32-image w=6 recheck was 26/32 empty (81.25%). Run logs complete the 10/10 and 32/32 replays; the 407/500 original run is incomplete, so its rate is conditional on completed rows.

Dead/misleading code: chair_ans.py is post-hoc scoring, not generation; img_start_idx/img_end_idx are unused; attention traces and pos_emb are unused; return_dict=True is not return_dict_in_generate=True. CHAIR treats empty captions as having no unsupported objects, so EOS collapse can mechanically improve CHAIR.

Verdict: mixed but primarily genuine VSV×SLA interaction under beam search, not a structural beam implementation failure. Confidence 85%. The incorrect six-layer default, punctuation, non-literal VSV implementation, unspecified stopping defaults, and environment inconsistencies are real reproducibility problems and may change severity, but they do not explain the decisive 8/10 versus 0/10 module ablation gap; changing 25,30 to 26,30 leaves 8/10 empty. Minimal decisive follow-up: on the same fixed IDs, sweep gamma with VSV fixed (0, .05, .10, .20, .30), record first-step EOS rank/logit/probability and empty rate, and repeat the best setting on a held-out 100-image set; include min_new_tokens=16 only as a guardrail comparison.

Evidence references:
- /workspace/VISTA/exp_results/new_observation/beam5_eos_collapse_ablation_20260830.md:10-78
- /workspace/VISTA/chair_eval.py:35,49-64,98,123-142
- /workspace/VISTA/llava/model/language_model/llava_llama.py:89-103
- /workspace/VISTA/steering_vector.py:29,65,113-129
- /workspace/VISTA/llm_layers.py:15-32,132-150
- /workspace/VISTA/model_loader.py:433
- /workspace/VISTA/eval_data_loader.py:14-16
- /workspace/VISTA/environment.yml:21-27,156,170-171,243-254,288-299
- local Transformers 4.37 generation/utils.py:553,2948,3001-3013; beam_search.py:264,946
- local LLaVA config.json and generation_config.json: eos=2, pad=0

review_independence=same-family; acceptance_status=provisional; reviewer_model=gpt-5.6-sol; reviewer_reasoning=ultra.