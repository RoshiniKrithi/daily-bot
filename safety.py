"""Triple-Tier Contest Safety System for Zero-Contest Streak Bot.

Guarantees absolute ZERO contest interaction using three independent safety layers
and fail-closed design logic (UNKNOWN = UNSAFE).
"""

from __future__ import annotations

import re
from typing import Any

# Tier 1 URL Blacklist Patterns (Case-insensitive)
CONTEST_URL_PATTERNS: list[str] = [
    "/contest/",
    "/contests/",
    "/starters/",
    "starters",
    "/challenge/",
    "/compete/",
    "/arena/",
    "/competition/",
    "contestId=",
    "contest_id=",
    "/weekly-contest",
    "/biweekly-contest",
]

# Tier 2 & Tier 3 Active Contest Indicators (Case-insensitive)
CONTEST_KEYWORD_PATTERNS: list[str] = [
    "contest ends in",
    "contest starts in",
    "live contest in progress",
    "virtual contest in progress",
    "active contest",
    "rated event in progress",
    "contest problem statement",
    "contest scoreboard",
    "contest leaderboard",
    "contest standings",
    "join contest",
    "register for contest",
    "enter contest",
    "submit to contest",
]


class ContestSafetyGuard:
    """Centralized safety guard enforcing triple-tier safety checks."""

    @staticmethod
    def is_contest_url(url: str) -> bool:
        """TIER 1 — URL / Route Safety Filter.

        Returns True if the URL matches any contest pattern, False if safe.
        """
        if not url:
            return True  # Fail-closed if URL is empty

        normalized_url = url.lower()
        for pattern in CONTEST_URL_PATTERNS:
            if pattern.lower() in normalized_url:
                return True

        return False

    @staticmethod
    def validate_problem_metadata(
        url: str,
        title: str,
        breadcrumbs: list[str] | None = None,
        meta_tags: dict[str, Any] | None = None,
    ) -> tuple[bool, str]:
        """TIER 2 — Problem Metadata Validation.

        Confirms problem belongs to normal practice catalog and is not associated
        with an active, past, or virtual contest.

        Returns:
            (True, "PASS") if safe.
            (False, reason_string) if unsafe or ambiguous.
        """
        try:
            if ContestSafetyGuard.is_contest_url(url):
                return False, "[CRITICAL SAFETY] Tier 1 URL Filter matched contest pattern."

            if not title or not title.strip():
                return False, "[CRITICAL SAFETY] Missing or empty problem title (Fail-closed)."

            # Check title for contest indicators
            title_lower = title.lower()
            if "contest" in title_lower or "hackathon" in title_lower or "competition" in title_lower:
                return False, f"[CRITICAL SAFETY] Problem title contains contest keywords: '{title}'"

            # Inspect breadcrumbs if available
            if breadcrumbs:
                for crumb in breadcrumbs:
                    crumb_lower = crumb.lower()
                    if any(pat in crumb_lower for pat in ["contest", "competition", "hackathon", "starters"]):
                        return (
                            False,
                            f"[CRITICAL SAFETY] Breadcrumb indicates contest context: '{crumb}'",
                        )

            # Inspect meta tags if available
            if meta_tags:
                meta_str = str(meta_tags).lower()
                for keyword in CONTEST_KEYWORD_PATTERNS:
                    if keyword in meta_str:
                        return (
                            False,
                            f"[CRITICAL SAFETY] Meta tag contains contest indicator: '{keyword}'",
                        )

            return True, "PASS"

        except Exception as err:
            # Fail-closed design: UNKNOWN = UNSAFE
            return False, f"[CRITICAL SAFETY] Metadata validation error (Fail-closed): {err}"

    @staticmethod
    def perform_contest_dom_audit(dom_content: str) -> tuple[bool, str]:
        """TIER 3 — DOM Circuit Breaker.

        Audits live rendered DOM content immediately before submission.

        Returns:
            (True, "PASS") if DOM is clean of contest indicators.
            (False, reason_string) if any contest indicator is detected.
        """
        try:
            if not dom_content or not dom_content.strip():
                return False, "[CRITICAL SAFETY] Empty DOM content provided for audit (Fail-closed)."

            dom_lower = dom_content.lower()

            # Regex search for countdown timers first
            if re.search(r"contest\s+(ends|starts)\s+in", dom_lower):
                return False, "[CRITICAL SAFETY] Contest countdown timer detected in DOM."

            for keyword in CONTEST_KEYWORD_PATTERNS:
                if keyword in dom_lower:
                    return (
                        False,
                        f"[CRITICAL SAFETY] Contest indicator found in DOM: '{keyword}'",
                    )

            return True, "PASS"

        except Exception as err:
            # Fail-closed design
            return False, f"[CRITICAL SAFETY] DOM audit exception (Fail-closed): {err}"

    @staticmethod
    def final_submission_gate(
        url: str,
        title: str,
        dom_content: str,
        is_authenticated: bool,
        is_practice_catalog: bool,
    ) -> tuple[bool, str]:
        """FINAL SUBMISSION GATE.

        Submission is permitted ONLY if all safety tiers pass and authentication is active.

        Returns:
            (True, "APPROVED") if all checks pass.
            (False, failure_reason) if ANY check fails.
        """
        if not is_authenticated:
            return False, "[ABORT] User is not authenticated."

        if not is_practice_catalog:
            return False, "[ABORT] Problem is not from normal practice catalog."

        # Tier 1: URL Check
        if ContestSafetyGuard.is_contest_url(url):
            return False, f"[CRITICAL SAFETY] Tier 1 URL check failed for URL: {url}"

        # Tier 2: Metadata Check
        meta_pass, meta_reason = ContestSafetyGuard.validate_problem_metadata(url, title)
        if not meta_pass:
            return False, f"Tier 2 Metadata check failed: {meta_reason}"

        # Tier 3: DOM Audit
        dom_pass, dom_reason = ContestSafetyGuard.perform_contest_dom_audit(dom_content)
        if not dom_pass:
            return False, f"Tier 3 DOM Audit failed: {dom_reason}"

        return True, "APPROVED"
