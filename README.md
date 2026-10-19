# Job Radar

Daily scan for early-career roles (Class of May 2027). Every morning it pulls
new-grad listings from GitHub job lists (zapplyjobs, speedyapply, SimplifyJobs)
plus company job boards (Greenhouse, Lever, Ashby), scores each title against
my role families, skips anything already seen, and emails the new matches.

**Today's matches → [LATEST.md](LATEST.md)** · past days in [`digests/`](digests/)


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
