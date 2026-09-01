# Research Findings

## 2026-08-30 — VISTA fixed-prefix termination experiment

- **Experiment:** 32 historical combined-beam collapse cases plus 32 M00-length-matched controls; M00/M10/M01/M11 at fixed prefixes `k={0,1,3,5,10}`.
- **Execution:** 64/64 complete, no exceptions.
- **Verdict:** partial support, medium confidence; integrity audit remains WARN.
- **Supported:** VSV causes a large pre-beam upward EOS-margin shift; a smaller positive VSV×SLA interaction appears at `k=0,1`.
- **Not supported:** the interaction is not consistently positive, is not detectably collapse-specific, and does not yet prove beam is only an amplifier.
- **Constraint for future work:** do not infer beam mechanism from fixed-prefix logits alone. Run actual four-method beam outcomes and traces.
- **Primary result directory:** `newest_find_out/result/termination_audit/`.

## 2026-08-31 — Real decoding gate: greedy versus beam

- **Experiment:** completed the 64-image mechanism cohort under all four configurations for greedy decoding, and completed the matching M11 beam=5 recovery run.
- **Completion:** greedy 256/256 records and beam M11 64/64 records, both with zero exceptions.
- **Observed outcome:** M00/M01/M10 produced 0/64 empty outputs for both decoding settings. M11 produced 2/64 empty outputs under greedy (2/32 collapse, 0/32 control) and 28/64 under beam=5 (26/32 collapse, 2/32 control).
- **Working interpretation:** a pre-beam contribution is plausible, but beam=5 is a strong amplifier rather than a passive readout. The mechanism-enriched cohort cannot support prevalence claims.
- **Result-to-claim:** partial support, medium confidence, integrity WARN. Do not attribute the effect specifically to double-path injection yet: the prior repeated-batch and cache consistency gates remain unresolved.
- **Next gate:** repair and rerun the batch/cache/no-cache or FP32 reference controls before B2 counterfactual path decomposition. B2 remains the next supplementary discriminator only after those controls pass.

## 2026-08-31 — Batch/cache exclusion control

- **Experiment:** reran the preregistered 4-image batch-repeat and cache-consistency control with decision-level EOS/top-k logging; 4/4 images completed with no execution exceptions.
- **Strict numerical gate:** still failed (`batch` max all-vocabulary difference 0.0703; `cache` 0.03125, versus 0.002 tolerance).
- **Decision-level result:** the strongest non-EOS token was unchanged in all 240 batch and 240 cache comparisons; top-5 was unchanged in 236/240 batch and 239/240 cache comparisons. However EOS rank was exactly unchanged in only 97/240 batch and 141/240 cache comparisons (maximum rank shifts 27 and 32, respectively).
- **Conclusion:** ordinary FP16 arithmetic explains much of the all-vocabulary drift, but this control does **not** exclude EOS-rank sensitivity. Do not claim cache/batch artifacts have been ruled out, and do not advance to B2 as a confirmatory mechanism test. The next required control is beam-candidate/finished-hypothesis tracing around the affected EOS ranks, or a stronger FP32/no-cache reference.

## 2026-08-31 — B2 fixed-prefix path split

- **Experiment:** 64/64 mechanism-cohort images completed, with all five frozen prefixes and four counterfactual path combinations (1,280 records); no execution exceptions.
- **Result:** At k=0, mean EOS margin moved from -15.770 (C00) to -10.271 with VSV only in the final path (C10), -13.311 with VSV only in the SLA path (C01), and -7.881 with both paths (C11). The double-path interaction was -0.069, not a positive jump; it was also non-positive at k=1,5,10 and approximately zero at k=3.
- **Interpretation:** both paths move EOS upward, but the final path accounts for most of the shift and the joint effect is additive/sub-additive, not super-additive. This contradicts the planned double-injection mechanism claim. The pattern is nearly identical for collapse and control images, so it does not explain collapse selectivity.
- **Decision:** stop treating B2 generation validation as confirmation of double-path injection. Any further run should instead test the remaining alternative: VSV-induced EOS bias crossing a beam-search/scorer threshold.
