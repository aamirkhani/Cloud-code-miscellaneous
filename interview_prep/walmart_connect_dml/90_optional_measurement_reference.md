# 90 — OPTIONAL reference: Ads Measurement (attribution, incrementality, clean rooms)

> **Not your role.** Before you shared the real posting (R-2630449, *Distinguished Data Scientist, Creative Intelligence*), I guessed a measurement-platform role. Keep this file only as background: the creative JD says creative signals should power "**performance measurement**", so you should know how creative impact gets measured (creative A/B tests, lift, attribution). Skim §3–§4 if you have spare time. Skip the rest.

## 1. The role, decoded

| What the posting says | What it means | What they'll test |
|---|---|---|
| "Lead platform development for measurement solutions **from 0 to 1**" | Greenfield platform. They want an architect and builder, not a maintainer | Can you design a whole platform end to end and sequence an MVP? |
| "**Incrementality**" | Causal lift: test/control, holdouts, ghost ads, geo tests | Experiment design, estimators, variance, interference |
| "**Attribution**" | Closed-loop credit for sales from ad exposure, online + in-store | Attribution engine design, windows, dedupe, identity, late data |
| "**Data cleanroom measurement**" | Brands combine their data with Walmart's without raw data leaving | Privacy tech: aggregation thresholds, differential privacy, PSI, query controls |
| "**Partner integrations**" | Off-site/DSP, Vizio CTV, Spotify-type audio, publishers, measurement vendors (iSpot, Nielsen…) | Data contracts, APIs, identity matching, SLAs, reconciliation |
| "**GenAI-powered reporting**" | Natural-language insights, end-of-campaign narratives, "ask your data" | Text-to-SQL over a semantic layer, grounding numbers, evals |
| "Supporting **real-time and offline**" | Streaming numbers for optimization (pacing/bidding feedback, live dashboards) **and** audited batch numbers for billing/reporting | Lambda/Kappa, exactly-once, watermarks, reconciliation between the two |
| "Set technical direction, **design reviews**, triage production issues" | Distinguished IC: hands-on and org-wide | Leadership stories, incident handling |
| 10+ yrs ML & **data-intensive platform** development; 4+ yrs staff+ tech lead | Data platform engineering is at the core, not just models | Distributed data systems depth |
| Preferred: **AdTech measurement experience**, **patents in data mining/ML**, **real-time streaming** | Your patents count; streaming and ad-measurement are gaps | — |
| Plus: experimentation systems, ranking/auction mechanics, personalization | Your existing pack (02/03) covers auction/ranking | — |

**Context you should know (public reporting):**
- Walmart Connect launched **incremental sales measurement for Sponsored Search** (announced April 2025), described as **test-and-control on first-party retail data**, contrasted with observational/third-party-data approaches; rolled out to managed advertisers.
- **Sponsored Search earned MRC accreditation** (fall 2025) for first-party **click and impression** metrics. MRC = Media Rating Council; accreditation means **audited, documented, reproducible measurement**, including invalid-traffic (IVT) filtering.
- **Closed-loop measurement**: ad exposure across Walmart properties *and off-site* → sales on walmart.com *and in 4,600+ stores*.
- **Vizio CTV measurement is the open problem**: Digiday reported agencies still see **incrementality as a sticking point** for Walmart–Vizio CTV, and one agency built its own POS analysis after unimpressive early results. *That's your opening: "I'd make CTV incrementality credible."*
- **Walmart DSP + Spotify** etc. advertise outcome tracking against store sales (off-site partner integrations).
- A **Distinguished Data Scientist** posting exists for the "next-generation ads incrementality measurement platform" (causal inference, RCTs). **Your role is likely that scientist's engineering counterpart**, so expect a question on how you'd partner with science.
- Walmart's SIGIR 2026 paper on Sponsored Search retrieval makes relevance the primary training signal and uses engagement only to order already-relevant items. That's a nice detail to show you read their work (it supports the "engagement ≠ relevance" view, which is also "attribution ≠ causation").

---

## 2. Revised gap analysis for THIS role

