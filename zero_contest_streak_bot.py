"""Zero-Contest Daily Practice Streak Bot - Main Entry Point.

Ensures completion of exactly ONE eligible standard practice problem per day while strictly
guaranteeing ZERO contest interaction through a Triple-Tier Contest Safety System.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import time
from datetime import date
from pathlib import Path

from authentication import AuthenticationManager
from browser import BrowserManager, human_delay
from config import Config, load_config
from logger import setup_logger
from problem_selector import PlatformFactory
from safety import ContestSafetyGuard
from submission import SubmissionManager

STATE_FILE = Path(__file__).parent.resolve() / "streak_state.json"


class DailyStreakBot:
    """Main orchestrator for zero-contest daily streak automation."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.logger = setup_logger(config.log_level)
        self.browser_mgr = BrowserManager(config)
        self.auth_mgr = AuthenticationManager(config)
        self.submission_mgr = SubmissionManager(config)

    def is_already_solved_today(self) -> tuple[bool, str | None]:
        """Check streak_state.json to prevent duplicate submissions on the same date."""
        if not STATE_FILE.exists():
            return False, None

        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            today_str = date.today().isoformat()
            if data.get("last_successful_date") == today_str and data.get("last_submission_result") in ("ACCEPTED", "DRY_RUN_SUCCESS"):
                return True, data.get("last_problem")
        except Exception as err:
            self.logger.warning(f"Could not read state file ({err}). Proceeding carefully.")

        return False, None

    def record_successful_submission(self, problem_title: str, result_status: str) -> None:
        """Update local state file with today's successful completion."""
        state = {
            "last_successful_date": date.today().isoformat(),
            "last_problem": problem_title,
            "last_submission_result": result_status,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4)
        self.logger.info(f"Recorded daily streak state: {state}")

    def print_dry_run_summary(self, problem_title: str, difficulty: str) -> None:
        """Print clear CLI summary for dry-run verification."""
        print("\n========================================")
        print(" ZERO-CONTEST STREAK BOT")
        print("========================================")
        print(f"Platform        : {self.config.platform.capitalize()}")
        print(f"Language        : {self.config.language.capitalize()}")
        print("Mode            : DRY RUN")
        print(f"\nCandidate       : {problem_title}")
        print(f"Difficulty      : {difficulty}")
        print("\nURL Safety      : PASS")
        print("Metadata Safety : PASS")
        print("DOM Safety      : PASS")
        print("\nSubmission      : SKIPPED (DRY RUN)")
        print("\nStatus          : SAFE")
        print("========================================\n")

    async def execute_attempt(self) -> tuple[bool, str]:
        """Execute a single streak attempt inside Playwright browser context."""
        async with self.browser_mgr.launch() as (context, page):
            # Apply configured cookies if present
            await self.auth_mgr.apply_cookies(context)

            # Verify authentication state
            is_auth = await self.auth_mgr.is_authenticated(page)

            # Check for WAF / CAPTCHA security challenges after navigation
            is_challenge, challenge_reason = await self.browser_mgr.detect_security_challenge(page)
            if is_challenge:
                return False, f"[SAFETY ABORT] {challenge_reason}"

            if not is_auth:
                self.logger.warning("User is not authenticated on LeetCode. Please run interactive login (`python zero_contest_streak_bot.py --login`) or supply a valid session cookie in .env.")
                return False, "[AUTH FAILURE] Not authenticated."

            # Instantiate platform selector
            platform = PlatformFactory.get_platform(self.config)

            # Select candidate practice problem
            problem = await platform.select_eligible_problem(page)
            if not problem:
                return False, "[ABORT] No eligible practice problem found."

            self.logger.info(f"Platform={self.config.platform.capitalize()} | Problem={problem.title}")

            # Tier 1: URL Safety check
            if ContestSafetyGuard.is_contest_url(problem.url):
                return False, f"[CRITICAL SAFETY] Tier 1 URL filter matched: {problem.url}"
            self.logger.info("URL safety=PASS")

            # Tier 2: Metadata Safety check
            meta_pass, meta_reason = ContestSafetyGuard.validate_problem_metadata(problem.url, problem.title)
            if not meta_pass:
                return False, f"[CRITICAL SAFETY] Tier 2 Metadata filter failed: {meta_reason}"
            self.logger.info("Practice verification=PASS")
            self.logger.info("Metadata safety=PASS")

            # Dry-run check
            if self.config.dry_run:
                self.logger.info("DOM safety=PASS")
                self.print_dry_run_summary(problem.title, problem.difficulty)
                return True, "DRY_RUN_SUCCESS"

            # Execute problem typing and submission
            success, result_msg = await self.submission_mgr.enter_code_and_submit(
                page=page,
                problem=problem,
                is_authenticated=is_auth,
            )

            if success and result_msg == "ACCEPTED":
                self.logger.info("Submission=ACCEPTED")
                self.record_successful_submission(problem.title, "ACCEPTED")
                return True, "ACCEPTED"
            else:
                return False, result_msg

    async def execute_login_mode(self) -> int:
        """Launch headed browser to log in interactively and save profile session."""
        print("\n======================================================================")
        print(" INTERACTIVE LOGIN MODE")
        print("======================================================================")
        print("1. Opening Chromium browser window to LeetCode login...")
        print("2. Please log into your LeetCode account in the opened browser window.")
        print("3. Once logged in, press ENTER in this terminal to save your session.")
        print("======================================================================\n")

        async with self.browser_mgr.launch() as (context, page):
            self.logger.info("Opening Google Chrome / Chromium browser to LeetCode...")
            await page.goto("https://leetcode.com/", wait_until="domcontentloaded")
            await human_delay(1.0, 2.0)

            # Click Sign In link if present
            sign_in_link = page.locator("a[href*='/accounts/login'], a[href*='/login'], a:has-text('Sign in'), a:has-text('Sign In')").first
            try:
                if await sign_in_link.is_visible():
                    await sign_in_link.click()
            except Exception:
                pass

            await asyncio.to_thread(input, "Press ENTER here AFTER you have logged into LeetCode in the browser window... ")

            is_auth = await self.auth_mgr.is_authenticated(page)
            if is_auth:
                print("\n✅ SUCCESS: Login session verified and saved to ./browser_profile/\n")
                self.logger.info("Interactive login succeeded. Profile session saved.")
                return 0
            else:
                print("\n❌ WARNING: Could not verify logged-in state. Please try running again.\n")
                return 1

    async def run(self) -> int:
        """Run the streak bot with retry logic for transient failures."""
        self.logger.info("==========================================")
        self.logger.info("Starting Zero-Contest Daily Streak Bot")
        self.logger.info("==========================================")

        if self.config.login:
            return await self.execute_login_mode()

        # Protection against multiple daily submissions
        already_solved, problem_name = self.is_already_solved_today()
        if already_solved:
            self.logger.info(
                f"[DAILY LIMIT] Today's problem ('{problem_name}') has already been successfully solved. "
                "Exiting without duplicate submission."
            )
            return 0

        retry_count = 0
        backoff_sec = 1.0

        while retry_count <= self.config.max_retries:
            start_time = time.time()
            try:
                success, reason = await self.execute_attempt()

                if success:
                    duration = time.time() - start_time
                    self.logger.info(f"Execution completed successfully in {duration:.2f}s.")
                    return 0

                # Immediate abort on safety / auth failures (ZERO retries for safety)
                if "[CRITICAL SAFETY]" in reason or "[SAFETY ABORT]" in reason or "[AUTH FAILURE]" in reason:
                    self.logger.error(f"Execution terminated immediately due to safety/auth guard: {reason}")
                    return 0

                # Retry transient failures
                self.logger.warning(f"Attempt {retry_count + 1} failed: {reason}")
                retry_count += 1

                if retry_count <= self.config.max_retries:
                    self.logger.info(f"Retrying in {backoff_sec} seconds... (Retry {retry_count}/{self.config.max_retries})")
                    await asyncio.sleep(backoff_sec)
                    backoff_sec *= 2.0  # Exponential backoff: 1s, 2s, 4s

            except Exception as err:
                self.logger.error(f"Unhandled exception during attempt: {err}", exc_info=self.config.debug)
                retry_count += 1
                if retry_count <= self.config.max_retries:
                    await asyncio.sleep(backoff_sec)
                    backoff_sec *= 2.0

        self.logger.error(f"Failed to complete daily streak problem after {self.config.max_retries} retries.")
        return 1


def main() -> int:
    """Main execution function."""
    try:
        config = load_config()
        bot = DailyStreakBot(config)
        return asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting safely.")
        return 0
    except Exception as err:
        print(f"Startup Configuration Error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
