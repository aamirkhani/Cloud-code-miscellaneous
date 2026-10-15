# 07 — Question Bank (140 questions with model answers)

**How to drill:** cover the answer, say yours out loud in under 60 seconds, then compare. Mark ⭐ any you missed and repeat them Sunday night.

---

## A. Ads business & auctions (1–18)

1. **What is retail media and why is it growing?** Retailers selling ads on their own properties and off-site using first-party shopper data. Growing because of high purchase intent, closed-loop measurement, cookie deprecation, and margins far above retail.
2. **What's Walmart's advantage over Amazon/Google?** Omnichannel closed loop (online + 4,600 stores), first-party purchase data, broad grocery frequency, and Vizio CTV inventory. Versus Google: observed conversions, not modeled ones.
3. **How does GSP pricing work?** Rank by bid×pCTR; winner in slot i pays the minimum bid that keeps its rank: score_{i+1}/pCTR_i.
4. **Is GSP truthful?** No. Bidders can gain by shading. VCG is truthful. GSP persists because it's simple, stable, and revenue-competitive in equilibrium.
5. **Why multiply bid by pCTR?** It converts CPC bids into expected revenue per impression (eCPM), aligning revenue with relevance, because a high bid with low click probability earns nothing.
6. **What's a reserve price and how would you set it?** Minimum price to win. Learn per query/category from the bid distribution (Myerson-optimal reserve under distribution assumptions). Test via A/B. Watch fill rate and advertiser churn.
7. **First-price vs. second-price?** First-price: pay your bid, so bid shading is required. Second-price: pay next price. Open web moved to first-price for transparency across header bidding.
8. **What is bid shading?** In first-price auctions, bid b* = argmax (v − b)·P(win|b) using a learned win-rate model.
9. **How do you decide how many ads to show (ad load)?** Per-query dynamic allocation: show an ad in a slot only if its value (revenue + λ·expected GMV) exceeds the displaced organic item's value. Tune λ with long-term holdouts.
10. **What is the relevance floor?** A minimum query–ad relevance threshold applied regardless of bid. It protects shopper trust and advertiser ROI.
11. **Ads vs. organic: should the ad model be the same as the organic ranker?** Share representations (embeddings, relevance features), but objectives differ: ads need calibrated pCTR for pricing, organic optimizes GMV/engagement. Joint whole-page optimization is the end state.
12. **What happens if pCTR is over-predicted by 20%?** Over-ranks those ads, distorts prices (second-price inputs), autobidding overbids, and budgets deplete early. Revenue may tick up short-term while advertiser ROAS falls and churn follows.
13. **Explain CPC vs. CPM vs. CPA billing.** Who bears risk: CPM means the advertiser bears click risk; CPC means the platform bears CTR risk; CPA means the platform bears conversion risk too.
14. **What metrics would an advertiser care about?** ROAS, iROAS, sales, new-to-brand customers, share of voice, CPC, impression share.
15. **What is new-to-brand?** Purchases from shoppers who haven't bought the brand in N months (e.g. 12). Important to CPGs for growth.
16. **Sponsored Brands vs. Sponsored Products?** SB: brand banner + multiple products at the top, more upper-funnel. SP: individual product listings inline.
17. **How might Sparky (conversational assistant) ads differ?** Fewer slots, higher stakes per slot; relevance must be very high; disclosure; ad must fit the answer; pricing may be CPC or per-mention; measurement via conversation-to-purchase.
18. **What's the "relevance tax"?** Shopper cost of seeing ads instead of best organic results, which lowers conversion. Must be measured and capped.

## B. Prediction models & ranking (19–45)

