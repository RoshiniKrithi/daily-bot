"""Coding Platform Abstract Interface and Platform Implementations (LeetCode, CodeChef, HackerRank)."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page

from config import Config
from problem_validator import ProblemInfo, ProblemValidator
from safety import ContestSafetyGuard

logger = logging.getLogger("StreakBot")

# Standard practice catalog solutions map for deterministic, safe practice solving
PRACTICE_SOLUTIONS: dict[str, dict[str, str]] = {
    "stone-game-iv": {
        "title": "Stone Game IV",
        "url": "https://leetcode.com/problems/stone-game-iv/",
        "difficulty": "Hard",
        "code": (
            "class Solution:\n"
            "    def winnerSquareGame(self, n: int) -> bool:\n"
            "        dp = [False] * (n + 1)\n"
            "        for i in range(1, n + 1):\n"
            "            k = 1\n"
            "            while k * k <= i:\n"
            "                if not dp[i - k * k]:\n"
            "                    dp[i] = True\n"
            "                    break\n"
            "                k += 1\n"
            "        return dp[n]\n"
        ),
    },
    "find-the-lexicographically-smallest-valid-sequence": {
        "title": "Find the Lexicographically Smallest Valid Sequence",
        "url": "https://leetcode.com/problems/find-the-lexicographically-smallest-valid-sequence/",
        "difficulty": "Medium",
        "code": (
            "class Solution:\n"
            "    def validSequence(self, word1: str, word2: str) -> list[int]:\n"
            "        n, m = len(word1), len(word2)\n"
            "        last_match = [-1] * m\n"
            "        j = m - 1\n"
            "        for i in range(n - 1, -1, -1):\n"
            "            if j >= 0 and word1[i] == word2[j]:\n"
            "                last_match[j] = i\n"
            "                j -= 1\n"
            "        ans = []\n"
            "        j = 0\n"
            "        changed = False\n"
            "        for i in range(n):\n"
            "            if j == m:\n"
            "                break\n"
            "            if word1[i] == word2[j]:\n"
            "                ans.append(i)\n"
            "                j += 1\n"
            "            elif not changed:\n"
            "                if j == m - 1 or (last_match[j + 1] != -1 and last_match[j + 1] > i):\n"
            "                    ans.append(i)\n"
            "                    j += 1\n"
            "                    changed = True\n"
            "        return ans if len(ans) == m else []\n"
        ),
    },
    "two-sum": {
        "title": "Two Sum",
        "url": "https://leetcode.com/problems/two-sum/",
        "difficulty": "Easy",
        "code": (
            "class Solution:\n"
            "    def twoSum(self, nums: list[int], target: int) -> list[int]:\n"
            "        seen = {}\n"
            "        for i, num in enumerate(nums):\n"
            "            diff = target - num\n"
            "            if diff in seen:\n"
            "                return [seen[diff], i]\n"
            "            seen[num] = i\n"
            "        return []\n"
        ),
    },
    "palindrome-number": {
        "title": "Palindrome Number",
        "url": "https://leetcode.com/problems/palindrome-number/",
        "difficulty": "Easy",
        "code": (
            "class Solution:\n"
            "    def isPalindrome(self, x: int) -> bool:\n"
            "        if x < 0:\n"
            "            return False\n"
            "        s = str(x)\n"
            "        return s == s[::-1]\n"
        ),
    },
    "roman-to-integer": {
        "title": "Roman to Integer",
        "url": "https://leetcode.com/problems/roman-to-integer/",
        "difficulty": "Easy",
        "code": (
            "class Solution:\n"
            "    def romanToInt(self, s: str) -> int:\n"
            "        mapping = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}\n"
            "        total = 0\n"
            "        prev = 0\n"
            "        for char in reversed(s):\n"
            "            val = mapping[char]\n"
            "            if val < prev:\n"
            "                total -= val\n"
            "            else:\n"
            "                total += val\n"
            "                prev = val\n"
            "        return total\n"
        ),
    },
    "valid-parentheses": {
        "title": "Valid Parentheses",
        "url": "https://leetcode.com/problems/valid-parentheses/",
        "difficulty": "Easy",
        "code": (
            "class Solution:\n"
            "    def isValid(self, s: str) -> bool:\n"
            "        stack = []\n"
            "        mapping = {')': '(', '}': '{', ']': '['}\n"
            "        for char in s:\n"
            "            if char in mapping:\n"
            "                top = stack.pop() if stack else '#'\n"
            "                if mapping[char] != top:\n"
            "                    return False\n"
            "            else:\n"
            "                stack.append(char)\n"
            "        return not stack\n"
        ),
    },
}


class SolutionProvider:
    """Provides Python solution code for standard practice and daily challenge problems."""

    @staticmethod
    def get_solution(slug: str) -> str | None:
        """Resolve solution code for problem title slug."""
        # 1. Local solution map check
        if slug in PRACTICE_SOLUTIONS:
            return PRACTICE_SOLUTIONS[slug]["code"]

        # 2. Dynamic fetch from kamyu104/LeetCode-Solutions
        try:
            import urllib.request
            url = f"https://raw.githubusercontent.com/kamyu104/LeetCode-Solutions/master/Python/{slug}.py"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                code = resp.read().decode("utf-8")
                if "class Solution" in code:
                    # Sanitize Python 2 syntax
                    code = code.replace("xrange", "range")
                    logger.info(f"Successfully dynamically resolved Python solution for '{slug}'")
                    return code
        except Exception as err:
            logger.warning(f"Dynamic solution fetch for '{slug}' failed: {err}")

        return None


class CodingPlatform(ABC):
    """Abstract Base Class for platform integrations."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.validator = ProblemValidator(target_difficulty=config.difficulty)

    @abstractmethod
    async def select_eligible_problem(self, page: Page) -> ProblemInfo | None:
        """Select exactly one eligible non-contest practice problem."""
        pass


