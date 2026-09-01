# Fixed-prefix factorial results (64 images)

- Completed: 64/64; exceptions: 0.
- Native-vs-FP32 EOS-margin mean absolute difference: 0.005055.

## FP32 interaction by cohort and prefix

| Cohort | k | Mean interaction | 95% bootstrap CI |
|---|---:|---:|---:|
| collapse | 0 | 0.2940 | [0.1445, 0.4507] |
| collapse | 1 | 0.2128 | [0.0173, 0.4249] |
| collapse | 3 | -0.6830 | [-0.7749, -0.5897] |
| collapse | 5 | -0.6900 | [-0.9080, -0.4829] |
| collapse | 10 | -0.7682 | [-0.9163, -0.6187] |
| control | 0 | 0.1507 | [0.0300, 0.2730] |
| control | 1 | 0.1657 | [-0.0203, 0.3617] |
| control | 3 | -0.7440 | [-0.8453, -0.6465] |
| control | 5 | -0.8544 | [-1.0719, -0.6497] |
| control | 10 | -0.6756 | [-0.8455, -0.5131] |

Positive interaction means M11 shifts EOS margin upward beyond additive VSV and SLA effects; negative means sub-additive/counteracting interaction.

Full method means are in `method_summary.csv`; all main effects and interactions are in `effect_summary_bootstrap.csv`.
