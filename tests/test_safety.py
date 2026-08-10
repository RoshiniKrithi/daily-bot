"""Unit tests for Triple-Tier Contest Safety System."""

from __future__ import annotations

import pytest

from safety import ContestSafetyGuard


class TestURLSafetyFilter:
    """Test Tier 1 URL Safety Filter."""

    def test_normal_practice_url_is_safe(self) -> None:
        url = "https://leetcode.com/problems/two-sum/"
        assert ContestSafetyGuard.is_contest_url(url) is False

    def test_contest_path_url_is_unsafe(self) -> None:
        url = "https://leetcode.com/contest/weekly-contest-300/problems/two-sum/"
        assert ContestSafetyGuard.is_contest_url(url) is True

    def test_uppercase_contest_url_is_unsafe(self) -> None:
        url = "HTTPS://LEETCODE.COM/CONTESTS/WEEKLY-300"
        assert ContestSafetyGuard.is_contest_url(url) is True

    def test_contest_query_param_is_unsafe(self) -> None:
        url = "https://leetcode.com/problems/two-sum/?contestId=9823"
        assert ContestSafetyGuard.is_contest_url(url) is True

    def test_codechef_starters_url_is_unsafe(self) -> None:
        url = "https://www.codechef.com/starters100/problems/FOO"
        assert ContestSafetyGuard.is_contest_url(url) is True

    def test_hackerrank_compete_url_is_unsafe(self) -> None:
        url = "https://www.hackerrank.com/compete/challenge/foo"
        assert ContestSafetyGuard.is_contest_url(url) is True

    def test_empty_url_fails_closed(self) -> None:
        assert ContestSafetyGuard.is_contest_url("") is True


class TestMetadataValidation:
    """Test Tier 2 Problem Metadata Validator."""

    def test_valid_practice_metadata(self) -> None:
        url = "https://leetcode.com/problems/two-sum/"
        title = "Two Sum"
        breadcrumbs = ["Problems", "Two Sum"]
        is_safe, reason = ContestSafetyGuard.validate_problem_metadata(url, title, breadcrumbs)
        assert is_safe is True
        assert reason == "PASS"

    def test_contest_title_metadata_is_unsafe(self) -> None:
        url = "https://leetcode.com/problems/problem-from-contest/"
        title = "Weekly Contest 350 - Problem A"
        is_safe, reason = ContestSafetyGuard.validate_problem_metadata(url, title)
        assert is_safe is False
        assert "[CRITICAL SAFETY]" in reason

    def test_contest_breadcrumb_is_unsafe(self) -> None:
        url = "https://leetcode.com/problems/some-problem/"
        title = "Some Problem"
        breadcrumbs = ["Contests", "Weekly Contest 350", "Some Problem"]
        is_safe, reason = ContestSafetyGuard.validate_problem_metadata(url, title, breadcrumbs)
        assert is_safe is False
        assert "[CRITICAL SAFETY]" in reason

    def test_empty_title_fails_closed(self) -> None:
        url = "https://leetcode.com/problems/two-sum/"
        is_safe, reason = ContestSafetyGuard.validate_problem_metadata(url, "")
        assert is_safe is False
        assert "Fail-closed" in reason


class TestDOMAudit:
    """Test Tier 3 Live DOM Audit."""

    def test_clean_practice_dom(self) -> None:
        dom = "<html><body><h1>Two Sum</h1><button>Submit</button></body></html>"
        is_safe, reason = ContestSafetyGuard.perform_contest_dom_audit(dom)
        assert is_safe is True
        assert reason == "PASS"

    def test_dom_with_contest_ends_in(self) -> None:
        dom = "<html><body><div>Contest Ends In 01:23:45</div></body></html>"
        is_safe, reason = ContestSafetyGuard.perform_contest_dom_audit(dom)
        assert is_safe is False
        assert "Contest countdown timer detected" in reason

    def test_dom_with_leaderboard(self) -> None:
        dom = "<html><body><h2>Contest Leaderboard</h2></body></html>"
        is_safe, reason = ContestSafetyGuard.perform_contest_dom_audit(dom)
        assert is_safe is False
        assert "leaderboard" in reason.lower()

    def test_dom_with_virtual_contest(self) -> None:
        dom = "<html><body><div>Virtual Contest In Progress</div></body></html>"
        is_safe, reason = ContestSafetyGuard.perform_contest_dom_audit(dom)
        assert is_safe is False
        assert "virtual contest" in reason.lower()

    def test_empty_dom_fails_closed(self) -> None:
        is_safe, reason = ContestSafetyGuard.perform_contest_dom_audit("")
        assert is_safe is False
        assert "Fail-closed" in reason


class TestFinalSubmissionGate:
    """Test Final Submission Gate integration."""

    def test_gate_approves_safe_submission(self) -> None:
        url = "https://leetcode.com/problems/two-sum/"
        title = "Two Sum"
        dom = "<html><body><h1>Two Sum</h1></body></html>"
        approved, reason = ContestSafetyGuard.final_submission_gate(
            url=url,
            title=title,
            dom_content=dom,
            is_authenticated=True,
            is_practice_catalog=True,
        )
        assert approved is True
        assert reason == "APPROVED"

    def test_gate_rejects_unauthenticated(self) -> None:
        url = "https://leetcode.com/problems/two-sum/"
        title = "Two Sum"
        dom = "<html><body><h1>Two Sum</h1></body></html>"
        approved, reason = ContestSafetyGuard.final_submission_gate(
            url=url,
            title=title,
            dom_content=dom,
            is_authenticated=False,
            is_practice_catalog=True,
        )
        assert approved is False
        assert "not authenticated" in reason

    def test_gate_rejects_contest_url(self) -> None:
        url = "https://leetcode.com/contest/weekly-300/problems/two-sum/"
        title = "Two Sum"
        dom = "<html><body><h1>Two Sum</h1></body></html>"
        approved, reason = ContestSafetyGuard.final_submission_gate(
            url=url,
            title=title,
            dom_content=dom,
            is_authenticated=True,
            is_practice_catalog=True,
        )
        assert approved is False
        assert "[CRITICAL SAFETY]" in reason
