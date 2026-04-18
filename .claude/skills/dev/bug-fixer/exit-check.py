#!/usr/bin/env python3
"""
Exit Check: bug-fixer (Hard Gate)

Deterministic gate verifying that bug fixes are properly documented
and follow the systematic debugging methodology.

Severity levels:
  - high:   Blocks progress. Must fix before proceeding.
  - warning: Does not block, but PM should review.
  - info:   Informational, for traceability.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from _utils.exit_check_base import add_issue, print_and_exit

REPORT_PATH = Path(".claude/state/LAST_BUGFIX.md")


def check():
    # ── HARD GATE: LAST_BUGFIX.md must exist ──
    if not REPORT_PATH.exists():
        add_issue(
            "fix_report_missing",
            f"{REPORT_PATH} does not exist. "
            "bug-fixer must document the fix before marking complete.",
            level="high",
        )
        return

    text = REPORT_PATH.read_text(encoding="utf-8")

    # ── HARD GATE: Report must contain structured debugging evidence ──
    has_hypothesis = bool(re.search(r"hypothesis|假设", text, re.IGNORECASE))
    has_evidence = bool(
        re.search(r"evidence|证据|stack.?trace|日志|log", text, re.IGNORECASE)
    )
    has_root_cause = bool(re.search(r"root.?cause|根因|根本原因", text, re.IGNORECASE))

    evidence_count = sum([has_hypothesis, has_evidence, has_root_cause])
    if evidence_count == 0:
        add_issue(
            "fix_report_weak",
            "Bug fix report lacks hypothesis, evidence, or root cause. "
            "Must include at least one structured debugging element.",
            level="high",
        )
    elif evidence_count == 1:
        add_issue(
            "fix_report_partial",
            "Bug fix report has only one debugging element. "
            "Best practice: include hypothesis, evidence, AND root cause.",
            level="warning",
        )

    # ── HARD GATE: Minimum report length ──
    if len(text.strip()) < 100:
        add_issue(
            "fix_report_too_short",
            f"Bug fix report is only {len(text.strip())} chars. "
            "A meaningful fix report needs at least 100 chars.",
            level="high",
        )

    # ── WARNING: Check for escalation pattern (3+ attempts) ──
    attempt_markers = re.findall(
        r"(?:attempt|try|attempt|尝试|第\s*\d+\s*次)", text, re.IGNORECASE
    )
    if len(attempt_markers) >= 3:
        add_issue(
            "escalation_needed",
            f"Bug fix has {len(attempt_markers)}+ attempt markers. "
            "Consider architectural review per SKILL.md Pitfall 3.",
            level="warning",
        )

    # ── INFO: Check for test verification ──
    has_test_verification = bool(
        re.search(
            r"test.*pass|regression|verified|验证|测试通过|回归", text, re.IGNORECASE
        )
    )
    if not has_test_verification:
        add_issue(
            "no_test_verification",
            "Bug fix report does not mention test verification. "
            "SKILL.md Stage 4 requires running failing test + full test suite.",
            level="info",
        )

    # ── INFO: Check for business impact ──
    has_impact = bool(
        re.search(
            r"business.?impact|user.?impact|priority|业务影响|用户影响|优先级",
            text,
            re.IGNORECASE,
        )
    )
    if not has_impact:
        add_issue(
            "no_business_impact",
            "Bug fix report does not mention business/user impact. "
            "PM Gate: bug priority should map to business impact (MoSCoW).",
            level="info",
        )


def main() -> int:
    check()
    print_and_exit("Bug Fixer")


if __name__ == "__main__":
    raise SystemExit(main())
