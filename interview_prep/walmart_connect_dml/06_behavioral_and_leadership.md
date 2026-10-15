# 06 — Behavioral, Leadership & Your Story

At Distinguished level the behavioral rounds test **scope, judgment, influence without authority, technical vision, and raising others**. Walmart's stated values: **Respect for the Individual, Act with Integrity, Serve the Customer, Strive for Excellence**. Walmart also talks about being "people-led, tech-powered." Weave in "serve the customer": for Connect that means **both** shoppers and advertisers.

---

## 1. Your 90-second pitch ("Tell me about yourself")

> "I'm a Principal Engineer at Samsung with 25 years building production systems and about a decade shipping deep learning. Three things define my work.
>
> **First, I build models from scratch and ship them under hard constraints:** generative models for inpainting and face synthesis, multimodal fusion on AR glasses, all running in millisecond budgets on constrained hardware, using distillation and quantization.
>
> **Second, I win on measurable outcomes:** my motion-vector SpaceWarp beat Google's solution and became the default reprojection on Galaxy XR. On our golf AI glasses I argued that one fused model would beat separate per-sensor pipelines, and the data proved it.
>
> **Third, research depth:** seven publications, including work recasting reinforcement learning as diffusion, five patents, and a SIGGRAPH submission.
>
> Why Walmart Connect: retail media is where ML turns most directly into dollars, and Walmart has something nobody else has, closed-loop data from impression to basket, online and in-store. The problems you're hiring for (calibrated prediction at scale, bidding as constrained optimization, multimodal creative generation, LLM agents for advertisers) line up closely with what I've done. Bidding is a control problem, creative generation is identity-preserving synthesis, and distillation is how you serve LLM quality at ranking latency. I've spent the last few weeks going deep on the ads side specifically."

Practice until it's **85–95 seconds**, natural, not memorized-sounding.

---

## 2. "Why ads? You've been in XR/graphics." (They WILL ask)

> "Three reasons. One, the feedback loop: in XR, it takes years from model to market. In ads, a better calibrated model shows up in revenue and advertiser ROI within days. I like being measured. Two, the problems are deep and they suit my background: auctions and pacing are optimization and control, I've done RL research, and ranking is representation learning, which is what I do. Three, Walmart specifically: closed-loop measurement and incrementality make it possible to optimize what actually matters, incremental sales, rather than proxies. I'm honest that I haven't operated an ad stack, so I've been studying it seriously. Things like calibration under negative downsampling, ESMM for sample-selection bias, and budget-split experiments. But the hard part of this job at Distinguished level is technical judgment across a large system, and that transfers."

---

## 3. STAR stories: build each one, then rehearse it out loud

Format: **S**ituation (1 line) · **T**ask (1 line) · **A**ction (3–5 lines, *your* decisions and tradeoffs) · **R**esult (numbers) · **Ads bridge** (1 line). Fill the `[ ]` with real numbers you remember.

### Story A — Beating Google: Motion-Vector SpaceWarp → default on Galaxy XR
- **S:** Galaxy XR needed frame synthesis to halve GPU load; Google had a competing solution in the platform.
- **T:** Deliver a reprojection that beat it on quality and performance.
- **A:** Designed motion-vector + depth reprojection; [key technical choice, e.g. how you handled disocclusion/stretch]; built the evaluation harness to compare head-to-head [metrics]; worked across [teams: runtime, compositor, Google partners].
- **R:** Beat Google's solution on [perf / accuracy numbers]; **shipped as the default** reprojection path on Galaxy XR.
- **Use for:** "Tell me about your biggest impact," "competing with a strong incumbent," "a decision backed by data."
- **Ads bridge:** "Same playbook I'd use for a new ranker: head-to-head on agreed metrics, decided by data, not by whose team built it."

### Story B — One fused model beats N pipelines (Golf Mode AI)
- **S:** Separate IMU, audio, and video pipelines for hit detection/scoring; each team owned one.
- **T:** Improve accuracy and power on a low-power sensing chip.
- **A:** Proposed a single multimodal model; ran the comparison; designed the glasses/phone/watch streaming architecture; curated first-person data with a filtering pipeline.
- **R:** Measurably higher accuracy than per-sensor pipelines [number]; fully automatic scoring with zero user input.
- **Use for:** "Influencing without authority," "technical vision," "consolidation."
- **Ads bridge:** "Ads has the same fragmentation: separate models for search, display, CTV, and now conversational. The unified shopper model argument is the same argument."

