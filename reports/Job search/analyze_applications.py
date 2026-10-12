"""Merge harvested job-application email rows into a master list and print funnel stats.

Usage: python3 analyze_applications.py <tsv files...>
Each TSV: date msg_id thread_id to_addr sender company role event note
A hotmail_export.tsv from the Chrome-extension harvest can be passed too (same columns or
date|sender|company|role|event|folder; missing columns are left blank).
"""
import csv, re, sys
from collections import Counter, defaultdict

COLS = ["date", "msg_id", "thread_id", "to_addr", "sender", "company", "role", "event", "note"]


def norm(s):
    s = (s or "").lower()
    s = re.sub(r"\b(inc|llc|ltd|corp|corporation|co|the|technologies|labs?)\b\.?", "", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def ats(sender):
    s = (sender or "").lower()
    for key, name in [("greenhouse", "Greenhouse"), ("myworkday", "Workday"), ("ashby", "Ashby"),
                      ("lever", "Lever"), ("gem.com", "Gem"), ("linkedin", "LinkedIn"),
                      ("successfactors", "SuccessFactors"), ("sapsf", "SuccessFactors"),
                      ("icims", "iCIMS"), ("smartrecruiters", "SmartRecruiters"),
                      ("workable", "Workable"), ("eightfold", "Eightfold"), ("jobvite", "Jobvite")]:
        if key in s:
            return name
    return "direct/other"


rows = []
for path in sys.argv[1:]:
    with open(path, newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            r = {c: (r.get(c) or "").strip() for c in COLS}
            if r["date"]:
                rows.append(r)

# dedupe by message id (or by date+sender+role when id is missing)
seen, uniq = set(), []
for r in rows:
    k = r["msg_id"] or (r["date"], r["sender"], norm(r["company"]), norm(r["role"]), r["event"])
    if k not in seen:
        seen.add(k)
        uniq.append(r)
rows = uniq

# one application = (company, role); role-less events attach to the company
apps = defaultdict(lambda: {"events": Counter(), "first": "9999", "last": "0000", "to": set(), "ats": set(), "company": "", "role": ""})
for r in rows:
    if r["event"] in ("sent", "other", "otp"):
        continue
    key = (norm(r["company"]), norm(r["role"]))
    a = apps[key]
    a["company"] = a["company"] or r["company"]
    a["role"] = a["role"] or r["role"]
    a["events"][r["event"]] += 1
    a["first"] = min(a["first"], r["date"])
    a["last"] = max(a["last"], r["date"])
    a["to"].add(r["to_addr"])
    a["ats"].add(ats(r["sender"]))

def status(a):
    e = a["events"]
    if e["interview"] or e["assessment"]:
        return "positive"
    if e["reject"]:
        return "rejected"
    if e["confirm"] or e["viewed"]:
        return "pending"
    if e["recruiter"]:
        return "recruiter"
    return "unknown"

print(f"messages: {len(rows)}   distinct applications/threads: {len(apps)}")
print("events:", dict(Counter(r["event"] for r in rows)))
print("to:", dict(Counter(r["to_addr"] for r in rows)))
print("status:", dict(Counter(status(a) for a in apps.values())))
companies = Counter(norm(k[0]) for k in apps)
print("distinct companies:", len(companies))
print("most-applied companies:", companies.most_common(25))

by_week = defaultdict(Counter)
import datetime as dt
for a in apps.values():
    d = dt.date.fromisoformat(a["first"])
    wk = (d - dt.timedelta(days=d.weekday())).isoformat()
    by_week[wk][status(a)] += 1
print("\nweek_of  apps  positive  rejected  pending")
for wk in sorted(by_week):
    c = by_week[wk]
    print(wk, sum(c.values()), c["positive"], c["rejected"], c["pending"])

by_ats = defaultdict(Counter)
for a in apps.values():
    for t in a["ats"]:
        by_ats[t][status(a)] += 1
print("\nATS  apps  positive  rejected")
for t, c in sorted(by_ats.items(), key=lambda x: -sum(x[1].values())):
    print(t, sum(c.values()), c["positive"], c["rejected"])

# role keyword buckets
buckets = {"principal": r"principal|distinguished", "staff": r"\bstaff\b", "senior": r"senior|sr\b",
           "director/head/lead": r"director|head|\blead\b|manager|architect",
           "research": r"research|scientist", "ml/ai": r"machine learning|\bml\b|\bai\b|deep learning",
           "cv/3d/graphics/xr": r"vision|perception|3d|graphics|xr|\bar\b|\bvr\b|render|robot|embodied",
           "off-target": r"full.?stack|front.?end|backend|\.net|typescript|react|electrical|site reliability|data engineer|platform engineer|sre"}
print("\nbucket  apps  positive  rejected")
for b, rx in buckets.items():
    c = Counter(status(a) for a in apps.values() if re.search(rx, a["role"].lower()))
    print(b, sum(c.values()), c["positive"], c["rejected"])

with open("master_applications.tsv", "w", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["company", "role", "status", "first_seen", "last_seen", "inbox", "ats", "events"])
    for a in sorted(apps.values(), key=lambda a: (a["company"].lower(), a["role"].lower())):
        w.writerow([a["company"], a["role"], status(a), a["first"], a["last"], "+".join(sorted(a["to"])),
                    "+".join(sorted(a["ats"])), " ".join(f"{k}:{v}" for k, v in a["events"].items())])
print("\nwrote master_applications.tsv")
