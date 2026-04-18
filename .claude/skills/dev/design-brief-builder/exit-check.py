#!/usr/bin/env python3
"""
Exit Check: design-brief-builder (PM Direction Gate G1)

Deterministic gate for design brief quality. Verifies visual design
specifications, references, accessibility, and brand guideline presence.

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

DESIGN_PATH = Path(".claude/state/L3-design.md")
SPEC_PATH = Path(".claude/state/L2-spec.md")


def check():
    # ── 1. Design brief must exist ────────────────────────────
    if not DESIGN_PATH.exists():
        add_issue("file_missing", f"{DESIGN_PATH} does not exist.", level="high")
        return

    text = DESIGN_PATH.read_text(encoding="utf-8")

    # ── 2. Must contain at least one hex color ─────────────────
    if not re.search(r"#[0-9A-Fa-f]{3,6}", text):
        add_issue(
            "color_missing",
            "No hex color values found. Design Brief must specify exact colors.",
            level="high",
        )

    # ── 3. Must mention interaction or motion ─────────────────
    if not re.search(r"interaction|motion|animation|transition", text, re.IGNORECASE):
        add_issue(
            "interaction_missing",
            "No interaction or motion guidelines found.",
            level="warning",
        )

    # ── 4. PM Direction Gate (G1) checks ──────────────────────
    check_brand_guideline(text)
    check_accessibility(text)
    check_spec_alignment(text)


def check_brand_guideline(design_content):
    """PM Direction Gate G1: Verify brand guideline reference.

    Design brief must either reference a brand guideline or explicitly
    state "no brand constraints" — ambiguity about brand is a PM decision gap.
    """
    has_brand = re.search(
        r"[Bb]rand\s+[Gg]uideline|[Bb]rand\s+[Gg]uide|品牌规范|品牌指南|"
        r"[Bb]rand\s+[Mm]anual|品牌手册|[Bb]rand\s+book",
        design_content,
        re.IGNORECASE,
    )
    has_no_brand = re.search(
        r"无品牌约束|no\s+brand\s+constraint|no\s+brand\s+guideline|"
        r"no\s+brand\s+reference|无品牌限制|无品牌要求",
        design_content,
        re.IGNORECASE,
    )

    if has_brand:
        add_issue(
            "brand_guideline_found",
            "Design brief references brand guidelines.",
            level="info",
        )
    elif has_no_brand:
        add_issue(
            "no_brand_constraint_explicit",
            "Design brief explicitly states no brand constraints. This is acceptable.",
            level="info",
        )
    else:
        add_issue(
            "brand_guideline_missing",
            "Design brief has no brand guideline reference and does not explicitly "
            "state 'no brand constraints'. PM Direction Gate G1 requires either: "
            "(1) brand guideline reference, or (2) explicit 'no brand constraints' declaration.",
            level="warning",
        )


def check_accessibility(design_content):
    """PM Direction Gate G1: Verify accessibility statement presence."""
    has_a11y = re.search(
        r"accessibility|a11y|可访问|无障碍|WCAG|ARIA|accessibility\s+statement",
        design_content,
        re.IGNORECASE,
    )
    if has_a11y:
        add_issue(
            "accessibility_found",
            "Design brief includes accessibility guidelines.",
            level="info",
        )
    else:
        add_issue(
            "accessibility_missing",
            "Design brief has no accessibility statement. "
            "PM Direction Gate G1: specify WCAG level or explicitly "
            "state accessibility requirements.",
            level="warning",
        )


def check_spec_alignment(design_content):
    """PM Direction Gate G1: Verify design brief aligns with spec."""
    if not SPEC_PATH.exists():
        add_issue(
            "spec_not_found_for_alignment",
            "L2-spec.md not found. Cannot verify design-spec alignment.",
            level="info",
        )
        return

    spec_content = SPEC_PATH.read_text(encoding="utf-8")

    spec_has_target_user = re.search(
        r"[Tt]arget\s+[Uu]ser|目标用户|用户画像|[Uu]ser\s+[Pp]ersona",
        spec_content,
        re.IGNORECASE,
    )
    design_has_user_ref = re.search(
        r"[Tt]arget\s+[Uu]ser|目标用户|用户画像|[Uu]ser\s+[Pp]ersona|"
        r"[Uu]ser\s+[Dd]emographic|受众",
        design_content,
        re.IGNORECASE,
    )

    if spec_has_target_user and not design_has_user_ref:
        add_issue(
            "design_missing_user_alignment",
            "L2-spec defines target users but design brief does not reference them. "
            "PM Direction Gate G1: design direction must align with user persona.",
            level="warning",
        )


def main() -> int:
    check()
    print_and_exit("Design Brief")


if __name__ == "__main__":
    raise SystemExit(main())
