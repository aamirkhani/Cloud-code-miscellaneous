# 05 — ML System Design Walkthroughs

## The framework (use this every time, out loud)

1. **Clarify & frame (3–5 min)**: who are the users (shopper/advertiser/Walmart)? What's the business goal? Scale (QPS, catalog size, advertisers)? Latency? What exists today?
2. **Metrics (3 min)**: north star, offline metric, online metric, **guardrails**.
3. **High-level architecture (5 min)**: draw the boxes: data → training → serving → feedback.
4. **Deep dive on the ML (15 min)**: labels, features, model, loss, training cadence, calibration, cold start.
5. **Serving & scale (5–8 min)**: latency budget per stage, QPS math, caching, fallbacks.
6. **Evaluation & launch (5 min)**: offline → shadow → A/B (right unit of randomization!) → ramp.
7. **Risks & evolution (3–5 min)**: failure modes, feedback loops, privacy, **12–24 month roadmap**. ← *Distinguished differentiator: always end with the roadmap.*

**Distinguished-level signals to hit in every design:** state tradeoffs explicitly, name what you'd *not* build yet, quantify (back-of-envelope), consider org/platform reuse, tie to $ and shopper trust.

---

## Design 1 — Sponsored Products ranking for walmart.com search

**Prompt:** "Design the system that decides which sponsored products appear in search results and in which positions."

**1. Clarify.** ~100K+ peak QPS search; tens of millions of ad-eligible items; millions of campaigns; ads must render inside a ~100 ms page budget (ads ~30 ms). Goals: ad revenue, advertiser ROAS, no harm to GMV/search.

