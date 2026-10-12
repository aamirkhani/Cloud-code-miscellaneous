# Job search audit and new strategy (Oct 12, 2026)

**Source:** all of Gmail (aamer.khani.1@gmail.com), including Hotmail mail forwarded into it.
Window: Jul 1 – Oct 12, 2026; there is no job-search mail before July.
Hotmail forwarding is known to drop mail, so **every count below is a minimum**. That especially
applies to replies you sent from Hotmail, which never reach Gmail.

**How it was collected:** 9 date-window passes over ATS senders and application keywords, with
every page followed to the end. Then 7 different "gap" queries: Spam/Trash, Sent, human recruiters,
body text, LinkedIn, and the Promotions/Social tabs. The gap queries found about 580 more messages,
which are merged in. Threads with more than 5 messages were read in full.
Result: 5,328 messages → **~2,000 distinct applications (company + role) at ~875 companies.**
Full list: `master_applications.tsv`.

---

## 1. What is actually happening

| Month | New applications | Rejections received | New companies that interviewed you | Hit rate |
|---|---|---|---|---|
| Jul | 349 | 41 | 17 | 4.9% |
| Aug | 204 | 86 | 18 | **8.8%** |
| Sep | 777 | 330 | 31 | 4.0% |
| Oct (12 days) | 241 | 127 | 6 | 2.5% |

**Finding 1: interviews haven't dried up, but volume is diluting them.** You keep landing roughly
7–10 new companies a week. Sending 3–4× more applications in September did not produce 3–4× more
interviews: the hit rate halved and rejections quadrupled. The response that feels like it is
"fading out" is mostly the rejection pile growing faster than the interviews.
(October is still early. Some of those applications will produce interviews later.)

**Finding 2: the biggest leak is interview → offer, not resume → interview.**
72 companies screened or interviewed you since July: GM, Waymo, Apple (twice), Qualcomm, Lucid,
Amazon, Google, Samsung Semiconductor, Anduril, Snap, Figure, Niantic, ByteDance, Synopsys,
Tesla, and others. I can't see a single offer. At least 10 ended in a rejection **for the same role
right after the interview**: Waymo, Apple, Niantic, Bedrock, Latitude, Samsung Semi, Intuitive,
Synthesia, Metropolis, and C3 AI. Getting 1 or 2 of those over the line is worth more than
1,000 more applications.

**Finding 3: you apply to the same companies far too many times.**
Apple 110, Verkada 50, NVIDIA 48, Snap 46, **Anthropic 43**, Qualcomm 36, EA 29, Discord 29,
Synopsys 23, XPENG 22, Reddit 20, Lockheed 19. A recruiter sees all of these together on one
candidate profile. Forty-plus applications reads as untargeted, and it usually gets the profile
quietly deprioritized for *every* role there, including the one you fit.

**Finding 4: your niche converts about 2× better than generic ML.**

| Role type (by title) | Applications | Interviews | Rate |
|---|---|---|---|
| CV / 3D / graphics / XR / perception / robotics | 177 | 17 | **9.6%** |
| Staff | 289 | 19 | 6.6% |
| Director / Head / Lead / Architect | 201 | 13 | 6.5% |
| Generic ML / AI | 756 | 36 | 4.8% |
| Senior | 467 | 20 | 4.3% |
| Principal | 162 | 6 | 3.7% |
| Research Scientist / Research Engineer | 247 | 6 | 2.4% |
| Off-target (front-end, .NET, full-stack, SRE, electrical, data eng.) | 101 | 1 | **1.0%** |

**Finding 5: how you apply matters a lot.**

| Channel | Applications | Interviews | Rate |
|---|---|---|---|
| Direct emails / humans / recruiters | 620 | 96 | **15%** (includes recruiter-led threads) |
| Ashby | 184 | 10 | 5.4% |
| Workable | 55 | 4 | 7% |
| Greenhouse | 880 | 16 | 1.8% |
| LinkedIn Easy Apply | 108 | 2 | 1.9% |
| Workday | 133 | 1 | 0.8% |
| Gem | 62 | 0 | 0% |