19. **Walk me through a pCTR model.** Sparse ID embeddings + user behavior sequence (target attention) + dense features → feature interaction (DCN-v2) → MLP → sigmoid. BCE loss, downsampled negatives with recalibration, daily + incremental training.
20. **Why does CVR modeling suffer from sample selection bias?** Trained on clicks only, served on all impressions. ESMM models pCTCVR over all impressions with pCVR as a latent factor.
21. **Data sparsity in CVR?** Conversions are ~100× rarer than clicks. Share embeddings with CTR task (multi-task), auxiliary tasks (add-to-cart), and priors.
22. **Delayed feedback: how to handle?** Wait windows, importance weighting, delayed-feedback models (exponential delay distribution), fake-negative correction, or re-label after window with streaming updates.
23. **What's MMoE and why over shared-bottom?** Multiple experts with per-task softmax gates. It reduces negative transfer when tasks conflict. PLE adds task-specific experts.
24. **How do you handle position bias?** Position as a training feature (set constant at inference), or a shallow position tower (PAL), or IPW with randomization-estimated propensities.
25. **What is DIN?** Deep Interest Network: attention over user's historical behaviors weighted by relevance to the candidate ad. A user's diverse interests get activated selectively.
26. **Feature crosses: why and how in deep models?** Capture interactions like user×category. Explicit: FM, DCN cross layers. Implicit: MLP (inefficient at learning multiplicative interactions).
27. **How do you handle a billion-ID embedding table?** Hashing / frequency thresholds, sharding across hosts (model parallel), mixed precision/int8, TTL eviction, mixed dimension by frequency.
28. **How do you cold-start a new ad?** Content-based embeddings (multimodal image+text), category priors with Bayesian smoothing, exploration slice, ID embedding initialized from similar items' mean.
29. **Two-tower vs. cross-encoder?** Two-tower: independent encoding enables ANN retrieval, fast but weaker interactions. Cross-encoder: joint encoding, accurate, too slow for retrieval. Use for ranking/teacher.
30. **What is logQ correction?** In-batch negatives oversample popular items; subtract log of sampling probability from logits to debias.
31. **How do you mine hard negatives safely?** From ANN results of the current model excluding positives; filter likely false negatives (e.g. with a relevance teacher); mix with easy/random negatives.
32. **How would you evaluate a retrieval model offline?** Recall@K of items eventually clicked/purchased; recall of final-auction winners; coverage; latency at target recall.
33. **Why multi-stage ranking?** Cost. The heavy model can't score millions of candidates in ~10 ms.
34. **How do you ensure early stages don't filter good candidates?** Measure recall of downstream winners; distill ranker scores into pre-ranker; send some random candidates through (exploration).
35. **What features are unique to Walmart?** Store-level inventory, pickup/delivery options, price competitiveness, Walmart+ membership, grocery replenishment cycles, in-store purchase history, rollback/promo status.
36. **How do you handle seasonality (Black Friday)?** Fresh incremental training, event features, recency-weighted data, pre-season warm-up with last year's analogous period, tighter monitoring and calibration.
37. **How would you use images in ranking?** Precomputed visual embeddings (CLIP-like trained on Walmart catalog + engagement), as features and for cold start; creative-level CTR models for display.
38. **How to model user sequences at scale?** Truncate/limit to last N events; long-term interest via precomputed user embeddings (offline); short-term via online attention; retrieval-based long sequence (SIM, Alibaba).
39. **What are generative recommenders?** Transformers trained on action sequences to predict next action/item (HSTU), or generating semantic item IDs (TIGER). They show scaling laws.
40. **How to do relevance labeling at scale?** Human raters on stratified samples + LLM labeler calibrated against humans (agreement/κ) → millions of labels → train cross-encoder → distill.
41. **Pointwise vs. pairwise vs. listwise losses?** Pointwise (BCE) gives calibrated probabilities, which ads need. Pairwise/listwise optimize order. Often combine: BCE + ranking loss with a weight.
42. **Diversity in ads results?** Re-rank with MMR or determinantal point processes; per-advertiser caps; brand diversity rules.
43. **How do you prevent one advertiser from dominating?** Per-advertiser slot caps, diversity constraints, auction rules. Monitor concentration (HHI).
44. **How do you handle out-of-stock?** Hard filter at retrieval using store-level inventory; feature for low-stock risk; auto-pause signals to advertiser.
45. **When would you use GBDT over a deep model?** Small/tabular data, quick strong baselines, interpretability, budget forecasting regressors. Deep models win with huge sparse data and sequences.

## C. Calibration & offline metrics (46–56)

