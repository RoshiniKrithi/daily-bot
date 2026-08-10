"""Submission Manager for Zero-Contest Streak Bot.

Handles editor interaction, live pre-submit DOM contest audits, final submission gate verification,
and submission result tracking through Playwright browser UI.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page

from browser import human_delay
from config import Config
from problem_validator import ProblemInfo
from safety import ContestSafetyGuard

logger = logging.getLogger("StreakBot")


class SubmissionManager:
    """Manages browser interaction for code entry and submission."""

    def __init__(self, config: Config) -> None:
        self.config = config

    async def enter_code_and_submit(
        self,
        page: Page,
        problem: ProblemInfo,
        is_authenticated: bool,
    ) -> tuple[bool, str]:
        """Navigate to problem, inspect DOM, enter solution, verify final gate, and submit.

        Returns:
            (True, "ACCEPTED") if submission succeeded and was accepted.
            (False, failure_reason) if aborted or failed.
        """
        if not problem.solution_code:
            return False, "[ABORT] No solution code provided for problem."

        logger.info(f"Navigating to problem page: {problem.url}")
        await page.goto(problem.url, wait_until="domcontentloaded", timeout=30000)
        await human_delay(1.0, 2.0)

        # 1. Tier 1 URL Check on current browser URL
        current_url = page.url
        if ContestSafetyGuard.is_contest_url(current_url):
            return False, f"[CRITICAL SAFETY] Browser navigated to contest URL: '{current_url}'"

        # 2. Extract DOM content for audit
        dom_content = await page.content()
        page_title = await page.title()

        # 3. Tier 3 DOM Audit before typing
        dom_pass, dom_reason = ContestSafetyGuard.perform_contest_dom_audit(dom_content)
        if not dom_pass:
            return False, f"[CRITICAL SAFETY] Pre-entry DOM Audit failed: {dom_reason}"

        # 4. Locate Editor and ensure Python3 language is selected
        logger.info("Locating code editor component...")
        visible_editor = page.locator(".monaco-editor, .view-lines, [role='code'], div[class*='monaco-editor']").first

        try:
            await visible_editor.wait_for(state="visible", timeout=45000)
        except Exception as err:
            return False, f"[DOM FAILURE] Code editor not found or not visible: {err}"

        # Ensure editor language is set to Python3
        await self.ensure_python_language(page)

        # 5. Type solution into editor (if not dry run)
        if self.config.dry_run:
            logger.info("[DRY RUN MODE] Safety checks passed. Code typing and submission SKIPPED.")
            return True, "DRY_RUN_SUCCESS"

        logger.info("Focusing editor and clearing existing code...")
        await visible_editor.click()
        await human_delay()

        # Select all and delete previous boilerplate
        await page.keyboard.press("Control+A")
        await page.keyboard.press("Backspace")
        await human_delay(0.2, 0.5)

        logger.info("Entering Python solution code...")
        await page.keyboard.type(problem.solution_code, delay=5)
        await human_delay(0.5, 1.0)

        # 6. Re-perform final DOM Audit immediately prior to clicking submit
        fresh_dom = await page.content()
        gate_pass, gate_reason = ContestSafetyGuard.final_submission_gate(
            url=page.url,
            title=page_title,
            dom_content=fresh_dom,
            is_authenticated=is_authenticated,
            is_practice_catalog=problem.is_practice_catalog,
        )

        # Check if login is required on problem page
        login_prompt = page.locator("text='You need to log in / sign up to run or submit', text='You need to log in'")
        if await login_prompt.count() > 0 and await login_prompt.first.is_visible():
            return False, "[AUTH FAILURE] LeetCode requires user login to submit code."

        if not gate_pass:
            return False, f"[CRITICAL SAFETY] Final Submission Gate REJECTED: {gate_reason}"

        # 7. Locate and Click Submit Button
        logger.info("Locating console Submit button...")
        submit_button = page.locator(
            "button[data-e2e-locator='console-submit-button'], "
            "[data-e2e-locator='console-submit-button'], "
            "button[data-cypress='submit-code-btn'], "
            "button:has-text('Submit')"
        ).first

        if not await submit_button.is_visible():
            return False, "[DOM FAILURE] Submit button is not visible on page."

        logger.info("Clicking Submit button...")
        await submit_button.click()
        await human_delay()

        # 8. Wait for submission result modal container
        logger.info("Waiting for submission evaluation result...")
        result_locator = page.locator(
            "[data-e2e-locator='submission-result'], "
            "div[class*='result-state'], "
            "div[class*='resultcontainer'], "
            "div[class*='submission-result'], "
            "span[data-cypress='submission-result'], "
            "a[href*='/submissions/detail/']"
        )

        try:
            await result_locator.first.wait_for(state="visible", timeout=35000)
            result_text = await result_locator.first.inner_text()
            # Clean non-ASCII characters for log encoding safety
            clean_text = result_text.encode('ascii', errors='ignore').decode('ascii').strip()
            logger.info(f"Submission result received: '{clean_text[:100]}'")

            if "accepted" in clean_text.lower():
                return True, "ACCEPTED"
            elif "wrong answer" in clean_text.lower():
                return False, f"Submission result: Wrong Answer ({clean_text[:50]})"
            elif "time limit exceeded" in clean_text.lower():
                return False, f"Submission result: Time Limit Exceeded ({clean_text[:50]})"
            elif "runtime error" in clean_text.lower():
                return False, f"Submission result: Runtime Error ({clean_text[:50]})"
            elif "compile error" in clean_text.lower():
                return False, f"Submission result: Compile Error ({clean_text[:50]})"
            else:
                return False, f"Submission result pending or unrecognized: '{clean_text[:100]}'"

        except Exception as err:
            # Check if page URL or content changed to submission detail
            current_url = page.url
            if "/submissions/detail/" in current_url:
                logger.info("Submission detail URL detected! Result accepted.")
                return True, "ACCEPTED"

            return False, f"Timed out waiting for submission result modal: {err}"

    async def ensure_python_language(self, page: Page) -> None:
        """Ensure Python3 is selected in LeetCode's editor language dropdown."""
        try:
            # Check current language button in editor bar
            lang_btn = page.locator(
                "button[id*='headlessui-menu-button'], "
                "button:has-text('C++'), button:has-text('Java'), button:has-text('C#'), "
                "button:has-text('C'), button:has-text('JavaScript'), button:has-text('TypeScript'), "
                "button:has-text('Go'), button:has-text('Rust'), button:has-text('Python3'), button:has-text('Python')"
            ).first

            if await lang_btn.count() > 0 and await lang_btn.is_visible():
                btn_text = (await lang_btn.inner_text()).strip()
                if "python" in btn_text.lower():
                    logger.info(f"Editor language is already set to '{btn_text}'.")
                    return

                logger.info(f"Editor language is currently '{btn_text}'. Switching to Python3...")
                await lang_btn.click(force=True)
                await human_delay(0.5, 1.0)

                # Find Python3 or Python option in dropdown list
                python_option = page.locator(
                    "div[role='option']:has-text('Python3'), li:has-text('Python3'), "
                    "span:has-text('Python3'), div:has-text('Python3'), "
                    "div[role='option']:has-text('Python'), li:has-text('Python')"
                ).first

                if await python_option.count() > 0:
                    await python_option.click(force=True)
                    logger.info("Successfully switched editor language to Python3.")
                    await human_delay(0.5, 1.0)
        except Exception as err:
            logger.warning(f"Could not switch language automatically: {err}")
