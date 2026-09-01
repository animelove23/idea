# Experiment Code Review — Re-review 1

**Reviewer**: fresh GPT-5.6-Sol, xhigh  
**Review independence**: same-family  
**Deployment verdict**: NOT_READY

## Blocking findings

1. Cache consistency was not checked at `k=0`, and hard gates compared only final and augmented components rather than the actual mixed SLA logits. Cache checks must run at all five prefixes and no-op/batch/cache checks must include `mixed`.
2. Per-layer diagnostics were emitted only for VSV-off. Both off/on hidden norms and per-layer native/FP32 logit scales are required.
3. Cohort construction did not validate that the supplied baseline JSONL came from the registered M00 generator/config/summary. It must verify method, prompt, checkpoint, candidate-manifest hash, and DONE status.
4. M0 provenance omitted builder code/commit, `tokenizer.model`, and the externally loaded CLIP vision tower.
5. M00 output records did not explicitly distinguish `missing_record`, `exception`, `empty_after_decode`, `eos_at_step1`, and `short_nonempty`.

## Nonblocking findings

- Inference-mode/OOM safety, explicit checkpoint loading, release-native SLA arithmetic, separate FP32 projection, all five prefix values, per-prefix no-op and batch controls, cleanup, and frozen-output refusal were accepted.
- Cohort summary idempotence and precision-separated interaction summaries should be improved.

## Gate decision

GPU deployment remains blocked. This is the one allowed re-review under the current experiment-bridge cadence; the blocking findings must be fixed and reviewed in a subsequent continuation before launch.
