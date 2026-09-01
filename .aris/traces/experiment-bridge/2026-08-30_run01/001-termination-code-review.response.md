# Experiment Code Review

**Reviewer**: fresh GPT-5.6-Sol, xhigh  
**Review independence**: same-family  
**Acceptance status**: provisional  
**Deployment verdict**: NOT_READY

## BLOCKING issues that must be fixed before GPU deployment

1. Manual forwards run with autograd enabled and are likely to OOM. `model.eval()` does not disable gradients. VSV extraction and every fixed-prefix, repeated-batch, and cached forward occur outside `torch.inference_mode()`. Moving outputs to CPU without detaching retains graphs. Wrap all per-image inference, including `obtain_vsv`, in `torch.inference_mode()`.

2. The reported logits are neither release-exact FP16 logits nor the promised FP32 projections. Final logits are projected in model dtype and then cast, while each SLA projection is cast before averaging; mixing is consequently FP32. Preserve a release-exact path by averaging/mixing before casting, and separately compute clearly labeled FP32 projections from FP32 hidden states and LM-head weights.

3. Required B1 diagnostics are missing. The implementation discards per-SLA-layer logits and hidden states, so there are no hidden norms or per-layer SLA logit-scale measurements required by the plan. Log these during the first GPU run to avoid rerunning.

4. The default fixed-prefix experiment uses only `0,1,3`, while the preregistered set is `{0,1,3,5,10}`. No-op is tested only at prompt position and repeated batch only at `k=0`; the planned per-prefix numerical control is incomplete. Use all five prefixes and run the relevant controls at them.

5. The generated mechanism cohort does not use preregistered M00 baseline lengths. It uses the existing VSV+SLA greedy artifact and raw nearest-word matching, rather than M00 greedy lengths and same-decile controls. Rebuild Cohort M after producing M00 baseline lengths.

6. M0 provenance is insufficient. Cohort metadata hashes only selected ID lists. The sanity config lacks source/manifest hashes, checkpoint/config hash, code commit/dirty state, dependency versions, model dtype, and explicit generation defaults. Record the actual runtime configuration before deployment.

7. Frozen manifests can be silently overwritten. Cohort outputs are rewritten unconditionally. Refuse overwrite or verify an existing manifest is byte-identical.

8. Checkpoint lookup depends on working directory. `ModelLoader` uses `../download_models/llava-v1.5-7b`; this fails when launched from `/workspace`. Accept and use an explicit resolved checkpoint path, then record that path.

9. Runtime failures do not produce honest completion records. A short M00 prefix raises immediately; other exceptions can leave partial JSONL with no final summary, and rerun then refuses the directory. Catch per-image/run failures, write explicit exception or early-EOS records and a final FAIL summary, and restore model state in an outer `finally`.

## NON-BLOCKING issues

- Validate that custom prefix sets contain zero and a positive value; current summary `max()` calls otherwise fail.
- Cohort output filenames hard-code `100` and `64` even when CLI sizes differ.
- Rename generic summary `status` to `hard_checks_status`; it is not a mechanism verdict.
- Four-image interaction mean/min/max is only sanity output and must not be interpreted as bootstrap evidence.

## CORRECT aspects worth preserving

- Defaults correctly use paper prompt without period, VSV λ=0.17, SLA γ=0.3, and indices 26–30.
- M00/M10/M01/M11 mapping and interaction arithmetic match the plan.
- Prefix construction is correct for LLaVA image-token expansion.
- Final-position and hidden-state layer indexing match the release.
- Cache masks/past lengths are apples-to-apples.
- Batch repetition and wrapper cleanup are correct in a fresh model.
- EOS probability/rank/margin, entropy, scale and top-token metrics are correct.
- Cohort construction enforces uniqueness and balanced paired IDs.

## Final deployment verdict

**NOT_READY**