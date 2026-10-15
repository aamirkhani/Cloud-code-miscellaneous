# 15 — Creative Intelligence System Designs (6 full walkthroughs)

Use the framework from `05`: **Clarify → Metrics → Architecture → Deep dive → Scale/cost → Eval & launch → Risks & roadmap.** For this role, also always cover: **safety by design**, **the judge stack**, and **what becomes shared platform**.

Time budget for a 45-min design: 5 clarify · 5 metrics · 8 architecture · 15 deep dive · 5 scale · 4 eval/launch · 3 roadmap.

---

## Design 1: "Generate Sponsored Brands / display creative for any advertiser from a product SKU"

### 1. Clarify (ask 3–4 of these)
- Who: national brands with brand kits, or long-tail sellers with only catalog images? (Both. Long tail benefits most.)
- Which formats: Sponsored Brands banner, display IAB sizes, social-style 1:1/9:16, CTV end cards?
- Interactive (advertiser waits in UI) or bulk (generate for all SKUs overnight)? (Both. Interactive needs ~5–20 s preview; bulk is throughput-optimized.)
- Human review today? Approval SLA? Policy constraints per category?
- Success = adoption + performance + no brand/policy incidents.

### 2. Metrics
- **Adoption**: % advertisers using generated creative; assets launched per advertiser; time-to-launch.
- **Quality/safety**: critical-failure rate in production (audit), human-review overturn rate, advertiser rejection/edit rate.
- **Performance**: creative-level CTR/CVR vs. advertiser-uploaded baseline **in randomized within-ad-group tests**; ROAS.
- **Efficiency**: $ and GPU-seconds per *shipped* asset (not per generated), human-review minutes per shipped asset.
- **Guardrails**: shopper experience (ad CTR shouldn't come from clickbait), latency.

### 3. Architecture
```
Advertiser intent (SKU(s), goal, placements, brand kit, optional prompt)
   │
   ▼
Context assembly ─► Catalog service (images, title, attributes, price, category, policy class)
   │               Brand-kit store (logo, palette, fonts, tone, do/don't rules)
   │               Placement specs (sizes, safe zones, text limits)
   ▼
PLANNER (LLM, structured output): creative brief → N concepts {scene, mood, season, layout family, copy angle}
   │
   ├─► PRODUCT LAYER: best catalog image → segmentation/matting (alpha) → cleanup → LOCKED
   ├─► SCENE LAYER: diffusion background generation conditioned on concept + product placement mask
   │                (inpaint/outpaint around fixed product; depth/edge ControlNet for perspective; IP-adapter for brand style)
   ├─► HARMONIZATION: estimate scene lighting → relight product edges, contact shadow, color match (product pixels' identity preserved)
   ├─► COPY: LLM grounded in catalog attributes + brand tone → headline/sub/CTA candidates (JSON, length-limited)
   │         → claim-NLI check vs catalog → banned-claim filter
   ▼
COMPOSITION ENGINE (deterministic renderer): layout template/learned layout → place layers, logo, text (brand fonts),
   price/badges rendered from LIVE pricing data, legibility & WCAG contrast enforced, per-placement adaptation
   ▼
JUDGE STACK (file 12): deterministic → specialists → VLM rubric → calibration → router
   ▼
Advertiser review UI (variants, edit controls, "why flagged" evidence) ─► approve ─► asset store (+lineage, C2PA)
   ▼                                                                                   │
Ad serving (creative selection via bandit) ─► impressions/clicks/orders ─► performance store ─► learning loop
```

### 4. Deep dive (pick the 2–3 they care about)
**a. Why the hybrid ("generate background, compose deterministically") architecture:**
- Product pixels are real → fidelity by construction; judges only verify the boundary.
- Text, logo, price rendered deterministically → no garbled text, exact brand fonts, live prices, WCAG checks are exact.
- Generative model does what it's good at: scenes, mood, lighting, context.
- Tradeoff: less "magical" integration (e.g. product interacting with hands). Handle with harmonization (shadows, relighting) and a later tier of controlled full-generative scenes with stricter judging.

**b. Harmonization (your edge):** estimate lighting of generated scene (SH coefficients or env map), relight the product layer with an SH shading ratio applied to the alpha-matted product (subtle, bounded so identity is preserved), add contact shadow from estimated light direction and a depth/ground-plane estimate, match color temperature. Without this, composites look "pasted."

**c. Brand conditioning at scale:** thousands of brands → per-brand LoRA has ops cost (training, storage, swapping). Default: **reference-based conditioning** (IP-Adapter-style style references + palette constraints + prompt from brand kit); per-brand LoRA only for top-spend brands where evals show a gap. Enforce palette with ΔE checks.

**d. Copy:** catalog-grounded generation; constrained to placement lengths; claims checked by NLI; tone classifier vs. brand tone; Spanish variants.

**e. Variant strategy:** generate K concepts × M renders → judge → keep top few diverse (MMR on embeddings) → advertiser picks → bandit decides in serving.

### 5. Scale & cost
- Back-of-envelope (state assumptions): 1M SKUs × 5 placements × 4 variants = 20M assets per refresh. At ~1–2 GPU-seconds per 1024² image with a few-step distilled model (vs. ~10–20 s at 30–50 steps), that's 20–40M GPU-s ≈ **5.5–11K GPU-hours** per full refresh. So: generate **on demand for active campaigns**, cache by (SKU image, concept, template, model version), and adapt existing renders across placements via cheap outpaint/crop instead of regenerating.
- Interactive path: low-res preview (fast few-step) → full-res + upscale on selection.
- Queues per priority (interactive > bulk), GPU autoscaling, idempotent jobs keyed by request hash.

### 6. Eval & launch
- Offline: golden set of SKUs per category (incl. hard ones: transparent bottles, reflective packaging, apparel, multi-packs), human rating protocol, judge calibration.
- Beta with opt-in advertisers; 100% human review initially → **raise auto-approve coverage segment by segment** as calibrated precision proves out.
- Online: randomized creative tests inside ad groups (generated vs. advertiser-uploaded).

### 7. Risks & roadmap
- Risks: misrepresentation, IP (competitor products in scene), regulated categories, "AI look" fatigue, advertiser trust. Mitigations: lock product, category policies, IP detectors, C2PA/disclosure policy, advertiser approval mandatory initially.
- Roadmap: video (Design 3), personalization (Design 5), conversational editing via Marty ("make it fall-themed").

---

## Design 2: "Design the automated evaluation system for generated creative"
Use `12` in full. Structure for the interview:
1. Failure-mode taxonomy & severity → gates vs. objectives.
2. Judge stack cascade (draw it).
3. Labels: rater ops, κ, gold questions, stratified sampling.
4. Calibration: per-segment Platt/isotonic, meta-judge, ECE; threshold selection with CI lower bounds.
5. Routing & economics (coverage × cost vs. error cost).
6. Drift: frozen-input and frozen-judge tests, PSI, CUSUM, canaries.
7. Reliability: fail-closed, abstention, versions, audit trail.
8. Goodhart: separate reward/gatekeeper/scoreboard.
9. Platform: eval harness as a shared service (any team registers a generator; gets dashboards, golden sets, judges).
**Close with numbers:** "Success = review cost per shipped asset down 50%+ while audited critical-error rate stays below X per 10K."

---

## Design 3: "Turn an advertiser's product images into short video ads for Sponsored Videos and CTV"

1. **Clarify**: inputs (images only? existing long video?), formats (6/15/30 s; 16:9 CTV, 9:16, 1:1), sound on/off, approval process, CTV broadcast standards.
2. **Approach ladder (recommend staged):**
   - **Tier 1, deterministic motion graphics** from stills: templates with parallax (2.5D via monocular depth: your depth/reprojection background is exactly this), Ken Burns, kinetic typography, product spin from multi-angle images. Safe, cheap, fast. Ship first.
   - **Tier 2, adaptation of existing advertiser video**: shot detection, highlight scoring, cut-downs 30→15→6 s, **subject-tracked reframing** 16:9→9:16 (detect + track + smooth crop path with a Kalman/one-euro filter), auto-captions, end cards per placement, loudness normalization.
   - **Tier 3, generative**: image-to-video for scene/background motion with the **product composited as a tracked locked layer**; text-to-video b-roll for lifestyle shots *without* the product, then composited.
3. **Audio**: licensed music library with beat detection for cut timing; TTS voiceover from approved script (pronunciation lexicon for brand names); captions always (WCAG + muted autoplay).
4. **Eval (video judge)**: per-frame checks on samples; product identity tracking score over time; OCR stability; flicker/warping error; frozen/reversed detection (**your Temporal-Distance Predictability metric**); audio ASR → moderation; caption accuracy; CTV technical QC (resolution, frame rate, loudness).
5. **Scale/cost**: video gen costs ≫ images (frames × resolution). Use tier 1/2 for the majority, tier 3 selectively; low-res preview → upscale; cache shots.
6. **Metrics**: completion rate, view-through, CTR, cost per asset, approval rate, critical-error rate.
7. **Roadmap**: personalized end cards (local store availability), shoppable CTV overlays (Vizio), dynamic versions by season.

---

## Design 4: "Build structured creative understanding signals that targeting, ranking and measurement teams consume"

1. **Clarify consumers first**: ranking (pCTR features & cold start), targeting (audience–creative fit), measurement/insights (what attributes drive performance), policy, generation (conditioning + feedback).
2. **Schema**: versioned taxonomy (visual, semantic, messaging, brand, format-fit, quality, policy, accessibility) + embeddings (general CLIP/SigLIP + Walmart-tuned creative embedding). Each attribute: definition, type, allowed values, confidence, extractor version, coverage.
3. **Extraction**: specialists (OCR, detection, logo, faces, IQA/aesthetic) + VLM structured extraction (JSON schema) → **distilled students** for cheap full-coverage extraction; confidence/abstention; human audit for precision per attribute.
4. **Serving**: batch backfill for all existing creatives; event-driven extraction on upload/generation (minutes); feature store (offline for training, online for ranking); signal cards (docs); SLAs; backward-compatible schema evolution; deprecation policy.
5. **Quality**: precision/recall vs. human audit per attribute, calibration, drift per attribute, coverage.
6. **Adoption metric**: # consuming models; **downstream lift** (e.g. pCTR NE improvement from adding creative features, cold-start CTR prediction error for new creatives).
7. **Insights caution**: attribute–performance correlations are confounded (brand, budget, placement, category, season). Use within-ad-group randomized creative tests, matched comparisons, DML/hierarchical models. Never publish "lifestyle images get +20% CTR" from raw correlations.
8. **Roadmap**: signals as conditioning for generation ("generate with attributes that win in this category"), creative-aware targeting.

---

## Design 5: "Closed-loop creative optimization: learn from performance to generate better creative"

1. Generate diverse variants → judge-gated → serve within ad group with **Thompson sampling** (Beta priors from category-level creative CTR; hierarchical priors) → collect impressions/clicks/conversions.
2. **Creative performance model**: pCTR(creative features, embedding, placement, audience, product) trained on randomized-variant data (cleaner) + observational data with debiasing (position, placement).
3. **Generator improvement**:
   - **Prompt/concept policy learning** (cheapest): learn which concepts/layout families win per category → planner priors.
   - **Best-of-N reranking** with performance model (bounded exploitation).
   - **Preference tuning** (Diffusion-DPO / reward fine-tuning) on pairs from tests (winner vs. loser in same ad group), with KL regularization.
4. **Guardrails against reward hacking**: performance reward never overrides gatekeepers; clickbait detection (CTR↑ but CVR↓ = misleading creative); shopper metrics guardrail; human-anchored scoreboard.
5. **Experimentation**: creative-split tests (randomize creative within ad group); measure CTR **and CVR** **and** downstream (returns/complaints). Budget/auction interference is small for creative tests within an ad group but note it.
6. **Risks**: homogenization (all ads look the same → diversity regularization), novelty effects (decay of new-creative boost), feedback loops starving exploration.

---

## Design 6: "Adapt one master creative to 30 placements automatically"
1. Inputs: master creative as **layers** (preferred: product layer, background, logo, headline, CTA) or a flat image (then decompose: segmentation + OCR + inpaint text out).
2. Per placement spec: aspect, size, safe zones, text limits, min font, logo rules.
3. Algorithm: (a) choose layout family for aspect, (b) **background extension** via outpainting (your inpainting core) or smart crop via saliency (keep product + key elements), (c) re-place product/logo/text by constraint solver (non-overlap, safe zones, hierarchy, alignment grid), (d) copy shortening by LLM within char limits (claims re-checked), (e) contrast enforcement (choose text color/scrim to reach 4.5:1).
4. Judge: layout rule validator (deterministic), product not cropped, legibility, outpaint seam/artifact detector, fidelity.
5. Metrics: % placements auto-produced passing gates; manual-fix rate; performance parity vs. designer-made versions.
6. This is the **fastest first win** for the roadmap: low hallucination risk, high advertiser value, uses existing approved assets.

---

## Practice prompts (40-min timer, out loud)
1. Design a system that detects and fixes distorted text in generated ads.
2. Design alt-text generation for every ad image, WCAG-compliant and accurate.
3. Design the human review tooling + labeling program feeding your judges.
4. Design creative personalization at serve time for Sparky conversational ads.
5. Your auto-approve precision dropped from 98.5% to 95% this week. Debug it.
6. A major brand complains a generated ad misrepresented their product. Walk through the incident response and the systemic fix.
7. Design brand-kit ingestion: from a PDF style guide to enforceable rules.
8. Decide build vs. buy for the image generation model (open weights vs. API).
