# 03 — Retrieval, Ranking & Serving at Scale (100K+ QPS)

## 1. The funnel (draw this from memory)

```
Request (query, user, context)          budget: ~100 ms end-to-end for search page; ads gets ~30–50 ms
   │
   ├─ Query understanding (5 ms)        spell-correct, tokenize, category classifier, intent, query embedding (cached)
   │
   ├─ Candidate retrieval (10 ms)       millions of ads → ~1–5K candidates
   │     • lexical: inverted index on keywords/titles (BM25), advertiser-chosen keywords
   │     • semantic: two-tower ANN (HNSW / ScaNN / FAISS-IVF-PQ)
   │     • behavioral: item-to-item co-view/co-buy, user-history-based
   │     • filters: in-stock at user's store/zip, budget remaining, policy, targeting rules
   │
   ├─ Pre-ranking (5 ms)                ~5K → ~300; light model (two-tower dot product or small MLP)
   │
   ├─ Ranking (10–15 ms)                ~300 → scored; heavy multi-task model (pCTR, pCVR, relevance)
   │     • features fetched from online feature store (batch fetch; this is often the real bottleneck)
   │
   ├─ Auction + re-rank (2–5 ms)        eCPM, reserves, relevance floor, diversity, whole-page allocation, pricing
   │
   └─ Log everything                     impressions, features-at-serve-time, auction outcome → Kafka → training data
```

**Why multi-stage:** cost. A heavy model on 5K candidates × 100K QPS = 500M inferences/s. Infeasible. Each stage trades recall for precision at decreasing cost.

**Stage consistency problem:** an early stage may filter what the ranker would love. Fixes: train pre-ranker to **distill the ranker's scores** (rank-distillation), measure **recall@K of final winners** at each stage.

---

## 2. Two-tower retrieval (your contrastive expertise applies directly)

- Query/user tower `q = f(query, user, context)`; ad/item tower `a = g(title, image, category, brand, ID)`.
- Score = cosine(q, a)/τ. Train with **InfoNCE over in-batch negatives** (+ hard negatives).
- **Sampling-bias correction** (Yi et al. 2019, Google): popular items appear as in-batch negatives more often, so subtract `log(p_item)` from logits (logQ correction).
- **Hard negatives:** same category but not clicked; items ranked high by the current model but not engaged. Too-hard negatives = false negatives (actual relevant items). Mine carefully, like with MoCo/DINO.
- **Item tower is precomputed** offline → ANN index; query tower runs online (or cached for head queries; ~top 10% of queries cover a large share of traffic).
- **Index freshness:** new ads need embeddings within minutes. Use streaming embedding + incremental index updates (HNSW supports inserts; IVF needs periodic rebuild).
- **Multimodal item tower:** image + title + attributes. CLIP-style pretraining on Walmart catalog pairs. **Your strongest technical contribution story.**

**ANN options:** HNSW (graph, high recall, memory-heavy), IVF-PQ (compressed, billion-scale), ScaNN (anisotropic quantization). Know the recall-vs-latency-vs-memory tradeoff.

---

## 3. Ranking model (production-grade sketch)

```
Sparse IDs ─► embedding tables (sharded)  ─┐
User seq   ─► target-attention / transformer over last N events (keyed on candidate) ─┤
Dense feats ─► normalize/bucketize          ─┼─► feature interaction (DCN-v2 cross + MLP)
Text/image ─► precomputed embeddings        ─┘         │
                                                       ▼
                                      MMoE / PLE experts + per-task gates
                                     ┌────────┬─────────┬──────────┬──────────┐
                                     pCTR     pCVR      pATC       relevance
                                     (ESMM: pCTCVR = pCTR × pCVR trained on all impressions)
Position ─► shallow bias tower (train only) ─► added to pCTR logit
```

- **Loss:** Σ w_t · BCE_t (+ calibration-friendly; avoid pure ranking losses for pCTR because the auction needs probabilities). Add pairwise/listwise for relevance if needed.
- **Task balancing:** uncertainty weighting, GradNorm, or tuned static weights. **Your composite-loss experience applies.**
- **Training cadence:** daily full retrain + **hourly/streaming incremental fine-tune** (ads data is non-stationary: new ads, promos, holidays). Freshness gives measurable lift. The Facebook 2014 paper showed this.
- **Embedding hygiene:** frequency thresholds, hashing for long tail, TTL eviction, mixed-dimension embeddings.

---

## 4. Relevance model (shopper protection)

- **Query–item relevance** classifier (e.g. 4-grade: exact/substitute/complement/irrelevant, a la Amazon ESCI dataset).
- Teacher: **cross-encoder / LLM** (expensive, accurate). Labels from human raters + **LLM-as-labeler** (big cost win, since an LLM can label millions of pairs; calibrate against humans).
- Student: distilled into a small model served in ranking. **This is exactly your knowledge-distillation background (EMA teacher → edge student).**
- Use as: (1) hard floor, (2) feature in ranking, (3) multiplier in auction score.

---

## 5. Serving at 100K+ QPS: the systems answer

