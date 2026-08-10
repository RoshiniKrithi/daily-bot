"""Authentication Manager for Zero-Contest Streak Bot.

Handles session cookie injection, persistent profile verification, and authentication state checks.
Stops execution safely if security challenges (CAPTCHA / Cloudflare) or expired logins are detected.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import BrowserContext, Page

from config import Config

logger = logging.getLogger("StreakBot")


class AuthenticationManager:
    """Manages platform authentication and session validity."""

    def __init__(self, config: Config) -> None:
        self.config = config

    async def apply_cookies(self, context: BrowserContext) -> None:
        """Inject session cookies from configuration into the browser context if available."""
        cookies = []
        if self.config.leetcode_session:
            session_val = self.config.leetcode_session.strip().strip('"').strip("'")
            cookies.append({
                "name": "LEETCODE_SESSION",
                "value": session_val,
                "domain": ".leetcode.com",
                "path": "/",
                "secure": True,
                "sameSite": "Lax",
            })
        if self.config.csrftoken:
            csrf_val = self.config.csrftoken.strip().strip('"').strip("'")
            cookies.append({
                "name": "csrftoken",
                "value": csrf_val,
                "domain": ".leetcode.com",
                "path": "/",
                "secure": True,
                "sameSite": "Lax",
            })

        if self.config.codechef_session:
            cc_val = self.config.codechef_session.strip().strip('"').strip("'")
            cookies.append({
                "name": "Authorization",
                "value": cc_val,
                "domain": "www.codechef.com",
                "path": "/",
                "secure": True,
                "sameSite": "Lax",
            })
            cookies.append({
                "name": "authtoken",
                "value": cc_val,
                "domain": ".codechef.com",
                "path": "/",
                "secure": True,
                "sameSite": "Lax",
            })
        if self.config.codeforces_session:
            cf_val = self.config.codeforces_session.strip().strip('"').strip("'")
            cookies.append({
                "name": "JSESSIONID",
                "value": cf_val,
                "domain": "codeforces.com",
                "path": "/",
                "secure": True,
                "sameSite": "Lax",
            })
        if self.config.hackerrank_session:
            hr_val = self.config.hackerrank_session.strip().strip('"').strip("'")
            cookies.append({
                "name": "_hr_session",
                "value": hr_val,
                "domain": ".hackerrank.com",
                "path": "/",
                "secure": True,
                "sameSite": "Lax",
            })

        if cookies:
            logger.info("Injecting configured session cookies into browser context...")
            await context.add_cookies(cookies)

    async def is_authenticated(self, page: Page) -> bool:
        """Check whether the user is currently logged in on the platform.

        Inspects live GraphQL userStatus and rendered DOM to confirm authenticated session.
        """
        try:
            if self.config.platform == "leetcode":
                logger.info("Checking authentication state on LeetCode...")
                await page.goto("https://leetcode.com/problemset/all/", wait_until="domcontentloaded", timeout=30000)

                # Check for Cloudflare / Security challenge title
                page_title = (await page.title()).lower()
                if "just a moment" in page_title or "challenge" in page_title:
                    logger.warning("Cloudflare challenge page detected during authentication check.")
                    return False

                # 1. Query LeetCode GraphQL userStatus API
                try:
                    gql_res = await page.evaluate(
                        """async () => {
                            try {
                                const r = await fetch('https://leetcode.com/graphql/', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({
                                        query: 'query checkAuth { userStatus { isSignedIn username userSlug } }'
                                    })
                                });
                                return await r.json();
                            } catch (e) { return null; }
                        }"""
                    )
                    if gql_res and "data" in gql_res:
                        user_status = gql_res["data"].get("userStatus")
                        if user_status and user_status.get("isSignedIn"):
                            username = user_status.get("username", "user")
                            logger.info(f"Authentication verified via GraphQL API for user '{username}'.")
                            return True
                        elif user_status and user_status.get("isSignedIn") is False:
                            logger.warning("GraphQL userStatus returned isSignedIn = False.")
                            return False
                except Exception as err:
                    logger.debug(f"GraphQL userStatus check error: {err}")

                # 2. Check if user profile avatar or profile link is visible in DOM
                user_avatar = page.locator(
                    "#navbar_user_avatar, [data-cypress='user-avatar'], img[alt*='avatar'], "
                    "a[href*='/profile/'], a[href*='/u/'], div[id='user-profile-app']"
                )
                if await user_avatar.count() > 0 and await user_avatar.first.is_visible():
                    logger.info("Authentication verified: User avatar detected.")
                    return True

                # 3. Check if navbar sign in link is visible
                sign_in_link = page.locator("nav a[href*='/accounts/login'], nav a[href*='/login']")
                if await sign_in_link.count() > 0 and await sign_in_link.first.is_visible():
                    logger.warning("User is NOT logged in. Navigation 'Sign in' link detected.")
                    return False

                logger.warning("User authentication could not be verified.")
                return False

            else:
                # Platform-specific DOM inspection for CodeChef, Codeforces, HackerRank
                logger.info(f"Checking authentication state on {self.config.platform.capitalize()}...")
                if self.config.dry_run:
                    logger.info(f"Dry-run mode active for platform '{self.config.platform.capitalize()}'. Authentication guard passed.")
                    return True

                # Non-dry-run auth verification
                user_avatar = page.locator("a[href*='/users/'], a[href*='/profile/'], .avatar, [class*='user-head']")
                if await user_avatar.count() > 0 and await user_avatar.first.is_visible():
                    logger.info(f"Authentication verified on {self.config.platform.capitalize()}.")
                    return True

                logger.warning(f"User is not logged in on {self.config.platform.capitalize()}.")
                return False

        except Exception as err:
            logger.error(f"Error checking authentication state: {err}")
            return False