class LeetCodePlatform(CodingPlatform):
    """LeetCode Platform Implementation."""

    async def select_eligible_problem(self, page: Page) -> ProblemInfo | None:
        """Select a standard practice problem from LeetCode catalog and validate safety."""
        logger.info("Navigating to LeetCode practice catalog...")
        await page.goto("https://leetcode.com/problemset/all/", wait_until="domcontentloaded", timeout=30000)

        # 1. Attempt to query today's official LeetCode Daily Challenge Question
        try:
            gql_query = (
                "query questionOfToday { "
                "  activeDailyCodingChallengeQuestion { "
                "    date link "
                "    question { title titleSlug difficulty } "
                "  } "
                "}"
            )
            daily_res = await page.evaluate(
                """async (q) => {
                    try {
                        const r = await fetch('https://leetcode.com/graphql/', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ query: q })
                        });
                        return await r.json();
                    } catch (e) { return null; }
                }""",
                gql_query,
            )

            if daily_res and "data" in daily_res:
                daily = daily_res["data"].get("activeDailyCodingChallengeQuestion")
                if daily and "question" in daily:
                    slug = daily["question"]["titleSlug"]
                    title = daily["question"]["title"]
                    diff = daily["question"]["difficulty"]
                    link = daily["link"]
                    url = f"https://leetcode.com{link}"

                    solution_code = SolutionProvider.get_solution(slug)
                    if solution_code:
                        logger.info(f"Official LeetCode Daily Challenge Question found: '{title}' ({url})")
                        problem = ProblemInfo(
                            title=title,
                            url=url,
                            difficulty=diff,
                            is_practice_catalog=True,
                            problem_id=slug,
                            solution_code=solution_code,
                        )
                        valid, reason = self.validator.validate(problem)
                        if valid:
                            logger.info(f"Successfully selected Official Daily Challenge problem: '{title}'")
                            return problem
                    else:
                        logger.warning(f"Could not resolve solution for official daily challenge '{title}' ({slug}). Falling back to practice catalog.")
        except Exception as err:
            logger.warning(f"Could not fetch official Daily Challenge metadata: {err}")

        # 2. Fallback through standard candidate practice problems
        for slug, data in PRACTICE_SOLUTIONS.items():
            url = data["url"]

            # Tier 1 URL Check
            if ContestSafetyGuard.is_contest_url(url):
                logger.warning(f"Candidate problem URL '{url}' matched contest filter! Skipping.")
                continue

            problem = ProblemInfo(
                title=data["title"],
                url=url,
                difficulty=data["difficulty"],
                is_practice_catalog=True,
                problem_id=slug,
                solution_code=data["code"],
            )

            # Validate metadata and eligibility
            valid, reason = self.validator.validate(problem)
            if valid:
                logger.info(f"Successfully selected practice problem: '{problem.title}' ({problem.url})")
                return problem
            else:
                logger.warning(f"Problem '{problem.title}' failed validation: {reason}")

        logger.error("No eligible practice problem passed safety validation.")
        return None