Your strongest leads came through people: Expedition Brands/Bot Auto, Google's recruiter, Apple
Maps, Qualcomm's referral-style outreach, and Tesla's recruiting call. Cold Workday and Greenhouse
applications are close to a lottery at this volume.

---

## 2. Act on these now (open items found in the mail)

"No reply seen" means no reply in Gmail. You may have answered from Hotmail, so please check.

| Company | What's open | Last email |
|---|---|---|
| **Unit8 SA** | Interview **Tue Oct 13, 9:15 AM PT** (6:15 PM GMT+2) | Oct 12 |
| **CrowdStrike** | Recruiter screen Mon Oct 12, 8:00 AM PT. Did it happen? Send a thank-you. | Oct 10 |
| **Google** | Online assessment was due **Oct 12, 2:33 AM PT**. If you missed it, reply to Amanda Duarte today and ask for a new link. | Oct 11 |
| **Logitech** | NDA reminders keep coming after you said you signed. Their system didn't record it, so **re-sign through the link in the Oct 9/11 email** and reply with a screenshot. | Oct 11 |
| **Redwood Materials** | Recruiter Maria Romero: "Are you still interested in rescheduling? Please provide your availability." No reply seen. | Oct 9 |
| **Tesla** | Meeting reminder (Oct 11) after the Daisy Adin recruiting call | Oct 11 |
| **Bot Auto (via Shawna, Expedition Brands)** | You were presented for Staff/Principal Algorithm Engineer, DL/CV. Follow up for interview dates. | Oct 9 |
| **Electronic Arts** | Recruiter chats for Rendering SWE (UFC) and Generative Engine Tools. Follow up. | Oct 7 |
| **Synopsys** | Phone interview, Staff SWE req 18106. Send a thank-you or follow-up. | Oct 5 |
| **Matic** | ~2-hour technical take-home offered. No reply seen. | Sep 29 |
| **Neros** | Perception Lead phone interview Sep 30. Follow up. | Sep 28 |
| **Stanley Black & Decker** | TA manager Nathan Main followed up 3× about a screen (Principal AI Solution Architect). No reply seen. | Sep 14 |
| **Cellanome** | Sr. Staff recruiter Emily Hawkins call. No reply seen. | Sep 15 |
| **Apple Maps** | Staff MLE, Platform Intelligence: interviewed Oct 1. Follow up. | Oct 1 |
| **Voxel, PlusAI, Lucid, Amazon, Uandor** | Multi-round processes with no final answer. Send a polite status check to each. | Sep–Oct |

---

## 3. The new strategy

### A. Shrink the funnel and aim it (from ~60 applications a day to ~10–15 good ones)
1. **One lane, one story:** *ML for real-time 3D / XR / perception*: on-device vision, generative
   imaging, neural rendering, reprojection, robotics perception. This lane converts at 9.6%.
   Generic "ML Engineer, Ads/Search/Platform" roles and research-scientist roles at frontier labs
   convert at 2–5%, so drop them unless there's a referral.
2. **Hard cap: no more than 2 roles per company per 90 days.** Pick the single best-fit role. Never
   apply to front-end, .NET, full-stack, SRE, data engineering, or electrical/hardware roles.
3. **Prefer Staff and "Principal/Staff" over pure Principal titles**, and Lead/Architect roles in your
   lane. A pure Principal title at a big company is 3.7%; Staff is 6.6%. Apply as Staff and
   negotiate the level later.
4. **Target companies (Bay Area / 100 mi) where your exact work is the product:** Meta Reality
   Labs, Apple Vision Products / Maps, Google XR/Android XR, Snap Spectacles (one role only),
   Niantic Spatial, Qualcomm XR, Magic Leap, Varjo, Valve, Pico/ByteDance XR, Samsung Research
   America (as an external hire), NVIDIA Omniverse/graphics research, Unity/Epic, Luma, Pika,
   Runway, World Labs, Figure, 1X, Physical Intelligence, Skild, Zoox, Waymo Sim, Wayve,
   Applied Intuition, Parallel Domain, Bot Auto, Matic, Bedrock, Neros, Anduril (perception).