**2. Metrics.**
- North star: **long-term total value** = ad revenue + λ·GMV (don't optimize revenue alone).
- Offline: pCTR/pCVR **log loss/NE**, AUC, GAUC, **calibration ratio per segment**; relevance model precision at the floor threshold.
- Online: RPS (revenue/search), ad CTR, advertiser ROAS; **guardrails**: GMV/search, organic CTR, search exit rate, p99 latency.

**3. Architecture.**
```
Query → QU (spell, category, embedding) → Retrieval [keyword index | two-tower ANN | item-to-item]
     → filters (in-stock @ store, budget, policy, targeting) → ~3K
     → pre-rank (distilled two-tower) → ~300
     → rank (multi-task: pCTR, pCVR, relevance) → auction (eCPM, reserve, relevance floor) → slot allocation with organic
     → log features + auction → Kafka → streaming join w/ clicks/orders → training
```

**4. ML deep dive.**
- *Labels:* click (impression-level); conversion within 14-day window (delayed); add-to-cart (dense auxiliary signal).
- *Model:* MMoE with ESMM structure (pCTR, pCTCVR), target attention over the shopper's last ~100 events, DCN-v2 interactions, multimodal item embeddings for cold start, shallow position tower.
- *Relevance:* LLM-labeled + human-audited query–item pairs → cross-encoder teacher → distilled student served inline; used as hard floor + feature.
- *Calibration:* downsampling correction + isotonic per (slot, device, category group); monitored hourly.
- *Training:* daily full retrain on ~30 days + hourly incremental; embedding TTLs.
- *Cold start:* content embeddings + Bayesian-smoothed CTR priors + 2–5% exploration traffic for new ads.

**5. Serving.** Latency split: QU 5 / retrieval 10 / pre-rank 5 / rank 12 / auction 3 ms. Ranking on GPU with dynamic batching; features batch-fetched from co-located cache; fallback to pre-rank scores on timeout; head-query caches.

**6. Launch.** Offline replay → shadow scoring (compare calibration live) → 1% user-split A/B → ramp. **Interleaving** for fast relevance-ranker comparisons. **Long-term ad-load holdout** to measure shopper-retention effects.

**7. Risks & roadmap.**
- Risk: revenue-optimizing model drifts into showing less relevant ads, which costs long-term GMV. Mitigation: relevance floor + GMV term + long-term holdout.
- Risk: feedback loop starves new advertisers → exploration budget.
- **Roadmap:** (Q1–2) multi-task + calibration platform; (Q3–4) **whole-page optimization** jointly allocating ads and organic; (Y2) **shopper foundation model** (generative sequence model) shared across search ads, display, CTV, Sparky.

---

## Design 2 — Autobidding with budget + target ROAS ("Max sales" campaigns)

**Prompt:** "Advertisers give us a daily budget and target ROAS. Design the system that bids for them."

**1. Clarify.** Second-price auction for Sponsored Products. Millions of campaigns. Bid decision per auction must be < 1 ms (it's inside the auction loop). Value = expected attributed sales (or incremental sales, long term).

**2. Metrics.** Advertiser: conversions/sales achieved vs. manual-bid baseline at same spend, **ROAS constraint satisfaction rate** (% of days within ±10% of target), **budget utilization** (% spend, no overspend > 2–5%), smoothness. Platform: revenue, advertiser retention. Guardrail: shopper metrics unchanged.

**3. Formulation (write on whiteboard).**
max Σ x_i·v_i  s.t.  Σ x_i·c_i ≤ B,  Σ x_i·v_i ≥ T·Σ x_i·c_i
Dual → per-auction bid: **b_i = v_i·(1+μ)/(λ+μ·T)**, where v_i = pCVR_i × E[order value_i] (× pCTR for CPM-equivalence).
So bidding = **(a) value prediction** + **(b) online control of λ, μ**.

**4. Components.**
- **Value model**: calibrated pCTR × pCVR × predicted basket value (the ranking model's outputs + order-value regressor). Calibration errors map 1:1 to bid errors.
- **Pacing controller** per campaign: target spend curve shaped by **forecasted traffic** (hour-of-day, day-of-week, events). Update λ every few minutes: λ ← λ + η·(actual_spend − target_spend) (normalized), clipped. μ updated similarly on the realized ROAS error, using a **delayed-conversion-corrected** ROAS estimate.
- **Forecasting service**: predicts available auctions/win-rate per campaign for setting initial λ (warm start so day 1 doesn't misbehave). Also powers "estimated results" in the advertiser UI.
- **Budget service**: distributed spend counters with bounded staleness; per-region token allocation; hard stop near budget.
- **Bid landscape**: P(win|bid) curves to simulate.

**5. Where RL fits (you should raise this).** The controller treats each campaign independently, but all autobidders interact in the same auctions (a game). RL/MPC can learn λ trajectories using simulators from logged auctions. Plan: build an **auction replay simulator** first (essential for safe iteration), compare PID vs. dual-GD vs. RL policy in sim, then budget-split A/B. *"My RL work taught me to beat a strong classical baseline before shipping a learned policy. Matched-compute comparisons are the whole point of my papers."*

**6. Experiment design.** **Budget-split**: each campaign's budget is split 50/50 into two shadow campaigns, one per arm, and traffic is randomized by user. This avoids the "treatment steals budget" bias.

**7. Risks & roadmap.** Oscillation (controller gain tuning), holiday spikes (forecast-driven pre-adjustment), conversion delay making ROAS look bad early in day (use predicted conversions). **Roadmap:** optimize for **incremental** sales (uplift-based value) instead of attributed sales. That's the advertiser-trust endgame and Walmart's closed-loop data makes it feasible.

---

## Design 3 — "Marty": an agentic assistant for advertisers

**Prompt:** "Design an LLM agent that helps advertisers create and optimize campaigns."

**1. Clarify.** Users: self-serve sellers (long tail) and agencies. Actions: answer questions, diagnose performance, create/edit campaigns, suggest keywords/bids. Must never take an unwanted money-moving action.

**2. Metrics.** Task success rate (golden set + live verification via API state), deflection of support tickets, **campaigns launched via agent and their 30-day ROAS vs. manual**, advertiser retention, CSAT. Guardrails: incorrect-action rate (target ~0), hallucinated-number rate, latency (TTFT < 1.5 s), cost per conversation.

**3. Architecture.**
```
Advertiser UI ─► Gateway (auth, tenant ID, rate limit)
  ─► Router (small model: intent → {question, diagnose, create, optimize, policy})
  ─► Specialist agents (LangGraph-style state machine), each with typed tools:
       • Reporting tool: semantic layer / text-to-SQL over advertiser's own metrics (tenant-filtered)
       • Campaign API tools: create/update (dry-run returns diff)
       • Recommendation tools: keyword suggester, bid simulator (calls forecasting service from Design 2)
       • Policy/Help RAG: docs + ad policies (hybrid retrieval + reranker)
  ─► Guardrails: arg schema validation, spend-change limits, confirm step, PII filter, injection defense
  ─► Response w/ citations + numbers linked to query results
  ─► Logging → eval & fine-tuning data flywheel
```

**4. Model strategy.** Start with a strong hosted/self-hosted LLM + prompting + tools. Collect traces → **SFT a mid-size open model** on successful trajectories → **DPO** on preference pairs (advertiser thumbs-up/down + expert rating) → **distill** router and simple intents into small models. Cascade: small model for simple FAQs, large for multi-step diagnosis.

**5. Diagnosis capability (the hard, valuable part).** "Why did my ROAS drop?" → agent runs a structured decomposition: impressions (auction competitiveness, bid, budget-capped hours) × CTR (creative, position) × CVR (price change, out-of-stock, competitor promo) × AOV. Implement as a **deterministic analytics tool** the LLM calls, then narrates. Don't let the LLM do arithmetic.

**6. Evals & launch.** Golden set per intent; simulated advertiser conversations (LLM user-simulator); red-team (injection via product titles!); staged autonomy L0→L2; beta with opt-in advertisers.

**7. Roadmap.** L3 autonomy within advertiser-set guardrails ("keep ROAS ≥ 3, you can move ±15% budget across campaigns"); proactive alerts ("your top SKU is going out of stock in 3 days, pause ads?"); multi-agent coordination with creative generation (Design 4).

---

## Design 4 — Automated creative generation for Sponsored Brands / display

**Prompt:** "Generate ad images and headlines for advertisers automatically."

**Key points (detail in 04 §6):**
- Inputs: product images (catalog), brand kit, campaign goal, placement specs (sizes).
- Pipeline: segmentation → **locked product layer** → diffusion background (in/outpainting, ControlNet/IP-Adapter for layout & style) → **relighting/harmonization (your SH lighting work)** → LLM copy grounded in catalog attributes → template rendering per size.
- **Quality gates:** product-fidelity (embedding sim, OCR diff of packaging), brand safety, policy, aesthetic score, text legibility.
- **Selection:** creative-level pCTR model + **Thompson sampling** across variants, with per-category priors.
- **Metrics:** adoption rate, time-to-launch, CTR vs. advertiser-supplied creative, rejection rate at review, cost per generated asset.
- **Scale/cost:** batch GPU generation offline (not request-time), distilled/few-step diffusion (**consistency models, which you've worked with**) to cut cost 5–10×.
- **Roadmap:** video cut-downs for CTV (Vizio inventory), personalized creative by audience segment, closed loop where creative performance data trains the generator's preference model (DPO for diffusion).

---

## Design 5 — Off-site / CTV audience targeting with Walmart first-party data

**Prompt:** "A CPG brand wants to reach likely buyers of its new snack on CTV (Vizio) and the open web via Walmart DSP. Design targeting and measurement."

- **Audience building:** propensity model P(buy category/brand in next 30 days | purchase history, browse, recency/frequency); **lookalikes** from seed (past buyers) via embedding similarity over shopper embeddings; **uplift-based targeting** (target persuadables, not sure-things).
- **Identity:** Walmart account ↔ device graph (Vizio household IP/ACR, logged-in app, hashed email). Household-level for CTV. Privacy: matching inside clean room, aggregation thresholds, opt-outs.
- **Bidding (DSP, first-price RTB):** value = P(conversion | impression) × value; **bid shading** using win-rate curves; frequency capping across devices.
- **Measurement:** closed-loop sales attribution (online + in-store) **plus** incrementality via randomized holdout of households (ghost-bid logging) → report **iROAS**. CTV view-through attribution massively over-credits, so experiments are mandatory.
- **Roadmap:** unified cross-channel frequency/reach optimization (search + display + CTV + in-store screens) driven by one shopper model and one measurement framework.

---

## Design 6 — Incrementality measurement platform

**Prompt:** "Advertisers don't trust ROAS. Build a system that measures true incremental impact for every campaign."

- **Always-on randomized holdouts** at user level (e.g. 2–5% control per campaign or per advertiser) with **ghost-bid logging**: in control, run the auction, record would-have-won, don't show. Estimator: compare treated-would-win vs. control-would-win subgroups (an unbiased estimate of the effect on the exposed, much lower variance than ITT).
- **Cost of holdout** = lost revenue → adaptive holdout sizes (bigger for large advertisers who demand rigor; pooled hierarchical estimates for small ones).
- **Variance reduction:** CUPED with pre-period purchases, stratification by shopper segment.
- **In-store/CTV:** geo experiments (synthetic control across store regions) where user-level is impossible.
- **Modeled layer:** train an uplift / incremental-value model on experiment data → predict incrementality for every campaign, including those not in an experiment. Use it for (a) reporting iROAS and (b) feeding **incremental value into autobidding (Design 2)**.
- **Halo & cannibalization:** measure brand-level and category-level effects (did the ad just shift sales from another Walmart SKU? For Walmart, that matters; for the brand, maybe not).
- **Product:** self-serve lift studies in Ad Center; confidence intervals shown honestly.
- **Distinguished angle:** "Measurement is the moat. Walmart can sell *proven incremental sales* in a way open-web platforms can't. I'd make incrementality the objective the whole stack optimizes, not just a report."

---

## Practice prompts (do these with a 40-min timer)
1. Design query-to-ad relevance for Sponsored Products (labels, LLM teacher, distillation, thresholds).
2. Design ad load optimization: how many ads per search page, per query?
3. Design keyword recommendation for new advertisers.
4. Design ads inside Sparky's conversational answers.
5. Design budget forecasting ("if you spend $X, you'll get Y clicks").
6. Design fraud/invalid-click detection.
7. Design a real-time feature platform for ads.
8. Design the training platform for a 1B-ID embedding ranking model retrained hourly.
