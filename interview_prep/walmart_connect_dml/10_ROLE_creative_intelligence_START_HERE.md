# 10 — START HERE: Distinguished Data Scientist, Creative Intelligence (R-2630449)

**Walmart Ads · Walmart Global Tech · Sunnyvale · $169K–$338K base + bonus + stock · Interview: Mon Oct 19, 3:30 PM**

This file replaces `00`/`01` as your entry point. Files `02`–`09` are still useful **ads background**, so skim them. Files `90`/`91` (measurement) are optional.

---

## 1. Read the JD like an interviewer

The JD has **five technical pillars** and **one leadership pillar**. Every interview question will map to one of them.

| # | JD line (paraphrased) | What they really want | Your fit |
|---|---|---|---|
| P1 | **Generative creative systems**: images, copy, **video**, other assets; *high-quality, on-brand, compliant, performant* at advertiser scale | Someone who can architect generation that's product-faithful and brand-safe, and that actually lifts CTR | 🟢 **Images: very strong** (inpainting, diffusion, GANs, identity-preserving synthesis). 🟡 Copy (LLM) medium. 🟡 Video gen medium (strong video *eval* and frame synthesis) |
| P2 | **Automated evaluation, "models judging model output"**: *calibration* to human/advertiser preference, *drift detection*, *reliability at production scale*; defenses vs. *distortion, hallucination, policy violations* | **The heart of the role.** They name it twice (JD + requirements) | 🟡→🟢 You've **built and published a reference-free quality metric for generated video, with a negative result when it was used as a loss** (Goodhart). Gap: VLM-as-judge in production, calibration/drift ops |
| P3 | **Structured representations of creative content**: attributes, categories, quality signals, consumed by **targeting, recommendations, performance measurement** | A creative "genome" platform other teams adopt | 🟡 CV/CLIP/DINO strong. Gap: designing signals as products for ads consumers |
| P4 | **Automated composition & adaptation**: CV + generative; many formats and placements; no manual production | Layout, smart crop, outpaint, re-layout, legibility | 🟢 Inpainting/outpainting, depth, relighting, 3D graphics, compositing (dual-layer alpha compositing paper!) |
| P5 | **Shared infrastructure**: eval harnesses, generation pipelines, quality signals that *compound* | Platform thinking, not one-off projects | 🟡 OpenXR framework + SDK experience. Need to say it in ads terms |
| L | Translate *ambiguous, evolving* creative-product goals into a **sequenced roadmap**; Distinguished scope; influence without authority; explain tradeoffs to senior business audiences | Vision + execution + communication | 🟢 Beat-Google story, multimodal-fusion story, OpenXR extension proposal, 4× EVP awards |

**Minimum quals**: you exceed them (MS + 25 yrs). **Preferred**: publications ✅ (7), Python/torch/TF ✅, PhD ❌ (offset by publications + patents), Spark/Scala 🟡, **WCAG 2.2 AA accessibility**. That last one is a free differentiator: alt-text generation and contrast checks for generated creative (see §6).

### This is the best-fit role for your résumé
Unlike the general ads-ML roles, **this JD is mostly about generative CV with evaluation rigor, which is your core.** The interview will test whether you can (a) operate at **advertiser scale with safety built in**, (b) build **reliable automated judges**, and (c) connect creative to **ads business outcomes**. Those three are your study priorities.

---

## 2. Gap analysis (ranked by interview risk)

