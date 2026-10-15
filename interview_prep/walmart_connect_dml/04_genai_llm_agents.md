# 04 — GenAI, LLMs & Agents for Ads

The posting puts **custom LLMs, multimodal generative models, RAG, and autonomous multi-agent systems** at the top. Walmart Connect has shipped **Marty** (an advertiser agent), the **Automated Creative Generator**, **GenAI campaign insights**, and **ads inside Sparky**. Expect at least one deep question here.

---

## 1. Where GenAI fits in Walmart Connect (your map)

| Use case | Who benefits | Tech | Key risk |
|---|---|---|---|
| **Marty: advertiser agent** (campaign setup, keyword suggestions, bid advice, "why did my ROAS drop?") | Advertisers, especially the long tail of small sellers who lack agencies | LLM + tools (campaign API, reporting DB) + RAG over help docs/policies | **Money-moving actions** (budget/bid changes) need confirmation, limits, audit logs |
| **Creative generation** (backgrounds, lifestyle images, headlines, video cut-downs) | Advertisers (80% faster production reported) | Diffusion (inpainting/outpainting around product cutouts), LLM copywriting, brand-kit conditioning | **Product fidelity** (no hallucinated packaging/size), brand safety, claims compliance |
| **Campaign insights / reporting narratives** | Advertisers, account managers | Text-to-SQL / semantic-layer + LLM summarization | Numeric hallucination; must ground every number in a query result |
| **Ads in Sparky** (conversational shopping) | Shoppers + advertisers | LLM response + sponsored product insertion; relevance + disclosure | Trust: clearly labeled, relevant, doesn't distort the answer |
| **Query understanding / relevance labeling** | Ranking | LLM as labeler → distilled into a small relevance model | Label noise, cost; calibrate vs. human raters |
| **Catalog enrichment** | Retrieval/targeting | LLM/VLM extracts attributes from images + titles | Attribute errors propagate into targeting |
| **Keyword/audience generation** | Advertisers | LLM proposes, relevance model + historical data verifies | Irrelevant expansions waste spend |
| **Ad policy review** | Trust & safety | Multimodal classifier + LLM reviewer + human escalation | False negatives on regulated categories |

> **Distinguished framing:** "GenAI in ads has two jobs. It lowers the cost of being an advertiser: creative, setup, optimization, which grows the long tail of the marketplace. And it creates new inventory: conversational surfaces like Sparky. Both need the same platform: a model gateway, eval harness, grounding layer, and guardrails. I'd build that once and let product teams compose on it."

---

## 2. LLM training & adaptation ladder (know when to use which)

1. **Prompting + few-shot**: fastest. Use frontier API or a hosted open model.
2. **RAG**: when knowledge changes or is proprietary (campaign data, policies). No training.
3. **Fine-tuning (SFT)**: when you need format/style/tool-use behavior or domain jargon consistently. **LoRA / QLoRA** (low-rank adapters; QLoRA = 4-bit base + LoRA). Multi-LoRA serving lets one base serve many tasks.
4. **Preference optimization**: **RLHF** (reward model + PPO) or **DPO** (direct preference optimization; no reward model; loss on chosen vs. rejected pairs). **GRPO** (group-relative, used for reasoning models). *Your RL background makes this your strongest LLM topic, so go deep if asked.*
5. **Continued pretraining** on domain corpus (catalog, ad copy, query logs). Expensive; justify with evals.
6. **Distillation** into small models (7B → 1–3B or smaller) for latency/cost. *Your edge-distillation experience transfers directly.*

**Rule of thumb you can state:** "Prompt → RAG → SFT → preference tuning → distill. Move right only when evals show a gap the cheaper step can't close."

### DPO in one line (in case they ask)
`L = −log σ( β·[ log π(y_w|x)/π_ref(y_w|x) − log π(y_l|x)/π_ref(y_l|x) ] )`. It increases the margin of the preferred over the rejected response relative to a frozen reference. It's implicitly a KL-regularized reward maximization.

### LoRA in one line
`W = W₀ + (α/r)·B·A`, A ∈ R^{r×d}, B ∈ R^{d×r}, r ≪ d; only A, B trained. ~0.1–1% of params.

---

## 3. RAG done properly

```
User question ─► query rewrite (LLM) ─► hybrid retrieval: BM25 + dense (bi-encoder) ─► top 50
             ─► re-rank (cross-encoder) ─► top 5–8 chunks ─► prompt with citations ─► LLM ─► answer + cited sources
             ─► post-check: groundedness / faithfulness classifier; refuse if unsupported
```
- **Chunking**: semantic/section-aware, 200–800 tokens, overlap; keep metadata (doc type, date, advertiser scope).
- **Access control at retrieval time**: an advertiser must only retrieve *their own* campaign data. Filter by tenant ID **inside the retriever**, never trust the LLM to filter. **This is a security point that impresses interviewers.**
- **Structured data ≠ RAG**: for "what was my ROAS last week," use **tool calling into a SQL/semantic layer**, not vector search. Numbers come from queries, words from the LLM.
- **Eval RAG**: retrieval recall@k on labeled Q→doc, answer faithfulness (LLM-judge + spot human checks), answer correctness on golden set, citation precision.

---

## 4. Agents and multi-agent systems

**ReAct**: interleave *Thought → Action (tool call) → Observation* until done. **Chain-of-Thought** for reasoning. **Plan-and-execute**: planner LLM makes a plan, executor runs tools, re-plans on failure.

