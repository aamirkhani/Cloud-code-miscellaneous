# 02 — Ads ML Fundamentals (Retail Media Edition)

Goal: by Monday you can talk about ads like someone who has worked in it for a year. Each section ends with **"Say it like this"**, a 2–3 sentence answer you can use in the interview.

---

## 1. The business: what Walmart Connect is

**Retail media network (RMN):** a retailer sells ad space on its own properties (and off-site) to brands, mostly the suppliers whose products it sells. Walmart Connect is Walmart's RMN. Its global ad business is reported in the **multi-billion-dollar range, growing ~25%+/yr**; check the latest earnings for exact numbers before Monday.

**Ad products (know these names):**
| Product | What it is | ML core |
|---|---|---|
| **Sponsored Products** (Sponsored Search) | Paid product listings inside search results and browse/item pages on walmart.com and the app. CPC-priced. **Biggest revenue line** | Query–ad relevance, pCTR/pCVR, auction, autobidding, keyword/targeting expansion |
| **Sponsored Brands** | Brand banner + logo + several products at the top of search | Same, plus creative selection |
| **Sponsored Videos** | Video units in search | Video understanding, pCTR for video |
| **Display (on-site / off-site)** | Banners on Walmart properties and across the web via **Walmart DSP** (built with The Trade Desk) | Audience modeling, lookalikes, bid shading in first-price RTB |
| **CTV via Vizio** | Walmart acquired Vizio (~$2.3B). CTV ads targeted with Walmart shopper data, **measured against actual purchases** | Cross-device identity, audience building, incrementality |
| **In-store media** | Screens, radio, sampling in 4,600+ US stores | Store-level measurement (geo experiments) |
| **Sparky ads** | Ads inside Walmart's GenAI shopping assistant | Conversational ad relevance; LLM-native ad formats |
| **Marty** | Agentic assistant *for advertisers*: campaign setup, bidding, keywords, insights | LLM agents, RAG over campaign data, tool use |
| **Automated Creative Generator** | GenAI creative production (reported ~80% faster in beta) | Diffusion/LLM creative, brand safety |
| **Walmart Luminate / Scintilla** | Shopper insights / data products for suppliers | Analytics, privacy-safe aggregation |

**Retail media's structural advantage, which you should say early:**
1. **Closed-loop measurement**: Walmart sees the ad impression *and* the purchase (online + in-store, via Walmart+ / app / card linkage). Google/Meta must infer conversions; Walmart **observes** them.
2. **High-intent inventory**: a shopper searching "paper towels" is at the bottom of the funnel.
3. **First-party data** that survives the death of third-party cookies.

**The three-sided tension (the central concept):**
- **Shopper**: wants relevant results. Too many or irrelevant ads hurt conversion, trust, and long-term GMV.
- **Advertiser**: wants ROAS and incremental sales.
- **Walmart**: wants ad revenue **and** GMV **and** shopper retention.

Every design decision trades these off. E.g. **ad load** (how many ad slots per page) and the **relevance floor** (minimum relevance for an ad to show).

> **Say it like this:** "Retail media's moat is closed-loop data: we see the impression and the basket. So the ML problem isn't just predicting clicks. It's predicting incremental sales while protecting the shopper experience, because organic conversion is the asset ads are monetizing."

---

## 2. Metrics vocabulary (memorize)

| Metric | Formula | Notes |
|---|---|---|
| CTR | clicks / impressions | |
| CVR | conversions / clicks | Post-click; usually a 7- or 14-day attribution window in retail |
| CPC | spend / clicks | Sponsored Products is CPC-billed |
| CPM | spend / impressions × 1000 | Display / CTV billing |
| **eCPM** | expected revenue per 1000 impressions = bid × pCTR × 1000 (for CPC ads) | **The common currency for ranking mixed ad types** |
| **ROAS** | attributed sales / ad spend | Advertiser's main KPI. "ROAS of 4" = $4 sales per $1 |
| **iROAS** | **incremental** sales / ad spend | The truth. Usually much lower than ROAS |
| ACoS | spend / attributed sales = 1/ROAS | Amazon vocabulary; advertisers use it |
| RPM / RPS | revenue per mille (page views) / revenue per search | Walmart-side monetization |
| Ad load | ad slots / total slots | Shopper-experience guardrail |
| Fill rate | slots filled / slots available | |
| Take rate / Ads % of GMV | ad revenue / GMV | Industry: Amazon ~ several %; Walmart is growing toward it |
| GMV | gross merchandise value | **Guardrail**: ads must not reduce GMV per search |