class CodeChefPlatform(CodingPlatform):
    """CodeChef Platform Integration Implementation."""

    async def select_eligible_problem(self, page: Page) -> ProblemInfo | None:
        """Select a standard practice problem from CodeChef catalog."""
        logger.info("Navigating to CodeChef practice catalog...")
        await page.goto("https://www.codechef.com/practice", wait_until="domcontentloaded", timeout=30000)

        for slug, data in CODECHEF_PRACTICE_SOLUTIONS.items():
            url = data["url"]

            if ContestSafetyGuard.is_contest_url(url):
                logger.warning(f"CodeChef problem URL '{url}' matched contest filter! Skipping.")
                continue

            problem = ProblemInfo(
                title=data["title"],
                url=url,
                difficulty=data["difficulty"],
                is_practice_catalog=True,
                problem_id=slug,
                solution_code=data["code"],
            )

            valid, reason = self.validator.validate(problem)
            if valid:
                logger.info(f"Successfully selected CodeChef practice problem: '{problem.title}' ({problem.url})")
                return problem
            else:
                logger.warning(f"CodeChef problem '{problem.title}' failed validation: {reason}")

        logger.error("No eligible CodeChef practice problem passed safety validation.")
        return None


class CodeforcesPlatform(CodingPlatform):
    """Codeforces Platform Integration Implementation."""

    async def select_eligible_problem(self, page: Page) -> ProblemInfo | None:
        """Select a standard practice problem from Codeforces problemset catalog."""
        logger.info("Navigating to Codeforces problemset catalog...")
        await page.goto("https://codeforces.com/problemset", wait_until="domcontentloaded", timeout=30000)

        for slug, data in CODEFORCES_PRACTICE_SOLUTIONS.items():
            url = data["url"]

            if ContestSafetyGuard.is_contest_url(url):
                logger.warning(f"Codeforces problem URL '{url}' matched contest filter! Skipping.")
                continue

            problem = ProblemInfo(
                title=data["title"],
                url=url,
                difficulty=data["difficulty"],
                is_practice_catalog=True,
                problem_id=slug,
                solution_code=data["code"],
            )

            valid, reason = self.validator.validate(problem)
            if valid:
                logger.info(f"Successfully selected Codeforces practice problem: '{problem.title}' ({problem.url})")
                return problem
            else:
                logger.warning(f"Codeforces problem '{problem.title}' failed validation: {reason}")

        logger.error("No eligible Codeforces practice problem passed safety validation.")
        return None