**Multi-agent pattern for an advertiser assistant (Marty-like):**
```
             ┌──────────── Orchestrator / router (intent classification, small fast model)
             │
  ┌──────────┼───────────────┬───────────────────┬──────────────────┐
  Campaign    Performance       Creative            Policy/Help
  agent       analyst agent     agent               RAG agent
  (create/    (text-to-SQL on   (calls image/       (docs, FAQs,
  edit via    reporting store,  copy generators)    billing rules)
  API tools)  explains drivers)
  │
  └─► Guardrail layer: schema-validated tool args, spend-change limits, dry-run diff, explicit
      human confirmation for any money-moving action, audit log, rollback
```
- **Tools** are typed function schemas (JSON Schema). Validate args server-side.
- **State/memory**: conversation state + advertiser context (account, campaigns) loaded deterministically, not "remembered" by the LLM.
- **Failure modes**: tool loops, wrong tool, hallucinated IDs, partial execution. Mitigations: step limits, idempotent tools, transactional "propose → confirm → apply."
- **Frameworks**: LangChain/LangGraph (graph-based agent state machines), LlamaIndex (RAG/data connectors), plus MCP for tool interoperability. Say you'd use them for velocity but keep the **core control loop owned in-house** for reliability and observability.

**Autonomy levels** (good Distinguished talking point):
L0 answer questions → L1 recommend actions → L2 act with confirmation → L3 act within guardrails (e.g. ±10% bid changes daily) → L4 fully autonomous campaign management. Move up levels only as eval + online metrics justify it. **Autobidding is effectively L4 for one narrow action already**, so the agent should *call* the bidding system, not replace it.

---

## 5. Evals: the most underrated topic, so bring it up yourself

- **Offline golden sets** per intent (500–5K examples), versioned; include adversarial and edge cases.
- **Task success metrics**: for agent, "campaign created correctly" (verify by API state), not "response sounded good."
- **LLM-as-judge**: rubric-based, pairwise preference; **calibrate judge against human labels** (agreement rate, Cohen's κ) and watch for position/verbosity bias.
- **Online**: A/B with business metrics (advertiser adoption, campaigns launched, spend retention, ROAS of campaigns created via agent vs. manual, support tickets deflected).
- **Regression gates in CI**: every prompt/model change runs the eval suite; block on drop.
- **Your hook:** "I published a reference-free quality metric for generated video, and a negative result when using it as a training loss: optimizing the metric directly let the model game it. That's Goodhart's law, and it's exactly the risk with LLM-as-judge reward models. You need held-out human-validated evals the model never trains on."

---

## 6. Generative creative (your home turf: own this)

**Pipeline for product-faithful ad creative:**
1. **Product segmentation** (SAM-style) → exact product cutout (pixels never regenerated).
2. **Background generation**: diffusion **inpainting/outpainting** conditioned on text prompt + brand kit (colors, style) via ControlNet/IP-Adapter-style conditioning, with the product layer **locked**.
3. **Harmonization**: relighting/shadows so product looks naturally placed. **Your spherical-harmonics lighting estimation + relighting work is directly applicable.**
4. **Copy**: LLM headline/description, constrained to catalog facts (grounded in product attributes; no claims not in the catalog).
5. **QA gates**: product-fidelity check (embedding similarity of product region vs. source; OCR on packaging text unchanged), brand-safety classifier, aesthetic/quality score, policy check.
6. **Optimization loop**: generate N variants → creative-level pCTR model (or bandit) selects → learns which styles work per category.

> **Say it like this:** "Creative generation is identity-preserving synthesis where the identity is the SKU. In my face-synthesis work the hard constraint was 'don't change who this is'. Here it's 'don't change what this product is'. I'd lock the product pixels, generate around them, relight to match, and gate every output with a fidelity check before it can serve."

---

## 7. Serving LLMs at scale (cost is the Distinguished concern)

- **Inference engines**: vLLM / TensorRT-LLM / SGLang: **continuous batching**, **PagedAttention** (KV-cache paging), prefix caching (shared system prompts!).
- **Speculative decoding** (draft model proposes, big model verifies): 2–3× speedup.
- **Quantization**: int8/fp8 weights, int4 (AWQ/GPTQ) for smaller models. *Your quantization expertise applies.*
- **Model routing / cascades**: small model handles 80% of requests; escalate hard ones to a large model. Classifier or confidence-based router.
- **Caching**: semantic cache for repeated questions (97% of Marty queries reportedly unique, so prefix caching matters more than response caching).
- **Latency budgets**: chat ~1–2 s time-to-first-token acceptable; **ads in search ranking path must be ms**, so LLMs there are *offline* (precompute embeddings, labels, attributes) or distilled.
- **Cost math example**: 10M agent turns/month × 3K tokens × $X per 1M tokens. Show you think in $/query and that the cascade cuts it 3–5×.

---

## 8. Responsible AI & governance checklist
- PII handling: shopper data never in prompts to external APIs. Use self-hosted models or approved enterprise endpoints.
- Tenant isolation in retrieval and tools.
- Disclosure: sponsored content in Sparky clearly labeled. (FTC endorsement guidelines.)
- Prompt-injection defense: tool outputs and retrieved docs are untrusted. Don't let retrieved text issue tool calls without validation.
- Red-teaming, abuse monitoring, incident response, model cards.

---

## 9. If you have 2–3 hours this weekend: build a mini-demo (optional but powerful)
"**Mini-Marty**": Python + any LLM API + SQLite of fake campaign data.
- Tools: `get_campaign_metrics(campaign_id, date_range)`, `propose_bid_change(campaign_id, pct)` (returns a diff, doesn't apply).
- RAG over 10 markdown "help docs."
- 20-question eval set with expected tool calls.
Then on Monday you can say "I built a small advertiser agent last weekend to pressure-test the guardrail design, and the interesting failure was X." *Only do this after 02/03/05 are solid.*