| Area | Your level | Risk | Plan |
|---|---|---|---|
| Causal inference / experimentation (RCT, ghost ads, CUPED, geo, synthetic control, power) | Light | 🔴 **Highest** | §4 + drills in `11_measurement_drills.py` |
| Real-time streaming data platforms (Kafka/Flink/Spark, exactly-once, late data, big stateful joins) | Light (GCP Data Engineer cert, 2017) | 🔴 High | §6 |
| Clean rooms & privacy-enhancing tech | None | 🔴 High | §5 |
| Attribution engine design | None | 🟠 Med-High | §3 |
| Reporting/OLAP serving at scale + auditability (MRC) | Light | 🟠 Med | §7 |
| GenAI reporting (text-to-SQL, grounded narratives) | Light | 🟠 Med | §8 + `04` §3 |
| Partner integrations | Some (Samsung↔Google platform work, IBM/Cisco/Boeing integrations) | 🟡 Med | §9 |
| ML craft, rigor, patents, leading technically | **Strong** | 🟢 | Lead with it |

### Your bridges for a *measurement* role (rewrite your stories around these)
1. **You build metrics, not just models.** You published a *reference-free metric* for generated video and a disciplined *negative result*. "Measurement is the discipline of not fooling yourself, and I've published on exactly that."
2. **Matched-compute, ablation-driven comparisons** in all your papers → you think in **controlled experiments**.
3. **Replay-verified results** → **reproducibility and auditability** (what MRC accreditation demands).
4. **Sensor fusion / Kalman / SLAM**: estimation under noise from multiple imperfect sources. That's the same mindset as **identity resolution** and **nowcasting delayed conversions** (estimating the final number before all data arrives).
5. **Golf Mode data pipeline** (filtering first-person footage, multi-device streaming glasses→phone→watch, power-aware streaming) → real-time, multi-source event pipelines.
6. **Android Analytics Dashboard**: you collected device behavioral data and built analytics on it. A small but real data-product precedent.
7. **JVM/JIT, Cisco/Boeing real-time systems** → you understand throughput, back-pressure, and memory in long-running stateful services (Flink jobs are long-running stateful JVM services!).
8. **OpenXR extension proposal** → designing **standards and contracts between parties**, which is what partner integrations and measurement methodology docs are.

### New 90-second pitch ending (replace the "why Walmart" part)
> "…What draws me to this role is measurement. Ads only work as a business if advertisers believe the numbers, and Walmart can do what nobody else can: connect an impression on walmart.com, a Vizio TV, or Spotify to a basket in a store. Making that causal, privacy-safe, real-time and auditable is a platform problem and a rigor problem. My work has always been about building the measurement before the model: reference-free metrics, matched-compute experiments, replay-verified results. I'd like to build that platform from zero to one."

---

## 3. Attribution engine: how it actually works

**Inputs:** ad events (impression, click, video-view, with campaign/ad/item/brand IDs, timestamp, user/household/device IDs, placement, channel), conversion events (online orders, **in-store POS transactions** linked by Walmart account / app scan / payment-token hash / Walmart+), product catalog (item → brand → category hierarchy).

**Core logic (per conversion):**
1. **Identity resolution**: map the event IDs to a person/household ID (deterministic: login, hashed email/phone; probabilistic: device graph for CTV/household IP). Keep the match rate and confidence as first-class metrics.
2. **Candidate touchpoints**: ad events for the same identity within the **lookback window** (e.g. 14 days for clicks, shorter for views; configurable per advertiser/product).
3. **Matching level**: **same SKU** (direct), **same brand** (brand halo), **same category** (category halo). Report each separately.
4. **Credit rule**: last-click (default for search), last-touch with view-through rules (display/CTV), or **data-driven MTA** (Shapley or a learned model).
5. **Dedupe**: one order credited once per rule; cross-channel dedupe so Search and Display don't both claim 100%.
6. **Filters**: invalid traffic (bots, click fraud) excluded *before* attribution (MRC requirement); returns/cancellations adjust sales later (restatement).

**Hard engineering problems (say these):**
- **Late and out-of-order data**: in-store transactions and partner data arrive hours or days late. Attribution must be **re-computable** (idempotent batch over a window) and real-time numbers must later **reconcile** with the batch numbers.
- **Huge stateful join**: clicks (billions) × orders within 14 days. In streaming, that's 14 days of state. Options: keep a compact per-identity recent-touch index in a KV store (RocksDB state / Bigtable / Cassandra) with TTL; or do the long-window join in batch and only short windows in streaming.
- **Restatements**: returns, IVT re-filtering, identity-graph updates change history, so you need **versioned outputs** and an audit trail.
- **Consistency across surfaces**: the same number must show in the advertiser UI, the API, the invoice, and the GenAI narrative. **One metrics layer.**

