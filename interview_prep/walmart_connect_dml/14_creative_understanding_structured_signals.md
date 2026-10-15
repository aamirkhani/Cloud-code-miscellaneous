# 14 — Creative Understanding & Structured Creative Signals (very detailed study guide)

> **JD bullet this chapter targets (R-2630449, Distinguished Data Scientist, Creative Intelligence):**
> "Build structured representations of creative content (attributes, categories, quality signals) that other teams can consume as reusable signals for targeting, recommendations, and performance measurement."
> Related asks: shared infrastructure so creative-AI capabilities **compound across use cases**; **artifact/distortion detection**; **image understanding, matching/cropping**.
>
> **Ground rule for the interview:** I do not know Walmart's internal systems. Everything below labeled **[Assumption]** is a reasonable industry pattern, not a claim about Walmart. Say "I'd expect" / "I'd want to check whether" when you use those parts.

---

## 0. The 60-second version (memorize this)

**Say it like this:**
"Today most ad systems treat a creative as an opaque blob with an ID. The ranker learns 'creative 81734 gets clicks' only after it has spent impressions, and nobody can say *why*. I'd build a **creative genome**: every image or video gets a versioned record of interpretable attributes (what is in it, what it says, how it looks, how good it is, whether it is safe and on-brand), plus dense embeddings. Those are produced by a tiered extraction stack: cheap specialist models and distilled students for every asset, with a VLM teacher for the hard and new attributes. Then I'd publish it like a product, with signal contracts, a feature store, signal cards, SLAs and monitoring, so targeting, recommendations, measurement, generation, and policy all use the same signals. The two hard parts aren't the models. They're keeping the taxonomy stable while it evolves, and not fooling ourselves when we read attribute-to-performance correlations, which are badly confounded by brand, category, budget and placement."

**Your bridge:** "My career is mostly turning pixels into structured, reliable signals that another system depends on: stereo-mode detection and classification (a patent), lighting estimation as spherical-harmonic coefficients that a renderer consumes, multimodal fusion that downstream product features consumed. The ads-specific part is who consumes the signals and how performance is measured, and that's what I've been studying."

---

## 1. Why structured creative signals?

### 1.1 The problem: creatives are opaque blobs

In a typical ads stack **[Assumption, industry-typical]**, a creative is stored as `(creative_id, advertiser_id, campaign_id, asset_uri, size, a few advertiser-entered fields)`. Downstream:

- **Ranking** sees `creative_id` as a sparse ID feature. That works for warm creatives and does nothing for a new one (cold start).
- **Measurement** reports CTR/ROAS per creative, but cannot generalize: "creative A beat B" does not transfer to creative C.
- **Generation** (GenAI creative tools) has no feedback loop that says which properties work.
- **Policy/brand safety** runs separate one-off classifiers, often duplicated across teams.
- **Search/ops** can't answer "show me every holiday-themed creative with a price claim in grocery."

### 1.2 What structured signals unlock (one row per consumer)

| Consumer | What they need | Example signal use |
|---|---|---|
| **Targeting** | Match creative style to audience/context | "Lifestyle, family, warm palette" creative for a family-shopper segment; "product-on-white, spec-heavy" creative for a comparison-shopping context |
| **Recommendations / ranking** | Features that generalize across creatives; cold-start priors | Creative embedding + attributes as pCTR features; quality score as prior for a brand-new creative |
| **Creative selection** | Which of N creatives to show for this user/context | Contextual bandit arms described by attributes, so learning is shared across similar creatives |
| **Measurement / insights** | Which attributes drive performance | "In grocery, showing price on the creative is associated with +x% CTR within campaign" (only with controls; Section 8) |
| **Generation** | Conditioning and reward | Generate with `{background: kitchen, text_ratio < 15%}`; reward model trained on attribute+embedding → performance |
| **Policy & brand safety** | Flags, auditability | Prohibited claims, misleading price, unsafe content, wrong-product, generated-artifact flags |
| **Search & ops** | Faceted retrieval over the creative library | Dedupe, reuse, audit "all creatives with logo < 2% area" |
| **Advertiser-facing tools** | Actionable guidance | "Your headline text covers 38% of the image; similar creatives with < 20% perform better in this placement" |

### 1.3 The "creative genome" concept

Borrowed from the Music Genome Project idea: describe every item with a fixed, expert-defined set of "genes" so that similarity and preference generalize. For creatives:

```
                        CREATIVE GENOME RECORD (one per creative_id x version)
┌──────────────────────────────────────────────────────────────────────────────────┐
│ identity:   creative_id, asset_hash, advertiser, campaign, linked SKUs           │
│ low-level:  palette, brightness, contrast, clutter, text_area_ratio, faces, ...  │
│ semantic:   objects, scene, setting, season/holiday, lifestyle_vs_on_white        │
│ messaging:  offer, price_shown, claims, CTA type, tone, language                  │
│ brand:      logo present/size/position, brand-color adherence                     │
│ format:     aspect, safe-zone violations, min font size, legibility               │
│ quality:    aesthetic, technical IQA, artifact score + heatmap, p(generated)      │
│ policy:     flags with reasons                                                    │
│ access.:    text contrast ratio, alt text, captions                               │
│ embeddings: general (SigLIP/CLIP), Walmart-tuned creative embedding               │
│ meta:       taxonomy_version, model_versions, confidences, timestamps, provenance │
└──────────────────────────────────────────────────────────────────────────────────┘
```

**Say it like this:** "The genome is the shared vocabulary. The point is that every consumer, from ranking to the advertiser UI, refers to 'lifestyle_scene' and means the same thing computed the same way, so improvements compound instead of being rebuilt five times."

**Why "compound across use cases" (JD language):** one OCR pass feeds text-area ratio (format), price-shown (messaging), claim detection (policy), legibility (format), and the artifact detector's warped-text check (quality). Build it once, version it, and five consumers improve when it improves.

---

## 2. Taxonomy design

### 2.1 The levels, with concrete attributes

#### (a) Low-level visual (cheap, deterministic or near-deterministic)

| Attribute | Type | How computed | Why it matters |
|---|---|---|---|
| Dominant palette | k colors (Lab), proportions | k-means in CIELAB on downsampled pixels | Brand adherence, seasonal look, audience style match |
| Brightness / contrast | float | Mean / std of luminance (L*) | Thumbnail-scale visibility, quality |
| Colorfulness | float | Hasler–Süsstrunk metric | Style; correlates with attention |
| Visual complexity / clutter | float | Edge density, JPEG-compressed size ratio, number of segments, spatial-frequency energy | Clutter hurts small placements |
| Text-area ratio | float in [0,1] | OCR boxes union area / image area | Legibility; some platforms historically penalized text-heavy images |
| Faces / people | count, size, gaze direction (opt.) | Face detector (e.g., RetinaFace-class) | "Human presence" is a classic creative variable; careful with demographic inference (governance, Section 7.8) |
| Product size & position | bbox area ratio, center offset | Detector / segmentation matched to the advertised SKU | "Product prominence" is a strong candidate driver |
| Background type | enum: white/solid, studio gradient, lifestyle scene, texture | Segmentation + classifier on background pixels | Product-on-white vs lifestyle is the most-asked question in retail creative |

#### (b) Semantic

| Attribute | Type | Notes |
|---|---|---|
| Objects | multi-label set, aligned to product taxonomy where possible | "pan, eggs, spatula" |
| Scene / setting | enum, hierarchical | `indoor > kitchen`, `outdoor > backyard`, `studio` |
| Season / holiday | multi-label | back-to-school, Halloween, Thanksgiving, holiday/Christmas, summer; important for retail calendars |
| Composition style | enum | product-on-white, lifestyle, flat-lay, in-use/demonstration, collage/multi-product, model-wearing |
| Activity | open-ish label | cooking, camping, unboxing |
| Mood | enum, low-confidence | cozy, energetic, premium; treat as soft |

#### (c) Messaging (mostly OCR + VLM)

| Attribute | Type | Notes |
|---|---|---|
| Offer present | bool + type | % off, $ off, BOGO, rollback-style price drop, free shipping |
| Price shown | bool + value | Must reconcile with catalog price (policy risk if mismatched) |
| Claims | multi-label | "#1", "clinically proven", "organic", "new" (policy-relevant) |
| CTA type | enum | Shop now, Add to cart, Learn more, none |
| Headline length / readability | int, score | Word count, reading grade |
| Tone | enum | Informational, urgent, playful, premium |
| Language | ISO code(s) | Spanish-language creative targeting |

#### (d) Brand

