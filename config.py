"""Edit this file to tune the daily scan. No code changes needed elsewhere."""

# ---- Recency & volume -------------------------------------------------------
MAX_AGE_DAYS = 14          # skip postings older than this (when a date is known)
MIN_SCORE = 6.5            # drop anything scoring below this
EMAIL_TOP_N = 40           # max rows in the email digest

# ---- Role families (matched against the job TITLE, case-insensitive regex) --
# weight = base fit score from the resume analysis
ROLE_FAMILIES = {
    "Applied AI / FDE": {
        "weight": 9,
        "patterns": [r"forward[- ]deployed", r"\bagent(ic|s)?\b", r"applied ai",
                     r"\bai engineer", r"conversational ai", r"\bllm\b",
                     r"ai solutions? engineer", r"generative ai"],
    },
    "AI Security": {
        "weight": 9,
        "patterns": [r"\b(ai|ml|machine learning)\b.*secur", r"secur.*\b(ai|ml)\b"],
    },
    "Security / D&R": {
        "weight": 8,
        "patterns": [r"security engineer", r"cyber ?security", r"\bcyber\b",
                     r"detection", r"\bsoc (analyst|engineer)", r"security operations",
                     r"security analyst", r"cyber-physical",
                     r"incident response", r"threat", r"vulnerabilit",
                     r"information security", r"application security"],
    },
    "Trading Ops": {
        "weight": 8,
        "patterns": [r"trading operations", r"trade support", r"trading support",
                     r"production engineer", r"site reliability", r"\bsre\b",
                     r"trading assistant", r"operations engineer"],
    },
    "Fraud / Surveillance": {
        "weight": 7.5,
        "patterns": [r"fraud", r"surveillance", r"trust (and|&) safety",
                     r"risk analyst", r"financial crime", r"\baml\b",
                     r"investigat", r"(platform|business) integrity"],
    },
    "ML / Data Science": {
        "weight": 7,
        "patterns": [r"machine learning", r"\bml engineer", r"data scientist",
                     r"\bai/ml\b"],
    },
    "OT / ICS Security": {
        "weight": 7,
        "patterns": [r"\bics\b", r"\bot\b.*secur", r"scada", r"industrial control",
                     r"critical infrastructure"],
    },
    "Software Engineering": {
        "weight": 6,
        "patterns": [r"software (engineer|developer|development engineer)", r"\bsde\b"],
    },
}

# ---- Early-career signals (bonus; REQUIRED for company-board sources) -------
EARLY_CAREER_PATTERNS = [
    r"new grad", r"new college grad", r"university grad", r"\bgraduate\b",
    r"early career", r"entry[- ]level", r"\bjunior\b", r"\bjr\.?\b", r"2027",
    r"campus", r"rotational", r"launch program", r"\bassociate\b",
    r"\b(engineer|analyst|developer|scientist) (i|1)\b", r"\bi\s*$", r"\blevel 1\b",
]
EARLY_CAREER_BONUS = 1.5

# ---- Hard exclusions (title) ------------------------------------------------
EXCLUDE_TITLE_PATTERNS = [
    r"\bsenior\b", r"\bsr\.?\b", r"\bstaff\b", r"\bprincipal\b", r"\blead\b",
    r"\bmanager\b", r"\bdirector\b", r"\bhead of\b", r"\bvp\b", r"\bmid\b",
    r"experienced", r"lateral", r"\bii\b", r"\biii\b", r"\biv\b",
    r"\b(engineer|analyst|developer|scientist) [2-9]\b", r"\bphd\b",
    r"ts/sci", r"top secret", r"polygraph", r"clearance required",
    r"2026 start", r"bilingual",
]
# Set to False if you want final-year internships/co-ops back in the results
EXCLUDE_INTERNSHIPS = True
INTERNSHIP_PATTERNS = [r"\bintern\b", r"internship", r"co-?op", r"summer 20\d\d"]

# ---- Location ----------------------------------------------------------------
NON_US_TERMS = [
    "london", "united kingdom", " uk", "amsterdam", "india", "bangalore",
    "bengaluru", "hyderabad", "canada", "toronto", "vancouver", "singapore",
    "sydney", "australia", "dublin", "ireland", "germany", "berlin", "munich",
    "paris", "france", "tel aviv", "israel", "hong kong", "tokyo", "japan",
    "mexico", "brazil", "poland", "romania", "calgary", "montreal",
]
EXCLUDE_REMOTE_ONLY = False   # True = drop roles that are remote-only

# ---- Already applied (company, title substring) -----------------------------
ALREADY_APPLIED = [
    ("wolverine", "c++"),
    ("wolverine", "trading operations"),
]

# ---- Sources -----------------------------------------------------------------
GITHUB_MARKDOWN_LISTS = [
    "https://raw.githubusercontent.com/zapplyjobs/New-Grad-Jobs-2027/main/README.md",
    "https://raw.githubusercontent.com/speedyapply/2027-AI-College-Jobs/main/NEW_GRAD_USA.md",
]
SIMPLIFY_JSON = ("https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/"
                 "dev/.github/scripts/listings.json")

# Company job boards (board token = the name in the company's job-board URL).
# Add more anytime, e.g. job-boards.greenhouse.io/<token>
GREENHOUSE_BOARDS = ["fiveringsllc", "klaviyocampus", "tenableinc", "wizinc",
                     "andurilindustries", "spacex", "discord", "coreweave",
                     "applovin", "asana", "vercel", "pathai", "redventures"]
LEVER_BOARDS = ["spotify", "palantir"]
ASHBY_BOARDS = ["openai", "snowflake", "sierra", "warp", "cartesia", "plaid",
                "skydio", "oneapp"]
