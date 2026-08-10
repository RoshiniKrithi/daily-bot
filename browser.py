"""Browser manager and Playwright interaction layer for Zero-Contest Streak Bot."""

from __future__ import annotations

import asyncio
import logging
import random
from pathlib import Path
from typing import AsyncIterator
from contextlib import asynccontextmanager

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from config import Config

logger = logging.getLogger("StreakBot")


async def human_delay(min_sec: float = 0.05, max_sec: float = 0.15) -> None:
    """Introduce a slight human-like micro delay between UI operations."""
    await asyncio.sleep(random.uniform(min_sec, max_sec))


class BrowserManager:
    """Manages Playwright browser lifecycle, persistent profile, and anti-bot challenge detection."""

    def __init__(self, config: Config) -> None:
        self.config = config

    @asynccontextmanager
    async def launch(self) -> AsyncIterator[tuple[BrowserContext, Page]]:
        """Launch Playwright Chromium using a persistent profile directory."""
        logger.info("Initializing Playwright Chromium instance...")
        async with async_playwright() as p:
            profile_dir = self.config.browser_profile_dir

            # Launch persistent browser context using installed Google Chrome if available
            try:
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=str(profile_dir),
                    channel="chrome",
                    headless=self.config.headless,
                    viewport={"width": 1280, "height": 800},
                )
            except Exception:
                logger.info("System Chrome channel not available, falling back to Playwright Chromium...")
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=str(profile_dir),
                    headless=self.config.headless,
                    ignore_default_args=["--enable-automation"],
                    viewport={"width": 1280, "height": 800},
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/122.0.0.0 Safari/537.36"
                    ),
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-infobars",
                    ],
                )

            # Get default page or create a new one
            page = context.pages[0] if context.pages else await context.new_page()
            page.set_default_timeout(30000)

            try:
                yield context, page
            finally:
                logger.info("Closing browser context safely...")
                await context.close()

    @staticmethod
    async def detect_security_challenge(page: Page) -> tuple[bool, str]:
        """Inspect page to detect WAF / Cloudflare / CAPTCHA / Security challenges.

        If a challenge is detected:
        returns (True, "Challenge Type")
        """
        try:
            content = (await page.content()).lower()
            title = (await page.title()).lower()

            challenge_indicators = [
                ("Cloudflare Challenge", "just a moment..."),
                ("Cloudflare Verification", "cf-challenge"),
                ("Cloudflare Turnstile", "challenges.cloudflare.com"),
                ("reCAPTCHA", "g-recaptcha"),
                ("hCaptcha", "hcaptcha"),
                ("Bot Verification", "verify you are human"),
                ("Access Denied", "access denied"),
                ("Rate Limit", "too many requests"),
            ]

            for name, indicator in challenge_indicators:
                if indicator in content or indicator in title:
                    return True, f"[SECURITY CHALLENGE DETECTED] {name}"

            return False, "NONE"

        except Exception as err:
            logger.error(f"Error checking for security challenge: {err}")
            return True, f"[SECURITY CHALLENGE ERROR] {err}"

    @staticmethod
    async def save_screenshot(page: Page, name_prefix: str = "error") -> Path | None:
        """Capture screenshot for failure diagnosis."""
        try:
            screenshots_dir = Path(__file__).parent.resolve() / "screenshots"
            screenshots_dir.mkdir(exist_ok=True)

            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = screenshots_dir / f"{timestamp}_{name_prefix}.png"

            await page.screenshot(path=str(filename), full_page=True)
            logger.info(f"Saved failure diagnostic screenshot: [screenshot](file:///{filename.as_posix()})")
            return filename
        except Exception as err:
            logger.error(f"Failed to capture screenshot: {err}")
            return None
