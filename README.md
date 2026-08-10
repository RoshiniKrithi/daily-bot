# 🚀 ZERO-CONTEST DAILY PRACTICE STREAK BOT

A production-quality Python 3.11+ browser automation application built with Playwright that completes **exactly ONE eligible standard practice problem per day** on coding platforms (LeetCode primary) to maintain a legitimate daily practice streak while strictly guaranteeing **ZERO contest interaction**.

---

## 📌 OVERVIEW & CORE PHILOSOPHY

Maintaining a daily practice streak is essential for skill building, but automated streak bots risk accidentally registering for, entering, or submitting solutions to live contests, rated events, or virtual competitions.

This application solves that problem with a **Triple-Tier Contest Safety System** and **Fail-Closed Architecture**:

```text
Safety Rule #1: SAFETY ALWAYS WINS OVER STREAK COMPLETION.
A missed daily streak is acceptable; an unintended contest submission is NEVER acceptable.
```

---

## 🏗️ PROJECT ARCHITECTURE

```text
Browser (Playwright Chromium)
   ↓
Authentication Manager (Persistent Profile / .env Cookies)
   ↓
Problem Selector (Platform Abstraction Factory)
   ↓
Tier 1: URL / Route Safety Filter (Blacklist Pattern Matcher)
   ↓
Tier 2: Problem Metadata Validator (Catalog & Breadcrumb Audit)
   ↓
Tier 3: Live DOM Circuit Breaker (UI Indicator & Countdown Audit)
   ↓
Final Submission Gate (Centralized Safety Approval)
   ↓
Browser UI Code Submission (Monaco Editor Keyboard Simulation)
   ↓
Result Evaluation & Local Daily State Logging
```

### Directory Structure

```text
zero_contest_streak_bot/
│
├── zero_contest_streak_bot.py   # Main CLI entry point & DailyStreakBot orchestrator
├── config.py                     # Configuration loader & startup setting validation
├── safety.py                     # Triple-Tier Contest Safety System & Final Gate
├── browser.py                    # Playwright Chromium manager & security challenge detector
├── authentication.py             # Session cookie injection & authentication verifier
├── problem_selector.py           # CodingPlatform abstraction & LeetCode implementation
├── problem_validator.py          # Metadata, difficulty, and eligibility validator
├── submission.py                 # Code entry, pre-submit DOM audit & result handler
├── logger.py                     # Structured logger writing to console & streak_execution.log
├── requirements.txt              # Core package dependencies
├── .env.example                  # Environment configuration template
├── README.md                     # Comprehensive project documentation
├── streak_state.json             # Daily execution state tracker (prevents duplicate runs)
├── streak_execution.log          # Detailed execution audit log
│
├── browser_profile/              # Persistent browser profile storage
└── tests/
    └── test_safety.py            # Pytest suite for safety filters and fail-closed logic
```

---

## 🛡️ TRIPLE-TIER CONTEST SAFETY SYSTEM

The bot enforces three independent, non-bypassing safety checks. Submission is permitted ONLY if **ALL THREE** tiers pass:

### 1. Tier 1 — URL / Route Safety Filter (`is_contest_url`)
- Pre-navigation and post-navigation case-insensitive blacklist check.
- Rejects URLs matching patterns such as `/contest/`, `/contests/`, `/starters/`, `/challenge/`, `/compete/`, `/arena/`, `/competition/`, `contestId=`, etc.

### 2. Tier 2 — Problem Metadata Validation (`validate_problem_metadata`)
- Confirms the problem belongs strictly to the normal practice catalog.
- Audits page titles, meta tags, and breadcrumbs for terms like `Contest Problem`, `Live Contest`, `Virtual Contest`, `Rated Event`, `Competition`, `Hackathon`, `Scoreboard`.

### 3. Tier 3 — DOM Circuit Breaker (`perform_contest_dom_audit`)
- Scans live rendered DOM immediately before typing and clicking submit.
- Detects contest indicators, countdown timers (`Contest Ends In`), leaderboard headers, and contest registration buttons.

