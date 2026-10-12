# Hotmail harvest — paste into the Claude Chrome extension

Gmail forwarding from Hotmail is unreliable, and the Microsoft 365 connector does not work with
free Outlook.com accounts. Your Chrome extension, though, can read Outlook.com in your own
signed-in browser. Paste the prompt below into it while signed in to outlook.live.com.

---

**PROMPT (copy everything below this line):**

You are doing a READ-ONLY audit of my Outlook.com (Hotmail) mailbox. Do not delete, move, reply,
mark, or click any link inside an email. Only search and read the message list.

Goal: a complete list of every job-application email since 2026-05-01.

1. Open https://outlook.live.com/mail/ . In the search box, run each query below **one at a time**.
   For each one, search **All folders** (use the search scope dropdown) so Junk and Archive are included.
   - `from:greenhouse-mail.io`
   - `from:myworkday.com`
   - `from:ashbyhq.com`
   - `from:lever.co`
   - `from:gem.com`
   - `from:successfactors.com OR from:sapsf.com`
   - `from:icims.com OR from:smartrecruiters.com OR from:jobvite.com OR from:workablemail.com`
   - `from:eightfold.ai OR from:oraclecloud.com OR from:taleo.net OR from:rippling.com`
   - `subject:application`
   - `subject:interview`
   - `"thank you for applying"`
   - `"your application"`
   - `"thank you for your interest"`
2. Scroll each result list to the very end (until no more results load). Results are not complete until you reach the end.
3. For every message dated 2026-05-01 or later, record one row (dedupe identical rows across queries):
   `date (YYYY-MM-DD) | sender email | company | job title | event | folder`
   where event is one of: confirm, reject, interview, assessment, otp, recruiter, other.
4. When finished, output the full table as **TSV inside one code block** (header row first) so I can
   copy it, then a line with total rows and counts per event and per folder.
   If the table is too long for one reply, output it in numbered parts and say "PART n of N".

---

When you have the TSV, save it as `reports/Job search/hotmail_export.tsv` in this repo (or paste it
into the Claude session), and the merge script will fold it into the master application list.

**Second reliable source (no email needed):** sign in at https://my.greenhouse.io with
aamerkhani@hotmail.com. MyGreenhouse lists *every* Greenhouse application tied to that email,
with status. LinkedIn → My Jobs → Applied does the same for Easy Apply. Workday has one candidate
portal per company, so check those individually.