### B. Get in through people (15% vs ~2%)
1. **Specialist recruiters.** Expedition Brands, Top1Talent, Harnham, and Saragossa already found
   you real leads. Tell 4–6 specialist agencies (XR / CV / autonomy) exactly what you want.
2. **Every week, for 5 target roles:** find the hiring manager or a team engineer on LinkedIn.
   Send a 3-line note with **one** matching paper or video (for example the SpaceWarp-for-transparency
   paper for XR roles, or the disocclusion inpainting paper for reprojection/rendering roles).
   Then ask for a referral.
3. **Ex-Samsung colleagues** who are now at Meta, Google, Apple, or Qualcomm: ask directly for
   referrals. A referral routinely beats 50 cold applications.
4. **Make the publications work for you:** pin the 7 papers and their videos on LinkedIn, and post a
   short video of the SpaceWarp/transparency work. Inbound recruiter interest grows with visible work.

### C. Fix interview → offer (the biggest leak)
1. **Debrief every lost loop.** For Waymo, Apple, Niantic, Samsung Semi, and Bedrock, ask the
   recruiter for feedback. Most will give one line, and that line tells you what to fix.
2. **Practice for the formats that are rejecting you:** ML coding (Waymo sent a prep guide), ML
   system design (on-device CV pipeline, training data → eval → deployment), and a 20-minute
   "deep dive" talk on Motion-vector SpaceWarp. Do 2–3 mock interviews a week (interviewing.io,
   Exponent, or peers).
3. **Behavioral stories for a long single-company career:** prepare 6 STAR stories. Cover shipping
   Galaxy XR SpaceWarp, beating Google's solution, leading without authority, a failure, and why
   you're leaving now.
4. **Salary filter.** "330K net / 430K gross" entered on application forms can screen you out
   automatically at Staff bands. Write "Flexible / market rate for level" (or the posted range) on
   forms, and give numbers only to a recruiter, after the screen.

### D. Fix the Chrome-plugin process
- Feed the plugin `master_applications.tsv` (or a "do not apply" list built from it) and have it
  **refuse to apply when the company already has 2 or more open applications** or rejected you
  in the last 90 days.
- Tell it to **write short, tailored answers** (2–4 sentences, one specific project plus one paper)
  instead of "very very high detail". Very long form answers read as auto-generated.
- Remove secrets and over-sharing from the plugin prompt: both passwords, date of birth, and home
  street address. Date of birth is never needed on an application, and including it invites
  age bias. Also keep EEO answers consistent: the prompt says both "Asian (east)" and "originally
  from Pakistan", which would be South Asian.
- **Change both passwords that were pasted into chats** (the Hotmail password and the job-site
  password), and stop reusing one password across every Workday tenant.

### E. Weekly rhythm
| Day | Activity |
|---|---|
| Mon | Pick 10–15 lane-fit roles (company cap enforced). Apply with a tailored resume. |
| Tue | 5 hiring-manager/engineer notes and 2 referral asks |
| Wed | Mock interview + ML system design practice |
| Thu | Follow up on every open process (table in §2) and contact recruiters |
| Fri | Publish or share one piece of work. Review this week's numbers. |

**Goal for 4 weeks:** about 60 applications, 4–6 new interviews a week, **at least 2 final rounds**.

---

## 4. Files
- `master_applications.tsv`: one row per (company, role) with status, first/last date, inbox, ATS, and event counts.
- `analyze_applications.py`: rebuilds the stats from harvested TSVs.
- `export_outlook_jobs.py`: optional. Run it on your Windows PC to capture Hotmail-only mail
  through Outlook desktop, so the counts stop being a minimum.
- `Hotmail harvest prompt for Chrome extension.md`: optional fallback for the same purpose.
