# 09 — Day-of Cheat Sheet (Monday, read once before 3:30 PM)

## Your 3 headline proofs
1. **Beat Google → shipped as default** reprojection on Galaxy XR.
2. **One fused multimodal model beat per-sensor pipelines** (Golf Mode AI).
3. **Research depth:** 7 papers (incl. RL as diffusion), 5 patents, SIGGRAPH/TOG submission.

## Your 4 bridges to ads
| Yours | Theirs |
|---|---|
| RL / constrained control | **Autobidding & pacing** (bid = value/λ) |
| Contrastive learning, distillation | **Two-tower retrieval; LLM teacher → fast relevance student** |
| Identity-preserving synthesis, SH relighting, consistency models | **Product-faithful creative generation** |
| ms-budget on-device inference, quantization, JVM/JIT | **100K-QPS serving, LLM serving cost** |

## Formulas
- eCPM = bid × pCTR × 1000
- GSP price_i = bid_{i+1}·pCTR_{i+1} / pCTR_i (≥ reserve)
- Downsampling fix: p = p'/(p' + (1−p')/w)
- Bid (budget only) = v/λ · with ROAS T: v(1+μ)/(λ+μT)
- Dual update: λ ← λ + η(spend − target_spend)
- CUPED: Y − θ(X − X̄), θ = cov(X,Y)/var(X)
- ROAS = sales/spend · iROAS = incremental sales/spend · ACoS = 1/ROAS
- NE = logloss / H(base CTR)

## Funnel + latency
QU 5 → Retrieval 10 (keyword + two-tower ANN + filters: stock, budget, policy) → Pre-rank 5 → Rank 12 (MMoE/ESMM, target attention, DCN, position tower) → Auction 3 (eCPM, reserve, relevance floor, whole-page) → log features at serve time.

## Must-say concepts (tick them off mentally)
☐ calibration per segment · ☐ ESMM / sample-selection bias · ☐ delayed feedback · ☐ position bias · ☐ relevance floor · ☐ whole-page optimization · ☐ budget-split experiments · ☐ ghost ads / iROAS · ☐ long-term holdout · ☐ train/serve skew (log-and-wait) · ☐ LLM eval harness · ☐ tenant isolation in RAG · ☐ human-confirm for money-moving agent actions · ☐ cascade/distill for cost

## Vision in 5 bullets (for "what would you do here")
1. **Shopper foundation model**: one sequence model across search ads, display, CTV, Sparky.
2. **Optimize for incrementality**, not attributed ROAS. Closed-loop data makes it possible.
3. **GenAI lowers the advertiser's cost-to-play** (Marty + creative), which grows the long-tail marketplace.
4. **Shared platforms**: features, evals, LLM gateway, guardrails, calibration service.
5. **Whole-page optimization** balancing shopper GMV and ad revenue, guarded by long-term holdouts.

## When stuck
"I haven't operated that part of an ad stack, so let me reason from first principles." Then cover incentives → data → model → latency → metric.

## Questions to ask THEM (pick 3–4)
1. "What's the biggest technical bet Connect is making in the next 18 months, and where does this role sit in it?"
2. "How do you currently measure incrementality, and how much does it feed back into bidding and ranking?"
3. "How unified is the modeling stack across Sponsored Search, display/DSP, and Vizio CTV today?"
4. "Where is Marty on the autonomy curve? Does it take actions for advertisers yet, and how are those evaluated?"
5. "What does success look like for this role at 12 months?"
6. "How do ads and organic search teams coordinate on ad load and relevance?"
7. "What's the split between GenAI platform work and core ads ML in this role?"

## Logistics
- Join 5 min early. Camera at eye level, water, paper + pen to draw diagrams (or a shared whiteboard tool).
- For design questions, **ask 2–3 clarifying questions first**, state metrics, then draw.
- Watch the clock: leave 5 minutes for "risks + roadmap" at the end of every design.
- Close: "I'm excited about this. The overlap between what Connect needs and what I've built is unusually high, and I'd love to bring it here."