### Fail-Closed Design (`UNKNOWN = UNSAFE`)
If any validation step encounters ambiguity, missing elements, or an exception:
- **Immediate Abort**: Never submits code.
- **Zero Retries for Safety**: Retries apply only to transient DOM loading issues, never safety failures.
- **Graceful Shutdown**: Closes context safely and logs the incident.

---

## 📦 INSTALLATION

### Prerequisites
- **Python**: 3.11 or higher
- **Browser**: Chromium (managed via Playwright)

### Setup Instructions

1. **Clone or navigate to repository**:
   ```bash
   cd "d:/daily bot"
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   # On Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright Chromium browser binaries**:
   ```bash
   playwright install chromium
   ```

---

## 🔑 AUTHENTICATION GUIDE

The bot supports two safe methods of maintaining platform login state.

### Option A — Persistent Playwright Profile (Recommended)
1. Launch the bot in headed mode:
   ```bash
   python zero_contest_streak_bot.py --dry-run
   ```
2. In the opened Chromium window, manually log into your LeetCode account.
3. Close the browser.
4. Your authenticated session will be safely stored in `./browser_profile/` and automatically reused on future automated runs without re-entering credentials.

### Option B — Environment Variables (`.env`)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill in your session cookies:
```env
LEETCODE_SESSION=your_leetcode_session_cookie_here
CSRFTOKEN=your_csrftoken_here
```

> [!IMPORTANT]
> Never commit `.env` or paste session tokens into source code. Treat session cookies with the same sensitivity as account passwords.

---

## ⚙️ CONFIGURATION OPTIONS

Configure default parameters in `.env` or override via CLI arguments:

| Setting | Default | Description |
|---|---|---|
| `PLATFORM` | `leetcode` | Target platform (`leetcode`, `codechef`, `hackerrank`) |
| `LANGUAGE` | `python` | Solution language (`python`) |
| `DIFFICULTY` | `Easy` | Target problem difficulty |
| `DAILY_PROBLEM_COUNT` | `1` | Must remain `1` to enforce strict single daily limit |
| `HEADLESS` | `false` | Set to `true` for background headless execution |
| `MAX_RETRIES` | `3` | Maximum retries for transient DOM timeouts |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

---

## 🖥️ CLI USAGE & DRY-RUN MODE

### 1. Mandatory Dry-Run Verification
Before enabling scheduled runs, always run a dry run to verify authentication and safety checks without submitting code:
```bash
python zero_contest_streak_bot.py --dry-run
```

**Expected Dry-Run Output**:
```text
========================================
 ZERO-CONTEST STREAK BOT
========================================

Platform        : LeetCode
Language        : Python
Mode            : DRY RUN

Candidate       : Two Sum
Difficulty      : Easy

URL Safety      : PASS
Metadata Safety : PASS
DOM Safety      : PASS

Submission      : SKIPPED (DRY RUN)