| Attribute | Type | Notes |
|---|---|---|
| Logo present / size / position | bool, area ratio, quadrant | Logo detector, or few-shot matching against a brand logo library |
| Brand-color adherence | ΔE distance to brand palette | Requires a brand-kit registry (advertiser-provided palettes) |
| Brand at first frame (video) | bool / seconds-to-first-logo | Video-specific |

#### (e) Format & placement fit

| Attribute | Notes |
|---|---|
| Aspect ratio, resolution | vs placement spec (e.g., IAB-style 300x250, 728x90, 320x50; onsite and offsite placements differ) |
| Safe-zone violations | Text or logo within margins that get covered by UI overlays (badges, "Sponsored" labels, buttons) |
| Min rendered font size | Legibility at the actual render size, not the source size |
| Legibility score | OCR confidence at downscaled render size is a good proxy |
| Crop-robustness | Does the subject survive the crops each placement will apply? (Section 6) |

#### (f) Quality signals

| Attribute | Notes |
|---|---|
| Aesthetic score | Learned predictor (Section 3.2) |
| Technical quality (IQA) | Blur, noise, compression, exposure (MUSIQ/MANIQA-class) |
| Artifact/distortion score + heatmap | Section 5 |
| p(generated) | Generated-vs-real; mainly for disclosure/policy, not a quality judgment by itself |
| Product fidelity | Does the depicted product match the catalog SKU image? (Section 5.4) |

#### (g) Policy flags
Prohibited or restricted content, misleading price/claim, competitor references, unsafe imagery, trademark issues, wrong-product, undisclosed generated content where disclosure is required. **[Assumption]** The actual policy list belongs to Walmart's ad policy and legal teams. The genome supplies **evidence features** and the policy system makes decisions.

#### (h) Accessibility

| Attribute | Notes |
|---|---|
| Text contrast ratio | WCAG relative-luminance contrast; 4.5:1 for normal text, 3:1 for large text (AA) |
| Alt text present / quality | Auto-generate alt-text candidates with a VLM; score advertiser-supplied alt text |
| Captions (video) | Present? Accurate vs ASR? |
| Flashing content (video) | Photosensitivity checks |

### 2.2 Design decisions that interviewers probe

**Closed vs open vocabulary**

| | Closed (fixed enum) | Open (free text / tags) |
|---|---|---|
| Pros | Stable features, joinable, measurable, calibratable | Captures the long tail and new trends |
| Cons | Misses new concepts; enum-update cost | Synonyms, drift, not directly usable as features |
| Use for | Anything a consumer builds a model or dashboard on | Discovery, search, candidate generation for new taxonomy nodes |

**Pattern:** closed core plus open periphery. Run an open-vocabulary tagger (VLM captions, CLIP nearest-text) and periodically **cluster open tags** to propose new closed nodes for human review. That's taxonomy evolution with a human in the loop.

**Hierarchy.** Use a DAG (directed acyclic graph), not a flat list: `setting > indoor > kitchen`. Benefits: consumers choose granularity, sparse leaves roll up to parents, and you get hierarchical consistency constraints (P(kitchen) ≤ P(indoor)).

**Align to the product taxonomy.** Objects and categories should map to Walmart's existing item/category taxonomy where possible **[Assumption: a product taxonomy exists and is the system of record]**. Then "creative shows a product from category X" joins directly to catalog, search and sales data. Don't invent a parallel object ontology.

**Attribute definitions are specs.** Every attribute gets a written definition, positive and negative examples, edge cases, and annotation guidelines. Example: is a product on a marble countertop with nothing else "lifestyle" or "studio"? Decide it, write it down, and version it.

**Versioning.**
- `taxonomy_version` (semantic versioning): **major** = meaning changed or node removed (breaking), **minor** = node added, **patch** = definition clarified.
- `model_version` per attribute extractor, independent of taxonomy version.
- The record stores both, so any value can be traced to (definition, model, timestamp).

**Say it like this:** "I treat the taxonomy like an API. Additive changes are cheap, meaning changes are major versions with a dual-publish window, and every attribute has a spec with examples, because if two annotators disagree on what 'lifestyle' means, no model will fix that."

**Your bridge:** "The stereo-mode classification work was exactly this: half the job was defining classes that were unambiguous at the edges, like side-by-side vs top-bottom vs mono with letterboxing, before training anything."

---

## 3. Extraction methods

### 3.1 The tiered extraction stack

```
                 asset upload / backfill
                          │
           ┌──────────────┴───────────────┐
           ▼                              ▼
  TIER 0: deterministic            TIER 1: specialist models (GPU, ms each)
  palette, brightness, size,       OCR, face det, object det/seg, logo det,
  aspect, hashes, safe zones       IQA, aesthetic head, saliency, artifact det
           │                              │
           └──────────────┬───────────────┘
                          ▼
             TIER 2: embedding backbone (SigLIP/CLIP; Walmart-tuned)
             zero-shot heads + distilled multi-label student heads
                          │
              low confidence / new attribute / policy-critical?
                          │ yes (~5–15% of traffic, a guess)
                          ▼
             TIER 3: VLM structured extraction (JSON schema, constrained decoding)
                          │
              still ambiguous or high stakes?
                          │ yes (< 1%)
                          ▼
             TIER 4: human review → gold labels → retrain students, audit
```

**Why tiered:** cost and latency. A VLM call per asset may be fine at upload volume, but it's expensive for backfilling tens of millions of assets and re-running on every taxonomy change. Distilled students on a shared backbone make re-extraction cheap.

### 3.2 Specialist models (know the names and what each one measures)

| Task | Model families | Notes |
|---|---|---|
| OCR | Text detection + recognition (DBNet/CRAFT-style detectors, transformer recognizers; PaddleOCR, docTR-class; or VLM OCR) | Gives text boxes for text-area ratio, price/claims, safe zones, warped-text checks |
| Object detection / segmentation | DETR/RT-DETR/YOLO-class detectors; SAM-class promptable segmentation; open-vocab detectors (OWL-ViT, Grounding DINO) | Open-vocab detectors let you prompt with the SKU's product type |
| Logo detection | Detector trained on logo datasets plus **few-shot matching** against a logo gallery (embedding similarity) | New brands appear constantly, so retrieval-based beats fixed classes |
| Face detection | RetinaFace / SCRFD-class | Count and size only by default; avoid demographic attribute inference unless governance approves |
| Aesthetic | **LAION-aesthetic-style predictor**: a small MLP on frozen CLIP ViT-L/14 image embeddings, trained on human aesthetic ratings (AVA, SAC) | Cheap; calibrate on ad-domain human ratings because "aesthetic" in AVA (photo contests) isn't "effective ad" |
| Technical IQA, learned | **MUSIQ** (multi-scale image quality transformer, handles native resolution/aspect), **MANIQA** (multi-dimension attention, NTIRE 2022 NR-IQA winner) | Trained on KonIQ-10k, SPAQ, PIPAL-type datasets with mean opinion scores |
| Technical IQA, classical NR | **BRISQUE** (natural scene statistics features + SVR, trained on MOS), **NIQE** ("opinion-unaware": distance from a natural-image NSS model; no training on human scores) | Fast, interpretable baselines; weaker on synthetic/composite ad imagery |
| Zero-shot IQA | **CLIP-IQA** (antonym prompt pairs such as "Good photo." vs "Bad photo.", softmax over the pair) | Good for adding new quality axes quickly ("sharp/blurry", "cluttered/clean") |
| Saliency | DeepGaze-class, U2-Net-class salient object detection | Cropping, product-prominence, "is the product where eyes go?" |

**Say it like this:** "I'd use classical NR-IQA like BRISQUE as a cheap sanity baseline, a learned model like MUSIQ for technical quality, and a separate aesthetic head. The important thing is that none of them were trained on ad creatives, so I'd collect a few thousand in-domain human ratings and recalibrate or fine-tune before anyone uses the score as a feature."

### 3.3 CLIP/SigLIP zero-shot tagging, done properly

**Mechanics:** For attribute value `v` with prompts `{p_1..p_k}` ("a product photo on a white background", "an e-commerce product shot with plain white backdrop", ...):

```
t_v = normalize( mean_i  normalize(TextEnc(p_i)) )        # prompt ensemble
s_v = cos(ImgEnc(x), t_v)
CLIP:   P(v | x) = softmax_v( s_v / τ )                    # mutually exclusive values
SigLIP: P(v | x) = σ( a · s_v + b )                        # independent, natural for multi-label
```

