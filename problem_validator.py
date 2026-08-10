"""Problem Metadata and Practice Verification Module."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from safety import ContestSafetyGuard

logger = logging.getLogger("StreakBot")


@dataclass
class ProblemInfo:
    """Problem metadata representation."""

    title: str
    url: str
    difficulty: str
    is_practice_catalog: bool
    problem_id: str | None = None
    solution_code: str | None = None


class ProblemValidator:
    """Validator for problem metadata, difficulty, and practice status."""

    def __init__(self, target_difficulty: str = "Easy") -> None:
        self.target_difficulty = target_difficulty.lower()

    def validate(self, problem: ProblemInfo) -> tuple[bool, str]:
        """Validate problem for difficulty, URL safety, and practice catalog status.

        Returns:
            (True, "PASS") if problem is fully eligible.
            (False, reason) if problem is ineligible or unsafe.
        """
        # Tier 1: URL Safety
        if ContestSafetyGuard.is_contest_url(problem.url):
            return False, f"[CRITICAL SAFETY] URL '{problem.url}' matched contest filter."

        # Tier 2: Metadata Safety
        meta_pass, meta_reason = ContestSafetyGuard.validate_problem_metadata(
            url=problem.url,
            title=problem.title,
        )
        if not meta_pass:
            return False, f"[CRITICAL SAFETY] Metadata safety check failed: {meta_reason}"

        # Practice catalog check
        if not problem.is_practice_catalog:
            return False, f"[INELIGIBLE] Problem '{problem.title}' is not in the normal practice catalog."

        # Difficulty check
        if self.target_difficulty != "any" and problem.difficulty.lower() != self.target_difficulty:
            # Allow if it's the top candidate practice problem / daily challenge
            logger.info(f"Problem difficulty '{problem.difficulty}' differs from default '{self.target_difficulty}', proceeding for practice streak.")

        logger.info(f"Problem '{problem.title}' passed metadata and safety validation.")
        return True, "PASS"
