# 09 — Day-of Cheat Sheet: Distinguished DS, Creative Intelligence (Mon 3:30 PM)

## The role in one line
Set direction for **generate → judge → understand → adapt → learn** for ad creative (image, copy, video) at Walmart advertiser scale, on **shared infrastructure**.

## Your 3 headline proofs
1. **Beat Google → shipped as default** (motion-vector SpaceWarp, Galaxy XR). Evaluation decided it.
2. **Built a judge, watched a model game it, published the negative result** (Temporal-Distance Predictability metric for generated video).
3. **Faithful generation from scratch**: identity-preserving face synthesis, inpainting, diffusion/consistency models, SH relighting, alpha compositing (SIGGRAPH/TOG submission).

## Bridges (say these phrases)
- "Ad creative is **identity-preserving generation where the identity is the SKU**."
- "**Lock what's real, generate only where needed, verify the rest.**" (disocclusion paper: verified pixels untouched)
- "**A judge stack, not a judge.**" Cascade by cost; calibrated to P(human approves); risk-routed.
- "**Separate the gatekeeper, the coach, and the scoreboard.**" (Goodhart)
- "Most fake-looking composites fail on **lighting**. I've built lighting estimators."
- "**One shared platform, not N silos**": like the single fused model that beat per-sensor pipelines.

## Judge stack (draw it)
Deterministic (format, safe zones, WCAG contrast, OCR diff, live price) → Specialists (fidelity, artifacts+heatmap, moderation, logo/IP, palette ΔE, claim-NLI) → VLM rubric judge (reference-based, evidence-first, JSON, logprob scores) → **Calibration** (Platt/isotonic per segment → P(approve)) → **Router** (auto-approve if calibrated precision lower-CI ≥ target · human · regenerate) → labels → recalibrate · drift monitors.

## Numbers & formulas
- WCAG contrast: (L₁+0.05)/(L₂+0.05); **≥ 4.5:1 normal, ≥ 3:1 large text** (≥18pt / 14pt bold) and UI components. L = 0.2126R + 0.7152G + 0.0722B on linearized sRGB.
- Cohen's κ = (pₒ − pₑ)/(1 − pₑ). Judge–human κ should approach human–human κ.
- Bradley–Terry: P(A≻B) = σ(s_A − s_B). Elo: s ← s + K(outcome − expected).
- PSI = Σ (a−e)·ln(a/e); < 0.1 stable, > 0.2 investigate.
- ECE = Σ_b (n_b/N)·|acc_b − conf_b|.
- Threshold: auto-approve iff P(bad)·C_bad < C_review; pick τ so the **lower CI bound** of precision ≥ target.
- Cost: few-step distilled diffusion ~1–2 GPU-s/image vs. ~10–20 s at 30–50 steps (assumption). Cache and adapt rather than regenerate.
- eCPM = bid × pCTR × 1000; creative affects pCTR → revenue and advertiser ROAS.

## Vision (5 pillars)
1. Faithful generation by construction (hybrid: locked product + generated scene + deterministic layout).
2. Judge stack with calibration, routing, drift monitoring.
3. Creative genome: attributes + embeddings + quality signals in the feature store.
4. Closed-loop optimization (bandits → performance model → preference tuning) with anti-reward-hacking guardrails.
5. Shared platform: generation gateway, eval harness, signal store, policy service, lineage.

**Roadmap:** 0–3 mo eval harness and taxonomy + placement adaptation win → 3–9 mo judge v1 with routing, genome v1, harmonized image gen → 9–18 mo video, closed-loop tuning, insights → 18–24 mo serve-time personalization, conversational editing (Marty).

## Must-mention concepts ☐
product lock · harmonization/relighting · brand kit (reference adapters vs per-brand LoRA) · claim NLI vs catalog · live price rendering · WCAG/alt text/captions · C2PA/disclosure · calibration per segment · position/verbosity/self-preference bias · frozen-input vs frozen-judge drift tests · fail-closed · audit sampling · Goodhart/KL/ensembles/best-of-N · randomized creative tests (confounding!) · Thompson sampling · distill judges · cost per *shipped* asset

## When stuck
"Let me separate what must be *guaranteed* from what should be *optimized*." Then: guarantee via architecture and gates, optimize via preference and performance.

## Questions to ask them (pick 3–4)
1. "Where is the bottleneck today: generation quality, review throughput, or advertiser adoption?"
2. "How is generated creative evaluated now, and how much still goes through human review?"
3. "What share of advertisers are long-tail sellers without design resources? Is that the primary customer?"
4. "How do creative signals reach ranking and targeting today? Is there a shared feature store for creative?"
5. "What's the video roadmap across Sponsored Videos, DSP and Vizio CTV?"
6. "What does success look like for this role in 12 months?"
7. "How do DS, engineering and policy/legal split ownership of safety decisions?"

## Logistics
Join 5 min early · water · pen & paper for diagrams · ask clarifying questions before designing · always end with risks + roadmap · close: "The overlap between what this role needs and what I've built (faithful generation and honest evaluation) is unusually high. I'd love to build this platform here."