Status          : SAFE
========================================
```

### 2. Normal Daily Execution
```bash
python zero_contest_streak_bot.py
```

### 3. Additional CLI Flags
- `--dry-run`: Performs all navigations and safety checks, skipping typing & submitting.
- `--headless`: Forces browser to run in background headless mode.
- `--debug`: Enables detailed verbose log output.

---

## 🧪 TESTING THE SAFETY SYSTEM

Run the automated Pytest suite to verify the safety guard:
```bash
python -m pytest tests/
```

Test coverage includes:
- Practice URL validation vs Contest URL rejection.
- Uppercase and query parameter contest URL detection.
- Practice metadata vs Contest metadata rejection.
- Live DOM audit for countdown timers (`Contest Ends In`) and leaderboards.
- Fail-closed behavior on missing or empty data.

---

## ⏰ AUTOMATED DAILY SCHEDULING

### 🪟 Windows Task Scheduler Setup

1. Open **Task Scheduler** (`taskschd.msc`).
2. Click **Create Basic Task** in the Actions pane.
3. **Name**: `ZeroContestStreakBot`.
4. **Trigger**: Select **Daily** and set desired daily time (e.g. `09:00 AM`).
5. **Action**: Select **Start a program**.
6. **Program/script**: Specify absolute path to Python executable:
   ```text
   D:\daily bot\venv\Scripts\python.exe
   ```
7. **Add arguments**:
   ```text
   D:\daily bot\zero_contest_streak_bot.py --headless
   ```
8. **Start in**: Set working directory:
   ```text
   D:\daily bot
   ```
9. Click **Finish**.
10. Test manually by right-clicking the task and choosing **Run**. Inspect `streak_execution.log`.

---

### 🐧 macOS / Linux Cron Setup

1. Open crontab editor:
   ```bash
   crontab -e
   ```
2. Add a daily entry at 09:00 AM (replace paths with your absolute paths):
   ```cron
   0 9 * * * /usr/bin/python3 /path/to/zero_contest_streak_bot/zero_contest_streak_bot.py --headless >> /path/to/zero_contest_streak_bot/cron.log 2>&1
   ```
3. Save and exit.

---

## 📊 LOGGING & STATE MANAGEMENT

### Audit Log (`streak_execution.log`)
Every execution records structured log lines:
```text
2026-08-08 09:00:01 | INFO | Starting Zero-Contest Daily Streak Bot
2026-08-08 09:00:02 | INFO | Checking authentication state on LeetCode...
2026-08-08 09:00:03 | INFO | Authentication verified: User avatar detected.
2026-08-08 09:00:04 | INFO | Platform=LeetCode | Problem=Two Sum
2026-08-08 09:00:04 | INFO | Practice verification=PASS
2026-08-08 09:00:05 | INFO | URL safety=PASS
2026-08-08 09:00:05 | INFO | Metadata safety=PASS
2026-08-08 09:00:06 | INFO | DOM safety=PASS
2026-08-08 09:00:12 | INFO | Submission=ACCEPTED
```

### Daily State File (`streak_state.json`)
Prevents duplicate daily submissions:
```json
{
    "last_successful_date": "2026-08-08",
    "last_problem": "Two Sum",
    "last_submission_result": "ACCEPTED",
    "timestamp": "2026-08-08 09:00:12"
}
```

---

## 🔧 EXTENDING TO ADDITIONAL PLATFORMS

The architecture separates platform-specific selectors from safety guards. To add a new platform (e.g. CodeChef or HackerRank):

1. Inherit from `CodingPlatform` in `problem_selector.py`:
   ```python
   class CodeChefPlatform(CodingPlatform):
       async def select_eligible_problem(self, page: Page) -> ProblemInfo | None:
           # Implement practice problem navigation & return ProblemInfo
           ...
   ```
2. Register the platform in `PlatformFactory.get_platform()`.
3. Add platform-specific contest URL patterns to `CONTEST_URL_PATTERNS` in `safety.py`.

---

## 🧯 TROUBLESHOOTING

| Issue | Cause | Solution |
|---|---|---|
| `[AUTH FAILURE]` | Session expired or cookie missing | Run `python zero_contest_streak_bot.py --dry-run` in headed mode and log in manually. |
| `[SECURITY CHALLENGE DETECTED]` | Cloudflare or CAPTCHA triggered | Bot stops immediately. Open browser manually, resolve challenge, and rerun. |
| `[CRITICAL SAFETY]` | URL or DOM matched contest keyword | Intended safe behavior. Problem will not be submitted. |
| Monaco Editor Not Found | DOM structure loading slowly | Increase timeout or verify browser window size. |

---

## 📄 LICENSE & DISCLAIMER

This software is for personal daily practice tracking on standard catalog problems only. It does not contain bypass mechanisms for anti-bot or CAPTCHA systems.