Key points:
1. **Prompt ensembles.** Average the normalized text embeddings over several templates and synonyms. The CLIP paper reported prompt engineering plus ensembling gives a few points of zero-shot ImageNet accuracy. More important for us, it reduces variance across attributes.
2. **Softmax vs sigmoid.** CLIP's softmax assumes exactly one value of the set applies. Use it for mutually exclusive enums (background type) and **include a "none/other" prompt**. SigLIP's sigmoid training yields per-pair scores that suit **multi-label** attributes (objects, holidays) better.
3. **Calibration.** Raw cosine scores aren't probabilities, and their scale differs per attribute. Fit a **per-attribute Platt/temperature or isotonic** mapping on a small labeled in-domain set (a few hundred examples per attribute is often enough to calibrate, though not to train).
4. **Known failure modes.** Text-in-image (CLIP reads text, the "typographic attack" effect: an image with the word "organic" scores high for "organic"), counting, spatial relations ("logo in top-left"), negation, and fine-grained SKU identity. Use specialist models for those.
5. **Linear probes beat zero-shot quickly.** With even ~100–500 labels per attribute, a logistic-regression probe on frozen embeddings usually beats zero-shot. Zero-shot is for bootstrapping and the long tail.

**Your bridge:** "This is home turf. I've trained contrastive models with InfoNCE and worked with CLIP and DINO features, and I know where CLIP-style embeddings are strong (style, scene, gist) and where they're weak (counting, small text, exact identity)."

### 3.4 VLM structured extraction (JSON schema + constrained decoding)

**Pattern:**
```
system: You are a creative auditor. Follow the attribute definitions exactly.
        If you are not confident, output "unknown". Do not guess.
input:  image (+ OCR text, + catalog title/brand/price for the linked SKU)
schema: {
  "composition_style": {"enum": ["product_on_white","lifestyle","flat_lay",
                                 "in_use","collage","model_wearing","unknown"]},
  "setting": {"enum": [...taxonomy leaves..., "unknown"]},
  "price_shown": {"type":"boolean"}, "price_value": {"type":["number","null"]},
  "offer_type": {"enum": ["pct_off","dollar_off","bogo","free_shipping","none","unknown"]},
  "claims": {"type":"array","items":{"enum":[...]}},
  "evidence": {"type":"string","maxLength":200}
}
```

- **Constrained decoding:** grammar/JSON-schema-constrained generation (e.g., vLLM guided decoding, Outlines, XGrammar-style engines, or provider "structured output" modes) guarantees parseable, enum-valid output. That removes a whole class of pipeline failures.
- **Caveat:** constraining the format doesn't make the content right. Forcing a field can push the model to hallucinate, so **always allow `unknown`** and keep the `evidence` field (short rationale or quoted OCR) for audits.
- **Ordering trick:** put `evidence` before the decision fields if you want reasoning-then-answer. Put it after if you want cheaper, more parallel decoding. Measure both.
- **Grounding inputs:** give the VLM OCR text and catalog metadata. Price reconciliation ("creative says $9.98, catalog says $12.48") becomes a structured comparison rather than a VLM guess.
- **Confidence from VLMs:** token log-probs over the enum choice, self-consistency (sample N times, agreement rate), or a verifier pass. Calibrate against human gold labels per attribute.

### 3.5 Confidence, abstention, and multi-label calibration

- Each attribute value is stored as `(value, confidence, source_model, version)`. **Never store a bare label.**
- **Abstention:** per attribute, choose a threshold on the risk–coverage curve (selective classification). Example: "background_type at 97% precision covers 88% of creatives; the rest go to Tier 3."
- **Multi-label calibration:** calibrate **per label** (temperature, Platt or isotonic per output). Check **ECE** and reliability diagrams per label, and check calibration within slices (category, placement, generated-vs-real), since global calibration hides slice miscalibration.
- **Hierarchical consistency:** enforce `P(child) ≤ P(parent)` after calibration, or decode top-down.
- **Thresholds are consumer-specific:** policy wants high recall, insights want high precision. Publish **calibrated probabilities**, not just thresholded booleans, and let consumers threshold.

**Say it like this:** "Every value ships with a calibrated confidence and a version. Consumers threshold for their own cost of errors. Policy wants recall, advertiser-facing insights want precision."

### 3.6 Distilling VLM labels into cheap students

```
  VLM teacher (Tier 3) on a stratified sample (~1–5M creatives)  ──► soft labels + confidences
                         │                                              │
  human gold set (~10–50K, stratified, multi-annotator) ──► calibrate teacher, measure teacher error
                         ▼
  STUDENT: shared vision backbone (frozen SigLIP or Walmart-tuned) + multi-label heads
           loss = Σ_attr w_attr · BCE(student, teacher_soft)  (+ CE on gold where available)
                         ▼
  serve student on 100% of assets; route low-confidence/disagreement to teacher
```

- Train on **soft labels** (teacher probabilities) where available, since they carry more information than hard labels. This is standard knowledge distillation (Hinton et al.).
- **Teacher noise is systematic, not random.** If the VLM confuses "flat-lay" with "product-on-white", the student learns that confusion. Measure teacher-vs-human agreement per attribute and **weight or exclude** attributes where the teacher is weak.
- **Shared backbone + many heads** is how capabilities compound: adding an attribute is a new head trained on cached embeddings, minutes not days. Re-extraction after a taxonomy minor-version bump is a cheap head inference over cached embeddings.

**Your bridge:** "This is the same pattern as my EMA-teacher-to-edge-student distillation work, with a VLM as the teacher and a multi-head student on a shared backbone. The lesson I'd bring: watch for teacher-specific biases and keep a human gold set that is never used for training, only for measuring both teacher and student."

### 3.7 Active learning with human labels

- **Selection strategies:** uncertainty (entropy, margin), **teacher–student disagreement**, committee disagreement, diversity sampling (k-center in embedding space), and **business-weighted** sampling (high-spend creatives, policy-sensitive categories).
- **Stratify** by category, placement, generated-vs-real, and language. Otherwise the long tail stays unlabeled.
- **Annotation quality:** multiple annotators per item on a subset, Krippendorff's alpha or Cohen's kappa per attribute. **Low agreement means the definition is bad, not the model.** Fix the spec before buying more labels.
- **Gold sets are frozen and versioned.** Keep a separate audit set sampled from production traffic monthly, to measure drift.

### 3.8 Video extensions

| Level | Signals | Methods |
|---|---|---|
| Shot | Shot boundaries, shot count, average shot length (pacing) | TransNetV2-class shot boundary detection |
| Keyframe | All image attributes per shot keyframe | Image stack on representative frames |
| Temporal | Time-to-first-product, time-to-first-logo, product screen-time %, motion energy, "hook" in first 2–3 s, end-card present | Detection tracks over time, optical flow magnitude |
| Audio | Speech present, music present/tempo, voiceover tone, loudness | Audio event classification, beat tracking |
| Speech/text | Transcript, spoken offer/price/CTA, language | ASR (Whisper-class), plus on-screen OCR per shot |
| Accessibility | Captions present and accurate (caption vs ASR WER), flashing frequency | |
| Aggregation | Creative-level = pooled shot features + temporal stats; also a video embedding (frame embeddings + temporal pooling/transformer) | |

**Your bridge:** "My multimodal fusion work, where one model fusing IMU, audio and video beat separate per-sensor pipelines, is directly relevant. For video creatives I'd fuse visual, ASR and audio features in one representation rather than stitching three separate scores together."

---

## 4. Embeddings vs. attributes

### 4.1 Both are needed

| | Dense embeddings | Interpretable attributes |
|---|---|---|
| Strength | Captures everything, including what no one named; best raw predictive power; similarity search | Human-readable, joinable, controllable, auditable, usable in reports and generation prompts |
| Weakness | Opaque; can't drive an advertiser recommendation; drifts with model version (not comparable across versions) | Lossy; only what you defined; extraction error |
| Primary consumers | pCTR/ranking models, retrieval, dedupe, bandit context, clustering | Measurement/insights, policy, generation conditioning, targeting rules, search facets, advertiser UI |
| Versioning pain | High: a new embedding model means re-index and retrain consumers | Lower: meaning stays stable across model upgrades if specs are stable |

**Say it like this:** "Embeddings are for machines that predict, attributes are for people and systems that need to reason or act. Ranking uses both. Insights and generation mostly use attributes. And you can bridge them: a linear probe from the embedding to each attribute tells you which attributes the embedding already encodes."

### 4.2 Training a Walmart-tuned creative embedding

Off-the-shelf CLIP/SigLIP embeddings know "a photo of a kitchen". They don't know "this is SKU 12345's variant vs. its near-identical competitor", or what makes an ad engaging. Fine-tune with **multiple contrastive objectives**:

```
                         ┌─── creative ↔ product (SKU image + title + attributes)
  creative image ──► f ──┼─── creative ↔ query   (search queries that led to clicks on it)
     (+ OCR text)        └─── creative ↔ engagement context (user/segment embedding of clickers)
```

| Objective | Positives | Negatives | What it teaches |
|---|---|---|---|
| Creative–product | Creative and its linked SKU's catalog image/title | In-batch other SKUs; **hard:** same category/brand, sibling variants | Product identity and fine-grained category; enables matching (Section 6) |
| Creative–query | Creative and queries with clicks on it | In-batch queries; hard: same-category queries without clicks | Shopping intent semantics |
| Creative–engagement | Creative and the aggregate embedding of users/segments who engaged | Segments that saw it and didn't engage | Audience affinity, useful for targeting |
| (Optional) creative–creative | Same campaign variants, or same SKU different style | | Style-invariant vs style-sensitive structure (choose deliberately) |

**Loss:** InfoNCE (or SigLIP sigmoid loss, which scales well to large batches and doesn't need a global softmax normalizer):

```
L = − Σ_i log [ exp(s(c_i, p_i)/τ) / Σ_j exp(s(c_i, p_j)/τ − log Q(p_j)) ]
```

- **logQ correction** (Yi et al., RecSys 2019, sampling-bias-corrected two-tower): with in-batch negatives, popular items show up as negatives more often than uniform sampling would. Subtracting `log Q(item)` (the estimated sampling probability) from logits corrects the implied softmax so you don't over-penalize popular items. This matters most for the creative–query and creative–engagement objectives, where popularity is very skewed.
- **Hard negatives:** same category, same brand, near-duplicate SKUs (sizes/colors). **Watch for false negatives:** different SKUs that are visually identical (a 12-pack vs a 24-pack box) should be masked or soft-labeled. Same discipline as MoCo/DINO-style training.
- **Engagement labels are biased** by position, placement and targeting (they only reflect who was *shown* the creative). Use it as one objective among several, with lower weight, or debias (inverse propensity weighting, position features). Don't let the embedding learn "creatives from big-budget campaigns".
- **Multi-task balance:** weighted sum of the objectives, with weights tuned on the downstream evaluation suite (Section 10), not on contrastive loss values.
- **Embedding hygiene:** fixed dimension (e.g., 256 via a projection head for serving), L2-normalized, versioned. Publish **old and new versions in parallel** during migration because consumers trained on v1 can't consume v2.

**Your bridge:** "I've trained MoCo-style InfoNCE models and ViT/DINO backbones. The Walmart-specific part is choosing the positive pairs from catalog and engagement data and correcting for popularity bias with logQ. I know the mechanism; the data is new to me."

---

## 5. Artifact & distortion detection (deep)

### 5.1 Why it's central for Creative Intelligence
Generative creative tools (background generation, outpainting, product-in-scene, resizing/recomposition) produce artifacts at some rate. A single melted product label or six-fingered hand in a sponsored placement is a brand-trust incident for both the advertiser and the retailer. The artifact signal works as a **gate** (block/repair before serving), a **reward/penalty** for the generator, and a **QA metric** for every generation model release.

### 5.2 Taxonomy of artifacts

| Artifact | What it looks like | Typical cause | Best detector |
|---|---|---|---|
| **Warped / garbled text** | Pseudo-letters, misspelled brand names, melted label text | Diffusion models' weak glyph modeling | OCR confidence collapse + OCR diff vs. catalog/packaging text |
| **Anatomical errors** | Extra or fused fingers, broken limbs, asymmetric faces | Generative priors | Hand/pose keypoint detectors + plausibility checks; trained classifier |
| **Melted / impossible geometry** | Product edges bending, handles merging, non-planar box faces | Inpainting/outpainting at product boundary | **Reference-based check** vs source SKU image (5.4) |
| **Inconsistent lighting & shadows** | Product lit from left, scene from right; missing or floating contact shadows | Compositing product into generated scene | Lighting estimation per region (e.g., spherical-harmonic fits) and shadow-direction consistency |
| **Texture repetition / tiling** | Repeating patterns in backgrounds, cloned objects | Upsampling, tiled generation | Autocorrelation / frequency peaks, patch self-similarity |
| **Composite halos / seams** | Bright or dark fringe at mask boundaries, color mismatch at edges | Matting errors, feathering | Boundary-band analysis around the product mask (gradient, color discontinuity) |
| **Color banding / posterization** | Steps in smooth gradients | Bit-depth loss, aggressive quantization | Histogram gaps, gradient-region analysis |
| **Compression artifacts** | JPEG blocking, ringing, chroma bleeding | Re-encoding, low quality settings | Blockiness metrics at 8x8 grid, IQA models |
| **Blur / upscaling artifacts** | Over-smooth, "waxy" textures, hallucinated detail | Super-resolution, low-res source | IQA (MUSIQ/MANIQA), high-frequency energy |
| **Product-fidelity errors** | Wrong color variant, changed logo, altered package text, wrong count | Generator "improves" the product | Reference-based: SSIM/LPIPS/DINO in product region, OCR diff, color ΔE |

**Key insight (say this):** "The most important artifacts in retail ads aren't generic GAN fingerprints. They're **product-fidelity errors**: the generator changed the product. We almost always have the **source catalog image**, so we can do *reference-based* checks that are much stronger than blind detection."

### 5.3 Detection approaches

**A. Supervised classifier on synthetically corrupted data (the workhorse).**
- Take clean creatives and product images, then **programmatically inject** each artifact type with known masks: warp text regions with thin-plate splines, re-render text with character substitutions, jitter product geometry at the mask boundary, composite with mismatched lighting, add halo bands of controlled width, posterize gradients, apply JPEG at quality q, tile textures.
- Also generate **real generator failures**: run your own generation pipeline at scale and have humans label failures. Synthetic corruptions give coverage, real failures give realism.
- Model: a ViT/ConvNeXt backbone with an image-level head (any-artifact, per-type multi-label) **plus a dense head** (per-patch artifact logits → localization heatmap), trained with mask supervision from the programmatic corruptions.
- **Domain gap warning:** classifiers trained only on synthetic corruptions can learn the corruption pipeline's signature. Mitigate with diverse corruption parameters, real-failure fine-tuning, and evaluation on real failures only.

**Your bridge (strong one):** "I've built synthetic-data rigs in 3D graphics: rendering with controlled perturbations and exact ground-truth masks. An artifact detector needs the same thing, a corruption engine with known masks per artifact type, so you get localization labels for free. Then you close the domain gap with a smaller set of real generator failures."

**B. Patch-level anomaly detection (unsupervised / one-class).**
- Model the distribution of "clean" patch features (e.g., DINOv2 patch tokens) from verified real product photos. Score test patches by distance to the clean distribution (PatchCore-style memory bank with kNN distance, or a Gaussian per position as in PaDiM).
- Pro: catches **unknown** artifact types. Con: high false-positive rate on legitimately unusual but clean content. Best used as a **feature** and a router to review, not as a sole gate.

**C. Frequency-domain features.**
- Generator upsampling (transposed conv, some VAE decoders) leaves **periodic spectral peaks** and abnormal high-frequency energy. This is well documented for GANs (e.g., Durall et al. 2020, Frank et al. 2020). Diffusion artifacts are subtler but often still visible in spectra or noise residuals.
- Use the FFT/DCT magnitude of high-pass residuals as an extra input channel or branch.
- **Fragile:** JPEG re-compression and resizing in the ad pipeline wash these out. Train with those augmentations, and don't over-rely on frequency cues for p(generated).

**D. Generated-vs-real detection (for p(generated)).**
- Classifiers on generator outputs (Wang et al. 2020 showed CNN-generated images were "surprisingly easy to spot" with augmentation; **UnivFD**, Ojha et al. 2023, uses frozen CLIP features + linear head for better generalization across generators); reconstruction-error methods (DIRE-style) for diffusion.
- **Provenance beats detection when available:** C2PA content credentials, generator-side watermarks (e.g., SynthID-class). If Walmart's own tools generate the asset, **log provenance at generation time** and don't infer it. **[Assumption]** about whether Walmart uses provenance metadata.
- Keep p(generated) **separate from quality**. Generated isn't bad. Artifacted is bad.

**E. Reference-based checks vs. the source product image (highest-precision signal).**

```
 source SKU image ──► segment product ──► features F_src (DINO patches, OCR text, color hist)
                                                │
 generated creative ──► locate product (detector / open-vocab "the <product type>")
                     ──► align (homography / keypoint matching, e.g., SuperPoint+LightGlue-class)
                     ──► features F_gen in aligned product region
                                                │
   compare:  SSIM (structure)  · LPIPS (perceptual)  · DINO patch cosine (semantic)
             OCR diff (edit distance on label/brand text)  · color ΔE (variant correctness)
             shape IoU of aligned masks  · logo match score
                                                │
                       per-check scores + localization map → fidelity score
```

- **Why several metrics:** SSIM is sensitive to lighting and alignment changes (false alarms when relighting is intended). LPIPS is better perceptually but not identity-specific. **DINO patch similarity** is robust to relighting but can miss small text edits, so **OCR diff** catches those. Color ΔE catches "the red variant became orange."
- **Intended vs unintended change:** generation legitimately changes lighting, perspective and scale. Use **relighting-tolerant** comparisons (normalize illumination, compare in a chroma-invariant space for structure checks), and alignment before comparison.
- **Thresholds** set per category: apparel tolerates drape changes, packaged goods tolerate almost no text changes.

**Your bridge:** "Lighting consistency is literally my research area. I've done spherical-harmonics lighting estimation. Fitting low-order SH lighting to the product region and to the scene separately and comparing the dominant light directions is a principled check for 'pasted-in' composites, and it's interpretable for a reviewer."

### 5.4 Localization heatmaps
- Output per-patch scores (from the dense head, anomaly scores, or reference-diff maps), upsample, and overlay.
- Uses: (1) **reviewer UX**, so humans see *where*; (2) **targeted repair**, re-inpainting only the flagged region; (3) **training signal** for the generator (region-weighted loss or reward); (4) **evaluating** the detector with localization metrics (pixel-AUROC, PRO score) in addition to image-level AUROC.

### 5.5 Operating the artifact gate

| Decision | Action |
|---|---|
| Fidelity score low (product changed) | **Block**; regenerate or repair; this is the high-severity class |
| Text artifact on brand/price text | Block; OCR-diff evidence logged |
| Moderate generic artifact | Auto-repair attempt → re-score → human review queue if still flagged |
| Low score, low confidence | Serve; sample for audit |

- Choose thresholds by **asymmetric cost**: a false negative (bad creative served) is much costlier than a false positive (one extra regeneration). Measure **precision at the operating recall** on a fresh real-failure set every generator release.
- Track **artifact rate per generator version, per category** as a release-gating metric for the GenAI team. That's the compounding infrastructure the JD describes.

---

## 6. Matching & cropping

### 6.1 Creative ↔ product matching ("is this the advertised SKU?")

**Why:** sponsored products and display ads link a creative to SKUs. Mismatches are policy issues (misleading ads), hurt relevance, and corrupt measurement (attribution to the wrong item).

```
creative ──► detect product instances (open-vocab detector prompted by SKU product type)
          ──► crop each instance ──► fine-grained product embedding (Walmart-tuned, Section 4.2)
                                          │
                        ANN search over catalog image embeddings (filtered to advertiser's brand/category)
                                          │
              top-k candidates ──► verifier: geometric keypoint verification + OCR match of brand/model text
                                          │
          outputs: matched_skus[], match_confidence, linked_sku_present (bool), variant_correct (bool)
```

- **Fine-grained retrieval** is the hard part: variants (size, color, count, flavor) look nearly identical. Use hard-negative training on sibling variants, and **combine visual + OCR** (package text often discriminates "12 oz" vs "24 oz").
- **Two-stage** (ANN recall, then verify) is the standard retrieval pattern, the same shape as ads retrieval and ranking.
- **Outputs as signals:** `linked_sku_visible`, `linked_sku_prominence` (area, saliency rank), `other_skus_visible` (competitor or multi-product), `variant_match`.

### 6.2 Near-duplicate detection & dedupe

| Method | Catches | Misses | Cost |
|---|---|---|---|
| Cryptographic hash (SHA-256) | Exact byte duplicates | Any re-encode | Trivial |
| **Perceptual hashes** (aHash, dHash, **pHash** = DCT-based, PDQ) + Hamming distance | Re-encodes, resizes, minor color shifts | Crops, overlays, layout changes | Very cheap; index with BK-trees or multi-index hashing |
| **Embedding similarity** (SSCD-style copy-detection embeddings, or DINO/CLIP) + ANN | Crops, overlays, text changes, recompositions | Can over-merge "same template, different product" | Moderate |
| Hybrid | pHash for fast exact-ish; embedding for semantic near-dupes; OCR diff to separate "same image, different price" | | |

- **Define duplicate per use case.** For **measurement**, "same image, different headline" is a *different* creative (that's the experiment). For **storage/review dedupe**, it's the same asset. For **policy**, a previously rejected image re-uploaded with a tiny change is a dupe and should inherit the rejection. Publish a **similarity graph** (pairwise scores with edge types), not one dedupe decision.
- Use cases: review deduplication (don't re-review), inherit labels across near-dupes (cheap coverage), detect advertisers cycling rejected creatives, collapse near-dupes in insights so one creative family doesn't dominate analysis, and diversity constraints in creative selection.

### 6.3 Smart cropping & reframing

**Problem:** one master creative must render in many aspect ratios (square feed, 16:9 banner, 9:16 story, 728x90 leaderboard). Naive center-crop cuts products, faces and text.

**Approach:**
1. Compute an **importance map** = weighted sum of: linked-product mask (highest), text boxes (must stay whole or be re-laid-out), logo, faces, and general saliency.
2. Solve for the crop window at target aspect that **maximizes covered importance** subject to hard constraints: product fully inside, no text box cut, safe-zone margins respected.
3. If no feasible crop exists: **recompose instead of crop**, i.e., outpaint the background (generative), or re-layout text as a separate layer if the source is layered. Then run the artifact/fidelity checks (Section 5) on the result.
4. Output as signals too: `crop_robustness[aspect]` (fraction of importance preserved) lets placements and ranking know which creatives survive which formats.

**Say it like this:** "Saliency alone isn't the objective. In ads, the advertised product and the offer text are the objective. So I'd crop to keep the product and text whole, use saliency to break ties, and fall back to outpainting when the crop isn't feasible, with the fidelity checker as a gate on the outpainted result."

**Cautionary tale to mention:** Twitter's saliency-based image cropping was publicly audited for demographic bias (2020–2021), and Twitter moved away from algorithmic cropping. Lesson: **audit cropping across demographic slices** of the people depicted, and prefer product- and text-anchored objectives over raw saliency.

---

## 7. Serving signals as a platform

### 7.1 Architecture (whiteboard this)

```
 ┌──────────── PRODUCERS ────────────┐
 │ upload event (new/changed asset)  │──► stream (Kafka-class) ──► REAL-TIME PATH
 │ taxonomy/model version bump       │──► orchestrator ──────────► BATCH BACKFILL PATH
 └───────────────────────────────────┘
                 │                                     │
                 ▼                                     ▼
        extraction workers (Tier 0–2 GPU, autoscaled)   bulk GPU jobs on cached embeddings
                 │  └─ low-conf → VLM queue (Tier 3) → human queue (Tier 4)
                 ▼
   ┌───────────────────────── CREATIVE SIGNAL STORE ─────────────────────────┐
   │ offline: versioned tables, point-in-time correct (creative_id, version, │
   │          signal, value, confidence, model_ver, taxonomy_ver, ts)        │
   │ online:  low-latency KV keyed by creative_id (+ embedding ANN index)    │
   │ registry: signal contracts, signal cards, lineage, owners, SLAs         │
   └─────────────────────────────────────────────────────────────────────────┘
        │              │                 │                │              │
     ranking/pCTR   targeting      measurement/BI      generation      policy &
     (online feats) (seg rules)    (offline joins)     (reward/cond)   review UI
        ▲
   monitoring: coverage, freshness, drift per attribute, audit precision, consumer usage
```

**[Assumption]** Walmart has some feature store and streaming stack. I'd plug into whatever exists rather than build a parallel one. Say so in the interview.

### 7.2 Signal contracts (schema & versioning)

A **signal contract** is the API: what the field means, its type, range, null semantics, freshness, quality guarantees, and deprecation policy.

```yaml
signal: creative.semantic.composition_style
version: 2.1.0                  # taxonomy semver
type: categorical_distribution  # calibrated probs over enum
values: [product_on_white, lifestyle, flat_lay, in_use, collage, model_wearing, other]
null_semantics: "missing = not yet extracted; 'other' = extracted, no class applies"
producer_model: comp_style_student v7 (backbone: wmt-creative-emb v3)
quality: {macro_precision@0.5: 0.93, ece: 0.03, audited: 2026-09, audit_n: 2400}
freshness_sla: "p99 < 10 min from upload; backfill complete within 72h of version bump"
owner: creative-intelligence-ds
consumers: [ads-ranking-pctr, insights-dashboard, genai-creative-reward]
deprecation: "v1.x served in parallel until 2026-12-31"
```

### 7.3 Online vs offline, real-time vs batch

| Path | When | Latency budget | Notes |
|---|---|---|---|
| **Real-time on upload** | New creative or edit | Seconds to minutes. Not in the ad-request path, so no ms budget, but needed before first serve for gating and cold-start features | Tier 0–2 inline; Tier 3 async; serve with "pending" values or block policy-critical ones until done |
| **Batch backfill** | New attribute, model or taxonomy version | Hours to days | Run on **cached backbone embeddings** for heads (cheap); full re-encode only for backbone changes |
| **Online serving** | Ranking request | ~1–5 ms feature fetch | Precomputed values in the online store; **never** run extraction in the request path |
| **Offline training** | Consumer model training | n/a | **Point-in-time correctness:** join the signal version that existed at impression time, or you leak future model improvements into training and get train/serve skew |

**Point-in-time subtlety (strong senior point):** if you backfill v2 attributes over historical creatives and the ranker trains on v2 for old impressions but serves v2 online, that's consistent. If the ranker trains on v1 historically but serves v2, that's skew. Rule: **train and serve on the same signal version**, and backfill history when you switch.

### 7.4 Cost & latency (back-of-envelope; illustrative numbers)

- Suppose ~10M active creatives and ~100K new or changed per day **[Assumption, illustrative]**.
- Tier 0–2 at ~20–50 ms GPU per image ≈ 100K × 0.05 s ≈ 1.4 GPU-hours/day. Trivial.
- Full backfill of 10M with backbone re-encode ≈ 10M × 0.03 s ≈ 83 GPU-hours. Fine as an occasional job.
- VLM on 10% of new uploads (10K/day) is affordable. A VLM on all 10M for every taxonomy change is the expensive thing to avoid. **Hence distillation and cached embeddings.**
- Video is ~10–100x per asset (shots, ASR). Sample frames per shot and cap the budget per video.

### 7.5 Model registry & lineage
- Every extractor registered with version, training data snapshot, gold-set metrics, and the signal(s) it produces.
- Lineage: signal value → model version → training data → taxonomy version. Needed for debugging ("why did 'lifestyle' prevalence jump 8% on Tuesday?" Answer: student v8 deployed) and for governance.

### 7.6 Documentation: "signal cards"
Like model cards, one per signal: definition and examples, intended uses and **non-intended uses** ("do not use face-count for audience demographic targeting"), quality by slice, known failure modes, version history, owner, how to request changes. Signal cards are how other teams adopt without meeting you.

### 7.7 Backward compatibility when the taxonomy changes

| Change | Strategy |
|---|---|
| Add a value/node (minor) | Additive; old consumers ignore it; but a **mutually-exclusive enum gaining a value shifts probability mass** from existing values, so notify consumers and publish a mapping |
| Split a node (`lifestyle` → `lifestyle_home`, `lifestyle_outdoor`) | Keep the parent as a **rollup** field (sum of children) so v1 consumers still work |
| Merge / redefine (major) | **Dual-publish** old and new versions for a deprecation window; provide an old→new mapping table; backfill history in the new version; consumers migrate and retrain on their own schedule |
| Embedding model change | Always major. Publish both embeddings in parallel; consumers retrain; ANN indices rebuilt; sunset old after adoption |

### 7.8 Quality monitoring & governance

- **Coverage:** % of active creatives (and % of impressions; weight by spend) with each signal, per version.
- **Freshness:** upload-to-signal latency distribution vs SLA.
- **Drift per attribute:** prevalence over time (PSI or JS divergence vs baseline), confidence distribution shift, abstention rate. Distinguish **real-world drift** (holiday season raises `holiday=christmas` prevalence, which is expected) from **model drift** (prevalence jumps at a model deploy). Annotate dashboards with deploy events and the retail calendar.
- **Label audits:** monthly stratified human audit of production values per attribute; precision/recall/ECE trend; alert on degradation.
- **Consumer-side monitoring:** downstream feature importance and the impact of dropping each signal (Section 10).
- **Access & governance:** advertiser data isolation (one advertiser's creative signals and performance insights must not leak to competitors, especially aggregated insights at fine granularity); PII (faces in creatives; don't infer sensitive attributes like race, age or gender of depicted people without explicit legal/policy approval); retention; approved-use lists per signal; audit logs of who consumes what.

**Say it like this:** "A signal platform succeeds when other teams can adopt it without talking to me. That means contracts, signal cards, SLAs, and monitoring that catches a bad deploy before a consumer's pCTR model does."

**Your bridge:** "Honestly, cross-team signal consumption at this scale is newer for me. What I've done is ship models whose outputs other product teams depended on, which taught me versioning and backward compatibility the hard way. Here I'd treat the creative signals as a product with internal customers, and I'd go and sit with the ranking and measurement teams first to learn what they actually need."

---

## 8. Using signals for performance insight

### 8.1 The naive analysis (and why it is wrong)

"Group by `has_lifestyle_image`, compare CTR: lifestyle 1.8%, on-white 1.2%, so lifestyle is +50%." Almost certainly confounded:

```
           brand size / budget ─────────┐
                │                        ▼
                ▼               placement & targeting quality ──► CTR
     creative attributes ───────────────────────────────────────► CTR
                ▲                        ▲
                │                        │
      category (grocery vs electronics) ─┘   season, auction competition, creative age/fatigue
```

| Confounder | Mechanism |
|---|---|
| **Brand / advertiser** | Big brands use agency lifestyle creatives *and* have brand equity that drives clicks |
| **Category** | Lifestyle is common in home/apparel and rare in electronics; base CTRs differ by category |
| **Budget / bidding** | Higher bids win better positions; position effects dwarf creative effects |
| **Placement** | Some placements favor certain formats; position and slot drive CTR |
| **Targeting** | Better-targeted campaigns may also invest in better creative |
| **Time / season** | Holiday creatives run in high-intent weeks |
| **Selection by the system** | The ranker already preferentially serves creatives it predicts will do well (feedback loop) |
| **Creative age** | Fatigue; newer creatives shown to fresher audiences |

### 8.2 Better designs, in order of credibility

1. **Randomized experiments (gold standard).** Multi-armed creative tests: the same campaign, the same targeting and bids, randomized creative assignment differing in an attribute (ideally *generated* variants that differ in exactly one attribute, which GenAI makes uniquely cheap). Generative creative turns observational questions into experiments, and that's a big opportunity.
2. **Within-campaign / within-ad-group comparisons.** Advertisers often run multiple creatives in the same ad group, which fixes advertiser, product, targeting and budget. Use **fixed effects** for campaign × placement × week; the attribute effect is identified from within-group variation. Caveat: within-group serving isn't random (the ranker/optimizer shifts traffic), so control for the serving policy or use only the early randomized/exploration phase.
3. **Exploration logs.** If the creative selector has an exploration component (bandit with known propensities), **inverse propensity weighting** on logged data gives unbiased estimates of attribute effects.
4. **Causal ML on observational data:** **double/debiased ML (DML)**: residualize CTR and the attribute on confounders (brand, category, placement, position, bid, time) with flexible ML models using cross-fitting, then regress residual-on-residual for the effect. Or **matching** (propensity or exact-on-category+placement plus embedding-nearest-neighbor) for comparable creative pairs. Always report **overlap**: if lifestyle images never appear in electronics, you can't estimate the effect there.
5. **Hierarchical (multilevel) Bayesian models:** `CTR ~ attributes + (1|advertiser) + (attributes|category) + placement + position`. Partial pooling gives stable per-category effects for sparse categories, with honest uncertainty.

**The attribute itself is "multi-valued treatment with measurement error":** attribute extraction errors attenuate estimated effects (regression dilution) and can be *differential* (the classifier is worse on some categories, which creates spurious heterogeneity). Use calibrated probabilities, validate on audited subsets, and run sensitivity analyses.

**Say it like this:** "Attribute-to-CTR correlations from observational data are mostly a map of who can afford agency creative. I'd use within-campaign fixed effects as a first pass, DML with cross-fitting when I need to adjust for many confounders, and I'd push hard for GenAI-enabled single-attribute A/B tests, because generation makes randomized creative experiments cheap."

**Your bridge:** (See `90_optional_measurement_reference.md` for DML mechanics.) "The creative case is a nice instance of it: the treatment is an extracted attribute, and the confounders are brand, category, placement and position."

### 8.3 Creative-level performance prediction

- **Model:** predict creative CTR (or CVR, ROAS) *conditional on context*: `f(creative attributes, creative embedding, SKU features, placement, category, advertiser features) → pCTR`, trained on impression logs with position/placement as features (or a position-bias tower), and evaluated on **new creatives held out by time and by advertiser** (cold-start evaluation).
- **Uses:** pre-launch scoring ("this creative is predicted bottom-quartile for this placement"), cold-start priors for ranking, reward for generation, prioritizing review.
- **Explanations:** SHAP over attributes gives *predictive* attributions, **not causal effects**. Say this out loud in the interview, because it's a common trap.

### 8.4 Insights for advertisers (with guardrails)

A statement like "Lifestyle images in grocery get 12% higher CTR" should only ship if:
- It comes from experiments or properly controlled within-campaign/DML analysis, with confidence intervals.
- It's **category- and placement-specific** (effects are heterogeneous).
- It's aggregated with **privacy thresholds** (no leakage of a specific competitor's performance; minimum advertiser counts per cell).
- The language is honest: "associated with" vs "causes", with an explanation of the method in an internal note.
- It's monitored: insights decay as creative trends and the ranker change.

### 8.5 Feeding back into generation

```
 attributes + embedding ──► performance model / reward model R(creative, context)
                                      │
   GenAI creative generator ◄─────────┤ (1) conditioning: generate with target attributes
                                      │ (2) reranking: generate N candidates, score, keep top-k
                                      │ (3) fine-tuning: RL / preference optimization against R
                                      ▼
   gates: artifact/fidelity (Sec. 5), policy, brand-kit adherence → serve → logs → retrain R
```

- **Best-of-N + rerank** is the safest first step. Fine-tuning against a learned reward invites **reward hacking** (the generator finds what R likes, e.g., saturated colors or giant price text, not what shoppers like). Mitigate with KL regularization to the base model, reward ensembles, hard constraint gates, and **online A/B validation** of R's predictions.
- **Exploration is required:** if you only generate what R already likes, R never learns about new styles. Reserve exploration traffic.
- Attribute conditioning gives advertisers **control** ("lifestyle, kitchen, warm palette, offer badge top-right"), which is often more valuable than pure optimization.

---

## 9. Integration with ranking & targeting

### 9.1 Creative features in pCTR models

| Feature form | How it enters the model | Notes |
|---|---|---|
| Creative embedding (frozen, precomputed) | Dense input, maybe projected to 32–64 d | Biggest cold-start win; versioned |
| Attribute probabilities | Dense features (calibrated probs) or bucketized | Interpretable; robust to embedding version changes |
| Quality scores | Dense | Also usable as a floor/penalty in auction scoring |
| Creative × context crosses | Feature crosses (DCN-style) or attention: `attribute × placement`, `embedding · user-embedding` | Lets the model learn "text-heavy hurts on small mobile slots" |
| `creative_id` sparse embedding | As before | Memorization for warm creatives; content features generalize |

**Cold start:** a new creative has no ID history. Content features let the model predict from similar creatives immediately, and the ID embedding takes over as data accrues. Some systems also **warm-start the ID embedding** from a content-to-ID-embedding mapper trained on warm creatives (meta-embedding style).

**Measuring value:** offline **Normalized Entropy (NE)** (log loss normalized by the entropy of the background CTR, from the Facebook 2014 ads paper) and AUC, *sliced by creative age* (new creatives < 24 h should show the biggest gain). Then an online A/B on CTR, revenue, and advertiser ROAS. A 0.1–0.5% NE gain is considered meaningful in mature ads rankers. Don't claim specific Walmart numbers.

### 9.2 Audience–creative matching (targeting)

- **Two-tower affinity:** user/segment tower ↔ creative tower trained on engagement (Section 4.2's creative–engagement objective). Score = affinity used for creative selection within an ad group, or as a ranking feature.
- **Attribute-level rules** for advertiser-facing targeting ("serve Spanish-language creative to Spanish-preference shoppers"): this is where interpretable attributes beat embeddings.
- **Guardrails:** don't let affinity models proxy protected characteristics, e.g., learning that creatives depicting certain demographics are shown only to certain demographics. Audit creative-delivery skew by depicted-people attributes. Ad delivery discrimination is a known regulatory and reputational risk area in the industry.

### 9.3 Creative selection per user/context: contextual bandits

```
 request context x (user segment, query, placement, device, time)
 arms a ∈ creatives in the eligible ad group, described by φ(a) = [attributes, embedding]
 model: reward r ~ f(x, φ(a))      e.g., LinUCB on x ⊗ φ(a), or neural model + Thompson sampling
 select a = argmax  E[r] + exploration bonus      (or sample from the posterior)
 log propensity p(a | x)  ──► enables unbiased offline policy evaluation (IPS / doubly robust)
```

- **Why attributes/embeddings as arm features:** learning is **shared across creatives**. A new creative with similar attributes inherits knowledge, which is crucial when ad groups have few creatives and short lives.
- **Log propensities.** This single design decision makes later causal analysis (Section 8.2) and offline policy evaluation possible.
- **Interaction with the auction [Assumption, industry-typical]:** the creative choice changes pCTR, which changes the eCPM bid. Selecting a creative inside the auction means the ranker scores (ad, creative) pairs, which multiplies candidates. Common compromise: pick the creative per ad first with a lightweight model, then auction.
- **Fatigue:** add frequency/recency features per user×creative; decay rewards over time.

**Your bridge:** "I haven't run bandits in production ads. But the structure, a model over context times item features with calibrated uncertainty, is familiar. The part I'd lean on the team for is the auction interaction and the experimentation infrastructure."

---

## 10. Metrics for the signals themselves

### 10.1 Metric stack

| Layer | Metric | How measured |
|---|---|---|
| **Intrinsic quality** | Precision / recall / F1 per attribute value; macro over values | Frozen human gold set (stratified), plus monthly production audit |
| | Calibration: ECE, reliability diagrams, per slice | Gold/audit sets |
| | Risk–coverage curves (precision at abstention threshold) | Gold set |
| | Inter-annotator agreement (ceiling) | Multi-annotated subset; if κ is 0.6, don't expect the model to look much better than that |
| | Embedding: retrieval recall@k on SKU matching, linear-probe accuracy on attributes | Benchmarks |
| | Artifact detector: image AUROC, precision at operating recall, pixel-AUROC/PRO for localization; **evaluated on real generator failures** | Real-failure set per generator version |
| **Operational** | Coverage (% creatives, % impressions, % spend) | Platform metrics |
| | Freshness: upload-to-signal p50/p99 vs SLA | Platform metrics |
| | Cost per 1K creatives; VLM call rate | Platform metrics |
| | Drift alarms, incident count | Monitoring |
| **Adoption** | Number of consuming teams/models/dashboards; queries per day; signals in production models | Registry and access logs |
| **Downstream impact** | Ranking: NE/AUC gain when adding creative features, especially for new creatives; online CTR/revenue/ROAS lift in A/B | Offline ablation + online experiments |
| | Policy: review-queue reduction at equal or better precision; time-to-approve | Ops metrics |
| | Generation: artifact rate per release; % generated creatives passing gates; performance of generated vs human creatives in A/B | GenAI pipeline + experiments |
| | Insights: advertiser adoption of recommendations and measured lift from following them (experiment) | Product analytics |

### 10.2 Ablations that prove value
- **Drop-one-signal-group ablation** in the pCTR model: remove embeddings / quality / semantic / messaging groups and measure NE change. That tells you which parts of the genome earn their keep.
- **Noise-injection test:** degrade an attribute's accuracy synthetically and measure downstream sensitivity. This tells you how much to invest in improving that extractor (value of accuracy).

**Say it like this:** "I'd hold the signal platform accountable at three levels: intrinsic accuracy and calibration against human audits, operational coverage and freshness, and downstream lift. If adding creative features doesn't move NE for new creatives, or doesn't cut review load, the signals aren't worth their cost no matter how good the F1 looks."

---

## 11. Twenty practice questions with model answers

**Q1. What is a "creative genome" and why build one?**
A versioned, structured description of every creative: interpretable attributes (visual, semantic, messaging, brand, format, quality, policy, accessibility) plus embeddings, each with confidence and lineage. It turns opaque creative IDs into shared features. Ranking gets cold-start generalization, measurement gets attribute-level insight, generation gets conditioning and reward, and policy and search get facets. Building it once and sharing it lets improvements compound across teams.

**Q2. How would you design the attribute taxonomy?**
Start from consumer needs (what will ranking, measurement, policy and generation actually use?). Organize into levels (low-level, semantic, messaging, brand, format, quality, policy, accessibility), make it a hierarchy aligned with the product taxonomy, use a closed core with an open-vocabulary periphery for discovery, write specs with positive/negative examples, measure annotator agreement to validate definitions, and version it with semver and dual-publishing for breaking changes.

**Q3. CLIP zero-shot vs VLM vs trained classifier: when do you use each?**
Zero-shot CLIP/SigLIP for bootstrapping and long-tail attributes (cheap, no labels; weak at text, counting, spatial relations). VLMs with JSON-schema constrained decoding as teachers for complex, compositional or text-dependent attributes and for low-confidence routing. Trained or distilled students on a shared backbone for 100% coverage at low cost. Specialist models (OCR, detectors, IQA) wherever a precise geometric or text measurement is needed.

**Q4. How do you make zero-shot tags trustworthy?**
Prompt ensembles over templates and synonyms; softmax with a "none/other" class for exclusive enums, and sigmoid (SigLIP) for multi-label; per-attribute calibration (temperature/Platt/isotonic) on a few hundred in-domain labels; check ECE per slice; abstain below a threshold chosen on the risk–coverage curve; switch to a linear probe once a few hundred labels exist.

**Q5. How do you scale VLM-quality labels to tens of millions of creatives?**
Distill: run the VLM on a stratified sample, calibrate it against a human gold set, train a multi-head student on a shared frozen backbone using soft labels, serve the student everywhere, and route low-confidence or teacher–student disagreement cases back to the VLM. Cache backbone embeddings so new attributes or taxonomy bumps are cheap head re-runs. Watch for systematic teacher errors and exclude attributes where the teacher disagrees with humans.

**Q6. How do you detect artifacts in generated product creatives?**
Layered: (1) a supervised detector with image-level and per-patch heads, trained on programmatically corrupted images with known masks plus real generator failures; (2) patch-level anomaly scores on DINO features for unknown artifact types; (3) frequency/noise-residual cues, augmented for JPEG and resize robustness; (4) most important, **reference-based fidelity checks** against the source SKU image: alignment, then SSIM/LPIPS/DINO patch similarity in the product region, OCR diff on package text, and color ΔE for variant. Outputs are scores plus localization heatmaps used for gating, repair and generator feedback.

**Q7. Why are reference-based checks so valuable here?**
In retail ads we almost always have the catalog image of the advertised product, so we can ask the precise question "did the generator change the product?" rather than the vague one "does this look generated?". It catches the highest-severity failure (misrepresenting the product), it's interpretable (here is the text diff), and it generalizes across generator versions because it doesn't depend on generator fingerprints.

**Q8. How do you build training data for an artifact detector?**
A corruption engine: thin-plate-spline warps of text, glyph substitution, boundary geometry jitter, mismatched-lighting composites, halo bands, posterization, JPEG at varied quality, texture tiling, each with exact masks, so you get localization labels free. Add real failures from running the generator at scale with human labels. Diversify corruption parameters to avoid learning the pipeline's signature, and evaluate only on real failures.

**Q9. Generated vs. real: should p(generated) be a quality signal?**
No, keep them separate. Generated content can be excellent, and real photos can be bad. p(generated) serves disclosure and policy. Quality and artifact scores serve gating and ranking. Prefer provenance (log generation in our own tools, C2PA credentials, watermarks) over detection, which is brittle under re-compression and across new generators.

**Q10. How do you verify the creative shows the advertised SKU?**
Detect product instances (open-vocab detector prompted by the SKU's product type), embed crops with a fine-grained Walmart-tuned product embedding, ANN-retrieve against catalog images filtered by brand/category, then verify with keypoint geometric matching and OCR of brand/size text. Output `linked_sku_visible`, prominence, variant match, and other SKUs visible. Train the embedding with hard negatives from sibling variants.

**Q11. How do you handle near-duplicate creatives?**
Hybrid: cryptographic hash for exact, perceptual hash (pHash/PDQ, Hamming distance) for re-encodes and resizes, copy-detection or DINO embeddings with ANN for crops and overlays, and OCR diff to distinguish "same image, different price". Publish a similarity graph with edge types, because "duplicate" means different things for measurement (headline variants are distinct), review (inherit decisions), and policy (re-uploaded rejected creatives).

**Q12. Design smart cropping for multi-format delivery.**
Build an importance map from the linked-product mask, text boxes, logo, faces and saliency. Search crop windows at the target aspect, maximizing importance under hard constraints (product whole, no text cut, safe zones). If infeasible, outpaint or re-layout, then gate with fidelity/artifact checks. Publish crop-robustness per aspect as a signal. Audit for demographic bias in subject selection (the Twitter cropping lesson).

**Q13. Embeddings or attributes: which do you give the ranking team?**
Both. Embeddings give the most predictive power and cold-start generalization. Calibrated attribute probabilities are interpretable, survive embedding-version changes, and enable crosses with context like placement. Measure with group ablations, sliced by creative age.

**Q14. How would you fine-tune a Walmart creative embedding?**
Multi-objective contrastive training (InfoNCE or SigLIP loss): creative ↔ linked SKU image/title, creative ↔ clicked queries, creative ↔ engaged-segment embeddings. In-batch negatives with logQ correction for popularity, hard negatives from same-category/brand and sibling variants with false-negative masking, debiasing or down-weighting of engagement signals, and weights tuned on downstream evaluations (SKU retrieval recall, attribute probes, pCTR NE). Version and dual-publish when it changes.

**Q15. A dashboard shows lifestyle images get 50% higher CTR. What do you say?**
Likely confounded by brand, budget, category, placement, position, season and the ranker's own selection. I'd re-estimate within campaign/ad-group with fixed effects for campaign × placement × week, use DML with cross-fitting on observational data where overlap exists, check attribute-extraction error by slice, and, best of all, run randomized creative tests using generated variants that differ only in that attribute. Report category-specific effects with confidence intervals.

**Q16. How do creative signals help cold start in ranking?**
A new creative has no ID history, so the pCTR model leans on content features: embedding, attributes, quality, and SKU features. The ID embedding takes over as impressions accrue, and it can be warm-started from content via a learned mapper. Measure NE/AUC on creatives in their first 24–72 hours, then confirm online.

**Q17. How would you choose among an advertiser's five creatives per request?**
A contextual bandit with context features (segment, query, placement, device) and arm features (attributes + embedding), so learning transfers across creatives. Use Thompson sampling or UCB, add fatigue features, and log propensities for off-policy evaluation and causal analysis. Decide where it sits relative to the auction, typically pre-auction per-ad selection for cost.

**Q18. A taxonomy change splits "lifestyle" into three children. How do you avoid breaking consumers?**
Minor version if additive: keep `lifestyle` as a rollup (sum of children) so v1 consumers continue to work, announce it in the signal card, backfill history so training and serving are consistent, and give consumers a migration window. If meaning changes, cut a major version, dual-publish with a mapping table, and sunset after consumers retrain.

**Q19. How do you monitor the signals in production?**
Coverage and freshness vs SLA; per-attribute prevalence drift (PSI) and confidence/abstention drift, annotated with deploy events and the retail calendar to separate real-world from model drift; monthly stratified human audits for precision/recall/ECE; downstream consumer metrics; and alerts that fire before a consumer's model degrades. Lineage lets you trace any shift to a model or taxonomy version.

**Q20. How do you prove the creative-signal platform is worth it?**
Three tiers: intrinsic (audited precision/recall/calibration, coverage, freshness, cost), adoption (consuming teams and production models), and impact (pCTR NE lift, especially for new creatives, and online CTR/revenue/ROAS lift; review-queue reduction at equal precision; artifact rate per generator release; measured advertiser lift from following insights in experiments). Drop-one-group ablations show which signals earn their cost.

---

## 12. Closing: how to position yourself on this bullet

**Say it like this (if asked "why are you the right person for creative understanding?"):**
"Creative understanding is computer vision applied to a business that measures everything. I bring deep CV and representation learning: ViT, DINO, contrastive InfoNCE, CLIP, distillation from big teachers into cheap students, multimodal fusion, and generative imaging with the physical intuition from 3D graphics and lighting estimation that artifact detection needs. What I'd learn from the team is the ads side: which signals the rankers and measurement teams actually consume, how creative selection interacts with the auction, and the experimentation stack. My plan for the first months would be to co-design the signal contracts with those consumers before building more models."

**Honest gaps to acknowledge (one sentence each, then pivot):**
- Ads ranking and auction mechanics in production → "I've studied the pipeline; I'd rely on the ranking team for auction interactions."
- Large-scale data platforms and feature stores → "I'd plug into the existing stack and focus on the signal contracts and quality."
- Cross-team signal consumption → "I've shipped models other teams depended on; here I'd run it as an internal product with consumer reviews."