**Data-driven attribution model** (ML part): predict P(conversion | touch sequence) with a sequence model; credit = drop in predicted probability when removing each touch (counterfactual removal) or Shapley approximations. **Calibrate against experiments.** *"Attribution models are only trustworthy where incrementality experiments anchor them."*

---

## 4. Incrementality: the core of this role (go deep)

### 4.1 Estimands (define before estimating; this impresses scientists)
- **ITT** (intent-to-treat): effect of *being assigned* to ad-eligible vs. holdout, regardless of exposure. Unbiased but diluted when exposure is low.
- **ATT on the exposed**: effect on people who actually saw the ad. Needs a *counterfactual exposed group in control* → **ghost ads**.
- **CACE/LATE**: with one-sided noncompliance (control never exposed), **CACE = ITT / exposure rate in treatment** (Wald estimator).
- **iROAS = incremental sales / spend**; **lift % = incremental / baseline**.

### 4.2 Designs
| Design | How | Pros | Cons |
|---|---|---|---|
| **User-level holdout (RCT)** | Hash(user, study) → control % never served the campaign | Gold standard | Lost revenue; needs logged-in identity; dilution |
| **Ghost ads / ghost bids** | Control users still go through auction; log "would have won" | Precise ATT, much lower variance than ITT | Must log counterfactual consistently; auction must be deterministic-ish; engineering in the ad server |
| **PSA/placebo** | Control sees a charity ad | Comparable exposure | Costs money; changes auction dynamics |
| **Intent-to-treat with predicted exposure** | Model who'd be exposed | Cheap | Model bias |
| **Geo experiments / matched markets** | Randomize stores/DMAs | Works for in-store media, CTV, linear | Few units → low power; spillovers |
| **Synthetic control / TBR** | Weighted combination of control regions reproduces treated pre-period | Works with 1 treated unit | Assumptions, inference is hard |
| **Switchback (time)** | Alternate on/off over time windows | For marketplace interference | Carryover effects |
| **Observational (PSM, DML, uplift)** | Model counterfactual from logs | Covers everything | Unverifiable confounding; use only when calibrated to RCTs |

### 4.3 Variance and power (have numbers ready)
- Per-arm n ≈ **2(z₀.₉₇₅ + z₀.₈)² σ² / δ²** ≈ **15.7 σ²/δ²** (α=0.05 two-sided, 80% power).
- Sales per user are **heavy-tailed and zero-inflated** → huge σ. Mitigations: **CUPED** with pre-period spend in category (often 30–60% variance cut), winsorize/cap, stratify (by prior purchase frequency), use **ratio metrics with delta method**, longer windows, aggregate small advertisers with **hierarchical Bayesian shrinkage** (partial pooling).
- **Ghost ads** shrinks the analyzed population to the would-be-exposed, which removes the noise from unexposed users.
- **Sequential testing** (always-valid p-values / mSPRT) so advertisers can peek at dashboards without inflating false positives. **This is a platform feature, so mention it.**
- **Multiple comparisons**: hundreds of campaigns → control FDR (Benjamini–Hochberg) in reporting, or present intervals with partial pooling.

