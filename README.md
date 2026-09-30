# Job Radar

Daily scan for early-career roles (Class of May 2027). Every morning it pulls
new-grad listings from GitHub job lists (zapplyjobs, speedyapply, SimplifyJobs)
plus company job boards (Greenhouse, Lever, Ashby), scores each title against
my role families, skips anything already seen, and emails the new matches.

**Today's matches → [LATEST.md](LATEST.md)** · past days in [`digests/`](digests/)

## Setup (one time, ~10 minutes)

1. **Create a repo.** On GitHub: New repository → name it `job-radar` → Private → Create.
   Upload every file from this folder (keep the `.github/workflows/` path).
2. **Allow the workflow to commit.** Repo → Settings → Actions → General →
   Workflow permissions → *Read and write permissions* → Save.
3. **Email (optional but recommended).** Make a Gmail App Password
   (Google Account → Security → 2-Step Verification must be on → App passwords).
   Then repo → Settings → Secrets and variables → Actions → New repository secret:
   - `SMTP_USER` = your Gmail address
   - `SMTP_PASS` = the 16-character app password
   - `EMAIL_TO`  = where the digest should go
   Skip this and results still land in `LATEST.md`.
4. **Test it.** Actions tab → *Daily job scan* → Run workflow.
   The first run is a big baseline (200+ matches); after that you only get what's new.

## Tuning (edit `config.py`)

| Want to… | Change |
|---|---|
| Add a company | its board name to `GREENHOUSE_BOARDS` / `LEVER_BOARDS` / `ASHBY_BOARDS` |
| Add a role family or keyword | `ROLE_FAMILIES` |
| See fewer / more results | `MIN_SCORE` |
| Include final-year internships | `EXCLUDE_INTERNSHIPS = False` |
| Log a new application | `ALREADY_APPLIED` |
| Change run time | the `cron` line in `.github/workflows/daily-job-scan.yml` |

Scores come from titles only, so always read the posting before applying:
check years of experience, graduation window, and clearance requirements.
