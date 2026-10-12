"""Export job-application emails from the Outlook desktop app on Windows to a TSV.

Reads the mailbox through the already signed-in Outlook (no password needed), across ALL
folders (Inbox, Junk, Archive, subfolders). Read-only: nothing is moved, marked or deleted.

    pip install pywin32
    python export_outlook_jobs.py            # writes hotmail_export.tsv next to this script
    python export_outlook_jobs.py 2026-05-01 # optional start date

Then commit/upload hotmail_export.tsv and run analyze_applications.py on it plus the Gmail TSVs.
"""
import csv, datetime as dt, os, re, sys
import win32com.client

START = dt.datetime.fromisoformat(sys.argv[1] if len(sys.argv) > 1 else "2026-05-01")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hotmail_export.tsv")

ATS = re.compile(r"greenhouse|myworkday|ashbyhq|lever\.co|gem\.com|icims|smartrecruiters|jobvite|"
                 r"jobs-noreply@linkedin|sapsf|successfactors|workablemail|taleo|eightfold|oraclecloud|"
                 r"rippling|bamboohr|recruitee|dover\.com|wellfound|cybercoders|breezy|avature", re.I)
TEXT = re.compile(r"thank you for applying|thanks for applying|your application|application (received|update)|"
                  r"candidacy|thank you for your interest|interview|online assessment|next steps", re.I)
EVENTS = [("otp", r"security code|verification code|verify your email|one-time"),
          ("interview", r"interview|phone screen|schedule (a|your) (call|time)|availability|speak with you"),
          ("assessment", r"assessment|coding (test|challenge)|hackerrank|codesignal|questionnaire"),
          ("reject", r"unfortunately|not (to )?(move|moving) forward|other candidates|not proceed|"
                     r"no longer (recruiting|available)|has been filled|different direction|decided to pursue"),
          ("viewed", r"application was viewed"),
          ("confirm", r"received your application|application (has been )?received|thank(s| you) for applying|"
                      r"has your application|we('|’)ll review|your application to")]
ME = ("aamerkhani@hotmail.com", "aamer.khani.1@gmail.com")


def sender_of(m):
    try:
        if m.SenderEmailType == "EX":
            return m.Sender.GetExchangeUser().PrimarySmtpAddress
    except Exception:
        pass
    return getattr(m, "SenderEmailAddress", "") or ""


def walk(folder):
    yield folder
    for sub in folder.Folders:
        yield from walk(sub)


def clean(s, n=200):
    return re.sub(r"\s+", " ", s or "").replace("\t", " ")[:n]


ns = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
rows, seen = [], set()
for store in ns.Folders:
    for folder in walk(store):
        try:
            items = folder.Items.Restrict("[ReceivedTime] >= '" + START.strftime("%m/%d/%Y %H:%M %p") + "'")
        except Exception:
            continue
        for m in items:
            if getattr(m, "Class", 0) != 43:  # MailItem only
                continue
            subj, snd = m.Subject or "", sender_of(m)
            body = (m.Body or "")[:1500]
            if not (ATS.search(snd) or TEXT.search(subj) or TEXT.search(body[:400])):
                continue
            if "jobalerts-noreply@linkedin" in snd.lower():
                continue
            mid = getattr(m, "EntryID", "")
            if mid in seen:
                continue
            seen.add(mid)
            text = subj + " " + body
            event = "sent" if snd.lower() in ME else next((e for e, rx in EVENTS if re.search(rx, text, re.I)), "other")
            rows.append({"date": m.ReceivedTime.strftime("%Y-%m-%d"), "msg_id": mid[-24:], "thread_id": clean(getattr(m, "ConversationID", ""), 40),
                         "to_addr": "hotmail", "sender": snd, "company": "", "role": "", "event": event,
                         "note": clean(f"[{folder.Name}] {subj} :: {body[:200]}")})

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, delimiter="\t", fieldnames=list(rows[0].keys()) if rows else ["date"])
    w.writeheader()
    w.writerows(sorted(rows, key=lambda r: r["date"]))
print(f"{len(rows)} job emails written to {OUT}")
