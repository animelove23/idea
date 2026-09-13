# VISTA Paper Compact Context for Codex

> Paper: **The Hidden Life of Tokens: Reducing Hallucination of Large Vision-Language Models via Visual Information Steering**
> Method: **VISTA = Visual Information Steering with Token-logit Augmentation**
> Scope of this note: method/framework + experimental setup/results + reproduction-relevant details.
> This is intentionally compact so a coding agent can use it instead of rereading the PDF.

---

## 1. Problem and core observation

VISTA is a **training-free, inference-time** method for reducing hallucination in LVLMs.

The paper motivates VISTA from token-logit ranking analysis and reports three observations:

1. **Gradual visual information loss**
   During long generation, visually grounded/genuine tokens become less favored while hallucinated tokens become more favored.

2. **Early excitation**
   Semantically meaningful tokens often reach stronger activation in layers shortly **before** the final layer, rather than at the final layer.

3. **Hidden genuine information**
   Some visually correct tokens are never decoded, although they still keep relatively high token-logit ranks internally.

These observations motivate two modules:

- **VSV (Visual Steering Vector)** → restore/reinforce visual information in activation/residual space.
- **SLA (Self-Logits Augmentation)** → reuse semantic information from late pre-final layers during decoding.

---

## 2. Base LVLM formulation

The input context is

```text
Xc = concat(Xs, Xv, Xq)
```

where:

- `Xs`: system-message tokens, possibly empty
- `Xv`: visual tokens from the vision encoder / multimodal interface
- `Xq`: user query tokens

Standard autoregressive generation uses the last-layer hidden state:

```text
x_t ~ softmax(H(h^L_{t-1}))
```

where `H` is the LM head and `L` is the final transformer layer.

The paper treats hidden states as a residual stream:

```text
h^l_t = h^(l-1)_t + a^l_t + m^l_t
```

where:

- `a^l_t`: MHA output
- `m^l_t`: FFN output

The residual stream is the intervention point used by VSV.

---

# 3. VISTA framework

## 3.1 VSV: Visual Steering Vector

### Goal

Construct an image-specific direction in activation space representing the contribution of visual information.

### Positive / negative context

```text
Positive:
Xp = concat(Xs, Xv, Xq)

Negative:
Xn = concat(Xs, Xq)
```

The negative context removes the image tokens while keeping the textual context.

Run both through the LVLM and collect the **last-token residual hidden state at every layer**.

```text
Vp = F(Xp)
Vn = F(Xn)
V_steer = Vp - Vn
```

Layer-wise:

```text
v^l_steer = v^l_pos - v^l_neg
```

VSV is computed **per image/input**, unlike amortized LLM steering vectors learned from many contrastive examples.

### Inference-time injection

At each decoding step and each transformer layer:

```text
h_tilde^l_t = h^l_t + lambda * v^l_steer
```

Then preserve the original hidden-state norm:

```text
h_tilde^l_t =
    h_tilde^l_t * ||h^l_t||_2 / ||h_tilde^l_t||_2
```

`lambda` controls visual-steering strength.

Interpretation:

```text
too small lambda -> weak visual reinforcement
moderate lambda  -> less hallucination
too large lambda -> over-emphasis on visual features, lower generation quality
```

---

## 3.2 SLA: Self-Logits Augmentation

### Goal

Use semantic information that appears strongly in the late layers before the final layer.

For decoding step `t`, take the `w` layers immediately before the final layer:

```text
layers: L-w, ..., L-1
```

Apply the same LM head to each hidden state and average:

```text
o_aug_t = (1/w) * sum_{l=L-w}^{L-1} H(h^l_t)
```

Final-layer logits:

```text
o_L_t = H(h^L_t)
```

Mix them:

```text
o_tilde_t = (1 - gamma) * o_L_t + gamma * o_aug_t
```

Then perform the normal decoding strategy on:

```text
softmax(o_tilde_t)
```

where:

- `gamma = 0` → normal final-layer decoding
- larger `gamma` → stronger contribution from earlier layers

The paper generally finds `gamma = 0.2–0.3` to give the best trade-off.

---

## 3.3 Combined inference flow

Conceptually:

```text
image
  |
vision encoder / multimodal projector
  |
visual tokens Xv
  |
  +--------------------------+
  |                          |
  v                          v
positive context Xp       negative context Xn
(with image)              (without image)
  |                          |
LVLM context forward     LVLM context forward
  |                          |
Vp per layer             Vn per layer
  +-----------+--------------+
              |
       V_steer = Vp - Vn
              |
              v
        autoregressive generation
              |
      each transformer layer
              |
 h <- h + lambda * V_steer[layer]
              |
       norm preservation
              |
  collect late pre-final hidden states
              |
 LM head on final layer + previous w layers
              |
 o = (1-gamma)*o_final + gamma*mean(o_early)
              |
       greedy / beam / nucleus
              |
           next token
```

The paper's Figure 3 visually shows three forward paths for explanation, but explicitly states that the three separate forward passes can be avoided in implementation.

No training or gradient update is required.

---

## 3.4 Implementation-oriented pseudocode

```python
# conceptual pseudocode, not literal repository API

# ---------- build image-specific steering vector ----------
pos = concat(system_tokens, visual_tokens, query_tokens)
neg = concat(system_tokens, query_tokens)

pos_h = model.context_forward(pos, return_hidden_states=True)
neg_h = model.context_forward(neg, return_hidden_states=True)

# take residual hidden state of the last context token for each layer
v_steer = [
    pos_h[layer][-1] - neg_h[layer][-1]
    for layer in range(num_layers)
]

# ---------- autoregressive generation ----------
for t in range(max_new_tokens):

    late_hidden = []

    for layer in range(num_layers):
        h_orig = transformer_block(layer, ...)

        # VSV
        h = h_orig + lambda_ * v_steer[layer]
        h = h * (norm(h_orig) / norm(h))

        if layer in range(num_layers - 1 - w, num_layers - 1):
            late_hidden.append(h)

    final_hidden = h

    final_logits = lm_head(final_hidden)

    # SLA: w pre-final layers
    aug_logits = mean([
        lm_head(h_l) for h_l in late_hidden
    ])

    logits = (1 - gamma) * final_logits + gamma * aug_logits

    next_token = decode(logits, strategy=...)
```

Exact hook/KV-cache details should follow the released repository; the paper specifies the math but not every software-engineering detail.

---

# 4. Token-ranking analysis used to motivate the method

For an image + LVLM-generated description, GPT-4o is used as an oracle to classify words into:

- **Decoded genuine**: generated and visually grounded
- **Hidden genuine**: visually present but omitted from the generation
- **Hallucinated**: generated but not visually grounded

The words are tokenized. If one word maps to multiple tokens, the paper uses the **first token as the proxy**.

For token `x`, layer `l`, time `t`:

```text
R^l_t(x) = rank(H(h^l_t), x)
```

Lower rank = higher probability.

Analysis setup:

- 500 random images from **MSCOCO**
- time is divided into **early / mid / late**
- temporal ranking aggregation uses only the **final five layers**
- layer-wise analysis averages over generation time

Main patterns:

```text
generation progresses:
genuine-token rank      -> worse
hallucinated-token rank -> better

across late layers:
semantic tokens often peak before final layer
```

This is the empirical motivation for VSV + SLA.

---

# 5. Experimental setup

## 5.1 LVLM architectures

Four LVLMs:

| Model | Visual-text alignment style |
|---|---|
| LLaVA-1.5 | linear projection |
| Shikra | linear projection |
| MiniGPT-4 | Q-Former |
| InstructBLIP | Q-Former |

The purpose is to show that VISTA is not tied to one multimodal architecture.

---

## 5.2 Decoding protocols

Three decoding strategies are tested:

```text
Greedy:
    choose highest-probability token

Beam search:
    beam_size = 5

Nucleus sampling:
    top_p = 0.9

Temperature:
    1.0 for all settings
```

---

## 5.3 Baselines

Besides the vanilla version of each decoding strategy:

- **DoLa**
  Internal / across-layer contrastive decoding in logits space.

- **VCD**
  Contrastive hallucination-mitigation baseline.

- **OPERA**
  Beam-search-specific hallucination mitigation.

- **PAI**
  Inference-time intervention method, the closest baseline to VISTA.

The paper reproduces baseline results using the same evaluation data/settings (prompt, temperature, etc.). Unsupported model/decoder combinations are omitted rather than reimplemented unofficially.

---

## 5.4 Default VISTA hyperparameters

Unless otherwise stated:

| Model | VSV lambda |
|---|---:|
| LLaVA-1.5 | 0.17 |
| MiniGPT-4 | 0.10 |
| Shikra | 0.12 |
| InstructBLIP | 0.17 |

