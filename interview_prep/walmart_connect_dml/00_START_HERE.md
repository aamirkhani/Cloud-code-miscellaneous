# Walmart Connect — Distinguished ML Engineer: Interview Prep Pack

**Candidate:** Aamer Khani · **Interview:** Monday Oct 19, 2026, 3:30 PM
**Role (most likely posting):** *Distinguished, Software Engineer – AI/ML Engineer – Walmart Connect* (Sunnyvale, req R-2458666)

## What the role asks for (from the public postings)

- Own the **engineering and ML strategy** for Walmart's ad business: **ad targeting, personalization, bidding optimization, attribution modeling, campaign analytics**.
- Own **custom LLMs, multimodal generative models, RAG pipelines, autonomous multi-agent systems**. Walmart Connect ships an advertiser agent ("Marty"), an Automated Creative Generator, GenAI campaign insights, and ads inside the Sparky shopping assistant.
- Set the **long-term AI engineering roadmap** for Walmart Ads.
- Bar: 12+ yrs ML engineering, 5+ at Principal/Staff/Distinguished; **hands-on LLM training/fine-tuning/deployment**; LangChain/LlamaIndex/ReAct/CoT; **low-latency distributed systems at 100K+ QPS**; Python/Go/Rust/C++ expert; MS/PhD.
- Preferred: **ad tech / retail media / e-commerce** experience; publications and patents.

## Files in this pack (read in this order)

| # | File | Purpose | Time |
|---|------|---------|------|
| 01 | `01_gap_analysis.md` | Where you're strong, where you're exposed, how to close each gap | 30 min |
| 02 | `02_ads_ml_fundamentals.md` | Retail media, auctions, CTR/CVR, calibration, bidding, pacing, attribution | 3–4 h |
| 03 | `03_recsys_ranking_at_scale.md` | Retrieval → ranking → re-ranking, model families, features, serving at 100K QPS | 3 h |
| 04 | `04_genai_llm_agents.md` | LLM fine-tuning, RAG, agents, evals, LLM serving: the GenAI half of the role | 3 h |
| 05 | `05_system_design_walkthroughs.md` | 6 full ML system designs, written the way you should say them | 4 h |
| 06 | `06_behavioral_and_leadership.md` | Distinguished-level stories built from your résumé, with the ads translation | 2 h |
| 07 | `07_question_bank.md` | 120+ likely questions with model answers | 3 h+ |
| 08 | `08_coding_drills.py` | Runnable ads-flavored ML coding drills with solutions and tests | 2 h |
| 09 | `09_day_of_cheat_sheet.md` | One-page review for Monday morning, plus questions to ask them | 20 min |

## 3.5-day schedule (today is Thu Oct 15)

**Thu evening (3 h)**: read 01, then 02 §1–4 (business model, auctions, metrics). Write your 90-second pitch (template in 06).

**Fri (7–8 h)**
- AM: finish 02 (calibration, bidding, pacing, attribution, incrementality).
- PM: 03 in full. Draw the funnel diagram from memory 3 times.
- Evening: run `python3 08_coding_drills.py` and re-implement 3 drills without looking.

**Sat (7–8 h)**
- AM: 04 (GenAI/LLM/agents). This is the half of the role that's growing fastest, so expect at least one question here.
- PM: 05 designs #1 (Sponsored Search ranking) and #2 (Autobidding). **Say them out loud** with a 45-minute timer.
- Evening: 06. Rehearse 6 stories out loud and record yourself.

**Sun (6–7 h)**
- AM: 05 designs #3–#6.
- PM: 07 question bank: cover the answers and answer aloud. Mark any you stumble on and redo them.
- Evening: one full mock: 5 min intro → 40 min design → 15 min behavioral → 5 min your questions.

**Mon (before 3:30 PM)**: 09 cheat sheet only. Light review. No new material after 1 PM. Test your camera and mic and have water ready.

## The single most important framing

> "I'm not an ads person who learned ML. I'm a deep-learning systems builder who has shipped models under hard latency budgets, trained multimodal and generative models from scratch, and done RL research, which is the math under autobidding. Ads is where those skills pay off most directly in dollars, and I've done the homework on the domain."

Then **show** the homework: use the vocabulary fluently (eCPM, pCTR calibration, second-price, pacing, iROAS, incrementality, closed-loop attribution). Fluency is what makes a domain switch believable.
