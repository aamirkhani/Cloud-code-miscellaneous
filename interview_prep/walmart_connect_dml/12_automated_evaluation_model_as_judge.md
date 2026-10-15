# 12 — Automated Evaluation of Generated Creative ("Models Judging Model Output")

> The JD names this twice: *"Design and own automated systems that evaluate generated creative quality, using models to judge model output, including calibration against human/advertiser preference and defenses against common failure modes (distortion, hallucination, policy violations)"* and *"Proven experience designing automated model-evaluation systems… including calibration, drift detection, and reliability at production scale."*
> **Treat this as the most important chapter.** Expect at least one deep dive on it.

---

## 0. The one-paragraph answer (memorize)

> "I'd build a **judge stack**, not a single judge. Cheap deterministic checks run first: format, safe zones, WCAG contrast, OCR diff against catalog text, product-fidelity similarity. Then specialist detectors for artifacts, policy and brand. Only then does a VLM judge score against a rubric. Every score passes through a **calibration layer** that maps it to the probability a human reviewer or advertiser would approve, fit on a continuously refreshed human-labeled set. A **risk-based router** auto-approves only where calibrated precision is above target for that category, sends uncertain or high-risk items to humans, and regenerates clear failures. I monitor **drift** on the generator, the judges, and the input mix with golden sets, distribution tests and audit sampling. And I never let the generator optimize directly against the deployed gatekeeper. My published negative result is exactly that failure: the model learned to game the metric."

---

## 1. Why evaluation is the bottleneck

- Generation is cheap; **human review is not**. At advertiser scale (thousands of brands × millions of SKUs × dozens of placements × variants) creative volume grows **combinatorially**, while human review capacity grows linearly. The **judge's precision at the auto-approve threshold determines how much of the generation you can actually ship.**
- **Trust asymmetry**: one hallucinated product claim or distorted logo shown to a national brand costs more than a thousand good images earn. That cost asymmetry should set the operating point, not accuracy.
- Evaluation is also the **training signal** (reward models, rejection sampling, preference data) and the **product metric** (are we getting better?). So evaluation sits at three places at once: gatekeeper, coach, and scoreboard. **Separate them** (see §8).

---

## 2. What "quality" means for ad creative: the taxonomy

Define a **failure-mode catalog** *before* building judges. Each dimension gets an owner, a detector, a golden set, and a target.