class HackerRankPlatform(CodingPlatform):
    """HackerRank Platform Integration Implementation."""

    async def select_eligible_problem(self, page: Page) -> ProblemInfo | None:
        """Select a standard practice problem from HackerRank Python domain catalog."""
        logger.info("Navigating to HackerRank Python practice catalog...")
        await page.goto("https://www.hackerrank.com/domains/python", wait_until="domcontentloaded", timeout=30000)

        for slug, data in HACKERRANK_PRACTICE_SOLUTIONS.items():
            url = data["url"]

            if ContestSafetyGuard.is_contest_url(url):
                logger.warning(f"HackerRank problem URL '{url}' matched contest filter! Skipping.")
                continue

            problem = ProblemInfo(
                title=data["title"],
                url=url,
                difficulty=data["difficulty"],
                is_practice_catalog=True,
                problem_id=slug,
                solution_code=data["code"],
            )

            valid, reason = self.validator.validate(problem)
            if valid:
                logger.info(f"Successfully selected HackerRank practice problem: '{problem.title}' ({problem.url})")
                return problem
            else:
                logger.warning(f"HackerRank problem '{problem.title}' failed validation: {reason}")

        logger.error("No eligible HackerRank practice problem passed safety validation.")
        return None


CODECHEF_PRACTICE_SOLUTIONS: dict[str, dict[str, str]] = {
    "START01": {
        "title": "Number Mirror",
        "url": "https://www.codechef.com/practice/course/basic-programming-concepts/DIFF500/problems/START01",
        "difficulty": "Easy",
        "code": "n = int(input())\nprint(n)\n",
    },
    "FLOW001": {
        "title": "Add Two Numbers",
        "url": "https://www.codechef.com/practice/course/basic-programming-concepts/DIFF500/problems/FLOW001",
        "difficulty": "Easy",
        "code": (
            "t = int(input())\n"
            "for _ in range(t):\n"
            "    a, b = map(int, input().split())\n"
            "    print(a + b)\n"
        ),
    },
}

CODEFORCES_PRACTICE_SOLUTIONS: dict[str, dict[str, str]] = {
    "4A": {
        "title": "Watermelon",
        "url": "https://codeforces.com/problemset/problem/4/A",
        "difficulty": "Easy",
        "code": (
            "w = int(input())\n"
            "if w > 2 and w % 2 == 0:\n"
            "    print('YES')\n"
            "else:\n"
            "    print('NO')\n"
        ),
    },
    "71A": {
        "title": "Way Too Long Words",
        "url": "https://codeforces.com/problemset/problem/71/A",
        "difficulty": "Easy",
        "code": (
            "n = int(input())\n"
            "for _ in range(n):\n"
            "    s = input().strip()\n"
            "    if len(s) > 10:\n"
            "        print(f'{s[0]}{len(s)-2}{s[-1]}')\n"
            "    else:\n"
            "        print(s)\n"
        ),
    },
}

HACKERRANK_PRACTICE_SOLUTIONS: dict[str, dict[str, str]] = {
    "py-hello-world": {
        "title": "Say Hello, World! With Python",
        "url": "https://www.hackerrank.com/challenges/py-hello-world/problem",
        "difficulty": "Easy",
        "code": 'print("Hello, World!")\n',
    },
    "py-if-else": {
        "title": "Python If-Else",
        "url": "https://www.hackerrank.com/challenges/py-if-else/problem",
        "difficulty": "Easy",
        "code": (
            "n = int(input().strip())\n"
            "if n % 2 != 0:\n"
            "    print('Weird')\n"
            "elif 2 <= n <= 5:\n"
            "    print('Not Weird')\n"
            "elif 6 <= n <= 20:\n"
            "    print('Weird')\n"
            "else:\n"
            "    print('Not Weird')\n"
        ),
    },
}


class PlatformFactory:
    """Factory to instantiate target coding platform."""

    @staticmethod
    def get_platform(config: Config) -> CodingPlatform:
        name = config.platform.lower()
        if name == "leetcode":
            return LeetCodePlatform(config)
        elif name == "codechef":
            return CodeChefPlatform(config)
        elif name == "codeforces":
            return CodeforcesPlatform(config)
        elif name == "hackerrank":
            return HackerRankPlatform(config)
        else:
            raise ValueError(
                f"Unknown platform: '{config.platform}'. Supported: leetcode, codechef, codeforces, hackerrank"
            )