Global SLA defaults:

```text
gamma = 0.3
w = 5
```

`lambda` and `gamma` are selected using a holdout validation set of:

```text
100 MSCOCO images
```

The selection criterion balances hallucination reduction and generation quality.

### Important POPE override

For **POPE**, output is only Yes/No and gradual visual-information loss is much less evident.

Therefore:

```text
VSV lambda = 0.01
```

for the POPE evaluation.

---

# 6. Benchmarks

## 6.1 CHAIR — main open-ended hallucination experiment

Purpose:

```text
open-ended image description / object hallucination
```

Data/config:

```text
dataset: MSCOCO 2014 validation
images: 500 randomly sampled
prompt:
"Please help me describe the image in detail"

max_new_tokens = 512
```

Metrics:

```text
CHAIR_I = hallucinated object instances / mentioned object instances
CHAIR_S = captions containing hallucinated object / all captions

lower = better
```

This is the most important reproduction benchmark if testing the paper's core hallucination claim.

---

## 6.2 POPE

Task:

```text
"Is there a <object> in the image?"
answer: Yes / No
```

COCO subset with three splits:

- random
- popular
- adversarial

Reported metrics:

```text
average Accuracy
average F1
higher = better
```

Because generation is very short, use the special `lambda = 0.01`.

---

## 6.3 MMHal-Bench

Contains:

```text
96 image-question pairs
```

Eight categories:

- ATTR: object attributes
- ADV: adversarial objects
- COMP: comparisons
- COUNT: counting
- SPAT: spatial relations
- ENV: environmental inference
- HOL: holistic description
- OTHER

Responses are evaluated using **GPT-4** against ground-truth answers.

Main-text comparison:

```text
Vanilla vs PAI vs VISTA
```

Greedy results are in the main paper; beam and nucleus results are in the appendix.

Reported trend:

- VISTA improves consistently across architectures
- approx. relative average-score gains:
  - LLaVA-1.5: ~20%
  - InstructBLIP: ~30%
- especially strong on ENV, ATTR, COUNT

---

## 6.4 MME

Full MME evaluation:

```text
14 visual-language abilities
perception + reasoning + knowledge integration
higher score = better
```

Used to check that hallucination mitigation does not destroy general LVLM capability.

---

# 7. Main CHAIR results

Format:

```text
Vanilla CHAIR_S / CHAIR_I  ->  VISTA CHAIR_S / CHAIR_I
lower is better
```

| Decoder | Model | Vanilla | VISTA |
|---|---|---:|---:|
| Greedy | LLaVA-1.5 | 46.4 / 12.1 | **20.4 / 6.9** |
| Greedy | MiniGPT-4 | 35.2 / 10.7 | **19.8 / 6.0** |
| Greedy | Shikra | 56.8 / 14.8 | **31.4 / 9.7** |
| Greedy | InstructBLIP | 38.0 / 10.7 | **27.4 / 8.1** |
| Beam | LLaVA-1.5 | 49.0 / 12.5 | **17.4 / 6.3** |
| Beam | MiniGPT-4 | 33.0 / 11.0 | **18.4 / 6.4** |
| Beam | Shikra | 53.8 / 14.4 | **32.2 / 9.5** |
| Beam | InstructBLIP | 37.8 / 10.7 | **26.8 / 7.8** |
| Nucleus | LLaVA-1.5 | 53.2 / 15.1 | **24.0 / 8.2** |
| Nucleus | MiniGPT-4 | 34.8 / 11.2 | **18.4 / 6.4** |
| Nucleus | Shikra | 56.4 / 15.9 | **31.8 / 9.7** |
| Nucleus | InstructBLIP | 46.6 / 13.1 | **29.4 / 9.1** |

Paper summary:

```text
VISTA gives roughly 40% relative hallucination reduction
over corresponding vanilla decoding in the open-ended task.
```

Important pattern:

```text
VISTA remains effective under greedy, beam, and nucleus.
```

---

# 8. POPE results

Format:

```text
Vanilla Avg.Acc / Avg.F1 -> VISTA Avg.Acc / Avg.F1
higher is better
```

