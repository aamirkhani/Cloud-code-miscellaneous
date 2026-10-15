# 01 — Gap Analysis: Your Résumé vs. Distinguished ML Engineer, Walmart Connect

> ⚠️ **Superseded.** This was written before the actual posting was known. The real role is **Distinguished Data Scientist, Creative Intelligence (R-2630449)**. See `10_ROLE_creative_intelligence_START_HERE.md` §2 for the role-specific gap analysis. Keep this file for the general ads-domain gaps (still relevant, but secondary).

## TL;DR

You're **over-qualified on deep-learning craft** and **under-evidenced on three things this role is hired for**:
1. **Ads and recommender domain** (auctions, CTR/CVR, bidding, attribution, retail media).
2. **Web-scale distributed serving and data** (100K+ QPS, feature stores, streaming, A/B testing on a two-sided marketplace).
3. **Production LLM/agent systems** (fine-tuning, RAG, agent orchestration, evals, LLM serving cost).

A Distinguished interviewer will probe whether you can **set direction for a $B ad business** in a domain you haven't worked in. Your job on Monday is to make the transfer feel low-risk: show domain fluency, map each of your wins to an ads analog, and show that you think in business metrics.

---

## A. Strengths to lead with (and their ads analogs)

| Your evidence | Why it matters to Walmart Connect | How to say it |
|---|---|---|
| Trained many PyTorch models from scratch (transformers, diffusion, GANs); composite-loss design; ablation discipline | Ranking models are multi-objective (CTR, CVR, relevance, revenue). Loss design and ablations are the core skill | "Multi-task ranking is a composite-loss problem, and I've built composite losses with six or more terms and per-phase schedules." |
| **Single-model multimodal fusion (IMU + audio + video) that beat per-sensor pipelines** | This is the same argument as **unified multi-task / multi-surface ranking** replacing per-surface models, and as **multimodal item embeddings** (image + title + behavior) | "I've already made the 'one model beats N siloed pipelines' argument and won it with data. Ads has the same fragmentation across search, display, CTV, and Sparky." |
| On-device inference, quantization, distillation, TFLite/ONNX, hard latency budgets (11.6 ms/frame, 90 FPS XR) | Ad serving has a ~100 ms end-to-end budget, and ranking gets maybe 10–30 ms for hundreds of candidates. **Distillation and quantization cut serving cost**, especially for LLMs | "I've lived inside millisecond budgets for a decade. Ad ranking at 100K QPS is the same problem with a different bottleneck: fan-out and feature fetch instead of GPU fill." |
| **RL research** (RL as diffusion; value iteration; RL cert) | **Autobidding and budget pacing are sequential decision problems** (constrained MDP, Lagrangian dual, bandits). Very few candidates can talk RL fluently | "Autobidding under budget and ROAS constraints is a constrained control problem. The dual-variable formulation is where my RL background applies directly." |
| Knowledge distillation (EMA teachers → edge students), DINO, MoCo/InfoNCE, CLIP | Two-tower retrieval is trained with **InfoNCE and in-batch negatives**. Teacher→student distillation is how you serve LLM-quality relevance at ranking latency | "Contrastive training is my home turf: in-batch negatives, temperature, hard-negative mining. That's exactly how two-tower ad retrieval is trained." |
| Generative imaging (inpainting, identity-preserving synthesis), diffusion | **Automated Creative Generator**: product-preserving background generation and image variants for ads. Identity preservation maps to *product/brand fidelity* | "Identity-preserving face synthesis maps directly to brand-safe, SKU-faithful creative generation. The product can't be hallucinated." |
| Reference-free temporal-quality metric for generated video | Evaluating GenAI output without ground truth: creative quality and LLM-agent output evals | "I've built a reference-free quality metric and published a negative result on using it as a loss. That's the evals mindset GenAI products need." |
| 7 publications, 5 patents, 4× EVP awards, shipped as default on Galaxy XR (beat Google's solution) | Preferred qualification; Distinguished-level proof of impact | Lead with "beat Google, shipped as default." It's a competitive-win story. |
| **Bixby Store Assistant**: in-store product search by voice + AR navigation, Lidar data pipeline, web-service API | **Retail + search + product catalog.** Your most direct retail evidence. Use it | "I've built product search for physical retail aisles, voice query to product location. That's on-site retail search with a spatial twist." |
| Android Analytics Dashboard (behavioral data collection) | Behavioral signals and user modeling | Minor; use only if asked about user data |
| GCP Professional Data Engineer cert | Data pipelines, BigQuery, Dataflow. Walmart runs heavily on GCP + Azure + on-prem | "I'm certified on GCP data engineering, so pipeline design at scale isn't foreign to me." |
| 25 yrs of production systems incl. JVM/JIT, real-time RTOS (Boeing Apache) | Systems depth: GC pauses, tail latency, JIT warmup. Real issues in JVM-based ad servers | "I've written JIT compilers. I know where p99 latency comes from." |

---

## B. Gaps, ranked by interview risk

### Gap 1 — Ads domain knowledge 🔴 HIGH RISK
**What's missing:** No ads, recommender, or e-commerce ranking on the résumé.
**What they'll probe:** How does a sponsored-search auction work? Why calibrate pCTR? How do you rank ads vs. organic? How would you build autobidding? How do you measure incrementality?
**How to close it (this weekend):** `02_ads_ml_fundamentals.md` and `03_recsys_ranking_at_scale.md`. You must be able to:
- Write and explain **eCPM = bid × pCTR (× quality)** and the **GSP pricing rule**.
- Explain **why calibration matters** (pricing, bidding, budgeting all consume probabilities, not ranks).
- Sketch **retrieval → pre-rank → rank → re-rank/auction** with latency per stage.
- Describe **budget pacing** (throttling vs. bid modification; PID / dual-variable).
- Contrast **last-touch attribution vs. incrementality (geo / ghost-ads / holdout)**.
- Explain **retail media's edge**: closed-loop attribution with first-party purchase data, online and in-store.

**Honest positioning:** Don't pretend. Say: *"I haven't run an ads stack. Here's how I'd reason about it…"* and then reason correctly. Distinguished interviewers respect first-principles reasoning plus honesty more than bluffing.

### Gap 2 — Web-scale distributed systems 🔴 HIGH RISK
**What's missing:** 100K+ QPS serving, distributed training on billions of rows, feature stores, streaming, online/offline consistency.
**What they'll probe:** Design the serving path for 100K QPS at p99 < 50 ms. How do you keep features consistent between training and serving? How do you train an embedding table with 1B IDs?
**Close it:** `03` §5–7 and `05`. Know:
- Fan-out math, caching tiers, request hedging, timeouts and fallbacks, load shedding.
- Feature store (offline/online, point-in-time joins), Kafka→Flink/Spark streaming features.
- Embedding sharding (model parallel) + dense data parallel (hybrid parallel, as in DLRM/TorchRec).
- Training/serving skew, log-and-train (logging features at serve time).

**Bridge:** Your JVM/JIT and real-time RTOS work is real systems depth. Use it to show you understand tail latency at a mechanical level (GC, thread scheduling, priority inversion).

### Gap 3 — Production LLMs / agents 🟠 MEDIUM-HIGH RISK
**What's missing:** No LLM fine-tuning, RAG, or agent system in production on the résumé. The posting explicitly requires it.
**What you do have:** transformers from scratch, ViT/DINO/CLIP, distillation, diffusion. That's the foundation.
**Close it:** `04_genai_llm_agents.md`. Be fluent in:
- SFT → preference tuning (DPO/RLHF; your RL helps here), LoRA/QLoRA, distillation into small models.
- RAG: chunking, hybrid retrieval (BM25 + dense), re-ranking, grounding, citations.
- Agents: ReAct, tool calling, planner/executor, guardrails, human-in-the-loop for money-moving actions (budget changes!).
- **Evals**: golden sets, LLM-as-judge with calibration, task-success metrics, online A/B.
- Serving: vLLM/continuous batching, KV cache, speculative decoding, quantization (your strength), cost per query.

**Recommendation:** if you have **any** side project with an LLM, even a weekend one, mention it. If not, consider building a tiny RAG or agent demo this weekend (2–3 h) so you can say "I built X and learned Y." This is optional; prioritize domain reading first.

### Gap 4 — Experimentation and causal inference 🟠 MEDIUM
**What's missing:** Online A/B testing in a marketplace; causal measurement.
**What they'll probe:** How do you A/B test a new bidding algorithm when advertisers share budgets? (Interference: budget-split designs.) How do you prove ads are incremental?
**Close it:** `02` §8–9, `07` experimentation section. Know CUPED, budget-split testing, interleaving for ranking, novelty effects, guardrail metrics.

### Gap 5 — Business and metric vocabulary 🟡 MEDIUM
ROAS, iROAS, CPC, CPM, eCPM, RPM, ad load, fill rate, take rate, advertiser retention, sponsored-product "relevance tax" on the shopper experience. At Distinguished level they want to hear you **tie technical choices to revenue, advertiser ROI, and shopper trust at the same time**. The three-sided tension (shopper / advertiser / Walmart) is the central idea.

### Gap 6 — Languages 🟢 LOW
Go/Rust preferred; you have C/C++/Java/Python, plus you've written a JIT. Say you're language-agnostic and that systems languages are native to you.

### Gap 7 — "Distinguished" scope signal 🟡 MEDIUM
Your résumé reads as a brilliant *individual* builder. Distinguished means **multi-org technical direction**: roadmaps, platform bets, raising the bar for 50–200 engineers, and influencing VPs.
**Close it:** In `06`, frame stories by **scope and leverage**: "I set the direction, X teams adopted it, it became the default." (The Galaxy XR SpaceWarp default is your best example. So is the proposed OpenXR extension, which is industry-standard influence.)

---

## C. Risk matrix: what to do if you get stuck

| If asked… | Don't | Do |
|---|---|---|
| A deep ads-specific detail you don't know | Bluff | "I haven't operated that piece. Here's how I'd derive it…" Then reason from first principles (incentives, data, latency) |
| "Why ads, coming from XR?" | Apologize | Give the transfer story (above) + genuine interest: retail media is the fastest-growing ad channel, with closed-loop data no one else has |
| "Have you served at 100K QPS?" | Say "no" and stop | "Not at that QPS. My constraints were per-frame latency on constrained hardware. Here's how I'd design for 100K QPS…" Then do the fan-out math |
| "Have you fine-tuned an LLM in production?" | Overclaim | Describe your transformer/distillation/RL depth, then walk through exactly how you'd do SFT→DPO→distill for an ads agent, with evals |

---

## D. Résumé tweaks (if you can still resubmit or bring a copy)
1. Move **Bixby Store Assistant** higher and reword it: "retail product search + navigation; voice query → product retrieval; Lidar/camera data pipeline; Java web-service API."
2. Add a line under ML skills: "Ranking / retrieval: contrastive two-tower (InfoNCE), distillation, multi-task loss design."
3. Under RL: "constrained sequential decision-making (relevant to bidding / pacing)."
4. Put "**beat Google, shipped as default on Galaxy XR**" in the first two lines of the summary.