| Rank | Gap | Why it's risky | Where to study | Hours |
|---|---|---|---|---|
| 1 | **Model-as-judge in production**: VLM/LLM judges, rubric design, calibration to human/advertiser preference, position/verbosity bias, drift detection, abstention/routing, judge-of-judges, Goodhart | Core of the JD; you've built metrics but not a production judge system | **`12_automated_evaluation_model_as_judge.md`** + drills in `17` | 5 |
| 2 | **Ads business context for creative**: how creative affects CTR/CVR/ROAS, placements, Sponsored Brands/Display/Video specs, creative testing, bandits, performance measurement and its confounding | They're the Ads DS team; you must speak ads | `19_diagrams…`, `02` §1–4, `14` §8 | 3 |
| 3 | **Video generation at production scale** | JD lists video explicitly; your strength is frame synthesis/eval, not text-to-video products | `13_video_ad_generation.md` | 2.5 |
| 4 | **Safety, moderation, policy, IP "from the start"** | A requirement line on its own; a failure here is brand-damaging | `11` §7, `12` §5 | 1.5 |
| 5 | **Structured creative signals as a platform** (schema, versioning, consumers, adoption) | Needs platform/product framing | `14_creative_understanding_structured_signals.md` | 2 |
| 6 | **LLM copy generation** (grounded, compliant, constrained) | Medium; LLM fundamentals in `04` | `11` §4, `04` | 1.5 |
| 7 | **Production cost/scale of GPU generation** | Distinguished-level tradeoffs ($/asset) | `11` §8, `15` | 1 |
| 8 | **Latest model landscape** (FLUX/SD3/DiT, video DiTs, VLM judges) | Name-dropping correctly shows you're current | `11` §2, `13` §3 | 1 |

### Your strengths → JD mapping ("bridges"): memorize the left column

| Your work | JD pillar | One-liner |
|---|---|---|
| **Identity-preserving face synthesis** (AAD, ArcFace identity loss) | P1 product fidelity | "Brand creative is identity-preserving generation where the identity is the SKU. The product can't drift." |
| **Mask-based inpainting** (gated/partial conv, contextual attention, edge-conditioned) + **disocclusion inpainting** paper | P1/P4 background generation, outpainting for aspect-ratio adaptation | "Outpainting a 1:1 product shot to 9:16 is the inpainting problem I've shipped." |
| **Disocclusion detection by triangle-stretch analysis**: pixel-accurate *masks of where generation is needed*, leaving *verified pixels untouched* | P1/P2 "lock what's real, generate only what's needed, verify the rest" | This is exactly the product-lock principle |
| **Spherical-harmonics 360° lighting estimation + relighting** | P1/P4 harmonization: a pasted product must match scene lighting | "Most 'fake-looking' composites fail on lighting. I've built lighting estimators." |
| **Exemplar colorization (pyramid non-local attention)** | P1 brand-palette transfer, style from reference | Reference-guided generation |
| **Reference-free temporal-quality metric for generated video** + **negative result as training loss** | **P2 core**: automated judges, Goodhart, video eval | "I've built a judge, and I've watched a generator game it. That's why I design judges with held-out human anchors and never train against the deployed judge." |
| **Composite loss design** (perceptual/LPIPS, style/Gram, edge, MS-SSIM, ArcFace, adversarial, temporal) | P2 multi-dimensional quality scoring | Each loss term ≈ a judge dimension |
| **GANs (PatchGAN, multi-scale discriminators)** | P2 artifact/distortion detection: a discriminator *is* a learned artifact detector | "Patch discriminators localize artifacts, the same design as a production distortion detector with heatmaps." |
| **Diffusion + consistency models (few-step)** | P1 cost at scale | "Few-step distillation is the difference between $X and $X/8 per asset." |
| **DINO/MoCo/CLIP, distillation** | P3 creative embeddings; distill expensive VLM judges into cheap students | |
| **Single-model multimodal fusion beat per-sensor pipelines** | P3/P5 unified signals; one shared platform vs. per-project | "Compounding capability is the same argument: one shared model and signal store, not N silos." |
| **Motion-vector SpaceWarp (beat Google, default on Galaxy XR)**, frame interpolation | P1 video: interpolation, temporal consistency, warping-error metrics | Video temporal-consistency expertise |
| **Dual-layer alpha compositing** (SIGGRAPH/TOG submission) | P4 deterministic layered composition (product layer + text layer + generated background) | "Layered compositing with correct alpha is literally how ad templates render." |
| **Synthetic-data rigs, domain randomization** (warp-field paper) | P2 training artifact detectors with programmatically corrupted data | |
| **On-device quantization/distillation** | P5 serving cost | |
| **Stereo-mode detection patent** (classify image layout) | P3 image-format/structure classification | Small but relevant |
| **Bixby Store Assistant** | Retail/product search context | |

---

