"""Configuration loader and settings manager for Zero-Contest Streak Bot."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if available
load_dotenv()


@dataclass(frozen=True)
class Config:
    """Immutable application settings container."""

    platform: str
    language: str
    difficulty: str
    daily_problem_count: int
    headless: bool
    max_retries: int
    log_level: str
    dry_run: bool
    debug: bool
    login: bool
    browser_profile_dir: Path
    leetcode_session: str | None
    csrftoken: str | None

    def validate(self) -> None:
        """Validate settings at startup. Fail fast if configuration is invalid."""
        supported_platforms = {"leetcode", "codechef", "hackerrank"}
        if self.platform.lower() not in supported_platforms:
            raise ValueError(
                f"Unsupported platform: {self.platform}. Supported: {supported_platforms}"
            )

        supported_languages = {"python", "python3"}
        if self.language.lower() not in supported_languages:
            raise ValueError(
                f"Unsupported language: {self.language}. Initially supported: Python"
            )

        if self.daily_problem_count != 1:
            raise ValueError("DAILY_PROBLEM_COUNT must be exactly 1 to enforce single daily problem limit.")

        if self.max_retries < 0 or self.max_retries > 5:
            raise ValueError("MAX_RETRIES must be between 0 and 5.")


def load_config(cli_args: list[str] | None = None) -> Config:
    """Load configuration combining environment variables and CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Zero-Contest Daily Practice Streak Bot"
    )
    parser.add_argument(
        "--platform",
        type=str,
        default=os.getenv("PLATFORM", "leetcode"),
        help="Target platform (default: leetcode)",
    )
    parser.add_argument(
        "--language",
        type=str,
        default=os.getenv("LANGUAGE", "python"),
        help="Target language (default: python)",
    )
    parser.add_argument(
        "--difficulty",
        type=str,
        default=os.getenv("DIFFICULTY", "Easy"),
        help="Target difficulty (default: Easy)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run safety checks and selection without typing or submitting code",
    )
    parser.add_argument(
        "--login",
        action="store_true",
        help="Launch headed browser window to log in interactively and save profile session",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=os.getenv("HEADLESS", "false").lower() == "true",
        help="Run browser in headless mode",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable verbose debug mode",
    )

    args = parser.parse_args(cli_args)

    project_root = Path(__file__).parent.resolve()
    browser_profile_dir = project_root / "browser_profile"
    browser_profile_dir.mkdir(exist_ok=True)

    config = Config(
        platform=args.platform.lower(),
        language=args.language.lower(),
        difficulty=args.difficulty,
        daily_problem_count=int(os.getenv("DAILY_PROBLEM_COUNT", "1")),
        headless=False if args.login else args.headless,
        max_retries=int(os.getenv("MAX_RETRIES", "3")),
        log_level="DEBUG" if args.debug else os.getenv("LOG_LEVEL", "INFO").upper(),
        dry_run=args.dry_run,
        debug=args.debug,
        login=args.login,
        browser_profile_dir=browser_profile_dir,
        leetcode_session=os.getenv("LEETCODE_SESSION"),
        csrftoken=os.getenv("CSRFTOKEN"),
    )

    config.validate()
    return config
