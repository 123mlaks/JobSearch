"""Daily early-career job scanner for Mehna (Class of May 2027).

Pulls new-grad listings from GitHub job lists + company job boards,
scores them against role families from config.py, skips anything already
seen, writes a dated digest, and (optionally) emails it.
"""
import hashlib
import html
import json
import os
import re
import smtplib
import sys
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import requests

import config as C

ROOT = Path(__file__).parent
SEEN_FILE = ROOT / "seen_jobs.json"
DIGEST_DIR = ROOT / "digests"
NOW = datetime.now(timezone.utc)
HEADERS = {"User-Agent": "job-radar/1.0 (personal job digest)"}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def get(url, **kw):
    r = requests.get(url, headers=HEADERS, timeout=30, **kw)
    r.raise_for_status()
    return r


def clean(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = text.replace("**", "").replace("__", "")
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def rel_age_to_date(age):
    """'16m', '3h', '2d', '1w', '3mo' -> datetime (None if unknown)."""
    m = re.match(r"^\s*(\d+)\s*(m|min|h|d|w|mo)\b", (age or "").lower())
    if not m:
        return None
    n, unit = int(m.group(1)), m.group(2)
    delta = {"m": timedelta(minutes=n), "min": timedelta(minutes=n),
             "h": timedelta(hours=n), "d": timedelta(days=n),
             "w": timedelta(weeks=n), "mo": timedelta(days=30 * n)}[unit]
    return NOW - delta


def parse_iso(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def job(company, title, location, url, posted, source, curated):
    return {"company": clean(company), "title": clean(title),
            "location": clean(location) or "See posting", "url": url,
            "posted": posted, "source": source, "curated": curated}


# --------------------------------------------------------------------------- #
# Sources
# --------------------------------------------------------------------------- #
def from_markdown_list(url):
    """Parse any markdown table with Company / Role|Position / Location / Posted|Age."""
    out, cols = [], None
    for line in get(url).text.splitlines():
        if not line.startswith("|"):
            cols = None if not line.strip() else cols
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        low = [clean(c).lower() for c in cells]
        if "company" in low and any(k in low for k in ("role", "position", "title")):
            cols = {name: i for i, name in enumerate(low)}
            continue
        if cols is None or set(line) <= set("|-: "):
            continue

        def cell(*names):
            for n in names:
                if n in cols and cols[n] < len(cells):
                    return cells[cols[n]]
            return ""

        links = re.findall(r"https?://[^\s\"')>]+", line)
        apply_cell = next((c for c in cells if "apply" in c.lower() and "http" in c), "")
        link = (re.findall(r"https?://[^\s\"')>]+", apply_cell) or links[-1:] or [None])[0]
        if not link:
            continue
        out.append(job(cell("company"), cell("role", "position", "title"),
                       cell("location"), link,
                       rel_age_to_date(clean(cell("posted", "age", "date posted"))),
                       url.split("/")[3], curated=True))
    return out


def from_simplify():
    out = []
    for j in get(C.SIMPLIFY_JSON).json():
        if not j.get("active") or not j.get("is_visible", True):
            continue
        ts = j.get("date_posted")
        posted = datetime.fromtimestamp(ts, timezone.utc) if ts else None
        if posted and posted < NOW - timedelta(days=C.MAX_AGE_DAYS):
            continue
        out.append(job(j.get("company_name"), j.get("title"),
                       ", ".join(j.get("locations") or []), j.get("url"),
                       posted, "SimplifyJobs", curated=True))
    return out


def from_greenhouse(token):
    data = get(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs").json()
    return [job(token, j["title"], (j.get("location") or {}).get("name", ""),
                j["absolute_url"],
                parse_iso(j.get("first_published") or j.get("updated_at")),
                f"greenhouse:{token}", curated=False)
            for j in data.get("jobs", [])]


def from_lever(company):
    data = get(f"https://api.lever.co/v0/postings/{company}?mode=json").json()
    return [job(company, j["text"], (j.get("categories") or {}).get("location", ""),
                j["hostedUrl"],
                datetime.fromtimestamp(j["createdAt"] / 1000, timezone.utc)
                if j.get("createdAt") else None,
                f"lever:{company}", curated=False)
            for j in data]


def from_ashby(board):
    data = get(f"https://api.ashbyhq.com/posting-api/job-board/{board}").json()
    return [job(board, j["title"], j.get("location", ""), j["jobUrl"],
                parse_iso(j.get("publishedAt")), f"ashby:{board}", curated=False)
            for j in data.get("jobs", [])]


def collect():
    tasks = [(from_markdown_list, u) for u in C.GITHUB_MARKDOWN_LISTS]
    tasks += [(lambda _: from_simplify(), "simplify")]
    tasks += [(from_greenhouse, t) for t in C.GREENHOUSE_BOARDS]
    tasks += [(from_lever, t) for t in C.LEVER_BOARDS]
    tasks += [(from_ashby, t) for t in C.ASHBY_BOARDS]
    jobs, errors = [], []
    for fn, arg in tasks:
        try:
            got = fn(arg)
            jobs += got
            print(f"  {arg}: {len(got)} listings")
        except Exception as e:  # one bad source shouldn't kill the run
            errors.append(f"{arg}: {e.__class__.__name__}")
            print(f"  {arg}: FAILED ({e})", file=sys.stderr)
    return jobs, errors


# --------------------------------------------------------------------------- #
# Filtering & scoring
# --------------------------------------------------------------------------- #
def any_match(patterns, text):
    return any(re.search(p, text, re.I) for p in patterns)


def score(j):
    title, loc = j["title"].lower(), j["location"].lower()
    if not title or any_match(C.EXCLUDE_TITLE_PATTERNS, title):
        return None
    if C.EXCLUDE_INTERNSHIPS and any_match(C.INTERNSHIP_PATTERNS, title):
        return None
    if any(t in f" {loc}" for t in C.NON_US_TERMS) and "united states" not in loc:
        return None
    if C.EXCLUDE_REMOTE_ONLY and loc.strip().startswith("remote"):
        return None
    if any(c in j["company"].lower() and t in title for c, t in C.ALREADY_APPLIED):
        return None
    if j["posted"] and j["posted"] < NOW - timedelta(days=C.MAX_AGE_DAYS):
        return None

    fams = [(n, f["weight"]) for n, f in C.ROLE_FAMILIES.items()
            if any_match(f["patterns"], title)]
    if not fams:
        return None
    family, s = max(fams, key=lambda x: x[1])

    early = any_match(C.EARLY_CAREER_PATTERNS, title)
    if not j["curated"] and not early:  # company boards mix all levels
        return None
    if early:
        s += C.EARLY_CAREER_BONUS
    if len(fams) > 1:                   # e.g. security + AI in one title
        s += 0.5
    s = min(round(s, 1), 10)
    return (family, s) if s >= C.MIN_SCORE else None


def job_id(j):
    key = f"{j['company']}|{j['title']}|{j['location']}".lower()
    return hashlib.sha1(re.sub(r"[^a-z0-9|]", "", key).encode()).hexdigest()[:16]


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #
def to_markdown(rows, errors, total):
    d = NOW.strftime("%Y-%m-%d")
    lines = [f"# New matches — {d}", "",
             f"{len(rows)} new postings (scanned {total} listings).", ""]
    if rows:
        lines += ["| Fit | Company | Title | Family | Location | Posted | Link |",
                  "|---|---|---|---|---|---|---|"]
        for r in rows:
            p = r["posted"].strftime("%b %d") if r["posted"] else "?"
            lines.append(f"| {r['score']} | {r['company']} | {r['title']} | "
                         f"{r['family']} | {r['location'][:40]} | {p} | "
                         f"[Apply]({r['url']}) |")
    if errors:
        lines += ["", "<details><summary>Sources that failed today</summary>", ""]
        lines += [f"- {e}" for e in errors] + ["", "</details>"]
    return "\n".join(lines) + "\n"


def to_html(rows):
    trs = "".join(
        f"<tr><td><b>{r['score']}</b></td><td>{html.escape(r['company'])}</td>"
        f"<td><a href=\"{html.escape(r['url'])}\">{html.escape(r['title'])}</a></td>"
        f"<td>{r['family']}</td><td>{html.escape(r['location'][:40])}</td>"
        f"<td>{r['posted'].strftime('%b %d') if r['posted'] else '?'}</td></tr>"
        for r in rows[:C.EMAIL_TOP_N])
    return ("<p>New early-career matches today:</p>"
            "<table border='1' cellpadding='6' cellspacing='0' "
            "style='border-collapse:collapse;font-family:sans-serif;font-size:13px'>"
            "<tr><th>Fit</th><th>Company</th><th>Title</th><th>Family</th>"
            f"<th>Location</th><th>Posted</th></tr>{trs}</table>")


def send_email(rows):
    user, pw, to = (os.getenv(k) for k in ("SMTP_USER", "SMTP_PASS", "EMAIL_TO"))
    if not (user and pw and to):
        print("Email secrets not set; skipping email.")
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Job radar: {len(rows)} new matches ({NOW:%b %d})"
    msg["From"], msg["To"] = user, to
    msg.attach(MIMEText(to_html(rows), "html"))
    with smtplib.SMTP_SSL(os.getenv("SMTP_HOST", "smtp.gmail.com"), 465) as s:
        s.login(user, pw)
        s.send_message(msg)
    print(f"Emailed {min(len(rows), C.EMAIL_TOP_N)} rows to {to}")


# --------------------------------------------------------------------------- #
def main():
    seen = json.loads(SEEN_FILE.read_text()) if SEEN_FILE.exists() else {}
    first_run = not seen
    print("Collecting listings...")
    jobs, errors = collect()

    new_rows, batch_ids = [], set()
    for j in jobs:
        if not j["url"]:
            continue
        jid = job_id(j)
        if jid in seen or jid in batch_ids:
            continue
        res = score(j)
        batch_ids.add(jid)
        if res:
            j["family"], j["score"] = res
            new_rows.append(j)
    # remember everything we looked at so it never repeats
    for jid in batch_ids:
        seen[jid] = NOW.strftime("%Y-%m-%d")
    cutoff = (NOW - timedelta(days=90)).strftime("%Y-%m-%d")
    seen = {k: v for k, v in seen.items() if v >= cutoff}
    SEEN_FILE.write_text(json.dumps(seen, indent=0, sort_keys=True))

    new_rows.sort(key=lambda r: (-r["score"],
                                 -(r["posted"].timestamp() if r["posted"] else 0)))
    md = to_markdown(new_rows, errors, len(jobs))
    DIGEST_DIR.mkdir(exist_ok=True)
    (DIGEST_DIR / f"{NOW:%Y-%m-%d}.md").write_text(md)
    (ROOT / "LATEST.md").write_text(md)
    print(f"{len(new_rows)} new matches from {len(jobs)} listings"
          + (" (first run: baseline)" if first_run else ""))

    if new_rows:
        send_email(new_rows)


if __name__ == "__main__":
    main()