### 4.4 Holdout economics (a Distinguished-level tradeoff)
Holdouts cost revenue (control isn't served). Tradeoffs: smaller holdouts (2–10%), **always-on platform-level holdout** shared by many campaigns (a "universal holdout"), rotate holdout membership to avoid permanent ad-free users, **ghost ads to get precision with small holdouts**. Offer **study-based** rigorous lifts for big advertisers and **modeled incrementality** (calibrated to studies) for the long tail.

### 4.5 Interference & pitfalls
- **Competition spillover**: holding out brand A's ads frees slots for brand B, so control isn't "no ads," it's "competitor ads." Define the estimand clearly ("vs. the marketplace without your ad").
- **Cross-device / household**: user randomized but household shares the TV, which contaminates. Randomize at the **household** level for CTV.
- **Identity gaps**: non-logged-in traffic can't be held out → ITT on logged-in only, report coverage.
- **SRM checks**, **pre-period A/A balance**, **novelty**, **holiday seasonality**.
- **Halo/cannibalization**: measure SKU, brand, category lift separately. For Walmart, category-level incrementality tells you whether the ad grew total GMV or just shifted share.

### 4.6 Geo experiments for in-store & CTV
- Units: stores or DMAs; **stratified/matched randomization** on pre-period sales.
- Analysis: **difference-in-differences**, **synthetic control** (non-negative weights summing to 1 on control units fitting treated pre-period), Google's **TBR**, augmented SC. Inference via placebo/permutation tests.
- Power is the binding constraint, so pre-register and run long enough. Combine with user-level results where possible.

### 4.7 From measurement to optimization (this is the vision)
Experiments → train **uplift models** (τ(x)) → predict incrementality for every campaign/impression → feed **incremental value into bidding and targeting** → advertisers optimize for iROAS. *"Measurement shouldn't just report. It should become the objective function."* Connect to Design 2 in `05`.

### 4.8 Partner with science
"Scientists own the estimand, design, and estimator; the platform owns assignment, logging, exposure, pipelines, correctness, and productization. My job is to make a new estimator go from notebook to production in weeks instead of quarters: a library of vetted estimators, standardized experiment metadata, and automatic validity checks (SRM, A/A, balance)."

---

## 5. Data clean rooms & privacy

**What a clean room is:** an environment where two parties (Walmart + a brand/agency/publisher) combine data for **approved aggregate analyses** without either seeing the other's row-level data.
**Industry reference points:** Amazon Marketing Cloud (AMC, the main competitor reference), Google Ads Data Hub, AWS Clean Rooms, Snowflake Data Clean Rooms, LiveRamp (Habu), InfoSum. Walmart's own data-collaboration products include Walmart Luminate (verify current naming/positioning).

**Controls (know these mechanisms):**
| Mechanism | What it does |
|---|---|
| **Aggregation thresholds** | Suppress any output cell with < k users (e.g. k=50–100) |
| **Query allow-listing / templates** | Only pre-approved analysis types (lift, overlap, reach/frequency, path-to-purchase) |
| **Differential privacy** | Add calibrated noise (Laplace/Gaussian) to outputs; track an **ε privacy budget** per partner/time; prevents differencing attacks |
| **Differencing-attack defense** | Repeated similar queries can isolate individuals → DP + query auditing + min-overlap rules |
| **Private Set Intersection (PSI)** | Match hashed identifiers (email/phone) without revealing non-matches |
| **Secure MPC / TEEs (confidential computing)** | Compute on encrypted data / in hardware enclaves |
| **Hashing + salting, tokenization, data minimization, retention TTLs** | Basics |
| **Consent & opt-out** (CCPA/CPRA, state laws) | Respect at identity-graph level, propagate deletions |

**Measurement in a clean room:** advertiser brings CRM / first-party sales (e.g. sales on other retailers or DTC), Walmart brings exposures → **cross-retailer lift**, overlap, reach & frequency, new-to-brand. Partner (e.g. Vizio ACR exposure, Spotify) brings exposure logs → matched to Walmart sales.

**Design tradeoff to articulate:** privacy noise vs. measurement precision. Small campaigns + DP noise + thresholds can kill signal, so design analyses at the right aggregation (campaign-level lift, not per-day per-SKU), and allocate ε budget to the queries that matter.

---

## 6. Real-time + offline data platform

### 6.1 Reference architecture
```
Ad servers / auction logs / ghost-bid logs ─┐
Click & impression beacons (IVT signals) ───┤──► Kafka (partitioned by identity/campaign; schema registry; data contracts)
Online orders, store POS, returns ──────────┤
Partner feeds (Vizio, DSP, Spotify, vendors)┘        │
                                                     ├─► Stream processing (Flink / Spark Structured Streaming / Beam-Dataflow)
                                                     │     • dedupe, IVT filtering, identity lookup
                                                     │     • short-window attribution (e.g. same-session/24h)
                                                     │     • real-time aggregates → pacing/bidding feedback + live dashboards
                                                     │     • event-time + watermarks; exactly-once sinks
                                                     │
                                                     └─► Lakehouse (raw immutable, partitioned by event date; Iceberg/Delta/BigQuery)
                                                           • batch attribution (full 14–30 day windows), incrementality estimation
                                                           • restatements (returns, IVT, identity updates) → versioned outputs
                                                           • reconciliation job: real-time vs batch diffs, alert if > threshold
                                                     ▼
                                     Metrics layer (single definitions) → OLAP serving (Druid/Pinot/ClickHouse/BigQuery BI Engine)
                                     → Advertiser UI · Reporting API · Billing · Clean room · GenAI reporting
```

### 6.2 Concepts to be fluent in
- **Event time vs. processing time; watermarks; allowed lateness**; what happens to events after the watermark (side-output → batch correction).
- **Exactly-once**: Kafka transactions + Flink two-phase-commit sinks, or **idempotent writes keyed by event ID** (simpler, often better). Clicks billed twice = money and trust lost.
- **Dedupe**: event IDs + bloom filters / keyed state with TTL.
- **Stateful stream joins**: interval joins (click within N hours before order); state size = rate × window, so a long window needs an external KV index.
- **Lambda vs. Kappa**: Lambda = streaming + batch with reconciliation (common for billing-grade numbers); Kappa = single streaming path with replay. **My answer: real-time path for speed, batch path as source of truth for billing and accredited metrics, with automated reconciliation.** That's the honest, auditable choice.
- **Backfills & replay**: immutable raw log + deterministic jobs → recompute any day.
- **Schema evolution & data contracts** with producers (ad server team, POS, partners).
- **Back-pressure, hot partitions** (a mega-advertiser on Black Friday), autoscaling.
- **Data quality**: freshness SLAs, completeness (row counts vs. source), anomaly detection on metrics (sudden drop in attributed sales = pipeline bug or real?).

### 6.3 Back-of-envelope (say it out loud)
- Suppose ~**10B ad events/day** (impressions+clicks across surfaces; use as an assumption) → ~115K events/s average, **~3–5× peak** → ~500K/s. At ~500 bytes/event that's ~5 TB/day raw.
- Kafka: ~100s of partitions; Flink: tens to hundreds of task slots; 14-day click state: if ~300M clicks/day × 14 × ~100 B ≈ **~420 GB** of state, so use RocksDB state backend or an external KV.
- Reporting: advertisers × campaigns × days × dimensions → pre-aggregate cubes; p95 dashboard query < 1–2 s.

---

## 7. Reporting serving & accreditation
- **Metrics layer / semantic layer**: one definition of "attributed sales," "ROAS," "new-to-brand," versioned and documented. All consumers (UI, API, invoices, GenAI) query through it.
- **OLAP**: Druid/Pinot for low-latency slice-and-dice with rollups; BigQuery/Snowflake for ad hoc; cache common queries.
- **Multi-tenancy**: row-level security by advertiser/agency; agency sees many advertisers.
- **MRC-style auditability**: documented methodology, IVT filtering (GIVT/SIVT), change management (every metric-logic change reviewed, versioned, and backtested), reproducibility (recompute any historical report), data lineage.
- **Correctness testing**: golden datasets with known expected outputs for attribution/lift logic; shadow runs of new logic vs. old with diff reports before switching; invariants (attributed sales ≤ total sales; sum of channel credits = total under MTA).

---

## 8. GenAI-powered reporting
- **Use cases**: end-of-campaign summaries, "why did ROAS drop," path-to-conversion explanations, natural-language Q&A over the advertiser's data, recommendations linked to Marty.
- **Architecture**: LLM → **semantic-layer tools** (`get_metric(metric, dims, filters, date_range)`), not free-form SQL on raw tables (safer, consistent definitions, tenant-scoped). Text-to-SQL only against curated views, with query validation and cost limits.
- **Grounding**: every number in the narrative must come from a tool result. A post-generation verifier checks that the numbers match. Include confidence intervals for lift and don't let the LLM overstate significance ("not statistically significant" must survive summarization).
- **Driver analysis**: deterministic decomposition (impressions × CTR × CVR × AOV; mix/rate decomposition; contribution of SKUs/placements) computed by code, narrated by the LLM.
- **Evals**: golden Q→answer sets per metric, numeric exact-match, faithfulness judge calibrated vs. humans, "statistical honesty" checks, latency, cost.
- **Your angle:** you know where evaluation metrics get gamed and how to keep held-out human-validated sets.

---

## 9. Partner integrations
- Types: **off-site exposure partners** (DSP inventory, CTV/Vizio ACR, audio/Spotify, social), **measurement vendors** (third-party verification, iSpot-like TV measurement), **advertiser data** (clean room uploads), **agency APIs** (reporting API).
- Engineering: standardized ingestion SDK/API, **data contracts** (schema, SLA, freshness, completeness), identity mapping (hashed IDs, PSI), **reconciliation** (partner-reported impressions vs. ours; acceptable discrepancy thresholds, typically < ~10%), sandbox + certification process for new partners, observability per partner.
- Governance: legal/privacy review per data flow, purpose limitation, retention.
- **0→1 tip**: build the first two integrations by hand, then extract the platform. Don't design the generic framework before you've seen two real partners.

---

## 10. ML inside the measurement platform (where your ML depth shows)
1. **IVT / click-fraud detection**: anomaly + supervised models on click patterns, device signals; must be explainable for accreditation.
2. **Identity resolution**: probabilistic household/device matching (features: IP, timing, co-location); a graph problem; precision over recall for measurement.
3. **Conversion nowcasting**: predict final attributed sales for recent days given delay distributions (like delayed-feedback modeling), so dashboards and bidding get timely numbers. *Your Kalman-filter / state-estimation background fits naturally here.*
4. **Uplift / heterogeneous treatment effects** for modeled incrementality (T/X-learners, causal forests, DML), calibrated to RCTs.
5. **MMM** with Bayesian priors from experiments, for cross-channel budget planning.
6. **Anomaly detection on metrics** (pipeline breaks vs. real business shifts), seasonality-aware.
7. **GenAI** for insights (above).

---

## 11. System design prompts for this role (practice these 3, 40 min each)

### Design A — "Build our measurement platform from 0 to 1"
1. **Clarify**: which channels first (Sponsored Search on-site); consumers (advertisers UI/API, billing, bidding, science); SLAs (real-time ≤ 15 min, final ≤ 48–72 h); accreditation needs.
2. **Principles**: one metrics layer; immutable raw logs; batch = source of truth, streaming = fast estimate; privacy by design; experiment assignment as a platform primitive.
3. **Components**: event ingestion + data contracts → identity service → attribution engine (configurable rules, versioned) → **experimentation service** (assignment/hashing, holdout registry, ghost-bid logging spec in ad server, exposure logging) → **lift estimation library** (ITT, ghost-ads ATT, CUPED, sequential, geo/SC) → metrics layer → OLAP + API → clean room → GenAI reporting.
4. **MVP sequencing (90 days → 1 year)**: (1) reliable attribution + reporting for search; (2) always-on holdouts + ghost bids → iROAS for top advertisers; (3) streaming for pacing feedback; (4) off-site/CTV via partner ingestion + household-level/geo experiments; (5) clean room; (6) GenAI insights; (7) modeled incrementality feeding bidding.
5. **Quality**: golden tests, reconciliation, SRM/A-A automation, lineage, change review.
6. **Org**: platform team vs. science vs. product. APIs between them.
7. **Risks**: holdout revenue cost (ghost ads + small holdouts), identity coverage, partner data quality, privacy noise vs. precision.

### Design B — "Real-time attribution for Sponsored Search with 14-day windows"
Flink keyed by identity; recent-touch index (TTL 14 d) in RocksDB/external KV; on order event → look up touches → apply rule → emit attributed sale (idempotent key = order_id × rule_version); late events → side output → batch correction; nightly batch recompute is authoritative; reconciliation alerts at > 0.5% diff; returns as negative adjustments. Discuss state size, hot keys, exactly-once, replays.

### Design C — "Measure incrementality of Vizio CTV campaigns on in-store + online sales"
Household-level randomized holdout using the Vizio device/household graph (ghost-bid logging in the CTV ad decisioning); outcome = Walmart purchases by matched households (online + store); match-rate reporting; CUPED with pre-period category purchases; for non-addressable inventory use **geo experiments** (DMA-level matched markets + synthetic control); report iROAS with intervals; validate with A/A tests; address the agency skepticism with **transparent methodology docs and third-party verification**. Clean-room delivery so the brand can join its own data.

### Bonus prompts
- Design a clean room for cross-retailer lift with an advertiser's CRM data.
- Design GenAI end-of-campaign reports that never misstate a number.
- Design invalid-traffic filtering that satisfies MRC.
- Your real-time and batch ROAS disagree by 8% for a big advertiser. Debug it.