| Dimension | Failure modes | Severity | Typical detector |
|---|---|---|---|
| **Product fidelity** | Product morphed/redrawn, wrong color/variant, wrong count, missing/duplicated items, packaging text garbled, logo altered, scale implausible (giant cereal box) | 🔴 Critical (misrepresentation) | Reference-based: masked DINO/CLIP similarity vs. catalog image, SSIM/LPIPS in product region, OCR diff vs. catalog text, logo detector match, keypoint/shape alignment |
| **Visual distortion / artifacts** | Melted geometry, extra fingers/limbs, warped text, texture repetition, halos/seams at composite boundary, inconsistent shadows/lighting, color banding, over-saturation (high CFG), blur, compression | 🟠 High | Artifact classifier (trained on synthetic corruptions + labeled failures), patch-level anomaly maps, IQA models, boundary-gradient checks |
| **Hallucination (text/claims)** | Copy states attributes not in catalog ("organic", "family size"), wrong price, invented discount, superlatives ("#1", "best"), health claims; image shows features the product lacks | 🔴 Critical | NLI/entailment of each claim vs. catalog attributes; price/promo check vs. pricing service; claim-pattern classifiers; VLM image-vs-attribute verification |
| **Policy & safety** | Nudity, violence, weapons, minors in unsafe contexts, hate symbols, drugs/alcohol rules, regulated categories (OTC/health, baby formula, firearms-adjacent), political, sensitive events | 🔴 Critical | Moderation classifiers (image + text + OCR'd text), category-policy rules engine, VLM policy judge for nuanced cases |
| **IP / brand safety** | Competitor logos, trademarked characters, celebrity likeness, copyrighted artwork styles, other brands' products in scene | 🔴 Critical | Logo detection against a blocklist, face recognition only for celebrity *blocking*, product detector "other-brand" check |
| **Brand compliance** | Off-palette colors, wrong font, logo too small/misplaced, violating clear space, off-tone copy | 🟠 High (advertiser trust) | Palette ΔE in CIELAB vs. brand kit, layout rule validator, tone classifier, VLM rubric |
| **Composition & legibility** | Text over busy background, low contrast (WCAG), text in unsafe zones, cropped product, clutter, poor hierarchy | 🟡 Medium | Deterministic: contrast ratio, safe-zone geometry, text-area ratio, saliency overlap; learned aesthetic/composition score |
| **Aesthetic / appeal** | Bland, unrealistic, "AI look", mismatched season, low perceived quality | 🟡 Medium | Aesthetic predictors, pairwise preference models (Bradley–Terry on human/advertiser choices) |
| **Relevance / fit** | Scene doesn't fit product (sunscreen in snow), audience/placement mismatch | 🟡 Medium | VLM judge + CLIP text-image alignment |
| **Performance potential** | Likely low CTR | 🟢 Optimize, not gate | Creative performance model (pCTR from creative features) |
| **Accessibility** | Missing alt text, contrast fail, no captions (video) | 🟡 Medium (WCAG) | Deterministic checks + alt-text generation & verification |

**Distinguished point:** quality is **multi-dimensional with different loss functions**. Critical dimensions are **gates** (veto, optimize for recall of failures); appeal and performance are **objectives** (rank, optimize, A/B). Never collapse them into one scalar "quality score" for gating. A beautiful image that misrepresents the product must fail regardless of aesthetics.

---

## 3. Architecture of the judge stack

```
                         ┌─────────────────────────────────────────────────────────────┐
 generated creative ───► │ STAGE 0  Deterministic checks (ms, ~free)                   │──fail──► reject + reason → regenerate
 (+ request context:     │  format/size · safe zones · WCAG contrast · font min size   │
  SKU, brand kit,        │  OCR diff vs catalog text · price/promo vs pricing service  │
  placement, category)   └───────────────┬─────────────────────────────────────────────┘
                                         ▼ pass
                         ┌─────────────────────────────────────────────────────────────┐
                         │ STAGE 1  Specialist models (10–100 ms, GPU-cheap)            │
                         │  product-fidelity (masked DINO/CLIP sim, LPIPS in mask)      │
                         │  artifact/distortion detector (+ heatmap)                    │
                         │  moderation (image, OCR text, copy) · logo/IP detector       │
                         │  brand palette ΔE · aesthetic/IQA · claim-NLI vs catalog     │
                         └───────────────┬─────────────────────────────────────────────┘
                                         ▼
                         ┌─────────────────────────────────────────────────────────────┐
                         │ STAGE 2  VLM rubric judge (100s ms–s, expensive)             │
                         │  only for items not already decided; rubric per dimension;  │
                         │  structured JSON output: score, evidence, failure tags      │
                         └───────────────┬─────────────────────────────────────────────┘
                                         ▼
                         ┌─────────────────────────────────────────────────────────────┐
                         │ CALIBRATION LAYER                                            │
                         │  per-dimension raw scores → P(human approves | features)    │
                         │  segmented by category / placement / generator version      │
                         └───────────────┬─────────────────────────────────────────────┘
                                         ▼
                         ┌─────────────────────────────────────────────────────────────┐
                         │ RISK-BASED ROUTER                                            │
                         │  auto-approve if P(approve) ≥ τ_cat AND no critical flag    │
                         │  human review if uncertain / high-risk category / new brand │
                         │  reject+regenerate if P(approve) ≤ τ_low                    │
                         └───┬──────────────────┬──────────────────────┬────────────────┘
                             ▼                  ▼                      ▼
                       advertiser preview   human review queue     regenerate (with failure tags
                       (approve/edit/reject) (labels!)              fed back into prompt/params)
                             │                  │
                             └──────► LABEL STORE ◄────── audit sample of auto-approved (e.g. 1–2%)
                                         │
                       ┌─────────────────┴──────────────────┐
                       ▼                                    ▼
             recalibrate weekly / on drift          retrain specialists & judge prompts/fine-tunes
                       │
               MONITORING: drift on inputs, generator outputs, judge scores, agreement with humans
```

**Design principles to say out loud:**
1. **Cascade by cost**: cheap and deterministic first. ~60–80% of decisions can often be made before the VLM (a plausible design target; measure it).
2. **Structured, evidence-bearing outputs**: every judge returns `{dimension, score, confidence, failure_tags, evidence (bbox/heatmap/quoted text)}`. Evidence makes human review faster and regeneration targeted.
3. **Calibrated probabilities, not raw scores**, so thresholds mean something and stay stable when a judge model is swapped.
4. **Segmented thresholds**: the auto-approve threshold for "baby formula" ≠ "paper towels." Risk-tiered by category and advertiser tier.
5. **Humans are a sensor, not a fallback**: every human decision is a label; an audit sample of auto-approved items measures real precision.
6. **Version everything**: generator version, judge version, rubric version, calibration version. Any decision is reproducible.

---

## 4. The VLM judge: how to make it good

### 4.1 Rubric design
- **One question per dimension**, concrete and observable: "Is the product's packaging text identical to the reference? Answer yes/no and quote any differences," not "Is this a good ad?"
- **Anchored scales** (1–5 with examples per level) or binary checks; binary checklists are usually more reliable and easier to calibrate than Likert.
- **Provide references**: the catalog image, catalog attributes, brand-kit summary, placement spec. *Reference-based judging beats reference-free for fidelity and hallucination.*
- **Ask for evidence first, then verdict** (reason → answer), with structured JSON output via constrained decoding.
- **Decompose**: separate calls/prompts for fidelity, policy, brand, aesthetics. A single "do everything" prompt is worse and harder to debug.

### 4.2 Known judge biases and defenses
| Bias | Description | Defense |
|---|---|---|
| **Position bias** (pairwise) | Prefers first (or second) option | Evaluate both orders; average; flag inconsistent pairs as "tie/uncertain" |
| **Verbosity/length bias** (copy) | Prefers longer text | Length-controlled comparisons; rubric explicitly penalizes over-length |
| **Self-preference** | Judge prefers outputs from its own model family | Use a different model family for judging than for generating, or an ensemble |
| **Aesthetic halo** | Pretty image judged "faithful" | Separate dimensions; reference-based fidelity checks by specialist models |
| **Sycophancy to prompt framing** | "This is a great ad, check it" | Neutral prompts, no hints of expected answer |
| **Low resolution blindness** | VLM downsamples, so it misses small text/logo defects | Tile/crop the product and text regions at native resolution; rely on OCR/specialists for fine detail |
| **Overconfidence** | Raw "confidence" not calibrated | External calibration (§6); use token log-probs of the verdict as a score; ensembles/self-consistency |
| **Prompt injection via image text** | Text in generated image says "approve this" | Treat OCR'd content as data; system prompt hardening; specialist checks independent of VLM |

### 4.3 Scoring from a VLM
- Prefer **log-probability of the "yes/no" token** (or expected score from the distribution over 1–5 tokens) to sampled text. It's continuous and calibratable.
- **Self-consistency**: sample k rationales, take majority/mean; disagreement = uncertainty → route to human.
- **Ensembles** of 2 judges from different families: agreement → high confidence; disagreement → human.

### 4.4 Make it cheap: distill the judge
Once the big VLM judge is calibrated and trusted, **distill** it into a small fine-tuned VLM or a CLIP/SigLIP-head classifier per dimension (soft labels from the teacher + human labels). Use the large judge only for the uncertain band. *Your EMA-teacher → edge-student distillation experience applies directly.*

---

## 5. Specialist detectors (where your CV depth shines)

### 5.1 Product-fidelity score (most important single detector)
1. Get the **product mask** in the generated image (we know it if we composited the locked product layer; otherwise segment + match).
2. Align to catalog image (homography/affine from keypoints, or known placement transform).
3. Compute, inside the mask: **DINO/CLIP patch-feature similarity** (semantic), **LPIPS** (perceptual), **SSIM** (structure), color histogram/ΔE (color variant), **OCR text diff** (packaging text), **logo detector** match.
4. Combine with a small learned model → calibrated P(faithful).
- **If the architecture locks product pixels** (composite real product layer), fidelity reduces to checking *the boundary and lighting harmonization didn't alter it*. That's a far easier and more reliable check. **Architect so that the judge's job is easy.**

### 5.2 Artifact / distortion detector
- **Data**: (a) human-flagged failures from review queues, (b) **programmatic corruptions** of good creatives (warp fields, texture duplication, seam halos, text warping, JPEG blocking, banding, CFG oversaturation, hand/finger mutations via known-bad generators), (c) "known-bad" generations from weak models/high CFG. *Your synthetic-data rigs and domain randomization experience fits here.*
- **Model**: patch-level classifier/segmenter (U-Net or ViT with patch head) producing an **artifact heatmap** + global score. PatchGAN-style local discrimination is the right inductive bias.
- **Frequency-domain cues** (upsampling checkerboard, spectral peaks) help for generated-image detection.
- **Boundary-specific check** for composites: gradient/color discontinuity along the product mask contour, shadow consistency (does the product cast a shadow consistent with estimated light direction? Your SH lighting work applies).

### 5.3 Text hallucination & claims (copy and in-image text)
- Extract claims from copy (LLM or rules) → each claim checked by **NLI** against catalog attributes/specs/reviews summary → "entailed / contradicted / unsupported." Unsupported is a fail for factual claims.
- Regex/classifier for **prohibited claim patterns** ("#1", "best", "cures", "guaranteed", "clinically proven" without substantiation).
- **Price/promo**: must match the pricing/promo service at render time, ideally *rendered by the template from live data*, never generated.

### 5.4 Policy & moderation
- Multi-modal: image classifier + OCR'd text + copy + metadata (category). Category-specific policies via a **rules engine** (e.g. alcohol ads: no minors, age-gating placement).
- **Asymmetric thresholds**: high recall on critical classes; humans resolve borderline.

---

## 6. Calibration against human & advertiser preference (core JD keyword)

### 6.1 What you calibrate *to*
- **Human reviewer decisions** (policy/quality approve vs. reject): the gatekeeping target.
- **Advertiser decisions** (accept/edit/reject in the creative builder; which variant they pick): preference target. Advertisers are **noisy, brand-specific, and biased toward their existing style**, so model per-brand or per-segment effects.
- **Shopper behavior** (CTR/CVR): performance target. **Not** a calibration target for safety.
These three can disagree. Keep them as **separate heads/scores**.

### 6.2 Getting good labels
- **Rater guidelines** with examples per failure mode; training and qualification tests for raters.
- **Inter-rater agreement** (Cohen's κ for 2 raters, Fleiss/Krippendorff α for more). *A judge cannot be expected to agree with humans more than humans agree with each other.* Report **judge–human κ next to human–human κ**.
- **Gold questions** embedded in rater queues to monitor rater quality.
- **Stratified sampling**: oversample rare failure modes and high-risk categories; record sampling weights to un-bias metrics.
- **Disagreement resolution**: adjudication by senior reviewers. Keep disagreement as a signal of ambiguous guidelines.

### 6.3 Calibration methods
- **Platt scaling** (logistic regression on the raw score/logit): few parameters, stable with small data.
- **Isotonic regression**: monotone, non-parametric, needs more data. Good once you have thousands of labels per segment.
- **Multi-feature calibration**: a small logistic/GBDT model taking all judge scores + category + placement + generator version → P(approve). This is the **meta-judge**. Keep it simple and monotone where possible.
- **Segment-wise calibration** with hierarchical shrinkage for small segments (partial pooling toward the global curve).
- **Metrics**: ECE, reliability diagrams, Brier score, log loss; **precision at the auto-approve threshold** (the business-critical number); recall of critical failures.

### 6.4 Choosing operating points (the routing math)
- For each segment, pick τ_approve such that **precision(auto-approved) ≥ target** (e.g. 99% for critical categories, 97% for low-risk), using a held-out labeled set with confidence intervals (Wilson/Clopper–Pearson lower bound ≥ target, not just the point estimate).
- **Coverage** = fraction auto-decided. Business value = coverage × volume × (human cost per item) − (residual error rate × cost per error).
- **Expected cost formulation**: approve iff P(bad) × C_bad < C_review. With C_bad ≫ C_review, the threshold is very conservative. *State that the costs come from policy/legal and the business, not from the DS team.*

### 6.5 Pairwise preferences → scores
- Collect **pairwise comparisons** (A vs. B) from advertisers/raters; fit **Bradley–Terry** (P(A≻B) = σ(s_A − s_B)) or **Elo** for streaming. That gives a latent preference score per creative/variant/style and is the training data for **reward models** and **Diffusion-DPO**.
- Pairwise is more reliable than absolute ratings for subjective dimensions (appeal).

### 6.6 Advertiser preference modeling
- Hierarchical model: global preference + per-category + per-brand offsets (brands differ: premium beauty ≠ value grocery).
- Use advertiser edits as rich signal: "changed background," "changed headline" tells you *which dimension* failed.

---

## 7. Drift detection & reliability at production scale

### 7.1 What drifts
| Source | Example | Detect with |
|---|---|---|
| **Input mix** | New categories onboarded, holiday season themes, new placement formats | PSI/KS on input features (category mix, image stats, embedding clusters) |
| **Generator** | New model version, prompt template change, upstream API model silently updated | Golden-prompt regression suite (fixed seeds); output embedding distribution shift; judge-score distribution shift |
| **Judge** | Judge model/provider update, prompt change, VLM non-determinism | **Fixed golden set re-scored daily**: score shift on identical inputs = judge drift (not generator drift). Pin judge versions |
| **Human labels** | Guideline changes, rater pool changes | Gold questions, rater κ trends |
| **Concept** | What advertisers/shoppers like changes; policies change | Calibration curve shift; advertiser acceptance trend |

**Key technique, worth saying explicitly:** *Disentangle generator drift from judge drift.* Re-score a **frozen** set of creatives with the current judge (judge drift), and score **fresh outputs from frozen prompts** with a **frozen** judge (generator drift). Two controlled measurements, like an A/A test for evaluation.

### 7.2 Monitoring metrics & alerts
- Daily: auto-approve rate, human-overturn rate on the audit sample, approval rate by segment, judge score distributions (PSI vs. reference week), judge–human agreement on fresh labels, failure-tag frequencies, latency/cost per item, timeouts/abstentions.
- Change detection: **CUSUM** or EWMA charts on approval/overturn rates; PSI > 0.2 = investigate (rule of thumb).
- **Canary every model/prompt change**: run new generator/judge on shadow traffic and compare decisions; require agreement/precision gates before ramp.

### 7.3 Reliability engineering for judges
- **Determinism**: temperature 0, pinned model versions, cached results keyed by (asset hash, judge version).
- **Timeouts & fallbacks**: if the VLM judge is down, **fail closed** (route to human or hold), never fail open to auto-approve.
- **Abstention**: judges output "uncertain" and the router honors it.
- **Rate-limits & cost budgets** per product; graceful degradation (skip aesthetic judge, never skip policy).
- **Audit trail**: why was this creative approved? All scores, versions, and evidence are stored. Needed for advertiser disputes and regulators.
- **Red-teaming**: adversarial prompts/assets (prompt injection in text, near-miss logos, borderline policy content) in the regression suite.

---

## 8. Goodhart's law: judges as optimization targets (your signature topic)

**The trap:** once a judge score is used as a reward (RLHF/DPO for diffusion, best-of-N, rejection sampling, prompt optimization), the generator finds the judge's blind spots: oversaturated "aesthetic" images, text the OCR misses, compositions that please the VLM but not humans.

**Your story:** *"I built a reference-free temporal-quality metric for generated video that correctly flagged frozen, reversed and shuffled clips. When I tried using it as a training loss, the model learned to satisfy the metric without improving real temporal quality. I published that as a negative result. It's why I separate gatekeeper, coach and scoreboard."*

**Defenses:**
1. **Separation of roles**: the **reward model** used for optimization ≠ the **gatekeeper judges** ≠ the **evaluation scoreboard** (held-out human-validated set that nothing trains on).
2. **KL regularization** to the reference model during preference tuning; early stopping on held-out human eval.
3. **Reward ensembles** and **uncertainty penalties**: optimize against the mean minus λ·std across reward models.
4. **Best-of-N with small N** is a safer optimizer than RL against the reward (bounded exploitation).
5. **Periodic human re-anchoring**: fresh human labels on current generator outputs to detect reward hacking (judge score ↑ but human preference flat or ↓).
6. **Track the gap**: plot judge score vs. human score over training. Divergence is the alarm.

---

## 9. Offline ↔ online: does the judge predict business outcomes?

- Judge scores measure **acceptability**; CTR measures **performance**. Validate the relationship: do higher-appeal creatives get higher CTR **in controlled tests** (same product, same placement, randomized creative)? Observational correlations are confounded by brand, budget, placement, and category.
- **Creative A/B tests / multi-armed bandits** within an ad group isolate the creative effect.
- Use online results to **fit a performance head** (creative pCTR model) with creative features + embeddings. That's the "performant" in the JD.
- **North-star metric set for the creative platform**: % of advertisers using generated creative, assets shipped per advertiser, **human review cost per shipped asset**, critical-error rate in production (from audits/advertiser complaints), creative-level CTR lift vs. advertiser-supplied baseline in randomized tests, time-to-launch.

---

## 10. Evaluating the evaluator: the metrics table to show

| Metric | Target example | Why |
|---|---|---|
| Recall on critical failures (policy/fidelity/hallucination) | ≥ 99% on golden set | Safety |
| Precision of auto-approve | ≥ 97–99% (by risk tier; lower CI bound) | Trust |
| Coverage (auto-decided %) | Maximize subject to above | Cost/scale |
| Judge–human κ vs. human–human κ | Judge within ~0.05 of human–human | Is the judge "human-level"? |
| ECE of calibrated P(approve) | < 0.02–0.03 | Thresholds are meaningful |
| Drift: PSI of judge scores week-over-week | < 0.1 normal; > 0.2 investigate | Stability |
| Audit overturn rate | Tracked daily, CUSUM alerts | Production truth |
| Cost & p95 latency per creative | Budgeted | Scale |

---

## 11. Video-specific evaluation (brief; details in `13`)
- Per-frame image checks on sampled frames + **temporal** checks: product-identity tracking across frames (embedding similarity of tracked product region to the reference over time), OCR stability of packaging text across frames, flicker/warping error (optical-flow-warped frame differences), motion presence (frozen detection), **temporal-order plausibility (your metric)**, audio checks (ASR → text moderation, loudness), caption correctness.
- FVD is distribution-level and **cannot gate individual videos**. Per-video judges are needed; that's literally what your paper addresses.

---

## 12. Interview drill: likely deep-dive questions and crisp answers

1. **"How do you know your LLM/VLM judge is any good?"** Compare to human labels on a stratified, adjudicated set; report judge–human agreement relative to human–human agreement; precision/recall per failure mode at the operating threshold with CIs; calibration (ECE); stability (re-score golden set daily).
2. **"The judge and advertisers disagree. Who wins?"** Depends on the dimension. On policy/fidelity, policy wins (advertisers can't approve a misrepresentation). On appeal/brand style, the advertiser's preference wins, and their choices become labels to recalibrate the preference head per brand.
3. **"How do you detect hallucinated product details in an image?"** Architect them away (locked product layer, template-rendered price), then reference-based checks: masked feature similarity, OCR diff, logo match, VLM yes/no verification of specific attributes against catalog.
4. **"What if the VLM provider updates their model?"** Pin versions; the golden set re-score detects drift; recalibrate before switching; shadow-run the new judge and compare decisions.
5. **"How would you cut human review by half without losing safety?"** Calibrate, segment thresholds by risk, raise coverage in low-risk segments first, cascade cheap checks, distill judges, add evidence to speed remaining reviews, and measure with audit sampling.
6. **"How do you set the threshold?"** Expected-cost or precision-target with a lower confidence bound on a held-out set, per segment, revisited when calibration drifts.
7. **"How do you prevent reward hacking when fine-tuning the generator?"** Separate reward model from gatekeepers and scoreboard; KL; ensembles; best-of-N; human re-anchoring; watch the judge–human divergence curve.
8. **"Why not one big VLM judge for everything?"** Cost, latency, low-res blindness, opaque failures, harder calibration; specialists are cheaper, localizable and individually testable; VLM is best for nuanced semantic checks.
9. **"How do you handle rare failure modes with few labels?"** Synthetic corruptions, targeted red-teaming, active learning (sample high-uncertainty items for labeling), stratified oversampling with weights.
10. **"What's drift detection for a judge, concretely?"** Two controlled tests: frozen inputs + current judge (judge drift), frozen judge + fresh outputs from frozen prompts (generator drift); plus PSI/KS on live score distributions and CUSUM on overturn rate.