**Guardrail metrics for any ads launch:** organic CTR, search conversion rate, GMV/search, bounce/exit rate, query reformulation rate, latency p99.

---

## 3. Auctions

### 3.1 Generalized Second Price (GSP), the classic for sponsored search
- Rank ads by **score = bid × pCTR** (often × quality/relevance factor, sometimes plus other terms).
- Ad in slot *i* pays the **minimum bid needed to keep its rank**:
  `price_i = (bid_{i+1} × pCTR_{i+1}) / pCTR_i  (+ $0.01)`
- Charged **per click** (CPC), so expected revenue per impression = pCTR_i × price_i.
- GSP is **not truthful** (bidding true value isn't a dominant strategy), but it's stable and well understood. Walmart Connect reportedly moved Sponsored Products to a (advanced) **second-price auction**.

**Worked example** (memorize, you might be asked to compute):
| Ad | Bid | pCTR | Score |
|---|---|---|---|
| A | $1.00 | 0.05 | 0.050 |
| B | $2.00 | 0.02 | 0.040 |
| C | $0.50 | 0.06 | 0.030 |
Ranking: A, B, C. A pays 0.040/0.05 = **$0.80/click**. B pays 0.030/0.02 = **$1.50/click**. C pays the reserve price (or the next ad's score).

### 3.2 VCG
- Each winner pays the **externality** it imposes on others. Truthful, but revenue is often lower than GSP and it's harder to explain. Used at Meta (historically) for some placements.

### 3.3 First-price auctions (display RTB / DSP)
- Open-web programmatic moved to **first-price** ~2019. Bidders use **bid shading**: bid less than value, learning the win-rate curve `P(win | bid)` and maximizing `(value − bid) × P(win | bid)`.
- Relevant to **Walmart DSP** (off-site display).

### 3.4 Reserve prices, quality floors
- **Reserve price** (floor): minimum CPC. Can be **personalized per query/category** (learned reserves raise revenue).
- **Relevance floor**: ad must exceed a relevance threshold regardless of bid. This protects the shopper. In retail, an irrelevant ad also costs the advertiser money for nothing.

### 3.5 Ads vs. organic blending
- Option A: **fixed slots** (e.g. positions 1, 4, 8…).
- Option B: **dynamic allocation**: compare ad's *total value* vs. displaced organic item's value:
  `value(ad) = α·eCPM + β·pCVR·price·GMV_weight + γ·relevance` vs. the organic item it displaces.
  Decide slot-by-slot. This is the **whole-page optimization** answer, and Distinguished candidates should bring it up.

> **Say it like this:** "Ranking is by bid times calibrated pCTR, with a relevance floor so we don't tax the shopper. Pricing is second-price. I'd push toward whole-page optimization, where an ad wins a slot only if its combined value (revenue plus expected GMV) beats the organic item it displaces."

---

## 4. Prediction models: pCTR, pCVR

### 4.1 Problem framing
- **pCTR** = P(click | impression, user, query, ad, context, position).
- **pCVR** = P(purchase | click, …). Trained on clicked samples only, which gives **sample selection bias (SSB)**: at inference you predict over all impressions.
  - Fix: **ESMM** (Entire Space Multi-task Model, Alibaba 2018): learn pCTR and pCTCVR = pCTR × pCVR over *all impressions*. pCVR is a latent tower.
- **Delayed feedback**: purchases arrive hours/days after the click. Recent samples look like negatives.
  - Fixes: wait window + correction, **importance weighting**, delayed-feedback models (e.g. DFM, Chapelle 2014), fake-negative weighting, re-labeling after the window.

### 4.2 Features (what actually matters)
- **IDs** (high-cardinality, learned embeddings): user ID, item/SKU ID, ad ID, advertiser ID, brand, category, query tokens.
- **Query–item relevance**: text match (BM25), semantic similarity from two-tower or cross-encoder, category match.
- **User behavior sequences**: recent searches, views, add-to-carts, purchases. Modeled with attention (DIN/DIEN/BST/transformers).
- **Item stats**: historical CTR/CVR (smoothed, with Bayesian priors for cold start), price, rating, reviews, in-stock, delivery speed, **price competitiveness**.
- **Context**: device, time, page type, slot position, store/zip (local availability!).
- **Cross features**: user×category affinity, query×brand.

### 4.3 Model families (chronological; know one line each)
- **LR + feature hashing + crosses** (Google, Yahoo, ~2010). Still a strong baseline. FTRL-Proximal optimizer.
- **GBDT + LR** (Facebook 2014): trees as feature transformers.
- **FM / FFM**: factorized pairwise interactions. Cheap and strong for sparse data.
- **Wide & Deep** (Google 2016): memorization (wide crosses) + generalization (deep).
- **DeepFM, DCN / DCN-v2** (explicit cross network), **xDeepFM**.
- **DLRM** (Meta 2019): embedding tables + dot-product interactions + MLP. Sharded embeddings.
- **DIN / DIEN** (Alibaba): **target attention** over user behavior sequence, keyed on candidate ad.
- **BST / transformers over sequences**; now **generative recommenders** (Meta HSTU 2024) and scaling laws for recsys.
- **Multi-task**: Shared-bottom → **MMoE** (Google 2018) → **PLE** (Tencent 2020). Predict CTR, CVR, add-to-cart, dwell together.

### 4.4 Calibration (very likely question)
**Why:** auction pricing, autobidding, budget forecasting, and advertiser reporting all treat pCTR as a *probability*. A model with great AUC but 20% over-prediction **overcharges/over-ranks** and breaks pacing.
**Causes of miscalibration:** negative downsampling, class imbalance, distribution shift, position bias, new ads.
**Fixes:**
- **Negative-downsampling correction:** if negatives were kept at rate *w*, then `p = p' / (p' + (1−p')/w)`.
- **Platt scaling** (logistic on logit), **isotonic regression**, **histogram binning**. Per-segment calibration (by slot, device, category).
- **Monitor:** calibration ratio = Σ predicted / Σ actual (target 1.0 ± 0.02) per segment; **ECE**; reliability diagrams.
- **Metrics:** **log loss / normalized cross-entropy (NE)** captures both ranking and calibration. **AUC** captures ranking only. Report both. Use **GAUC** (per-user/query-averaged AUC) for personalization.

### 4.5 Position bias
Clicks depend on position, not just relevance. Fixes:
- Include **position as a feature during training**, set to a constant (e.g. position 1) at serving.
- **Shallow tower for position** (PAL, Huawei 2019): `P(click) = P(seen|pos) × P(click|seen)`.
- Inverse propensity weighting (IPW) with propensities from randomization experiments.

### 4.6 Cold start
- New ads/items: content features (title, image, category embeddings from multimodal encoders), **Bayesian smoothing** of CTR toward category prior, **exploration** (UCB/Thompson for a small traffic share), meta-learned ID embeddings.
- **Your angle:** multimodal item embeddings (CLIP-style image+text) are where your vision expertise directly helps cold-start.

> **Say it like this:** "I'd train pCTR and pCVR jointly in an ESMM/MMoE-style multi-task model to fix sample-selection bias, correct for delayed conversions, handle position bias with a shallow position tower, and then calibrate per segment, because every downstream system (auction, bidding, pacing) consumes these as probabilities."

---

## 5. Advertiser-side optimization: bidding

### 5.1 Bid strategies Walmart offers (typical RMN)
- **Manual CPC** bids per keyword/item.
- **Dynamic bidding** (raise/lower manual bid by conversion likelihood). Reported on Walmart Connect.
- **Automated / autobidding**: advertiser sets a **goal** (max sales or clicks) and **constraints** (daily budget, target ROAS / max CPC). The platform bids per auction.

### 5.2 Autobidding math (the RL / optimization question; use your strength)
Advertiser objective over a day: maximize Σ_i x_i·v_i (value, e.g. pCVR × price) s.t. Σ_i x_i·c_i ≤ B (budget), optionally Σ x_i v_i / Σ x_i c_i ≥ ROAS_target.

**Lagrangian dual → optimal bid is linear in value:**
- Budget only: `bid_i = v_i / λ` where λ is the budget dual variable.
- With ROAS constraint: `bid_i = v_i · (1+μ)/(λ + μ·ROAS_target)`-style; still proportional to value.

The key insight: **the bid is value scaled by one or two dual variables**, and **λ is learned online** to spend the budget evenly. That's a 1-D control problem:
- **PID controller** on the spend-rate error, or
- **Online dual gradient descent**: `λ_{t+1} = max(0, λ_t + η·(spend_t − target_spend_t))`.
- RL formulations (e.g. Alibaba's **DRLB** / USCB) treat λ adjustment as an MDP. You can discuss when RL is worth it vs. a well-tuned controller. **Honest Distinguished answer: start with dual/PID, add RL only if there's measured headroom.**

**Pitfalls:** value estimation error (calibration again!), auction dynamics (all advertisers' bots react to each other), end-of-day budget exhaustion, cold start for new campaigns, non-stationary traffic (Black Friday, weekends).

### 5.3 Budget pacing
Goal: spend smoothly across the day, not blow the budget by 9 AM.
- **Probabilistic throttling**: participate in each auction with probability p_t, adjusted to match the target spend curve (shaped by expected traffic, *not* linear in time).
- **Bid modification**: scale bids (the λ above).
- Throttling is simpler; bid modification is more efficient (it gets cheap high-value auctions).
- **Distributed issue:** spend counters across thousands of ad servers are eventually consistent, so overspend happens. Use a central budget service with bounded staleness + overspend tolerance (e.g. ≤ 5%), local token buckets.

> **Say it like this:** "Under a budget constraint, the optimal bid is the value divided by a dual variable. So autobidding reduces to good value prediction plus an online controller on that one variable. I'd ship a dual-gradient pacing controller first, then test RL against it under a budget-split experiment, because my RL experience says the controller baseline is usually hard to beat."

---

## 6. Targeting and audiences

- **Keyword targeting**: exact / phrase / broad match. **Auto-targeting** (the platform picks queries) depends on query–item relevance models.
- **Query expansion / keyword recommendation**: given an item, suggest queries (two-tower retrieval in reverse, or an LLM generating candidates scored by a relevance model).
- **Audience targeting (display/CTV)**: segments from purchase history (e.g. "bought diapers in 90 days"), **lookalike modeling** (seed audience → classifier or embedding similarity), propensity models ("likely to buy category X in next 30 days").
- **Contextual targeting**: match ad to the page/content (embedding similarity). Privacy-friendly.
- **Privacy:** aggregation thresholds (k-anonymity), clean rooms for sharing with brands, differential privacy in reporting, consent/opt-out (CCPA). Retail media relies on data never leaving Walmart's walls.

---

## 7. Attribution

**Question:** which ad gets credit for a sale?
- **Last-touch / last-click**: simple, biased toward bottom-funnel.
- **Multi-touch (MTA)**: linear, time-decay, position-based, or **data-driven** (Shapley values, or a sequence model of conversion probability with/without each touch).
- **View-through attribution**: credit for impressions without clicks (CTV/display). Easily over-credits.
- **Attribution windows**: 14 days is common in retail; shorter for CPG impulse buys.
- **Halo**: ad for SKU A, shopper buys SKU B of the same brand. Retail media reports **brand halo** sales.
- **Online + in-store** closed loop: match identity (Walmart account, app, payment card hash) to in-store transactions. This is Walmart's big differentiator.

**The key point to make:** attribution ≠ causation. A shopper who searched "Tide" and clicked a Tide ad would probably have bought Tide anyway.

## 8. Incrementality (causal measurement), likely Distinguished-level probe

- **Randomized holdout**: withhold ads from a random % of users; incremental sales = treated − control. Clean but costly (lost revenue).
- **Ghost ads / ghost bids** (Johnson, Lewis, Nubbemeyer 2017): in the control group, log *when the ad would have shown* (ran the auction, didn't display), which gives a precise counterfactual and reduces noise vs. ITT.
- **PSA / placebo ads**: show a charity ad to control (costly, and the auction changes).
- **Geo experiments**: randomize ad spend by DMA/store region; analyze with **synthetic control** or **time-based regression (Google TBR)**. Needed for in-store and CTV.
- **Observational methods** when you can't randomize: propensity matching, double ML, uplift modeling. Trust them less.
- **MMM** (media mix models): Bayesian regression of sales on spend across channels (e.g. Google Meridian, Meta Robyn), calibrated with experiments.
- **Uplift modeling for targeting**: target users whose **treatment effect** is high (not whose purchase prob is high). T-learner, X-learner, causal forests. Segments: persuadables / sure things / lost causes / sleeping dogs.

> **Say it like this:** "ROAS rewards ads shown to people who'd buy anyway. I'd measure iROAS with ghost-bid holdouts for on-site and geo experiments for in-store and CTV, use those to calibrate a modeled MTA, and ultimately optimize bidding toward incremental value, which is the north star for advertiser trust."

---

## 9. Experimentation in an ads marketplace

- **Standard user-split A/B** works for ranking changes affecting shoppers, but **budget interference** breaks it for bidding/pacing: treatment and control share the same advertiser budget, so treatment can "steal" spend.
  - **Budget-split testing**: split each advertiser's budget and traffic 50/50 into independent sub-campaigns (LinkedIn/Meta style).
  - **Advertiser-split**: randomize advertisers. But they compete in the same auctions (interference again).
  - **Switchback / time-split**: alternate treatment over time windows.
- **Interleaving** for ranking: much more sensitive than A/B for comparing rankers.
- **Variance reduction: CUPED** (use pre-period metric as covariate), stratification, trimming outliers (whale advertisers).
- **Novelty/primacy effects, long-term holdouts** (keep 1% of users with fewer ads for months to measure long-term GMV impact of ad load). **Long-term holdouts are a Distinguished-level point**: short-term revenue tests systematically over-reward ad load.
- **Metrics hierarchy:** primary (ad revenue, advertiser ROAS/iROAS), guardrails (GMV/search, organic CTR, latency), diagnostics (CTR, calibration).
- **Offline→online gap:** AUC gains of +0.1% can matter; calibration and serving-skew often explain offline wins that fail online.

---

## 10. Brand safety, policy, quality

- Ad review: prohibited products, misleading claims, trademark/IP. Use ML classifiers + LLM review + human escalation.
- **GenAI creative risks**: hallucinated product attributes (wrong size/color), off-brand imagery, unsafe content, regulated categories (alcohol, OTC drugs, firearms-adjacent).
- Search relevance as a policy: an irrelevant ad on a sensitive query (e.g. "baby formula" during a shortage) is a PR problem.

---

## 11. Five papers to name-drop correctly
1. **McMahan et al. 2013, "Ad Click Prediction: a View from the Trenches"** (Google): FTRL, calibration, practical lessons.
2. **He et al. 2014, "Practical Lessons from Predicting Clicks on Ads at Facebook"**: GBDT+LR, data freshness, NE metric.
3. **Ma et al. 2018, ESMM**: sample-selection bias in CVR.
4. **Zhou et al. 2018, DIN**: target attention on user behavior.
5. **Johnson, Lewis, Nubbemeyer 2017, "Ghost Ads"**: incrementality measurement.
Bonus: **Covington et al. 2016, YouTube DNN recommendations** (two-stage); **Aggarwal et al. 2019, autobidding with constraints**; **Zhai et al. 2024, HSTU** (generative recommenders, scaling laws).
