"""Unit tests for Problem Selector and SolutionProvider."""

from unittest.mock import MagicMock, patch

from problem_selector import PRACTICE_SOLUTIONS, SolutionProvider


def test_solution_provider_local_slug():
    """Test resolving local solution from PRACTICE_SOLUTIONS."""
    sol = SolutionProvider.get_solution("stone-game-iv")
    assert sol is not None
    assert "winnerSquareGame" in sol
    assert "class Solution" in sol


def test_solution_provider_two_sum():
    """Test resolving two-sum local solution."""
    sol = SolutionProvider.get_solution("two-sum")
    assert sol is not None
    assert "twoSum" in sol


@patch("urllib.request.urlopen")
def test_solution_provider_dynamic_fetch_success(mock_urlopen):
    """Test dynamic HTTP solution retrieval and xrange syntax replacement."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = (
        b"class Solution(object):\n"
        b"    def exampleProblem(self, n):\n"
        b"        for i in xrange(n):\n"
        b"            pass\n"
    )
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    sol = SolutionProvider.get_solution("unknown-custom-slug")
    assert sol is not None
    assert "range(n)" in sol
    assert "xrange" not in sol


@patch("urllib.request.urlopen")
def test_solution_provider_dynamic_fetch_failure(mock_urlopen):
    """Test fallback to None when dynamic fetch fails."""
    mock_urlopen.side_effect = Exception("HTTP 404 Not Found")

    sol = SolutionProvider.get_solution("non-existent-problem-xyz")
    assert sol is None


def test_platform_factory_all_platforms():
    """Test PlatformFactory returns correct platform instances for all supported targets."""
    from config import Config
    from problem_selector import (
        CodeChefPlatform,
        CodeforcesPlatform,
        HackerRankPlatform,
        LeetCodePlatform,
        PlatformFactory,
    )

    def dummy_cfg(plat: str) -> Config:
        return Config(
            platform=plat,
            language="python",
            difficulty="Easy",
            daily_problem_count=1,
            headless=True,
            max_retries=3,
            log_level="INFO",
            dry_run=True,
            debug=False,
            login=False,
            browser_profile_dir=None,
            leetcode_session=None,
            csrftoken=None,
        )

    assert isinstance(PlatformFactory.get_platform(dummy_cfg("leetcode")), LeetCodePlatform)
    assert isinstance(PlatformFactory.get_platform(dummy_cfg("codechef")), CodeChefPlatform)
    assert isinstance(PlatformFactory.get_platform(dummy_cfg("codeforces")), CodeforcesPlatform)
    assert isinstance(PlatformFactory.get_platform(dummy_cfg("hackerrank")), HackerRankPlatform)

