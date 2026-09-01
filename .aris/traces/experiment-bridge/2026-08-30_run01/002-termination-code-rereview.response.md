NOT_READY

Blocking findings:

- Cache consistency is not checked at `k=0`; hard gates compare only final and augmented components, not the actual mixed SLA logits. Run cache checks at all five prefixes and include `mixed` in no-op/batch/cache comparisons.
- Per-layer diagnostics are emitted only for VSV-off. Log off/on hidden norms and per-layer native/FP32 scales.
- Cohort building does not verify that `--m00-jsonl` actually came from the M00 generator. Require and validate the M00 config/summary provenance, including method, prompt, checkpoint, candidate-manifest hash, and DONE status.
- M0 provenance lacks builder commit/code hash, `tokenizer.model`, and the externally loaded CLIP vision tower.
- M00 records do not explicitly distinguish missing, exception, empty-after-decode, EOS-at-step-1, and short-nonempty outputs.

Nonblocking findings:

- Inference-mode/OOM safety, explicit checkpoint loading, cleanup, release-native SLA arithmetic, true FP32 projection, enforced prefixes, per-prefix no-op, and per-prefix repeated-batch controls are correct.
- Improve identical cohort-summary idempotence and split the descriptive interaction summary by precision path.