| Decoder | Model | Vanilla | VISTA |
|---|---|---:|---:|
| Greedy | LLaVA-1.5 | 84.79 / 85.61 | **86.15 / 86.29** |
| Greedy | MiniGPT-4 | 76.76 / 76.82 | **77.06 / 77.80** |
| Greedy | Shikra | 81.32 / 82.01 | **82.44 / 82.47** |
| Greedy | InstructBLIP | 84.36 / 84.64 | **84.87 / 84.95** |
| Beam | LLaVA-1.5 | 85.45 / 84.93 | **85.83 / 85.95** |
| Beam | MiniGPT-4 | 73.68 / 72.40 | **75.96 / 77.17** |
| Beam | Shikra | 81.73 / 82.10 | **82.54 / 82.52** |
| Beam | InstructBLIP | 84.38 / 83.71 | **85.78 / 85.74** |
| Nucleus | LLaVA-1.5 | 81.26 / 82.40 | **85.35 / 85.54** |
| Nucleus | MiniGPT-4 | 60.56 / 62.04 | **66.96 / 68.05** |
| Nucleus | Shikra | 78.94 / 80.18 | **81.01 / 81.15** |
| Nucleus | InstructBLIP | 78.83 / 79.74 | **83.11 / 83.27** |

The improvement is most obvious under stochastic nucleus sampling.

---

# 9. MME full-set results

| Decoder | Method | LLaVA-1.5 | MiniGPT-4 | Shikra | InstructBLIP |
|---|---|---:|---:|---:|---:|
| Greedy | Vanilla | 1752.35 | 969.93 | 1101.50 | 1355.25 |
| Greedy | VISTA | **1771.87** | **1041.66** | **1256.22** | **1364.05** |
| Beam | Vanilla | 1749.57 | 869.74 | 1223.44 | 1357.02 |
| Beam | VISTA | **1763.15** | **1062.48** | **1323.25** | **1366.57** |
| Nucleus | Vanilla | 1625.22 | 845.30 | 1069.60 | 1397.71 |
| Nucleus | VISTA | **1738.56** | **1069.37** | **1254.31** | **1447.36** |

Conclusion:

```text
VISTA's hallucination reduction does not come from simply
suppressing generation; general multimodal performance is
maintained or improved.
```

---

# 10. Ablations

## 10.1 VSV strength lambda

Sweep in the main Shikra ablation:

```text
lambda = 0.00 ... 0.18
```

Trend:

```text
increasing lambda:
    CHAIR_S / CHAIR_I generally improve

too-high lambda:
    generation-quality F1 drops
```

Architecture-specific chosen values:

```text
MiniGPT-4  -> 0.10
Shikra     -> 0.12
LLaVA-1.5  -> 0.17
InstructBLIP -> 0.17
```

The appendix confirms architecture-specific sensitivity.

---

## 10.2 SLA mixing ratio gamma

Sweep:

```text
gamma = 0.0 ... 0.4
```

Trend:

```text
best trade-off around 0.2–0.3
too much early-layer mixing -> degraded generation quality
```

Default:

```text
gamma = 0.3
```

Interpretation: the final layer still contributes useful syntactic information, so replacing it too aggressively is harmful.

---

## 10.3 SLA window size w

Tested windows cover one through five pre-final layers.

For a 32-layer example:

```text
w=1: layer 31
w=2: layers 30-31
w=3: layers 29-31
w=4: layers 28-31
w=5: layers 27-31
```

General trend:

```text
larger window -> lower hallucination
```

Best reported configuration in Table 4:

```text
w = 5
gamma = 0.3
CHAIR_S = 42.8
CHAIR_I = 11.3
F1 = 78.4
```

The paper notes an inverse relation between window size and optimal gamma: broader windows may require more conservative mixing to remain stable.

---

## 10.4 VSV + SLA synergy

The lambda/gamma ablation matrices show that:

```text
VSV alone helps
SLA alone helps
moderate VSV + moderate SLA works best
```

They address complementary failure modes:

- VSV → insufficient visual grounding
- SLA → semantic information lost between pre-final and final layer

Generation quality remains relatively stable over a broad moderate parameter region.

---

# 11. Efficiency

Measured on LLaVA-1.5 with greedy decoding:

| Method | Latency (ms/token) | Throughput (token/s) |
|---|---:|---:|
| Vanilla Greedy | 28.54 (1.00x) | 35.04 (1.00x) |
| VCD | 58.34 (2.04x) | 17.14 (0.49x) |
| PAI | 57.78 (2.02x) | 17.31 (0.49x) |
| VISTA | **36.32 (1.27x)** | **27.53 (0.79x)** |

Thus VISTA adds ~27% latency over vanilla greedy in the reported setup and is substantially cheaper than VCD/PAI.