### Story C — Disciplined negative result (temporal metric as a training loss)
- **S:** Built a reference-free video temporal-quality metric; natural idea was to use it as a loss.
- **A:** Tested it rigorously; it got gamed (Goodhart); published the negative result rather than burying it.
- **R:** Saved [team/community] from a dead end; metric still valid as evaluation.
- **Use for:** "A time you were wrong / a failure," "integrity," "scientific rigor."
- **Ads bridge:** "This is why I'm careful with LLM-as-judge reward models and with optimizing attributed ROAS instead of incrementality."

### Story D — Industry influence: proposed OpenXR extension (Dual-Layer SpaceWarp)
- **A:** Identified transparency failure across the industry; designed dual-layer fix; proposed `XR_KHR_composition_layer_transparency`; SIGGRAPH/TOG submission with a collaborator.
- **Use for:** "Influence beyond your team," "setting technical direction for an ecosystem."
- **Ads bridge:** "At Distinguished level I'd expect to set standards across Connect: shared calibration, a shared eval harness, a shared feature platform. That's what the extension does for XR runtimes."

### Story E — Multi-year technical bet: Generative AI for Passthrough Eyes
- **A:** Built the multi-stage pipeline (inpainting, exemplar colorization, identity-preserving synthesis); designed composite losses; managed quality vs. real-time constraints.
- **Use for:** "Ambiguous problem," "long-horizon project," "tradeoffs between quality and latency."
- **Ads bridge:** directly applicable to creative generation with product fidelity.

### Story F — Real-time systems under hard constraints (Boeing Apache JVM / Cisco)
- **A:** Real-time JVM on INTEGRITY RTOS: mapped Java threads to static RTOS threads, implemented priority inheritance, retargeted the JIT.
- **Use for:** "Hardest technical problem," "deep systems debugging," and **to establish systems credibility** for the 100K-QPS discussion.
- **Ads bridge:** "Tail latency is a scheduling problem. I've dealt with it at the level of priority inversion."

### Story G — Conflict / disagreement
Pick a real one (e.g. pushing single-model fusion over per-sensor teams; or a disagreement on shipping vs. quality). Structure: **disagree with data, commit, follow up.** Show respect for the individual.

### Story H — Mentoring / raising the bar
Pick a real example: someone you grew, a review practice you introduced (ablation discipline, replay-verified results), or how you onboarded engineers to ML. Distinguished engineers are judged on **multiplying others**.

### Story I — Retail product search (Bixby Store Assistant)
- **Use for:** "Any retail or e-commerce experience?" Voice → product query → AR navigation, Lidar store mapping, Java backend API.

---

## 4. Distinguished-level questions & how to answer

| Question | What they're testing | Key moves |
|---|---|---|
| "What would you do in your first 90 days?" | Judgment, humility, prioritization | **30:** listen: meet leads of ranking, bidding, measurement, GenAI; read postmortems; study metric definitions; find where calibration/eval is weakest. **60:** pick 1–2 high-leverage technical bets with owners; ship one quick visible win (e.g. calibration monitoring or an eval harness for Marty). **90:** publish a 12–24 month technical strategy reviewed with peers and leadership |
| "What's your technical vision for Walmart Ads AI?" | Vision | (1) **One shopper foundation model** shared across surfaces; (2) **optimize for incrementality**, not attributed ROAS; (3) **GenAI lowers advertiser cost-to-play** (agent + creative) → grows the long-tail marketplace; (4) **shared platform**: feature store, eval harness, LLM gateway, guardrails; (5) **whole-page optimization** balancing shoppers and advertisers |
| "How do you influence teams that don't report to you?" | Influence | Data and prototypes beat slides; write the design doc; find the team whose problem you solve first; make adoption easy (libraries/platforms). Golf + OpenXR stories |
| "Tell me about a technical decision you'd make differently." | Self-awareness | Honest, specific, what you learned |
| "How do you balance research vs. shipping?" | Pragmatism | "Research earns its place by moving a production metric. Every paper I've done is replay-verified, and the SpaceWarp research shipped as the default." |
| "How do you decide build vs. buy (e.g. frontier LLM API vs. self-hosted)?" | Business judgment | Data sensitivity (shopper PII), cost at scale, latency, customization need, vendor lock-in; typically API for prototyping → self-hosted/fine-tuned for high-volume or sensitive paths |
| "How do you handle a launch that increases revenue but hurts shopper metrics?" | Values, Serve the Customer | Don't ship as-is; quantify long-term GMV cost with holdouts; find a variant that keeps revenue but respects guardrail; escalate tradeoff explicitly with data |

---

## 5. Things to avoid
- Over-indexing on XR detail. Keep graphics explanations to one sentence unless asked.
- "We" without "I": say what *you* decided.
- Bluffing ads specifics. Reason from first principles instead.
- Talking about models without metrics, or metrics without dollars/shopper impact.
- Being negative about Samsung. Frame the move as pull toward Walmart, not push.