46. **Why calibrate?** Downstream consumers (auction pricing, bidding, pacing, forecasting, reporting) use probabilities as values.
47. **Negative-downsampling recalibration formula?** p = p' / (p' + (1 − p')/w), w = negative keep rate.
48. **Platt vs. isotonic?** Platt: parametric sigmoid, smooth, little data. Isotonic: non-parametric monotone, needs more data, can overfit in sparse bins.
49. **How to monitor calibration?** Calibration ratio (Σp/Σy) per segment (slot, device, category, new vs. old ads), ECE, reliability diagrams, alerting on drift.
50. **AUC vs. log loss?** AUC is ranking only, insensitive to calibration. Log loss captures both. Normalized entropy (NE) = log loss / entropy of base rate, comparable across datasets.
51. **What is GAUC?** AUC averaged per user/query weighted by impressions. It reflects within-request ranking, which is what serving does.
52. **Offline gain, online loss: why?** Train/serve skew, calibration shift, feedback loops, leakage, metric mismatch, latency regression causing timeouts/fallbacks, novelty.
53. **What's a meaningful offline improvement?** At scale, +0.1–0.3% NE/AUC is often significant. Always verify online.
54. **How to detect label leakage?** Suspiciously large gains; features computed after the event; point-in-time join audits.
55. **What is ECE?** Expected calibration error: weighted average |accuracy − confidence| over bins.
56. **How does class imbalance affect training?** Downsampling negatives speeds training (recalibrate after); focal loss changes calibration and is rarely used for pCTR.

## D. Bidding & pacing (57–68)

57. **Derive the optimal bid under a budget constraint.** Max Σx v s.t. Σx c ≤ B → Lagrangian → win auction iff v − λc ≥ 0 → in second-price, bid = v/λ.
58. **With a target ROAS too?** bid = v(1+μ)/(λ + μT), with μ the ROAS dual. Still linear in value.
59. **How do you update λ?** Online dual gradient descent or PID on spend vs. target spend curve, every few minutes, clipped.
60. **Throttling vs. bid modification?** Throttling: randomly skip auctions; simple, uniform. Bid modification: more efficient, buys cheap high-value impressions first.
61. **What's the target spend curve?** Forecasted traffic/opportunity curve over the day, not linear time.
62. **How to avoid overspend in a distributed system?** Central budget service with periodic sync, local allowances (token buckets), stop bidding near budget with safety margin; accept bounded overspend and don't bill it.
63. **Why might RL help autobidding?** Captures non-stationary, multi-step effects and competition dynamics. But needs a simulator, is hard to debug, and must beat strong controller baselines.
64. **How to test a new autobidder?** Budget-split experiments per campaign; offline auction replay simulator first.
65. **What breaks autobidding in practice?** Miscalibrated values, conversion delay, sudden traffic shifts, competition feedback loops, tiny budgets (high variance), cold-start campaigns.
66. **Max-clicks vs. max-conversions vs. target-ROAS strategies?** Differ only in the value v (pCTR vs. pCTR·pCVR vs. pCTR·pCVR·AOV) and constraints.
67. **How do you forecast campaign delivery?** Replay recent auction logs with the campaign's settings (bid landscape simulation) and ML-predicted traffic.
68. **Game-theoretic concern with all advertisers autobidding?** Bids escalate toward values, reducing advertiser surplus. The platform should ensure fairness and stability, and set reserves thoughtfully. Autobidding equilibria are an active research area.

## E. Measurement & experimentation (69–84)

69. **Attribution vs. incrementality?** Attribution assigns credit for observed conversions. Incrementality measures what wouldn't have happened without the ad (causal).
70. **What is ghost ads?** In the control group, log when the ad would have been shown (would-have-won) without showing it. This gives a precise exposed-vs-would-be-exposed comparison.
71. **Why not just compare exposed vs. unexposed users?** Selection bias: targeting picks people likely to buy anyway.
72. **Geo experiments: when and how?** When user-level randomization is impossible (in-store media, TV). Randomize regions; analyze with synthetic control / time-based regression; power is limited.
73. **What is CUPED?** Regression adjustment using pre-experiment covariate: Y' = Y − θ(X − mean X), θ = cov(X,Y)/var(X). Reduces variance substantially.
74. **Interference in ads experiments?** Shared budgets and auctions couple treatment and control. Solutions: budget-split, cluster randomization, switchbacks.
75. **What's interleaving?** Merge results from rankers A and B in one list; credit clicks to originating ranker. ~10–100× more sensitive than A/B for ranking.
76. **Long-term holdout: why?** Short-term tests miss shopper fatigue from ad load. Keep a small group with reduced ads for months.
77. **Novelty effect?** Initial metric spike from change itself. Run long enough and analyze by exposure-days.
78. **How do you pick experiment duration?** Power analysis (MDE, variance), plus full weekly cycles, plus delayed conversions (attribution window).
79. **Multiple testing?** Pre-register primary metric; correct (Bonferroni/BH) for many metrics; treat guardrails as one-sided tests.
80. **What's MMM?** Media mix modeling: regression of sales on channel spend with adstock/saturation, Bayesian priors, calibrated with experiments. Strategic budget allocation.
81. **Uplift modeling?** Predict treatment effect τ(x) = E[Y|T=1,x] − E[Y|T=0,x] (T-/S-/X-learners, causal forests). Target high-τ users.
82. **Halo effect?** Ad for product A lifts sales of brand's product B. Measure at brand level.
83. **Cannibalization in retail media?** Ad shifts purchase from one Walmart SKU to another. Brand gains, Walmart's GMV may not. Measure category-level incrementality.
84. **SRM (sample ratio mismatch)?** Unequal group sizes vs. design, which signals a bug. Always check before reading results.

## F. Systems & scale (85–100)

85. **Design serving for 100K QPS at p99 < 50 ms.** Multi-stage funnel, horizontal stateless scoring tier, batched GPU inference, co-located feature caches, hedged requests, timeouts with fallbacks, multi-region, load shedding.
86. **Biggest latency contributors?** Feature fetch fan-out, embedding lookups, network hops, GC pauses, cold caches. Rarely model FLOPs.
87. **Training/serving skew: causes and fix?** Different feature code paths, staleness, defaults. Fix by logging served features and training on them, shared feature definitions, skew monitoring.
88. **What's a feature store?** Shared definitions, offline store for training with point-in-time joins, online store for low-latency serving, consistency guarantees.
89. **Streaming features?** Kafka events → Flink windowed aggregates (e.g. item CTR last 1h) → online store. Mind late events and watermarks.
90. **How to train hourly on fresh data?** Warm-start from previous checkpoint, train on the latest hour(s), validate on a holdout from the following window, automatic canary.
91. **Distributed training for recsys?** Hybrid: model-parallel embeddings (all-to-all) + data-parallel dense layers. TorchRec/HugeCTR.
92. **How to deploy a model safely?** Offline validation gates → shadow → canary 1% → automated checks (calibration, latency, revenue) → ramp; one-click rollback.
93. **What do you monitor in production?** Latency/QPS/errors, feature null rates and drift (PSI), prediction distribution, calibration ratio, revenue/CTR anomalies per segment.
94. **How do you handle a bad model pushed to production?** Auto-rollback on guardrail breach, fallback model, postmortem: why didn't gates catch it.
95. **Cache strategy for query embeddings?** LRU for head queries with TTL; compute tail on the fly; precompute for top-N queries daily.
96. **ANN index choices?** HNSW (high recall, memory heavy, incremental inserts), IVF-PQ (billion-scale compressed), ScaNN. Tradeoff: recall/latency/memory/update speed.
97. **How to keep the ad index fresh?** Streaming updates on campaign changes (budget exhausted, paused, bid change) within seconds. Embedding updates within minutes.
98. **GPU vs. CPU for ranking inference?** GPU for heavy dense/attention models with batching; CPU fine for small models and embedding-heavy lookups. Measure cost per 1K inferences at SLO.
99. **How to reduce serving cost by 50%?** Distillation, quantization (int8), pruning candidates earlier, caching, right-sizing batch windows, autoscaling to diurnal traffic, cascades.
100. **Explain tail-latency amplification.** With fan-out to N shards, p99 of the request ≈ the slowest shard, so a rare slow shard becomes common. Fix with hedging, replication, and reduced fan-out.

## G. GenAI, LLMs, agents (101–122)

101. **When RAG vs. fine-tuning?** RAG for changing or proprietary knowledge. Fine-tuning for behavior/format/tool-use consistency. Often both.
102. **Explain LoRA.** Freeze W, learn low-rank update BA. Tiny trainable params; can swap adapters per task.
103. **Explain DPO vs. RLHF.** RLHF: reward model + PPO with KL penalty. DPO: closed-form reparameterization, trains directly on preference pairs, more stable, no RM.
104. **How do you evaluate an LLM agent?** Task success verified by system state, tool-call accuracy, groundedness, safety violations, cost/latency. Offline golden sets + online A/B.
105. **LLM-as-judge pitfalls?** Position bias, verbosity bias, self-preference, drift. Calibrate against humans, randomize order, use rubrics.
106. **How do you prevent hallucinated numbers in campaign insights?** All numbers come from tool/SQL results; template with references; post-check that every number in the output appears in tool outputs.
107. **Prompt injection risk in ads?** Product titles/reviews/advertiser text could contain instructions. Treat as data, isolate, never allow retrieved content to trigger tools without validation.
108. **Multi-tenant isolation in RAG?** Tenant ID enforced in the retriever and tool layer, not in the prompt.
109. **How to reduce LLM serving cost?** Cascades/routing, distillation, quantization, prefix caching, batching (vLLM), speculative decoding, shorter prompts.
110. **What's continuous batching?** Scheduler adds/removes sequences at each decode step instead of waiting for a whole batch, so GPU utilization is much higher.
111. **What's KV cache and PagedAttention?** Cached keys/values for past tokens avoid recompute. Paging manages them in blocks to avoid fragmentation.
112. **Speculative decoding?** Small draft model proposes k tokens; big model verifies in one pass; accept matching prefix. Exact distribution preserved.
113. **How would you build keyword suggestion with LLMs?** LLM generates candidate queries from product info; filter by relevance model and historical query volume; rank by predicted performance; advertiser approves.
114. **How to keep generated creative product-faithful?** Lock product pixels; generate around them; fidelity checks (embedding similarity, OCR); human review for new categories.
115. **Diffusion for creative at scale: cost?** Batch offline, few-step samplers (consistency/distilled models), smaller resolutions + super-resolution, cache by product.
116. **What's ReAct?** Prompting pattern interleaving reasoning and tool actions with observations.
117. **When multi-agent vs. single agent?** Multi-agent when domains have distinct tools/prompts and can be tested independently. Otherwise single agent is simpler and more reliable. Don't add agents for fashion.
118. **Human-in-the-loop for budget changes?** Propose → show diff and projected impact → explicit confirm → apply → audit log → undo.
119. **How to use LLMs in the ranking hot path?** Generally don't. Use them offline for embeddings, labels, and attributes, and distill into fast models.
120. **How would you fine-tune for an advertiser agent?** Collect successful traces (human-verified), SFT on tool-use trajectories, DPO on preferences, eval gates, staged rollout.
121. **Guardrails for Sparky ads?** Clear "Sponsored" labeling, relevance threshold higher than search, no ad content altering factual answer, category restrictions.
122. **Open model vs. API?** API: speed to market, best quality. Self-hosted: cost at volume, data control, latency, fine-tuning freedom. Hybrid via a model gateway.

## H. Deep ML fundamentals (123–132)

123. **Bias-variance tradeoff in ranking?** More capacity and features reduce bias, but sparse IDs overfit, so you need regularization, embedding dropout, and frequency thresholds.
124. **Why does Adam/Adagrad suit sparse embeddings?** Per-parameter adaptive rates; rare features get larger updates. Sparse-aware optimizers avoid updating untouched rows.
125. **Batch norm vs. layer norm in recsys?** LayerNorm is common in sequence/attention parts. BN is problematic with streaming non-stationary data.
126. **Why EMA of weights?** Smoother, better-generalizing weights. You've used it in DINO-style training, and it's also used for stable serving models.
127. **Knowledge distillation loss?** KL between temperature-softened teacher and student distributions + hard-label loss. For CTR: distill logits with MSE/BCE on soft labels.
128. **Contrastive temperature effect?** Lower τ sharpens and focuses on hard negatives. Too low makes training unstable.
129. **How do you debug a model that stopped learning?** Check data pipeline (labels, joins), feature distributions, LR schedule, gradient norms, dead embeddings, loss per segment.
130. **What's a good ablation methodology?** Change one thing, matched compute, multiple seeds, confidence intervals, report negative results. (Your papers are built on this, so say it.)
131. **Transformers' complexity for long user sequences?** O(n²) attention. Use truncation, linear/sparse attention, retrieval of relevant sub-sequences (SIM), or caching.
132. **Diffusion vs. GAN for creative?** Diffusion is more stable and diverse with better controllability (ControlNet). GANs are faster at inference. Distilled diffusion closes the speed gap.

## I. Leadership & judgment (133–140)

133. **How would you set a 2-year ML roadmap for Walmart Ads?** Start from business goals (advertiser ROI, revenue, shopper trust), assess gaps, pick 3–5 bets (shopper foundation model, incrementality-optimized bidding, GenAI advertiser tools, shared eval/feature platforms, whole-page optimization), sequence by dependency and value, define metrics and owners.
134. **How do you handle disagreement with a VP on a technical direction?** Bring data, run a time-boxed experiment, write the tradeoff explicitly, commit once decided.
135. **How do you grow senior engineers?** Give ownership of hard problems, review designs Socratically, pair on critical code, sponsor them visibly.
136. **What's a technical debt you'd tackle first?** Usually feature/training skew and eval infrastructure, because they slow every team.
137. **How do you decide what NOT to build?** If it doesn't move a north-star metric within a reasonable horizon or unblock many teams, defer it. Kill projects that don't hit pre-agreed milestones.
138. **How do you work with product and science partners?** Shared metric definitions, joint design reviews, scientists own causal measurement, engineers own systems. Sit together.
139. **Describe your design review style.** Problem statement and metrics first, alternatives considered, failure modes, rollout and rollback plan, cost.
140. **What would make you successful here in one year?** One measurable bet shipped (e.g. +X% advertiser iROAS or Y% revenue at flat shopper metrics), a shared platform adopted by multiple teams, and a stronger senior engineering bench.