---

# 12. Evidence that VISTA fixes the identified phenomenon

The paper compares token rankings with and without VISTA.

Observed with VISTA:

```text
hidden genuine tokens:
    ranking improves / stays stronger

decoded genuine tokens:
    remain strongly ranked

hallucinated tokens:
    become less promoted, especially in mid/late generation
```

This directly connects the method back to the original "gradual visual information loss" diagnosis.

---

# 13. Minimal reproduction target for a coding agent

This section is a practical reproduction order, not an additional claim from the paper.

## Phase 1 — sanity check

```text
Model: LLaVA-1.5
Benchmark: CHAIR
Decoder: greedy
Prompt: "Please help me describe the image in detail"
Images: 500 MSCOCO 2014 val images
max_new_tokens: 512

lambda = 0.17
gamma = 0.3
w = 5
temperature = 1.0
```

Expected paper targets:

```text
Vanilla:
CHAIR_S = 46.4
CHAIR_I = 12.1

VISTA:
CHAIR_S = 20.4
CHAIR_I = 6.9
```

If this works, expand to:

```text
1. SLA-only
2. VSV-only
3. VSV + SLA
4. lambda/gamma sweep
5. beam search
6. nucleus sampling
7. other architectures
8. POPE / MMHal-Bench / MME
```

---

# 14. Code components Codex should look for / implement

Likely conceptual modules:

```text
model loading
visual-token creation
generation loop
residual-stream access / layer hooks
context hidden-state extraction
VSV construction
VSV residual injection
hidden-state norm restoration
pre-final hidden-state collection
LM-head projection of intermediate layers
SLA logits mixing
greedy decoder
beam decoder
nucleus decoder
CHAIR evaluation
POPE evaluation
MMHal evaluation
MME evaluation
ablation runner
latency/throughput profiler
```

Recommended internal API shape:

```python
compute_visual_steering(model, image, prompt) -> list[layer_vector]

generate_with_vista(
    model,
    image,
    prompt,
    vsv_lambda,
    sla_gamma,
    sla_window,
    decoding_strategy,
    ...
) -> text

evaluate_chair(outputs, annotations) -> chair_s, chair_i
```

---

# 15. Important implementation cautions

1. **VSV is layer-specific.**
   Do not compute one vector and reuse it for all layers.

2. **VSV is input/image-specific.**
   It is not a learned global steering vector.

3. **Negative context removes visual tokens but retains textual context.**

4. **Normalize after VSV injection.**
   The norm-preservation equation is part of the method.

5. **SLA uses layers before the final layer.**
   Do not include the final layer in `o_aug`; final logits are mixed separately.

6. **Use the same LM head for intermediate hidden states** (logit-lens style).

7. **SLA mixing happens before token selection.**
   Then greedy/beam/nucleus operates on the mixed logits.

8. **POPE uses a smaller lambda (`0.01`).**

9. **Do not train the LVLM.**
   VISTA is inference-time only.

10. **For baseline comparison, keep prompt/temperature/data identical.**

---

# 16. Items the paper does NOT clearly specify

Do not silently invent these when reproducing:

- exact GPU type / hardware used for the main experiments
- random seed for the 500-image sampling
- all exact checkpoint-size details in the experimental section
- every low-level hook / KV-cache optimization detail
- exact software environment versions in the paper text

For these, inspect the released repository/configs rather than guessing.

---

# 17. One-paragraph summary for Codex

VISTA is a training-free inference-time hallucination-reduction method for LVLMs. For each image/query, construct a per-layer Visual Steering Vector by subtracting the no-image context's last-token residual state from the image-conditioned context's state. During autoregressive decoding, add `lambda * v_steer[layer]` to every layer's residual state and renormalize to preserve the original norm. In parallel, Self-Logits Augmentation applies the LM head to the `w` layers immediately before the final layer, averages those logits, and mixes them with the final logits as `(1-gamma)*final + gamma*early_avg` before normal greedy/beam/nucleus decoding. Default `gamma=0.3`, `w=5`; lambda is model-specific (`0.17` LLaVA-1.5/InstructBLIP, `0.10` MiniGPT-4, `0.12` Shikra), with POPE using `0.01`. The main CHAIR experiment uses 500 MSCOCO-2014-val images, prompt `"Please help me describe the image in detail"`, max 512 new tokens, and reports large CHAIR_S/CHAIR_I reductions across four LVLMs and three decoding strategies.
