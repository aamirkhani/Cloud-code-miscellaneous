# 13 — Video Ad Generation, Adaptation & Evaluation: A Detailed Study Guide

**Role:** Distinguished Data Scientist, Creative Intelligence (Walmart Ads, R-2630449)
**Why this chapter exists:** the JD names **video** as a first-class output of the generative creative system, alongside images and copy. Video is also where your background is unusually strong: you have trained diffusion models from scratch, shipped motion-vector frame synthesis, built disocclusion inpainting, built H.265 capture pipelines, and published a per-video temporal-quality metric. The gap is that you have never run a *production* video-generation system, and you don't know the ad domain. This chapter is meant to close that gap well enough that you can lead the discussion.

**How to use it:** read §0 and §2 first, because they contain the thesis. §3 (technical refresher) and §7 (evaluation) are where you can show depth, so be ready to go to the whiteboard on them. §10 is a drill: cover the answers and say yours out loud.

> **Hedging rule for the interview:** do not claim to know Walmart's internal stack, their spec sheets, or which vendor models they use. Say "I'd expect…" or "the public spec I've seen says roughly…, and I'd confirm." Model names, parameter counts and benchmark numbers change every quarter. Treat everything below marked *(hedge)* as approximate.

---

## 0. The thesis in 60 seconds

**Say it like this:**
> "For video ads at Walmart's scale, I wouldn't start with text-to-video. I'd start with what is deterministic and brand-safe: templated motion graphics built from the catalog's product images, with 2.5D parallax, kinetic type and a correct end card. Second, automated cut-downs and reframing of the video advertisers already have. Third, generative models used *around* the product, not *on* it: animated backgrounds, lifestyle b-roll, and frame interpolation. The product itself stays a tracked, composited layer, so it cannot morph. All of this runs through a structured timeline representation, so that adaptation to 9:16, 6 seconds, CTV or in-store is a re-render rather than a re-generation. It's gated by an automated evaluator that scores per-frame quality, temporal quality, product fidelity and policy, and that evaluator is calibrated against human and advertiser judgments. The hard ML problem isn't generating pretty video. It's generating video you can *guarantee* shows the right product, says only approved claims, and doesn't secretly score well on a metric while looking frozen."

**Your bridge:** "I've worked on both ends of this. I've trained diffusion models from scratch, and I shipped frame synthesis from depth and motion vectors on Galaxy XR. I also published a reference-free per-video temporal metric, along with a negative result: when we used it as a training loss, the model gamed it. That experience is exactly why I'd design the evaluator and the generator as separate, adversarially-aware systems."

---

## 1. Video ad formats and specs

### 1.1 The placement landscape (Walmart-relevant)

| Placement | Where | Typical aspect | Typical length | Sound | What matters most |
|---|---|---|---|---|---|
| **Sponsored Videos (search/browse)** | Walmart.com / app search results, near Sponsored Products | Often 16:9 or square-ish in grid; confirm current spec *(hedge)* | Short; roughly 5–30 s range *(hedge, confirm)* | **Muted autoplay by default** | Hook in the first 1–2 s, readable on-screen text, captions, product legible at small size |
| **Onsite display/video (homepage, PDP)** | Walmart.com | 16:9, 1:1, 4:5 | 6–30 s | Usually muted | Same as above, plus brand blocks |
| **Social-style / vertical** | Off-site via DSP, social, Walmart app stories-like surfaces | **9:16**, 4:5, 1:1 | 6–15 s | Mixed; design for sound-off | Native look, fast pacing, safe zones for UI overlays |
| **Walmart DSP (off-site display/OLV)** | Open web, publisher inventory | 16:9 mostly, 1:1 | 15 / 30 s, **6 s bumpers** | Often sound-on but user-initiated | VAST compliance, multiple renditions |
| **CTV (incl. Vizio, acquired by Walmart; deal closed late 2024)** | Living-room TV, FAST channels, Vizio home screen | **16:9**, 1080p or higher | **15 s / 30 s** standard | **Sound-on**, lean-back | Broadcast-grade picture, **loudness compliance**, title-safe areas, mezzanine file quality |
| **In-store screens** | Walmart stores: TV walls, endcaps, checkout screens | Varies (landscape, portrait, odd panels) | Short loops, 5–15 s | **Usually silent** | Readability at distance, high contrast, no reliance on audio, loopability |

**Say it like this:**
> "Every placement is really a constraint set: aspect ratio, duration, sound-on or sound-off, safe zones, file spec, loudness and policy. The generator should take that constraint set as input. Treating each one as a separate creative project doesn't scale."

### 1.2 Anatomy of a short-form ad

```
 t=0s        1–2s            ~3–8s                 ~8–12s          last 2–3s
 |---HOOK---|---PRODUCT REVEAL---|-----BENEFIT/PROOF-----|----CTA----|--END CARD--|
  motion,     product hero shot,   1–2 benefits,           "Shop now   logo, product,
  pattern     packaging legible,   demo / lifestyle,       at Walmart" price/offer
  break,      brand cue early      supers (on-screen text)  + button    (if allowed),
  face/hand                                                  cue         legal supers
```

- **Hook (0–2 s):** the strongest predictor of completion rate in short-form. That means motion onset, an unexpected visual, a face or hand interacting with the product, or a bold text super. Branding in the first few seconds tends to help recall *(industry heuristic; hedge)*.
- **Product reveal:** packaging should be legible and **identical to the catalog SKU**, because retail media sells a specific item.
- **Benefit/proof:** 1–2 claims at most. **Every claim must be substantiated and approved.** Claims like "#1", "clinically proven" and "new" have legal requirements behind them.
- **CTA:** retail-specific ("Shop now", "Add to cart", "Find it in store").
- **End card:** logo, product, sometimes price/rollback. Price is dangerous in generated assets because prices change; render it from live data or leave it out.
- **Legal supers:** disclaimers ("Results may vary", "Offer valid through…", "Simulated image", "Professional driver"). They need a minimum on-screen duration and size so they're readable. Broadcast standards and some platforms have rules here *(hedge)*. Also add **AI-generated content disclosure** where a platform or regulation requires it. This is an evolving area, so check per platform *(hedge)*.

### 1.3 Technical specs you should know cold

| Item | Practical value | Notes |
|---|---|---|
| Frame rate | 23.976 / 24 / 25 / 29.97 / 30 fps | Keep the source rate; CTV often requires matching broadcast cadence *(hedge)* |
| Resolution | 1080p is the safe default; 4K for some CTV | Generators typically output 480p–720p natively, so you **need SR** for CTV |
| Codec delivery | H.264 (universal), HEVC/H.265 (CTV/efficiency), AV1 (web efficiency), ProRes/high-bitrate **mezzanine** for CTV ad servers to transcode | CTV SSPs often reject low-bitrate files *(hedge)* |
| Loudness, US broadcast | **CALM Act → ATSC A/85: −24 LKFS integrated, ±2 dB** | Many CTV/streaming specs follow −24 LKFS/LUFS; true-peak ceiling around −2 dBTP *(hedge)* |
| Loudness, EU | EBU R128: −23 LUFS | |
| Loudness, social/streaming music | often around −14 LUFS | Platform-normalized *(hedge)* |
| Safe areas | Title-safe ~90%, action-safe ~93% for TV; UI-overlay safe zones for 9:16 | Text and logo must sit inside the safe area |
| Captions | Burned-in (open) captions for muted placements; sidecar (WebVTT/SRT/CEA-608/708) for CTV | Also needed for accessibility, see §5 |

**Say it like this:**
> "One thing that's easy to miss is that CTV is broadcast. The generator has to emit a loudness-compliant mix around −24 LKFS, a mezzanine-quality file, title-safe text and caption tracks. A 720p diffusion output with a −14 LUFS social mix would be rejected at ingest."

**Your bridge:** "I've built H.265 capture pipelines, so I know the encoder side: rate control, GOP structure, and how sensor noise or generated grain eats bitrate. Generated video often has high-frequency shimmer, and that costs bits and causes banding at low bitrates."

---

## 2. The approaches spectrum, and why production is hybrid

### 2.1 Five approaches

```
 SAFER / CHEAPER / DETERMINISTIC  <------------------------------->  RICHER / RISKIER / COSTLIER

 (a) Template motion    (d) Edit/cut-down     (b) Image-to-video    (e) Avatars + TTS    (c) Text-to-video
     graphics from          advertiser's          animate product        voiceover            lifestyle b-roll
     product images         existing video        shot / scene                                 from scratch
```

| | Approach | How it works | Strengths | Risks | Cost |
|---|---|---|---|---|---|
| **(a)** | **Template / motion graphics** | Catalog images → background removal → layout engine → animation curves (Ken Burns pan/zoom, **2.5D parallax** from monocular depth, kinetic typography, transitions) → render | Deterministic, pixel-exact product, on-brand, cheap, fast, easy to adapt | Can look generic, so you need template diversity and good motion design | ~real-time render on CPU/GPU, fractions of a cent |
| **(b)** | **Image-to-video (I2V)** | Product or scene image as first frame (or keyframes) → video diffusion model animates it | Real motion, lighting changes, camera moves; grounded in a real image | Product morphing, text warping, physics errors | High, GPU-minutes per clip |
| **(c)** | **Text-to-video (T2V)** | Prompt → video | Lifestyle b-roll, scenes you don't have | No product grounding, IP/likeness risk, hallucination, highest variance | Highest |
| **(d)** | **Edit / cut-down / reframe** | Shot detection → shot scoring/highlight detection → selection under duration constraint → saliency-tracked reframing → captioning → music beat-sync | Uses advertiser-approved footage, so lowest policy risk; huge scale lever for CTV→social | Bounded by source quality; reframing can crop out key content | Low to moderate |
| **(e)** | **Avatars / TTS voiceover** | Script → TTS (brand voice) → optional talking avatar | Explainer and UGC-style ads at scale | Likeness rights, deepfake perception, lip-sync uncanny valley, pronunciation of product names, disclosure requirements | Moderate |

