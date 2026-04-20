#!/usr/bin/env python3
"""
PM Distribution Gate (CG4) — Exit Check
Validates that content has a complete distribution plan before publishing.
Ensures metadata, UTM tracking, and compliance are defined.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from _utils.exit_check_base import add_issue, print_and_exit, ensure_project_root

PROJECT_ROOT = Path(".")
STATE_DIR = PROJECT_ROOT / ".claude" / "state"
L6_DISTRIBUTION = STATE_DIR / "L6-distribution.md"


def check_l6_exists():
    if not L6_DISTRIBUTION.exists():
        add_issue(
            "file_missing",
            "L6-distribution.md does not exist — create distribution plan before publishing",
            level="high",
        )
        return False
    return True


def check_required_sections():
    if not L6_DISTRIBUTION.exists():
        return

    content = L6_DISTRIBUTION.read_text(encoding="utf-8")

    required = {
        "## Platform Strategy": "platform_strategy_missing",
        "## Compliance Checklist": "compliance_missing",
    }

    for section, code in required.items():
        if section not in content:
            add_issue(
                code,
                f"L6-distribution.md missing required section: {section}",
                level="high",
            )


def check_platform_count():
    if not L6_DISTRIBUTION.exists():
        return

    content = L6_DISTRIBUTION.read_text(encoding="utf-8")

    platform_count = content.count("### ")
    if platform_count < 1:
        add_issue(
            "no_platforms",
            "L6-distribution.md must list at least one platform",
            level="high",
        )


def check_utm_tracking():
    if not L6_DISTRIBUTION.exists():
        return

    content = L6_DISTRIBUTION.read_text(encoding="utf-8")

    if "## UTM Tracking" not in content:
        add_issue(
            "utm_missing",
            "L6-distribution.md missing UTM Tracking section — CG5 validation will be impossible without tracking",
            level="warning",
        )


def check_compliance_items():
    if not L6_DISTRIBUTION.exists():
        return

    content = L6_DISTRIBUTION.read_text(encoding="utf-8")

    if "## Compliance Checklist" in content:
        section = content.split("## Compliance Checklist")[1].split("##")[0]
        unchecked = section.count("[ ]")
        checked = section.count("[x]")
        if unchecked == 0 and checked == 0:
            add_issue(
                "compliance_empty",
                "Compliance Checklist has no items — add at least copyright and ad disclosure checks",
                level="warning",
            )


def main() -> int:
    ensure_project_root()
    check_l6_exists()
    check_required_sections()
    check_platform_count()
    check_utm_tracking()
    check_compliance_items()

    print_and_exit("PM Distribution Gate")


if __name__ == "__main__":
    raise SystemExit(main())