## 3. Your 90-second pitch (for THIS role)

> "I'm a Principal Engineer at Samsung. I've spent about a decade building generative vision systems from scratch and shipping them under hard constraints: inpainting, identity-preserving face synthesis, diffusion and consistency models, relighting from estimated scene lighting, and real-time frame synthesis. My motion-vector SpaceWarp beat Google's and became the default on Galaxy XR.
>
> Two things in this role match my work closely. **First, faithful generation.** In face synthesis the hard constraint is 'don't change who this is'. In ad creative it's 'don't change what this product is', and the techniques carry over: masks for what must stay real, generation only where needed, lighting harmonization, and identity losses.
>
> **Second, evaluation.** I published a reference-free quality metric for generated video, and then a negative result: when we trained against it, the model learned to game it. That experience shapes how I'd build a model-as-judge system: calibrated to human and advertiser preference, monitored for drift, and never the same judge you optimize against.
>
> What excites me about Walmart is the closed loop. You can generate creative, judge it, serve it, and learn from real shopper behavior, at a scale of thousands of brands and millions of products. I'd like to build the shared generation, evaluation and signal platform that makes that compound."

---

## 4. Your technical vision (answer to "what would you build here?")

**North star:** *Every advertiser, from a national CPG brand to a small marketplace seller, gets on-brand, compliant, high-performing creative for every placement, generated, judged, and improved automatically. Creative becomes a structured, measurable signal across Walmart Ads.*

**Five pillars (one sentence each, then go deep on whichever they pick):**
1. **Faithful generation by construction.** Hybrid pipeline: *real product pixels locked*, generative scene/background, *deterministic layout & text rendering*, lighting harmonization. Generate pixels only where generation is needed.
2. **A judge stack, not a judge.** Cheap deterministic checks → specialist detectors (artifacts, fidelity, OCR, policy, brand) → VLM rubric judge → **calibration layer mapping scores to P(human/advertiser approves)** → risk-based routing (auto-approve / human review / regenerate). Monitored for drift with golden sets and human audit sampling.
3. **Creative genome.** A versioned schema of creative attributes + embeddings + quality signals extracted for *every* creative (generated or uploaded), served via the feature store to targeting, ranking, recommendations, measurement and insights.
4. **Closed-loop optimization.** Variants → bandit serving → performance → creative performance model → *preference-tuned generation*, guarded against reward hacking by keeping the optimization reward separate from the safety/quality judges.
5. **Shared platform.** Generation gateway, eval harness, signal store, policy service, asset lineage. Every product (Automated Creative Generator, Sponsored Brands/Video builders, DSP display, Marty agent, Sparky) composes on it.

**Sequenced roadmap (say it this way):**
- **0–3 months: measure first.** Build the eval harness and golden sets, define the quality taxonomy and failure-mode catalog, put calibration dashboards on what exists today. Quick win: auto-adaptation of existing assets to more placements (crop/outpaint/re-layout) with fidelity gates.
- **3–9 months:** judge stack v1 in production with routing (cuts human review load), creative genome v1 (top 30 attributes + embeddings) adopted by one ranking/targeting consumer, image generation v2 with lighting harmonization and brand-kit conditioning.
- **9–18 months:** video adaptation and cut-downs, then image-to-video product animation. Closed-loop preference tuning from performance data. Creative insights for advertisers ("what works in your category") with proper causal controls.
- **18–24 months:** per-audience/per-placement personalized creative at serving time (template × asset × copy selection), conversational/agentic creative editing via Marty ("make it more summery").

**Name what you would NOT do first:** fully generative product imagery (hallucination risk), and training the generator against the same judge that gates quality (Goodhart). And no per-brand fine-tuned models before showing reference-adapter approaches can't reach quality (ops cost of thousands of LoRAs).

---