### 2.2 Details worth knowing for (a)

- **Background removal / matting:** segmentation (SAM-family) plus matting for hair and soft edges. Catalog images are often already on white, which makes this easy.
- **2.5D parallax:** monocular depth (MiDaS / Depth Anything / Marigold-style models *(hedge)*) → layer the scene into depth slices or a mesh → move a virtual camera slightly → **disocclusions appear at depth edges** → inpaint them. *This is your SpaceWarp problem: reprojection from depth, holes at disocclusions, and filling them.*
- **Kinetic typography:** text animation driven from the copy system (the JD's "copy" output), with font and color from the brand kit.
- **Beat-synced cuts:** onset/beat detection on the music track → snap transitions to beats.

**Your bridge:** "2.5D parallax is literally reprojection: you take an image and a depth map, move a camera, warp, detect disocclusions, and inpaint. I shipped that pipeline under a hard real-time budget on Galaxy XR. In an ad pipeline it's the cheapest way to get 'real' motion out of a still product photo without letting a diffusion model touch the product pixels."

### 2.3 Details worth knowing for (d)

```
 Advertiser 30s CTV spot
   │
   ├─ Shot boundary detection (TransNet-style / histogram+feature deltas)
   ├─ Per-shot features: product present? (detector + catalog match), logo present?, face?,
   │   motion energy, aesthetic score, speech segment (ASR), on-screen text (OCR), music beats
   ├─ Shot scoring (learned: predicts contribution to completion/recall; or rules for v1)
   ├─ Selection = constrained optimization:
   │     maximize Σ score(shot)   s.t.  Σ dur ≤ 15s (or 6s), must include product shot,
   │     must include end card/logo, keep narrative order, don't cut mid-word (ASR alignment)
   │     → knapsack/DP over ordered shots; trim at beats or speech pauses
   ├─ Reframe 16:9 → 9:16 / 1:1 (saliency + detection + smoothed crop path, §6)
   ├─ Re-time legal supers (they must survive the cut and stay readable)
   ├─ Captions (ASR → aligned subtitles → burned-in for muted placements)
   └─ Audio: re-edit music to new length (beat-aligned cuts, crossfades), loudness normalize
```

**Say it like this:**
> "Cut-downs are the most underrated lever. Advertisers already have approved 30-second spots, so making 15s, 6s and 9:16 versions automatically creates huge value with almost no policy risk. It's a constrained-selection problem. Generative models are barely involved."

### 2.4 Recommended staged roadmap

| Stage | What ships | Generative ML involved | Gate to next stage |
|---|---|---|---|
| **0. Foundations** (months 0–3) | Structured creative representation (timeline JSON, §2.5), brand kits, spec registry per placement, eval harness v0, human review UI | None, but sets up everything | Eval harness agrees with human reviewers on accept/reject (target Cohen's κ > 0.6) |
| **1. Template + parallax video from catalog** | 6–15 s product videos from product images and copy, all aspect ratios | Depth, matting, inpainting, copy LLM | Acceptance rate, advertiser adoption, VCR/CTR parity vs. static image ads |
| **2. Cut-downs and reframing** | 30→15→6 s, 16:9→9:16/1:1, auto-captions, loudness compliance | Shot scoring, saliency, ASR | Human-rated "would ship" ≥ target; legal supers preserved 100% |
| **3. Generative backgrounds / b-roll around a locked product** | I2V/T2V for *scene*, product composited as tracked layer | Video diffusion, relighting, harmonization | Product-fidelity score min-over-frames ≥ threshold on 99%+ of shipped clips |
| **4. Full I2V of product shots, voiceover, avatars (selectively)** | Hero product motion, TTS VO, limited avatar use with consent | I2V, TTS, lip-sync | Policy and legal sign-off, disclosure UX, incrementality test results |

Across all stages, run **creative-level performance modeling and bandit allocation** (§9) so that the system learns which structures actually work.

### 2.5 Structured representation of video creative (the JD names this)

Generate a **timeline**, not pixels. Pixels are a render target.

```json
{
  "creative_id": "c_8f3…", "version": 7, "brand_kit": "bk_acme_2026",
  "placement_spec": "walmart_sponsored_video_16x9_v3",
  "duration_s": 15.0, "fps": 30, "canvas": [1920, 1080],
  "tracks": {
    "video": [
      {"t":[0.0,2.0], "type":"generated_bg", "model":"i2v@v12", "seed":4411, "prompt_id":"p_…",
       "layers":[{"type":"product_layer","sku":"WM123","asset":"cutout_v3.png",
                  "transform_track":"kf_…","relight":"env_from_bg"}]},
      {"t":[2.0,8.0], "type":"source_clip", "src":"adv_upload_42.mov", "in":12.3, "out":18.3,
       "reframe_path":"crop_…"},
      {"t":[12.0,15.0], "type":"end_card", "template":"ec_logo_cta_v2", "cta":"Shop now"}
    ],
    "text": [{"t":[0.3,2.0], "role":"hook", "copy_id":"cp_…", "style":"bk.title"},
             {"t":[12.0,15.0], "role":"legal_super", "copy_id":"lg_…", "min_px":28}],
    "audio": [{"type":"music", "track":"lib_8812", "license":"lic_…", "beat_grid":"bg_…"},
              {"type":"vo", "tts_voice":"brand_voice_v2", "script_id":"s_…", "lexicon":"lx_acme"}],
    "captions": {"source":"vo_script", "burn_in": true, "sidecar":"webvtt"}
  },
  "claims": ["claim_id_77 (approved 2026-09-01)"],
  "provenance": {"c2pa": true, "models": ["i2v@v12","tts@v4"], "human_approver": null}
}
```

Why this matters:
- **Adaptation = re-render** with a new spec (aspect, duration). Shots and layers are re-laid-out by a constraint solver. You don't regenerate.
- **Evaluation can be structural:** "Is the logo on screen for ≥ 1.5 s?", "Is the legal super ≥ min duration?", "Is the product visible in the first 3 s?" These checks are exact, with no model needed.
- **Performance modeling** gets interpretable features (hook type, product-on-screen time, cuts/sec, CTA wording).
- **Provenance and versioning:** every pixel can be traced to a model version, seed and approved claim. Support **C2PA** content credentials where feasible *(hedge on platform support)*.

**Say it like this:**
> "I'd make the timeline the system of record. A generative model proposes a timeline, deterministic renderers and constrained generators fill it, and evaluators check both the timeline and the pixels. That's what makes 'adapt across formats and placements' tractable."

---

## 3. Video diffusion: an expert-level refresher

### 3.1 Latent video diffusion pipeline

```
 video x ∈ R^{T×H×W×3}
   │  3D causal VAE encoder  (e.g., 4× temporal, 8×8 spatial, C≈16 latent channels — common; hedge)
   ▼
 z ∈ R^{(1+T/4)×(H/8)×(W/8)×C}         ← first frame often encoded alone (causal) so images = 1-frame videos
   │  patchify (1×2×2) → tokens         ← N_tokens = T' × (H/16) × (W/16)
   ▼
 DiT / MM-DiT backbone with 3D RoPE, text tokens (T5/LLM encoder), timestep via adaLN
   │  trained with flow matching (rectified flow) or ε/v-prediction diffusion
   ▼
 denoised z  →  VAE decoder (tiled/chunked in time to fit memory)  →  frames
   │
   └─ optional: temporal interpolation (more fps), spatial SR (480p/720p → 1080p/4K)
```

### 3.2 3D VAEs and spatiotemporal compression

- **Why:** pixel-space video is too big. A 5 s 720p clip at 24 fps is ~121 frames × 1280×720×3 ≈ 335M values.
- **Causal 3D convolutions:** temporal padding happens only on the past side, so frame *t* depends on frames ≤ *t*. The first frame is encoded independently, which allows joint image+video training and makes I2V natural.
- **Typical compression:** 4×(time) × 8×8(space) with 16 channels is common in open models (CogVideoX, HunyuanVideo, Wan-family *(hedge)*). Some models push much harder, e.g. LTX-Video reports ~32×32×8 spatial-temporal compression with many more channels to enable near-real-time generation *(hedge)*.
- **Trade-off:** higher compression makes the DiT cheaper but loses fine detail. **Small text and logos are the first casualties**, which matters directly for packaging fidelity. This is a strong argument for compositing the product rather than generating it.
- **Losses:** reconstruction (L1 + LPIPS), KL (small), adversarial (patch GAN, often 3D). The VAE ceiling bounds the generator: if the VAE can't reconstruct 6-pt nutrition text, neither can the model.
- **Temporal chunked decode:** decoders run in overlapping temporal tiles with blending. Tile seams can create periodic flicker, which your temporal metrics should catch.

**Your bridge:** "Before trusting a video model with packaging, I'd measure the VAE ceiling: encode-decode real product videos and score OCR and logo fidelity. If the round trip already breaks the text, no amount of generator tuning fixes it."

### 3.3 Attention: factorized vs full 3D

| Design | How | Pros | Cons |
|---|---|---|---|
| **Factorized (2D spatial + 1D temporal)** | Alternate spatial self-attn within each frame and temporal attn across frames at the same spatial location (Video LDM / AnimateDiff era, inflated U-Nets) | Cheap: O(T·(HW)²) + O(HW·T²); can inflate a pretrained image model | Weak at large motion, because temporal attn only links co-located tokens and moving objects leave their column |
| **Full 3D attention** | All tokens attend to all tokens, O((T·H·W)²) | Best motion coherence and object permanence; standard in modern DiT video models (CogVideoX, HunyuanVideo, Wan *(hedge)*) | Quadratic cost dominates; needs FlashAttention, sequence parallelism, sparse/windowed tricks |
| **Sparse / windowed 3D** | Local 3D windows, sliding tile attention, learned sparsity *(hedge on names)* | Big speedups at high resolution | Can lose long-range consistency |

**Cost math (memorize the shape of it):**
- 5 s, 24 fps, 1280×720: 121 frames → latent frames 1 + 120/4 = **31**; spatial 160×90 latent → patch 2 → **80×45 = 3,600 tokens/frame** → **~112k tokens**.
- Full attention pairs per layer ≈ 112k² ≈ **1.25×10¹⁰**. Doubling duration means 2× tokens and **4× attention FLOPs**. Doubling resolution in each dim means 4× tokens and **16× attention**.
- Implication: **generate short (2–5 s) at moderate resolution, then extend, interpolate and super-resolve.** That's also why a template/compositing path is so much cheaper.

### 3.4 DiT-based video models

- **MM-DiT** (SD3-style): text and video tokens in one joint attention stream with separate weights per modality. The alternative is **cross-attention** to text embeddings.
- **Text encoders:** T5-XXL or LLM-based encoders (decoder LLM hidden states). Prompt rewriting with an LLM ("prompt extension") is standard practice because models are trained on dense, recaptioned data.
- **3D RoPE** for (t, h, w) positions supports variable aspect ratio and duration, which is important for 9:16 vs 16:9 *native* generation instead of cropping.
- **adaLN-Zero** timestep conditioning; **QK-norm** for stability at scale.
- **Training data:** recaptioning with a VLM, filtering for aesthetics, motion (optical-flow magnitude), OCR-text-heavy clips, scene cuts, watermarks. Multi-stage: images → low-res short video → high-res longer → quality fine-tune.
- **Mixture-of-experts over noise levels:** some recent open models split high-noise (layout/motion) and low-noise (detail) experts *(e.g., Wan 2.2 is described this way; hedge)*. This connects to your cosine-schedule work: different noise regimes do different jobs.

### 3.5 Flow matching / rectified flow

- Interpolation path: **x_t = (1 − t)·x₀ + t·ε**, t ∈ [0,1] (x₀ data, ε noise).
- Model predicts the **velocity v_θ(x_t, t, c) ≈ ε − x₀**; loss is ‖v_θ − (ε − x₀)‖².
- Sampling: integrate the ODE dx/dt = v from t=1 to 0 with Euler or higher-order solvers. Straighter paths need fewer steps.
- **Timestep sampling:** logit-normal or "shifted" schedules that put more weight at mid/high noise. **Resolution-dependent shift** matters because more tokens means more redundancy, so you need more noise to destroy structure. This is the same intuition behind your cosine schedule work, where the SNR schedule has to match the signal's redundancy.
- **CFG** still applies: v = v_uncond + w·(v_cond − v_uncond). It doubles cost unless distilled. Too high a w gives oversaturation and **reduced motion** (frozen video). Many systems use a separate or lower guidance on image conditioning in I2V.

**Your bridge:** "I've implemented DDPM, cosine schedules, CFG and consistency models from scratch. Flow matching is the same family with a linear path and velocity target. The practical knobs I'd watch in video are the timestep shift for token count and CFG-induced motion suppression."

### 3.6 Temporal consistency mechanisms

1. **Full 3D attention** (object permanence across frames).
2. **Correlated noise priors:** sample per-frame noise with a shared component (e.g., "mixed" or progressive noise) so frames start correlated *(PYoCo-style; hedge)*.
3. **Training on clean motion:** filter out clips with scene cuts, shaky handheld or compression artifacts.
4. **Temporal discriminators / adversarial losses** in the VAE and in distillation.
5. **Inference tricks:** noise re-initialization of low frequencies (FreeInit-style *(hedge)*), shared attention keys with the first frame, latent blending over overlaps.
6. **Post-hoc:** flow-guided temporal smoothing and deflicker. Use carefully, since it can blur detail.

### 3.7 Conditioning

| Control | Mechanism | Ad use |
|---|---|---|
| **First frame (I2V)** | Concatenate the first-frame latent (plus mask channel) to the noisy latent on the channel dim; optionally add a CLIP/SigLIP image embedding via cross-attn | Animate the catalog hero shot |
| **First + last frame / keyframes** | Condition at multiple timesteps with masks | Start on lifestyle, **end on an exact end-card-ready product frame** |
| **Camera control** | Camera extrinsics as **Plücker ray embeddings** per pixel (CameraCtrl-style), or text tokens ("slow dolly in") | Consistent "orbit the product" moves; matches templates |
| **Motion brushes / trajectories** | Sparse point trajectories or region masks with direction (DragNUWA / Motion-brush style *(hedge)*) | "Only the steam moves", "only the background moves", keep the product static |
| **Structure (ControlNet-style)** | Depth, edge, pose sequences | Re-render a reference motion with a new product or scene |
| **Reference identity** | Subject embedding / reference-image attention (identity-preserving) | Keep a product or a consented presenter consistent |

**Your bridge:** "Identity-preserving generation is my background: I've done identity-preserving face synthesis, where the key is injecting a reference embedding and then *verifying* identity with an independent embedding. The product version is the same pattern with DINO-style embeddings and OCR in place of a face-ID network."

### 3.8 Long-video generation

- **Autoregressive extension:** condition chunk *k+1* on the last *m* latent frames of chunk *k*. The risk is **drift and error accumulation** (color shifts, identity decay).
- **Sliding-window denoising:** overlapping windows denoised jointly, with overlaps averaged at each step.
- **Per-frame noise levels / "diffusion forcing"-style training** *(hedge)*: frames get independent noise levels, which lets the model treat recent frames as less noisy context for causal rollout. Distilled causal students (CausVid / self-forcing–style *(hedge)*) enable streaming generation.
- **Hierarchical / keyframe-first:** generate sparse keyframes for the story, then fill in between (interpolation), then SR. This fits ads well, because an ad is a sequence of *shots*, not one continuous take. You rarely need >5–8 s continuous generation; you **cut**.

**Say it like this:**
> "Ads are edited content. I'd never generate a 30-second continuous take. I'd generate 2–5 second shots that obey a storyboard and assemble them on the timeline. That sidesteps most long-video drift."

### 3.9 Frame interpolation and temporal super-resolution

- **Flow-based interpolation:** estimate bidirectional optical flow → warp both neighbors to time τ → blend with occlusion-aware weights → refine.
  - **RIFE:** directly estimates *intermediate* flow (IFNet), which makes it fast and real-time capable.
  - **FILM:** multi-scale shared feature extraction, robust to **large motion**.
  - **Softmax splatting:** forward-warp with importance weights (depth-like ordering) to resolve many-to-one.
- **Generative interpolation:** video diffusion conditioned on start and end frames handles large or nonlinear motion that flow can't.
- **Use in ads:** generate at 12–16 fps, interpolate to 24/30 fps (cheaper); re-time for 25 vs 29.97 fps delivery; smooth slow-motion product reveals.

**Your bridge:** "This is my home turf. SpaceWarp synthesizes intermediate frames from depth plus per-pixel motion vectors, beat Google's approach, and shipped as default on Galaxy XR. The failure modes are identical: disocclusions, thin structures, and transparent or reflective surfaces where flow is ill-defined. Product packaging is full of specular highlights and fine text, so that's where I'd look first. Unlike RIFE, I had *true* motion vectors and depth from the renderer, which is also a lesson for templated ads: if your renderer knows the motion, use it instead of estimating flow."

### 3.10 Spatial super-resolution

- Cascades: base model at 480–720p → **video SR** (diffusion-based or GAN-based, e.g., Real-ESRGAN-style per-frame plus temporal models) → 1080p/4K.
- **Per-frame SR flickers**, so you need temporal SR (recurrent/flow-aligned like BasicVSR-style *(hedge)*, or latent video diffusion SR).
- **Do not super-resolve the product layer.** Composite the original high-res product cutout *after* SR. This is a recurring theme: anything generative that touches product pixels is a fidelity risk.

### 3.11 Few-step distillation and acceleration for video

| Technique | Idea | Speedup | Risk |
|---|---|---|---|
| **CFG distillation** | Student learns guided output in one pass | ~2× | Loses guidance-scale control |
| **Progressive / step distillation** | Halve steps repeatedly | 50 → 4–8 steps | Detail loss |
| **Consistency distillation (LCM-style)** | Map any x_t to x₀ consistently | 2–8 steps | Blurriness, motion reduction |
| **Distribution matching (DMD/DMD2-style)** | Match student distribution to teacher via score difference, plus GAN loss | 1–4 steps | Mode collapse, **reduced dynamics** |
| **Adversarial post-training** | GAN loss on few-step student against real data | 1–2 steps | Instability |
| **Feature/step caching** | Reuse transformer features across adjacent timesteps (TeaCache-style *(hedge)*) | 1.5–2× | Subtle artifacts |
| **Sparse attention, FP8/INT8 quantization, sequence parallelism** | Systems tricks | 1.5–3× each | Quantization artifacts in VAE decode especially |

**Watch-out:** distilled video students often **move less**. Few-step objectives favor low-variance, near-static solutions, and a smoothness metric will *reward* that. This is exactly the failure your temporal-predictability metric flags.

**Your bridge:** "I've done consistency-model training and distillation/quantization for on-device deployment. The video-specific lesson is that you have to evaluate dynamics separately when you distill, because per-frame FID can improve while the clip quietly freezes."

### 3.12 Model families (hedge everything)

| Family | Who | Notes *(as of my knowledge; verify)* |
|---|---|---|
| Sora / Sora 2 | OpenAI | DiT on spacetime patches; Sora 2 added synchronized audio *(hedge)* |
| Veo (2, 3, …) | Google DeepMind | Strong prompt adherence; Veo 3 introduced native audio generation *(hedge)* |
| Gen-3 / Gen-4 | Runway | Pro tools: motion brush, camera control, references |
| Kling | Kuaishou | Strong motion and human realism |
| Others | Luma (Ray), Pika, MiniMax (Hailuo), ByteDance (Seedance) | Commercial APIs |
| **Open:** Wan 2.x | Alibaba | Open weights; 3D causal VAE + DiT; I2V/T2V variants *(hedge)* |
| **Open:** HunyuanVideo | Tencent | Large (~13B class) DiT, MLLM text encoder *(hedge)* |
| **Open:** CogVideoX | Zhipu / THUDM | 2B/5B, 3D VAE, expert-adaLN *(hedge)* |
| **Open:** LTX-Video | Lightricks | Highly compressed latent, near-real-time *(hedge)* |
| Open: Mochi, Open-Sora | Genmo / HPC-AI | Research-friendly |

**Say it like this:**
> "I'd be model-agnostic behind an interface: a routing layer that picks a vendor API or a self-hosted open model by task, cost and license. Licensing matters, since open weights aren't all commercially unrestricted. Indemnification and training-data provenance also matter for a retailer. I'd fine-tune an open model on licensed, brand-safe, retail-domain footage for the high-volume paths and keep vendor APIs for premium or exploratory work."

---

## 4. Product fidelity in video (the make-or-break problem)

**The core risk:** in a Sponsored Video, the product *is* the ad. A morphing cereal box, wrong flavor text, a melted logo or an extra handle on a mug is worse than no ad: it's misrepresentation of a specific SKU, and the advertiser loses trust.

### 4.1 Failure taxonomy

| Failure | Example | Detectable by |
|---|---|---|
| Shape morph | Bottle neck lengthens across frames | Mask IoU vs. reference after pose alignment; silhouette consistency |
| Texture/text drift | "Honey Nut" → "Hoeny Nut" by frame 40 | OCR per frame + edit distance to catalog text |
| Logo corruption | Swoosh distorts, colors shift | Logo detector + template/embedding match; Lab ΔE color |
| Identity swap | Becomes a generic competitor-looking box | Embedding similarity to reference (DINOv2 crop) |
| Count/part errors | Extra spout, missing cap | VLM structured question; part detector |
| Physics | Liquid pours upward, product floats, hand passes through | VLM judge + physics heuristics (flow divergence); hard |
| Hands/humans | 6 fingers, hand-object interpenetration | Hand-pose estimation + keypoint plausibility; VLM |
| Scale | Product the wrong size relative to the hand or the room | Catalog dimensions vs. estimated scale (depth + reference objects) |

### 4.2 Product fidelity score (design it on the whiteboard)

```
 Inputs: generated clip V, catalog reference images R = {r_1..r_k} (multi-view if available),
         catalog text (name, flavor, size), brand logo assets

 1. Localize & track product:
      first frame: grounded detection (open-vocab detector with SKU name) or known placement
      → promptable video segmentation (SAM 2-style) → mask M_t for every frame
      → track confidence c_t; if track lost, that's itself a flag

 2. Per-frame identity:
      crop_t = bbox(M_t);  s_t = max_j cos( DINO(crop_t), DINO(r_j) )      # view-robust via max over refs
      (optionally also a fine-grained retrieval model trained on catalog SKUs: rank of true SKU)

 3. Per-frame text fidelity:
      OCR(crop_t) → tokens; ed_t = normalized edit distance to expected text tokens (visible subset)
      stability: OCR string should not change across frames when the face is visible

 4. Logo & color:
      logo match score l_t; ΔE_t (CIEDE2000) of dominant brand colors vs reference

 5. Shape:
      IoU between M_t and the reference silhouette warped by estimated pose/homography

 Aggregate:  F = min_t  g(s_t, ed_t, l_t, ΔE_t, IoU_t)      ← MIN (or low percentile), not mean
             plus  drift = s_0 − min_t s_t                    ← catches gradual morph
 Gate: F ≥ τ_F (per-category thresholds calibrated to human "acceptable" labels)
```

Key design points:
- **Use the min or 5th percentile over frames, not the mean.** A single bad frame is visible, and morphing is often brief.
- **Drift relative to frame 0** catches slow morph that absolute thresholds miss when the reference itself is ambiguous.
- **View invariance:** single-view references fail when the product rotates. Use multi-view catalog images, or accept a lower similarity for back views but require text/logo checks on visible faces.
- **Calibrate per category:** apparel deforms legitimately, rigid boxes shouldn't.
- **Independent embedding:** don't use the same encoder for conditioning and verification, or the generator can satisfy the verifier without satisfying humans. Same Goodhart logic as §7.9.

**Your bridge:** "This is identity-preserving generation plus verification, which is what I did for faces: generate with a reference, verify with an independent identity model, and aggregate pessimistically across frames. And from SLAM, I'm used to tracking with confidence and treating a lost track as a signal, not noise."

### 4.3 Locking the product: compositing instead of generating

The strongest guarantee is to **not let the generator draw the product at all**.

```
 Catalog product cutout (high-res, alpha)  ──────────────┐
                                                         │
 Scene: I2V/T2V generates BACKGROUND + camera motion      │
   with product region MASKED / held out (or a proxy box) │
        │                                                 │
        ▼                                                 ▼
 Estimate scene camera motion & lighting      Product layer transform track
 (flow/homography/depth; env light estimate)  (2D affine or 3D pose via 2.5D/mesh proxy)
        │                                                 │
        └──────────────►  Harmonize & composite  ◄────────┘
                          - relight product (env-map / learned harmonization)
                          - contact shadows, reflections (shadow generation model or depth-based)
                          - matched grain/noise & motion blur (from scene flow)
                          - occlusions: hands in front of product via depth ordering / matting
                                │
                                ▼
                          Final frames (product pixels traceable to catalog asset)
```

Variants, from safest to riskiest:
1. **Static product, moving world:** product stays fixed (or follows a simple affine track); background, particles, light sweeps and steam are generated. Very safe.
2. **2.5D product motion:** small rotations from a depth or mesh proxy, with disocclusion inpainting limited to small angles. *Your SpaceWarp territory.*
3. **3D asset:** if a 3D model of the SKU exists (or is reconstructed from multi-view catalog images via NeRF/Gaussian splatting), render it with a real camera path. You get exact geometry and text, and full parallax.
4. **Generated product, verified:** I2V animates the actual product photo; the fidelity score gates the output; regenerate on failure. Highest realism, lowest guarantee.

**Harmonization is the actual hard part:** a pasted product with wrong lighting or no contact shadow looks fake. Approaches: learned image harmonization, relighting models conditioned on an estimated environment, generative "re-render the boundary only" (inpaint a thin band around the alpha edge plus the shadow region, with the product interior frozen).

**Your bridge:** "Generate the world, composite the product, re-render only the seam: that's very close to how XR reprojection works. You keep known-good pixels, synthesize only where you have no information, and handle the boundary carefully. I've shipped disocclusion detection and inpainting for exactly that kind of seam."

### 4.4 Physically plausible motion and humans

- Prefer **camera motion over object motion** for products. Camera moves are easy to make plausible, while object physics (pouring, squeezing) is where models fail.
- For hand-product interactions: use real advertiser footage, or constrain with pose/trajectory controls. Run hand-keypoint plausibility checks (finger count, joint angles) and **contact consistency** (hand mask and product mask touch without interpenetrating, judged by depth order).
- Run human-likeness policy checks: no generated people resembling real celebrities (face-recognition screening against a public-figure gallery, under legal guidance *(hedge)*), age-appropriateness, and diversity guidelines from the brand.

---

## 5. Audio

| Component | Approach | Risks / requirements |
|---|---|---|
| **Music selection** | Licensed stock library with metadata (mood, BPM, genre, energy curve); retrieve by embedding (text↔audio, CLAP-style) matched to the creative's mood; or generated music from a model trained on licensed data *(hedge on vendor)* | **Licensing scope** (territory, term, media: CTV vs. social vs. in-store), content-ID claims on platforms; generated-music provenance |
| **Beat sync** | Beat/onset/downbeat tracking → snap cuts and text animations to beats; re-edit music to target duration via beat-aligned segment removal plus crossfade; end on a musical resolution | Cuts mid-phrase sound amateur |
| **TTS voiceover** | Brand-voice TTS (consented, licensed voice actor clone or stock voice); script from the copy system; SSML for pacing/emphasis | **Pronunciation lexicon** for brand/product names (e.g., "Gruyère", made-up brand names, SKU-specific terms) using phoneme overrides; voice-clone consent and contracts; disclosure |
| **Lip-sync (avatars)** | Audio-driven talking-head / lip-sync models | Uncanny valley; likeness rights; higher policy scrutiny |
| **Loudness normalization** | Measure integrated loudness per **ITU-R BS.1770** (K-weighting, gating) → gain to target (−24 LKFS for US broadcast/CTV per A/85; platform-specific otherwise) → true-peak limiting (≈ −2 dBTP) | CALM Act compliance for broadcast; avoid loudness jumps vs. content |
| **Mixing** | Ducking music under VO (sidechain), dialog intelligibility | VO intelligibility on TV speakers and phones |
| **Captions / subtitles** | From script (best, since it's exact) or ASR (Whisper-class) → forced alignment → line breaking (≤ ~32–42 chars/line, reading speed ~15–20 cps *(hedge)*) → burn-in for muted placements; sidecar WebVTT/SRT, CEA-608/708 for TV | Caption accuracy for brand names; **legal supers ≠ captions**, so both must be readable |
| **Accessibility** | **WCAG 2.x:** captions for prerecorded audio (1.2.2, Level A), **audio description** for prerecorded video (1.2.3 A / 1.2.5 AA) where visual info isn't conveyed by audio | Text-to-describe: generate AD script from the timeline (the structure knows what's on screen); contrast ratios for text supers |

**Say it like this:**
> "Muted autoplay means the visual track has to tell the story alone: captions and supers do the work audio would. CTV is the opposite. It's sound-on and loudness-regulated, and the VO has to pronounce the brand name correctly every time. A pronunciation lexicon per brand is boring, but it's the difference between an advertiser trusting the system and churning."

**Audio evaluation:** ASR the final mix → compare to the approved script (WER on brand terms specifically), run text moderation on the transcript, audio fingerprinting against the licensed catalog (to confirm the intended track and catch unlicensed audio in advertiser uploads), loudness measurement, and clipping/true-peak checks.

---

## 6. Automated adaptation

### 6.1 Reframing 16:9 → 9:16 / 1:1 / 4:5

```
 per frame t:
   saliency map S_t (learned saliency + face/person detector + product detector + OCR text regions)
   importance-weighted target point p_t = argmax / weighted centroid with priority:
        product > on-screen text (if not re-renderable) > face > other salient
   shot boundaries → reset the filter (don't smoothly pan across a cut!)

 crop path:  raw p_t  ──►  smoothing filter  ──►  constrained path c_t
   - Kalman filter (constant-velocity model): state [x, ẋ], process noise sets responsiveness
   - or One-Euro filter: adaptive cutoff — smooths jitter at low speed, low lag at high speed
   - or offline: optimize path = argmin Σ‖c_t − p_t‖² + λ1‖c_t − c_{t−1}‖² + λ2‖c_t − 2c_{t−1} + c_{t−2}‖²
       (L1 variants → piecewise "static / constant pan" paths that look like a camera operator)
   - constraints: keep product bbox fully inside crop; respect UI safe zones (9:16 bottom/right overlays)

 fallbacks when two subjects are far apart (e.g., presenter left, product right):
   split-screen / stacked layout, or cut between them, or "letterbox + blurred fill", or
   generative outpainting to extend canvas vertically (riskier; never outpaint over product)
 text supers: don't crop burned-in text — re-render them from the timeline at new layout
```

Because the processing is **offline**, the best results come from a *non-causal* optimizer (smoothing over the whole shot), not a causal filter. Kalman/One-Euro are good for streaming previews.

**Your bridge:** "Smoothing a noisy target track under latency and jitter constraints is something I've done for years in SLAM and XR head-pose prediction. For offline reframing I'd use a global path optimization with L1 smoothness, which gives the 'locked-off or steady pan' look an editor would choose, and a Kalman or One-Euro filter only for real-time previews. And reset at shot boundaries."

### 6.2 Duration cut-downs (30 → 15 → 6 s)

- Shot scoring features: product visibility, logo, faces, motion energy, aesthetic, speech importance (an LLM rates script sentences for the key message), **position priors** (openings and end cards matter).
- **Constraints:** must include a product shot and the end card/logo; any claim kept must keep its legal super; no mid-word cuts (ASR word timestamps); music re-edited at beats.
- **6 s bumper is a different creative,** not a shorter one: one message, product plus logo. Often better as a template render from the same assets than a cut-down.
- Solve with **DP over ordered shots** (maintain narrative order) with trim options per shot, or ILP when constraints get complex.

### 6.3 End-card and placement adaptation

- Placement spec registry: CTA wording ("Shop now" vs. "Find in store" for in-store screens, no clickable CTA on CTV but maybe a QR code *(hedge on Walmart CTV formats)*), logo sizes, safe zones, end-card duration.
- In-store screens: no audio, distance legibility (bigger type, fewer words), **loopable** (match first and last frames or use seamless loop transitions).
- CTV: title-safe, larger type, slower pacing, 15/30 s exact frame counts.

### 6.4 Localization

- Language variants (English/Spanish is the obvious US case): translate copy with constrained MT plus brand glossary, re-render supers (text expansion → layout re-solve), TTS in target language, re-time captions; **claims and legal supers need per-language approval**.
- Regional variants: store-availability-aware CTAs, regional offers.

**Say it like this:**
> "Adaptation is a constraint-satisfaction problem over the structured timeline. If you adapt pixels by cropping and trimming finished renders, you get cut-off text and missing legal supers. If you adapt the timeline and re-render, those things are guaranteed by construction."

---

## 7. Evaluating generated video (deep)

### 7.1 The evaluation stack

```
             ┌──────────────────────────────────────────────────────────────────┐
 Level 0     │ STRUCTURAL / SPEC (exact): duration, fps, resolution, codec, loudness,│
 (exact)     │ logo on-screen ≥ x s, legal super ≥ min dur & size, safe zones, captions│
             └──────────────────────────────────────────────────────────────────┘
             ┌──────────────────────────────────────────────────────────────────┐
 Level 1     │ PER-FRAME: imaging quality (blur/noise/artifacts), aesthetics,      │
 (models)    │ text/prompt alignment, per-frame policy (image moderation, OCR→text)│
             └──────────────────────────────────────────────────────────────────┘
             ┌──────────────────────────────────────────────────────────────────┐
 Level 2     │ TEMPORAL: warping error, flicker, subject/background consistency,   │
             │ motion quality: dynamic degree, frozen/static, reversed, shuffled   │
             │ (temporal predictability), physics plausibility                     │
             └──────────────────────────────────────────────────────────────────┘
             ┌──────────────────────────────────────────────────────────────────┐
 Level 3     │ PRODUCT FIDELITY (§4.2): min-over-frames identity, OCR, logo, shape │
             └──────────────────────────────────────────────────────────────────┘
             ┌──────────────────────────────────────────────────────────────────┐
 Level 4     │ SEMANTIC JUDGE: VLM on sampled frames + temporal questions; brand   │
             │ fit, message clarity, claims match approved copy; audio ASR checks  │
             └──────────────────────────────────────────────────────────────────┘
             ┌──────────────────────────────────────────────────────────────────┐
 Level 5     │ HUMAN + MARKET: reviewer labels, advertiser approvals/edits,        │
             │ online performance (VCR, CTR, ROAS, incrementality)                 │
             └──────────────────────────────────────────────────────────────────┘
 Calibration flows UPWARD-TO-DOWNWARD: L5 labels calibrate thresholds & weights of L1–L4.
 Cheap levels run first (cascade); expensive VLM judge only on survivors.
```

### 7.2 Per-frame image quality

- **No-reference IQA:** MUSIQ / CLIP-IQA / learned artifact detectors (blur, noise, JPEG/VAE artifacts, oversaturation).
- **Aesthetics:** LAION-aesthetic-style predictors. These are biased toward a "pretty" style that may not suit a retail ad, so calibrate them on ad-domain labels.
- **Text/prompt alignment:** CLIP/SigLIP score per frame vs. prompt or storyboard step. It's weak at counts, relations and text rendering, so use it only as a coarse filter.
- **Aggregate:** mean *and* worst-k frames.

### 7.3 Temporal consistency

**Warping error (flow-based):**
```
 F_{t→t−1} = optical flow (RAFT-class) from t to t−1
 Ŵ_t = warp(I_{t−1}, F_{t→t−1})
 O_t = occlusion mask via forward–backward consistency:  ‖F_{t→t−1}(x) + F_{t−1→t}(x + F_{t→t−1}(x))‖ > ε
 E_warp = (1/T) Σ_t  Σ_x (1 − O_t(x)) · ‖I_t(x) − Ŵ_t(x)‖₁ / Σ_x (1 − O_t(x))
```
- Measures whether visible content is consistent with the motion, ignoring disoccluded regions.
- **Pitfall:** a static video has *zero* warping error. A low score can mean "consistent" or "frozen." **Always pair it with a dynamics measure.**
- **Flicker metrics:** temporal variance of mean luminance per region after motion compensation; high-frequency temporal energy in the residual. This catches VAE tile seams, SR flicker and lighting pulsation.
- **Subject consistency:** cosine similarity of DINO features of the tracked subject across frames. **Background consistency:** CLIP features of the background across frames.

**Your bridge:** "Forward-backward flow consistency for occlusion masks is exactly how I did disocclusion detection. The key point about warping error is that it rewards doing nothing, which leads straight to my temporal-predictability work."

### 7.4 Motion quality: frozen, reversed, shuffled (your metric)

**Problem:** many temporal metrics (smoothness, warping error, frame-to-frame similarity) **reward near-static video**. Generators, especially distilled ones or ones run at high CFG, tend to collapse toward near-static output. Some failures are invisible to smoothness entirely:
- **Near-static:** the camera barely drifts, the "video" is a still image.
- **Reversed:** liquid flows back into the bottle, smoke converges. Every frame-pair is smooth.
- **Shuffled / temporally incoherent:** locally plausible frames in a wrong order; jitter.

**Your Temporal-Distance Predictability metric:**
```
 A frozen ~5M-param regressor f(frame_i, frame_j) → predicted temporal distance d̂ (trained on real video)
 For a clip, sample pairs (i, j) with known true gaps Δ = j − i
 Score = mean log p(Δ | f(frame_i, frame_j))   ← log-likelihood of the true gaps under the predictor
 Interpretation:
   real-looking motion → true gaps are predictable → high likelihood
   near-static         → all pairs look "Δ≈0" → true large gaps unlikely → low score
   reversed            → arrow-of-time cues contradict → low score (if the model is direction-aware)
   shuffled            → predicted distances don't match index gaps → low score
 Reference-free, per-video (no real-video set needed), cheap (5M params)
```

**Contrast with FVD:** FVD is **distribution-level**. It compares Inception/I3D feature statistics of a *set* of generated videos to a *set* of real ones, so it can't score an individual clip, which is what a production gate needs.

**Say it like this:**
> "In a production gate you need a per-clip score, and you need one that doesn't reward the generator for freezing. I published a reference-free metric for exactly that. A small frozen network predicts the temporal distance between frame pairs, and a clip is scored by how likely its true frame gaps are. It catches near-static, reversed and shuffled footage, which smoothness metrics reward and FVD can't score per video."

### 7.5 FVD and its limits

- **Definition:** Fréchet distance between Gaussians fitted to I3D (Kinetics-trained) features of real vs. generated videos: ‖μ_r − μ_g‖² + Tr(Σ_r + Σ_g − 2(Σ_rΣ_g)^{1/2}).
- **Limits:**
  1. **Not per-video**, so it's useless as a gate and only good for model comparison.
  2. **Sample-hungry:** high variance at small N, and biased with few samples.
  3. **Content bias:** I3D features are dominated by per-frame appearance more than motion. Research has shown FVD can be insensitive to temporal corruption *(content-bias in FVD findings; hedge)*.
  4. **Domain mismatch:** Kinetics human-action features aren't suited to product tabletop shots.
  5. Gaussian assumption.
- **Alternatives:** features from self-supervised video models (VideoMAE / V-JEPA-style; e.g., JEDi-style metrics *(hedge)*), motion-specific distribution metrics (FVMD-style *(hedge)*). Still distributional.

### 7.6 VBench-style dimension decomposition

VBench decomposes quality into ~16 dimensions, each with a specialized evaluator *(hedge on exact list and tools)*:

| Dimension | Typical evaluator | Ad relevance |
|---|---|---|
| Subject consistency | DINO feature similarity across frames | Product/presenter stability (but not *identity to SKU*, which is our §4.2 score) |
| Background consistency | CLIP features across frames | Scene stability |
| Temporal flickering | Pixel differences on static-ish frames | VAE/SR flicker |
| Motion smoothness | Frame-interpolation model prior (does a mid-frame match interpolation?) | Jitter. **Rewards static.** |
| Dynamic degree | Optical-flow magnitude (RAFT) | Counterweight to smoothness: is there motion at all? |
| Aesthetic quality | LAION aesthetic predictor | Polish |
| Imaging quality | MUSIQ | Artifacts |
| Object class, multiple objects, color, spatial relationship, scene, human action | Detectors / captioners | Storyboard adherence |
| Appearance/temporal style, overall consistency | ViCLIP-style video-text alignment | Prompt fit |

VBench-2.0 adds "intrinsic faithfulness" dimensions such as physics, commonsense, and human fidelity *(hedge)*.

**The critique that marks you as an expert:** dimensions trade off (smoothness vs. dynamic degree), and a weighted average lets a model buy points on one axis by sacrificing another. Dynamic degree in VBench is close to binary, so a tiny drift can count as "dynamic." **Use dimensions as a vector with per-dimension gates, not a single averaged score**, and add direction- and order-aware motion checks (your metric).

### 7.7 VLM-as-judge for video

- **Inputs:** sample frames (e.g., 1–2 fps plus all shot-boundary frames plus the end card), sometimes as a contact-sheet grid with timestamps. Or use native video-input VLMs where available (some frontier models accept video directly *(hedge)*), with ASR transcript and OCR text as side channels.
- **Ask structured, checkable questions** rather than "rate 1–10":
  - "Does the product shown in frames 1–N match the reference image? Same brand text, same flavor, same color? (yes/no + frame indices of mismatch)"
  - "Is there any text in the video other than the approved copy below? List it."
  - "Do any hands have abnormal finger counts or pass through objects?"
  - **Temporal questions:** "Is the motion physically plausible in direction? Does anything move backward (liquid, smoke)?" "Do events occur in a sensible order?" "Does the product change shape between the first and last frame?"
  - Brand fit: "Does the visual style match these brand guideline examples?" (few-shot with brand exemplars)
- **Known judge failure modes:** coarse frame sampling misses brief artifacts (so combine with dense cheap metrics), weak fine-grained temporal reasoning, position bias in pairwise comparisons (swap order and average), verbosity/style bias, hallucinated "looks fine," and prompt-injection via on-screen text in advertiser uploads (treat OCR'd text as data).
- **Calibration:** collect human labels on a stratified set (by category, approach, placement) → measure judge agreement (κ, precision/recall per failure type) → fit per-question thresholds or a logistic **calibration layer** combining judge outputs with numeric metrics → monitor drift; re-calibrate when the generator or judge version changes.

**Say it like this:**
> "I'd use the VLM judge for semantic and policy questions it's actually good at, framed as verifiable yes/no questions with evidence: frame indices, text spans. I'd use dense specialized metrics for things VLMs miss at 1 fps, like flicker, brief morphs and motion direction. And I'd calibrate the combination on human labels per category, because a single global judge prompt will be miscalibrated across cereal boxes, apparel and TVs."

### 7.8 Policy and safety: per frame *and* per modality

| Channel | Checks |
|---|---|
| Visual per frame | Image moderation (nudity, violence, weapons, drugs, hate symbols), minors in sensitive contexts, celebrity/public-figure likeness, competitor logos/trademarks, misleading UI (fake buttons) |
| On-screen text | OCR every frame (text is generated *and* can appear in b-roll) → text moderation + **claims check**: only approved claim IDs; detect unapproved superlatives, health claims, prices |
| Audio | ASR → text moderation + claims check; music fingerprint vs. license; detect a generated voice resembling a real person |
| Category rules | Alcohol (age-gating, no minors), pharmacy/OTC (required disclosures), firearms (Walmart policy), political (generally restricted) *(hedge — Walmart's actual policies apply)* |
| Temporal | Subliminal flashes (a single bad frame), strobing/flashing for **photosensitive epilepsy** (e.g., more than 3 flashes per second violates WCAG 2.3.1-style guidance; broadcast has Harding-type tests *(hedge)*) |
| Provenance | AI-generated disclosure where required; C2PA credentials |

**Rule:** scan **every frame** for cheap classifiers (or at least every frame at shot boundaries plus 4–8 fps), because one bad frame is a policy failure.

### 7.9 Human-preference calibration and Goodhart risk

- **Label sources:** in-house reviewers (pass/fail plus failure tags), advertiser actions (approve / edit / reject, which edits they made: a strong *revealed-preference* signal), and online performance (noisy, confounded by targeting and placement).
- **Preference modeling:** pairwise comparisons (Bradley–Terry) between variants of the same brief, a reward model on top of frozen features plus metric vector, **calibrated per category and placement**.
- **Using evaluators to improve generators:** best-of-N reranking (safe), filtering training data (safe-ish), DPO/reward fine-tuning of the video model (risky).

**Goodhart, with your own result:**
> "I have a concrete negative result here. When I used my temporal-predictability metric as a training loss, the generator learned to game it: it satisfied the regressor without producing better motion as judged by humans. That's the general lesson. **Any evaluator you optimize against stops being an evaluator.** So: (1) keep a *held-out* evaluator family the generator never sees gradients or selection pressure from; (2) when doing best-of-N, audit with humans regularly, because selection is optimization too, just weaker; (3) ensemble diverse metrics so gaming one costs on another; (4) rotate and refresh judge models; (5) track divergence between the optimized metric and human or held-out metrics as an alarm."

**Your bridge:** "Most people talk about Goodhart abstractly. I've actually watched it happen to a metric I designed, and that's why I'd architect the eval system with an optimization firewall."

### 7.10 Putting the gate together

```
 accept(clip) =  spec_ok
               ∧ policy_ok (all frames, all text, audio)
               ∧ product_fidelity_min ≥ τ_F(category)
               ∧ temporal_predictability ≥ τ_T ∧ dynamic_degree ≥ τ_D(template-dependent) ∧ flicker ≤ τ_fl
               ∧ calibrated_judge_prob(acceptable) ≥ τ_J
 Route:  confident accept → advertiser preview;  borderline → human review queue;  reject → regenerate w/ new seed/params
 Thresholds τ chosen on human-labeled set for target precision (e.g., ≥ 99% of auto-accepted judged acceptable)
```

---

## 8. Production pipeline

### 8.1 Architecture

```
 Advertiser / campaign brief ──► Creative planner (LLM + rules): storyboard → timeline JSON variants
        │                                         │
        │                     ┌───────────────────┴────────────────────┐
        │                     ▼                                        ▼
        │            Deterministic render jobs                 Generative jobs (GPU queue)
        │            (templates, compositing, text, audio)     (I2V/T2V shots, inpainting, SR, interp)
        │                     │                                        │
        │                     └──────────► Assembly / render ◄─────────┘
        │                                         │
        │                                Eval cascade (§7) ──reject──► regenerate (bounded retries)
        │                                         │ accept/borderline
        │                                Human review / advertiser approval UI (edit timeline, not pixels)
        │                                         │ approved
        │                                Transcode ladder + mezzanine → ad server / VAST / CDN
        │                                         │
        └──────────────────────────────── Performance feedback (VCR, CTR, sales) → creative model + bandit
```

- **Async orchestration:** a workflow engine with per-stage idempotent tasks, content-addressed artifacts (hash of inputs → cache), retries with new seeds, priority queues (preview vs. final; premium advertisers; campaign launch deadlines).
- **Versioning:** every asset carries (model version, weights hash, seed, prompt, timeline version, eval versions). This gives reproducibility for advertiser disputes and audits.
- **Caching:** per-SKU cutouts, depth maps, mattes, embeddings, OCR of catalog images, 3D proxies; music beat grids; TTS of recurring lines; generated backgrounds reusable across SKUs in the same category ("kitchen countertop morning light" b-roll).

### 8.2 GPU cost math (state assumptions out loud)

**Assumptions (illustrative, hedge):** a ~14B open video DiT, 720p, 5 s clip, 50 steps with CFG (≈100 forward passes) takes on the order of **~20 GPU-minutes on one H100-class GPU** *(order-of-magnitude; varies widely with implementation)*. GPU cost ≈ **$2.50/GPU-hour** *(blended reserved/cloud; hedge)*.

| Config | GPU-s per 5 s clip | GPU-s per second of video | $ per 5 s clip |
|---|---|---|---|
| Undistilled, 50 steps × CFG | ~1,200 | **~240** | ~$0.83 |
| CFG-distilled, 50 steps | ~600 | ~120 | ~$0.42 |
| Few-step (4 steps, no CFG) + FP8 + caching | ~40–60 | **~8–12** | ~$0.03–0.04 |
| 480p preview, 4 steps | ~10–15 | ~2–3 | ~$0.01 |
| Spatial SR 720p → 1080p + interpolation | +~20–60 | +4–12 | +~$0.01–0.04 |
| **Template / compositing render (no diffusion)** | ~1–5 (GPU) or CPU | **<1** | **<$0.005** |

**Scale example:** 20,000 active advertisers/SKUs-of-interest × 10 variants × 3 aspect ratios × 15 s with **one** 5 s generated shot per variant (rest templated) = 600k generated shots (aspect ratios share the shot via reframing or native-aspect regenerate; assume shared, so 200k). At ~$0.04 distilled ≈ **$8k**, plus a ~2× regeneration factor from eval rejects ≈ **$16k per refresh cycle**. Undistilled it's ~$330k. **So distillation and the template-first design are the business case, not an optimization detail.** Also budget the evaluator: a VLM judge on ~20 frames per clip can rival the generation cost if you're not careful, so cascade cheap checks first.

**Say it like this:**
> "Here are my assumptions so you can push back. Tokens scale with frames × H × W and attention quadratically, so I'd generate short shots at 480–720p, distill to a few steps, preview cheaply, and only spend full compute on what a human or a bandit says is worth finishing. The template path costs nearly nothing and should carry most of the volume."

### 8.3 Preview-then-finalize

1. Low-res, few-step preview with a fixed seed (seconds).
2. Advertiser/reviewer picks or edits on the **timeline** (swap shot, change text, change music).
3. Final: same seed and conditioning at full steps/resolution. The **preview→final consistency** problem (same seed doesn't guarantee the same content at different resolution/steps) is solved by using the preview as an init/keyframe condition for the final (SDEdit-style), or by keeping the same model and steps and only upscaling.

### 8.4 Human-in-the-loop

- Review UI shows the clip plus the eval evidence (flagged frames, OCR diffs, fidelity curve over time, policy hits) so reviewers verify rather than search.
- Active learning: route borderline and disagreement cases to humans; feed their labels back to calibration.
- Advertiser approval is mandatory for brand-new generated content in v1. Later, use auto-approval for low-risk template variants under the advertiser's pre-approved brand kit and claims.

### 8.5 Delivery: transcoding and CDN

- **Mezzanine master** (high-bitrate ProRes or high-quality H.264/HEVC) → ad server/SSP transcodes; or deliver an ABR ladder yourself.
- **ABR ladder** (e.g., 1080p/720p/540p/360p) in **H.264** (compatibility), **HEVC/H.265** (CTV, 30–50% bitrate savings vs. H.264 at similar quality *(hedge)*), **AV1** (web/mobile where supported). Per-title or **per-shot encoding** with VMAF targets.
- **Generated-video encoding gotchas:** denoise or control synthetic grain before encode (or use AV1 film-grain synthesis); gradients/sky banding, so add dither; fast flicker destroys inter-prediction efficiency, so your flicker metric correlates with bitrate cost.
- **VAST/VPAID** (or SIMID) wrappers for video ad serving; quartile tracking events.

**Your bridge:** "I've built H.265 capture pipelines, including rate control and GOP decisions under device constraints. Per-shot encoding with VMAF targets, and treating generated noise as a bitrate tax, is something I'd own personally."

### 8.6 Monitoring

| Metric | Why |
|---|---|
| Stage latency/queue depth, GPU utilization, cost per *accepted* asset | Capacity and unit economics |
| Eval reject rate by reason, category, model version | Regression detection (a new model version raising morph rejects) |
| Human override rate (auto-accept later rejected, auto-reject overturned) | Judge calibration drift |
| Advertiser edit distance (how much they change) and approval rate | Product quality from the customer's view |
| Policy incidents post-launch (should be ~0) | Safety SLO |
| Online creative performance vs. control | Business value |
| Metric-vs-human divergence | Goodhart alarm (§7.9) |

---

## 9. Performance measurement and optimization

### 9.1 Metrics

| Metric | Definition | Notes |
|---|---|---|
| **Video completion rate (VCR)** | Completions / starts; quartiles (25/50/75/100%) via VAST events | Strongly affected by length, skippability, placement. Compare like for like |
| **View-through / viewable views** | e.g., MRC video viewability: ≥ 50% of pixels in view for ≥ 2 continuous seconds | Muted autoplay "views" are not attention |
| **View-through conversions** | Conversions after view without click within a window | Inflated by targeting; needs incrementality |
| **CTR** | Clicks / impressions | Onsite Sponsored Videos: click to PDP/add-to-cart; CTV: no click, so use QR scans or attribution |
| **ROAS / attributed sales** | Walmart's closed-loop advantage: purchases (online + in-store) linked to exposure | Retail media's selling point |
| **Incrementality / iROAS** | Lift vs. holdout (geo or user-level ghost ads) | The truth metric for creative value too |
| **CTV-specific** | Completion (often very high for non-skippable), reach/frequency, household attribution; Vizio ACR data can link exposure to viewing *(hedge on how Walmart uses it)* | Brand lift surveys |
| **Attention / brand lift** | Surveys, attention vendors | Upper funnel |

### 9.2 Creative-level performance models

- **Goal:** predict performance (VCR, CTR, conversion-rate uplift) of a creative *before* serving, and explain what drives it.
- **Features:**
  - Structured timeline features: time-to-product (s), product screen-time share, logo timing, number of cuts/sec, hook type (motion/face/text), caption presence, CTA wording, music BPM/energy, VO presence, duration, aspect ratio.
  - Learned embeddings: video encoder embeddings (frame-sampled CLIP/SigLIP or a video foundation model), audio embeddings, text embeddings of copy.
  - Context: placement, category, advertiser, audience segment, season.
- **Modeling:** two-tower or GBDT/DNN with creative × context interactions; **debias** for targeting and position (creatives served to better audiences look better), e.g., train on randomized-exploration traffic, use inverse propensity weighting, or include context features and calibrate.
- **Uses:** prior for bandits (cold start), creative guidance to advertisers ("show the product in the first 2 seconds"), and **reward signal for the creative planner** (carefully, to avoid Goodhart: optimize planner choices over *structured* attributes and keep a holdout).

### 9.3 Bandit selection across variants

- Per ad group: K variants (aspect ratios are not competing variants, since placement determines them; they compete *within* placement).
- **Thompson sampling** with Beta-Bernoulli for CTR or completion, or a contextual bandit (linear/neural TS) with placement and audience context.
- **Hierarchical priors** from the creative-performance model, so new variants start informed and small advertisers borrow strength across the category.
- **Delayed and sparse conversions:** optimize a faster proxy (VCR, click) with a conversion-model correction, or use a delayed-feedback bandit.
- **Guardrails:** minimum exploration, cap on serving unreviewed variants, brand-safety constraints, frequency caps (creative fatigue: rotate variants as performance decays with exposure).
- **Measure the system:** a creative-optimization holdout (random allocation) to measure the lift of the generator plus bandit vs. advertiser-provided creative alone.

**Say it like this:**
> "Generation creates candidates, the evaluator decides what's *allowed*, and the bandit decides what's *best*, informed by a creative-performance prior and measured against a holdout. I'd want the creative model to speak in structured attributes, because advertisers can act on 'show the product earlier' and they can't act on an embedding."

---

## 10. Twenty practice questions with model answers

**1. How would you build a system to generate video ads for Walmart advertisers?**
Staged hybrid. (1) A structured timeline representation plus a placement spec registry. (2) Template/2.5D-parallax videos from catalog images and approved copy, which are deterministic and pixel-exact for the product. (3) Automated cut-downs and reframing of advertiser footage. (4) Generative backgrounds and b-roll with the product composited as a tracked layer. (5) Selective I2V and VO. Everything is gated by a calibrated eval cascade (spec, policy, product fidelity, temporal, VLM judge) with humans on the borderline, then bandits and creative-performance models online.

**2. Why not just use text-to-video?**
It has no product grounding, so it hallucinates the SKU and packaging text. It has the highest policy, IP and likeness risk, the highest cost (tokens ∝ T×H×W, attention quadratic), and the highest variance. It's useful for lifestyle b-roll *around* a locked product, not for the product.

**3. How do you ensure the product doesn't morph?**
Prefer compositing the real catalog cutout over generated scenes: relight, add contact shadows, match grain and blur, and re-render only the seam. When the generator does draw the product, track it (detector → SAM 2-style masks), and score per frame: embedding similarity to the multi-view references, OCR edit distance to catalog text, logo and color ΔE, shape IoU. Aggregate with **min over frames** plus a drift term, calibrate thresholds per category, and use an independent verifier encoder.

**4. Explain how a modern video diffusion model works.**
A 3D causal VAE compresses ~4× in time and 8×8 in space. Latents are patchified into spacetime tokens, then a DiT with full 3D attention and 3D RoPE, conditioned on text (T5/LLM) and timestep via adaLN, is trained with flow matching (predict v = ε − x₀ along a linear path), with logit-normal or shifted timestep sampling. Sample with an ODE solver plus CFG, decode in temporal tiles, then optionally interpolate and super-resolve.

**5. Factorized vs. full 3D attention?**
Factorized (spatial plus temporal) is cheap and can inflate image models, but temporal attention only links co-located tokens, so large motion and object permanence suffer. Full 3D is coherent but O(N²) in T·H·W tokens. Sparse or windowed 3D is the middle ground.

**6. Walk through the compute scaling.**
5 s 720p at 24 fps → 31 latent frames × 3,600 tokens ≈ 112k tokens → ~1.25×10¹⁰ attention pairs per layer. 2× duration means 4× attention, 2× each spatial dim means 16×. So: generate short shots at moderate resolution, distill steps, interpolate and SR, and composite.

**7. How would you make 9:16 versions of a 16:9 CTV spot?**
Shot detection → per-frame saliency with priority (product > text > faces) → target track → offline path optimization with L2/L1 smoothness (piecewise static or pan), reset at cuts, constrain the product inside the crop and outside UI safe zones. Re-render supers from the timeline rather than cropping them. For two distant subjects, fall back to split/stacked layout or cut between them. Use Kalman/One-Euro only for real-time preview.

**8. How do you cut a 30 s spot to 6 s?**
Score shots (product, logo, speech importance, motion, position priors), then solve ordered selection under a duration constraint with must-include product and end card, no mid-word cuts, beat-aligned music re-edit, and legal supers preserved. Often a 6 s bumper is better built as a template from the same assets, with one message and product plus logo.

**9. What's wrong with FVD for production?**
It's distribution-level, so it can't score one clip. It's sample-hungry, its I3D features are biased toward appearance over motion and trained on human-action data rather than products, and it assumes Gaussians. It's fine for comparing model versions offline but useless as a per-asset gate.

**10. A distilled model's VBench motion-smoothness went up. Good news?**
Not necessarily. Smoothness, warping error and frame similarity all reward static video, and few-step distillation tends to reduce dynamics. Check dynamic degree, and use an order- and direction-aware per-video metric like temporal-distance predictability, which flags near-static, reversed and shuffled clips. Gate on dimensions as a vector, not an average.

**11. Describe your temporal metric and how you'd use it here.**
A frozen ~5M-param regressor predicts inter-frame temporal distance from frame pairs. A clip's score is the log-likelihood of the true gaps. It's reference-free, per-video and cheap. I'd use it as a gate and monitoring signal, alongside warping error and flicker, and *not* as a training loss, because my negative result showed the generator games it.

**12. How do you design a VLM-as-judge for video ads?**
Sample frames densely enough (1–2 fps plus shot boundaries plus end card) or use native video input. Pass OCR and ASR as side channels. Ask structured, evidence-demanding yes/no questions (product match, unapproved text, hands, motion direction, order). Swap positions in pairwise comparisons. Calibrate per category against human labels (κ, per-failure precision and recall) with a logistic layer that combines judge outputs with numeric metrics, and re-calibrate on any model change. Dense cheap metrics cover what the judge misses at low fps.

**13. How do you prevent Goodhart's law in creative optimization?**
Keep an optimization firewall: held-out evaluators the generator is never trained or selected against, an ensemble of diverse metrics, rotating judges, periodic human audits of best-of-N outputs, and alarms on divergence between optimized and held-out metrics. My metric got gamed as a loss, so I treat this as a real risk, not a theoretical one.

**14. What policy checks are specific to video vs. images?**
Every-frame scanning (one-frame violations and subliminal flashes), OCR on every frame, since text appears transiently, ASR plus text moderation of audio, music fingerprinting and license scope, voice and likeness checks, photosensitive flash/strobe limits, legal-super duration and readability, and AI disclosure and provenance (C2PA).

**15. How do you handle audio for CTV vs. Sponsored Videos?**
CTV is sound-on and broadcast: a BS.1770-measured loudness target around −24 LKFS (CALM Act / A/85), true-peak limiting, VO intelligibility, CEA-608/708 captions. Sponsored Videos are muted autoplay: burned-in captions and supers carry the message. For both: licensed music with beat sync, brand-voice TTS with a pronunciation lexicon, and WCAG captions and audio description.

**16. Estimate the cost of generating video variants at scale.**
State assumptions: ~20 H100-min per 5 s 720p clip undistilled (~240 GPU-s per video-s), about 25× less distilled to 4 steps without CFG (~10 GPU-s/s), and $2.50/GPU-hr gives ~$0.83 vs. ~$0.04 per shot. 200k shots per refresh comes to ~$330k vs. ~$8k, ×2 for rejects. The template path costs under $0.005. Conclusion: template-first, distill, preview at low res, finalize only what's approved.

**17. How would you measure whether generated video ads actually help?**
Online: VCR quartiles, viewable views, CTR, closed-loop attributed sales and ROAS, and most importantly **incrementality** via randomized holdouts (generated plus bandit vs. advertiser creative only), with geo or user-level holdouts for CTV. Offline: creative-performance models debiased for targeting. Also track advertiser adoption, approval rate and edit distance.

**18. How do you choose among 10 generated variants in-flight?**
Contextual Thompson sampling per placement, with hierarchical priors from a creative-performance model for cold start and pooling across small advertisers. Use proxy rewards (VCR or click) with delayed-conversion correction, guardrails (minimum exploration, brand-safety, frequency/fatigue caps), and a random-allocation holdout to measure lift.

**19. Where does frame interpolation fit, and what are its failure modes?**
Generate at lower fps and interpolate to 24/30, re-time across delivery frame rates, and make smooth product reveals. Flow-based methods (RIFE intermediate flow, FILM multi-scale for large motion, softmax splatting) fail at disocclusions, thin structures, transparency and specular surfaces, all common on packaging. Generative start/end-frame interpolation handles large motion at higher cost. In templated renders, use the renderer's true motion vectors and depth instead of estimating flow, which is exactly what I shipped in SpaceWarp.

**20. What's the "structured representation of creative content" for video, and why does it matter?**
A versioned timeline: shots and layers with sources (template, advertiser clip, generated with model, seed and prompt), product layers tied to SKUs, text tracks tied to approved copy and claim IDs, audio tracks with licenses, captions, placement spec and provenance. It makes adaptation a re-render, allows exact structural checks (logo time, super duration), gives interpretable features for performance models, and provides auditability for advertisers and legal.

---

## Appendix: one-page cheat sheet

- **Thesis:** template-first, cut-downs second, generate the world but composite the product, timeline as system of record, calibrated eval with an optimization firewall, bandits plus incrementality.
- **Numbers:** 4×8×8 VAE; 1×2×2 patch; 5 s 720p ≈ 112k tokens; 2× length = 4× attention; −24 LKFS ±2 (A/85/CALM); MRC video viewability is 50% pixels for 2 s; ~240 → ~10 GPU-s per video-s with distillation *(assumption)*.
- **Eval vector:** spec · policy (every frame, OCR, ASR) · product fidelity (min over frames + drift) · warping error + flicker · dynamic degree + temporal predictability · VLM structured judge · human calibration.
- **Your four bridges:** (1) SpaceWarp = reprojection, interpolation and disocclusion inpainting → parallax, interpolation, compositing seams. (2) Diffusion from scratch, CFG, consistency, distillation → video DiT, flow matching, few-step cost. (3) Identity-preserving faces → product identity verification. (4) Temporal-Distance Predictability plus its Goodhart negative result → per-video gate and eval firewall.