### 5.1 Back-of-envelope (do this out loud in the interview)
- 100K QPS × 300 candidates ranked = **30M model inferences/s**.
- If a ranking model is ~20 MFLOPs per candidate → 600 TFLOP/s of compute. On paper that's 1–2 modern GPUs at peak, but real utilization for small-batch, latency-bound, memory-bound (embedding lookup) inference is 10–30%, so it's ~5–10 GPUs of pure compute. Then add per-region replication, N+2 redundancy, peak-traffic headroom (holiday ~3×), and CPU hosts for feature fetch. Realistically that's tens to hundreds of nodes. **The point to make: compute is rarely the bottleneck. Memory bandwidth, feature fetch, and fan-out tail latency are.**
- Feature fetch: 300 candidates × ~50 features → batched multi-get to online store (Redis/Cassandra/Aerospike/custom), p99 < 5 ms needs **co-located caches** and **pre-joined item feature blobs**.
- Embedding tables: 1B IDs × 64 dims × 4 bytes = **256 GB**. Shard across hosts, or use fp16/int8 (your quantization strength) → 64 GB.

### 5.2 Tail latency techniques
- **Timeouts + graceful degradation**: if ranker times out, fall back to pre-rank scores; if a feature is missing, use defaults (the model must be trained with feature dropout so it tolerates this).
- **Request hedging** (send a duplicate request after p95), **load shedding**, **adaptive concurrency limits**.
- **Dynamic batching** on GPU inference servers (Triton/TorchServe-like); size the batch window to latency SLO.
- **Caching**: query embedding cache, head-query candidate cache, item features cache.
- **Model compression**: distillation, int8 quantization, pruning, fused kernels. Mention TensorRT/ONNX Runtime; you have ONNX experience.
- **JVM/GC**: if serving stack is Java/Scala, GC pauses dominate p99. Your JIT/JVM background is relevant here.

### 5.3 Reliability
- Multi-region active-active, canary deploys of models (shadow traffic → 1% → 10% → 100%), automatic rollback on calibration/latency regression.
- **Model monitoring**: feature drift (PSI), calibration ratio per segment, prediction distribution, revenue anomalies. A bad pCTR model **directly loses money per minute**.
- Kill switches; safe-mode rankers.

---

## 6. Data and training infrastructure

- **Logging**: log features **at serve time** ("log and wait") to eliminate training/serving skew. Join with click/conversion labels in a streaming joiner (Flink/Spark Structured Streaming), with **label delay windows**.
- **Feature store**: offline (BigQuery/Hive/Delta) + online (KV), **point-in-time correct joins** to prevent leakage. Feast/Tecton-style concepts.
- **Pipelines**: Kafka → Flink/Spark → feature store; Airflow/Kubeflow orchestration. Walmart uses a mix of GCP, Azure, and its own cloud (WCNP). Don't claim specifics; speak generally.
- **Distributed training**:
  - Dense part: data parallel (DDP), FSDP for big towers.
  - Embedding part: **model parallel / sharded** (TorchRec, HugeCTR), all-to-all communication. **Hybrid parallelism** is the DLRM pattern.
  - Throughput is IO-bound: data loader performance matters more than FLOPs.
- **Negative downsampling** (keep 1–10% of negatives) to cut training cost → **recalibrate**.

---

## 7. Feedback loops and exploration

- The model only sees outcomes for ads it chose to show, so it's biased toward the current policy.
- **Exploration** (ε-greedy on a small slice, Thompson sampling on uncertain new ads, boosted cold-start slots).
- **Counterfactual evaluation** of new policies with IPS/doubly robust estimators on logged randomized data.
- **Your RL background:** offline RL / off-policy evaluation are natural talking points.

---

## 8. Personalization at Walmart scale: specifics to mention

- **Local inventory**: an ad for an item out of stock at the shopper's store is wasted money. Availability is a hard filter and a feature.
- **Pickup/delivery context**, Walmart+ membership, **price sensitivity** (Walmart's shopper base skews value-seeking; price competitiveness features matter more than at luxury retailers).
- **Basket context**: complement ads (bought pasta → sauce ads). Sequence models over the current session.
- **Grocery replenishment cycles** (repeat purchase timing) are a strong signal unique to a grocery-heavy retailer.
- **Omnichannel**: in-store purchases linked to the account feed back into online targeting.

---

## 9. Generative recommenders (2024–2026 frontier): show you're current

- **HSTU (Meta 2024)**: treat user action history as a sequence, transformer predicts next action. Showed **scaling laws** for recsys (quality improves with compute like LLMs).
- **Semantic IDs** (TIGER, Google 2023): represent items as discrete code sequences (RQ-VAE) so a seq2seq model can *generate* item IDs. Retrieval becomes generation.
- **LLM-based ranking features**: LLM embeddings of queries/items; LLM-generated item attributes enrich the catalog.
- **Distinguished take:** "I'd invest in a foundation model for shopper behavior, one sequence model pretrained on all of Walmart's interaction logs, fine-tuned per surface (search ads, display, CTV, Sparky). That's the 'one model beats N silos' bet I made with multimodal fusion on the glasses." (This links directly to your Golf Mode AI story.)
