#!/usr/bin/env python3
"""
PM Content Strategy Gate (CG0) — Exit Check
Validates that content strategy is defined before production begins.
Ensures target audience, business goal, and KPI are specified.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from _utils.exit_check_base import add_issue, print_and_exit, ensure_project_root

# Use relative path for PROJECT_ROOT
PROJECT_ROOT = Path(".")

STATE_DIR = PROJECT_ROOT / ".claude" / "state"
L0_STRATEGY = STATE_DIR / "L0-strategy.md"


def check_l0_exists():
    """L0-strategy.md must exist for CG0."""
    if not L0_STRATEGY.exists():
        add_issue(
            "file_missing",
            "L0-strategy.md does not exist — create content strategy before production",
            level="high",
        )
        return False
    return True


def check_required_sections():
    """L0-strategy.md must contain required strategic sections."""
    if not L0_STRATEGY.exists():
        return

    content = L0_STRATEGY.read_text(encoding="utf-8")

    required_sections = {
        "## Target Audience": "target_audience_missing",
        "## Business Goal": "business_goal_missing",
        "## KPI": "kpi_missing",
    }

    for section, code in required_sections.items():
        if section not in content:
            add_issue(
                code,
                f"L0-strategy.md missing required section: {section}",
                level="high",
            )


def check_target_audience_specificity():
    """Target audience must be specific (not just 'everyone' or 'users')."""
    if not L0_STRATEGY.exists():
        return

    content = L0_STRATEGY.read_text(encoding="utf-8")

    # Extract Target Audience section
    if "## Target Audience" in content:
        section = content.split("## Target Audience")[1].split("##")[0]

        # Check for vague audience references
        vague_patterns = [
            r"anyone",
            r"everyone",
            r"all users",
            r"general audience",
            r"any person",
        ]
        for pattern in vague_patterns:
            if re.search(pattern, section, re.IGNORECASE):
                add_issue(
                    "vague_audience",
                    "Target audience is too vague — define specific segment (age, interests, pain points)",
                    level="warning",
                )
                break


def check_kpi_quantified():
    """KPI must include at least one quantified metric with target number."""
    if not L0_STRATEGY.exists():
        return

    content = L0_STRATEGY.read_text(encoding="utf-8")

    if "## KPI" in content:
        kpi_section = content.split("## KPI")[1].split("##")[0]

        # Should contain at least one number (%, views, rate, etc.)
        has_number = bool(re.search(r"\d+", kpi_section))
        if not has_number:
            add_issue(
                "kpi_not_quantified",
                "KPI section must include at least one quantified metric with a target number",
                level="high",
            )


def check_differentiation():
    """Differentiation strategy should be present."""
    if not L0_STRATEGY.exists():
        return

    content = L0_STRATEGY.read_text(encoding="utf-8")

    if "## Differentiation Strategy" not in content:
        if "## Differentiation" not in content:
            add_issue(
                "diff_missing",
                "L0-strategy.md missing Differentiation Strategy — how does this content stand out?",
                level="warning",
            )


def check_compliance():
    """Compliance requirements section should exist."""
    if not L0_STRATEGY.exists():
        return

    content = L0_STRATEGY.read_text(encoding="utf-8")

    if "## Compliance" not in content:
        add_issue(
            "compliance_missing",
            "L0-strategy.md missing Compliance Requirements section — add even if 'none'",
            level="warning",
        )


def main() -> int:
    ensure_project_root()
    check_l0_exists()
    check_required_sections()
    check_target_audience_specificity()
    check_kpi_quantified()
    check_differentiation()
    check_compliance()

    print_and_exit("PM Content Strategy Gate")


if __name__ == "__main__":
    raise SystemExit(main())
