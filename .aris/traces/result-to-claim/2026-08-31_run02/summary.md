# Result-to-Claim — Greedy/Beam Completion Gate

- verdict: partial
- confidence: medium
- integrity_status: warn
- review_independence: same-family
- acceptance_status: provisional

The 64-image mechanism-enriched cohort showed M11 empty decoding in 2/64 greedy runs and 28/64 beam=5 runs; M00, M01, and M10 each had 0/64 empty outputs in both decoder settings. Fixed-prefix B1 found a large VSV main effect on the collapse-group k=0 EOS margin (+7.854, 95% CI [7.564, 8.155]) and a small transient VSV×SLA interaction at k=0 (+0.294, 95% CI [0.144, 0.451]).

Route: repair the failed repeated-batch and cache consistency gates before B2. B2 counterfactual final-path/SLA-path decomposition remains warranted afterward, but cannot yet confirm double-path injection.