## 5. First 90 days (Distinguished version)
- **Days 1–30: listen and measure.** Meet product, engineering, ads ranking, policy/legal, brand-safety, measurement, and a few advertisers/agency users. Inventory existing generation and review pipelines. Collect 1–2K human-labeled examples per failure mode. Read the incident/rejection logs: *what fails today and why*.
- **Days 31–60: publish the eval contract.** Taxonomy of quality dimensions and failure modes; golden-set process; judge v0 calibrated against humans with reported agreement. Pick 2 high-leverage bets with owners.
- **Days 61–90: strategy doc + first win.** 18-month technical strategy reviewed with Product/Eng leadership; ship one measurable win (e.g. human review volume −40% at equal precision, or +N placements per asset with fidelity ≥ threshold).

---

## 6. Accessibility (preferred qual: easy points)
- **WCAG 2.2 AA** basics: text contrast **≥ 4.5:1** (normal) / **≥ 3:1** (large text ≥ 18pt or 14pt bold) and non-text UI 3:1; don't convey information by color alone; text alternatives for images (**alt text**); captions for video (prerecorded captions are Level A, audio description AA); avoid flashing > 3/sec.
- **Creative AI angle:** (1) **auto-generate alt text** for every ad image (VLM grounded in catalog), (2) **contrast check as a hard gate** in the layout engine, (3) **auto-captions** for video ads (also helps muted autoplay CTR), (4) legibility minimum font sizes per placement. "Accessibility is a judge dimension in my eval stack, and it also improves performance: captions help muted autoplay."
- Contrast formula: see `17_creative_coding_drills.py` (WCAG relative luminance).

---

## 7. Stories: re-aim the STAR stories from `06` at this JD

| Likely question | Story | Re-aim the ending at… |
|---|---|---|
| "Biggest impact" | SpaceWarp beat Google → default | Head-to-head eval decided it, so *evaluation drives decisions* |
| "Built an evaluation system" ⭐ | Temporal-Distance Predictability metric + negative result | Judge design, Goodhart, calibration, per-sample vs. distribution metrics (FVD can't score per-video) |
| "Generative system to production" ⭐ | Passthrough Eyes (identity-preserving expression synthesis, inpainting, colorization, real-time) | Fidelity constraints, composite losses, failure modes, latency budget |
| "Safety/constraints from the start" | Passthrough Eyes: identity preservation and not generating misleading faces; or SpaceWarp: never alter verified pixels | Constraints are part of the architecture, not a filter bolted on later |
| "Influence without authority / multiple workstreams" | Golf Mode: one fused model over per-sensor teams; OpenXR extension proposal | Shared platform over silos |
| "Ambiguous goals → roadmap" | Golf Mode AI from concept to SDK (vision, sensing, mapping, streaming) | Sequencing: what first, what later, why |
| "Explain a tradeoff to executives" | 4× EVP awards / exec demos (Autonomous Cab, Galaxy XR) | Translate quality vs. cost vs. latency into business terms |
| "Failure" | Metric-as-loss negative result | Integrity, and you published it |
| "CV depth" | Disocclusion detection via warp-Jacobian singular values + gated-conv U-Net (PSNR 11.85→19.84 dB in holes) | Artifact detection + targeted inpainting |

**Fill in real numbers before Monday** (latency, accuracy deltas, team sizes, adoption).

---

## 8. Study plan (Thu night → Mon 3:30 PM), creative edition

| When | What | Files |
|---|---|---|
| **Thu night (2–3 h)** | This file. Write your pitch. Skim the business diagrams (Part A) | 10, 19 Part A |
| **Fri AM (4 h)** | **Model-as-judge**: read fully, take notes, do drills 1–6 | **12**, 17 |
| **Fri PM (4 h)** | Generative image/copy/composition | **11**, 17 drills 7–12 |
| **Sat AM (4 h)** | Video + creative understanding | **13**, **14** |
| **Sat PM (4 h)** | System designs: say #1 and #2 out loud with a 40-min timer | **15** |
| **Sun AM (3 h)** | Ads business & ML diagrams (all of them); be able to draw 4 from memory | **19**, skim 02/03 |
| **Sun PM (4 h)** | Question bank: ⭐ questions aloud; behavioral stories aloud | **16**, 06 |
| **Sun eve (1.5 h)** | Full mock: pitch → design #3 → judge deep dive → 2 stories → your questions | 15, 12 |
| **Mon AM** | Cheat sheet only. Rest | **09** (creative version) |
