# Result-to-Claim Verdict

**Verdict:** partial  
**Confidence:** medium  
**Integrity status:** warn

## What the results support

- The 64-image fixed-prefix experiment completed 64/64 with no exceptions.
- In batch=1 non-cached teacher forcing, VSV strongly raises the EOS margin before beam search. For collapse cases at `k=0`, `M10-M00 = +7.854` with 95% bootstrap CI `[7.564, 8.155]`.
- A modest positive VSV×SLA interaction exists only at the earliest prefixes: collapse `k=0: +0.294 [0.144, 0.451]`; `k=1: +0.213 [0.017, 0.425]`.
- Release-native and explicit FP32-projection results closely agree.

## What the results do not support

- They do not show that the combined method is uniformly more EOS-promoting than VSV alone. SLA alone lowers EOS margin, and the interaction is significantly negative at `k=3,5,10`.
- The interaction pattern is not detectably stronger in known collapse cases than in matched controls; all paired collapse-control interaction-difference intervals include zero.
- Fixed-prefix results do not establish that beam search merely amplifies an already-formed combined-method EOS bias. Four-method beam outcomes and internal beam traces have not yet been run.

## Revised claim

For this LLaVA-1.5-7B release/configuration, VSV strongly raises EOS relative margins on fixed M00 prefixes. VSV×SLA adds a modest positive interaction only at the earliest prefixes and counteracts later; this pattern is not collapse-specific. Whether beam search amplifies the early shift or introduces a separate dynamic failure remains unresolved.

## Next experiment

Run M00/M10/M01/M11 under greedy and beam=5 on the matched cohort, recording per-step EOS candidate retention, beam parents, cache reorder, finished hypotheses, and scores. This directly tests whether the observed early VSV shift predicts actual empty termination.
