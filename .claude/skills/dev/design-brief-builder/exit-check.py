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

DESIGN_PATH = Path(".claude/state/L3-design.md")
SPEC_PATH = Path(".claude/state/L2-spec.md")

ISSUES = []


def check():
    # ── 1. Design brief must exist ────────────────────────────
    if not DESIGN_PATH.exists():
        ISSUES.append(("high", "file_missing", f"{DESIGN_PATH} does not exist."))
        return

    text = DESIGN_PATH.read_text(encoding="utf-8")

    # ── 2. Must contain at least one hex color ─────────────────
    if not re.search(r"#[0-9A-Fa-f]{3,6}", text):
        ISSUES.append(
            (
                "high",
                "color_missing",
                "No hex color values found. Design Brief must specify exact colors.",
            )
        )

    # ── 3. Must mention interaction or motion ─────────────────
    if not re.search(r"interaction|motion|animation|transition", text, re.IGNORECASE):
        ISSUES.append(
            (
                "warning",
                "interaction_missing",
                "No interaction or motion guidelines found.",
            )
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
        ISSUES.append(
            (
                "info",
                "brand_guideline_found",
                "Design brief references brand guidelines.",
            )
        )
    elif has_no_brand:
        ISSUES.append(
            (
                "info",
                "no_brand_constraint_explicit",
                "Design brief explicitly states no brand constraints. This is acceptable.",
            )
        )
    else:
        ISSUES.append(
            (
                "warning",
                "brand_guideline_missing",
                "Design brief has no brand guideline reference and does not explicitly "
                "state 'no brand constraints'. PM Direction Gate G1 requires either: "
                "(1) brand guideline reference, or (2) explicit 'no brand constraints' declaration.",
            )
        )


def check_accessibility(design_content):
    """PM Direction Gate G1: Verify accessibility statement presence."""
    has_a11y = re.search(
        r"accessibility|a11y|可访问|无障碍|WCAG|ARIA|accessibility\s+statement",
        design_content,
        re.IGNORECASE,
    )
    if has_a11y:
        ISSUES.append(
            (
                "info",
                "accessibility_found",
                "Design brief includes accessibility guidelines.",
            )
        )
    else:
        ISSUES.append(
            (
                "warning",
                "accessibility_missing",
                "Design brief has no accessibility statement. "
                "PM Direction Gate G1: specify WCAG level or explicitly "
                "state accessibility requirements.",
            )
        )


def check_spec_alignment(design_content):
    """PM Direction Gate G1: Verify design brief aligns with spec."""
    if not SPEC_PATH.exists():
        ISSUES.append(
            (
                "info",
                "spec_not_found_for_alignment",
                "L2-spec.md not found. Cannot verify design-spec alignment.",
            )
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
        ISSUES.append(
            (
                "warning",
                "design_missing_user_alignment",
                "L2-spec defines target users but design brief does not reference them. "
                "PM Direction Gate G1: design direction must align with user persona.",
            )
        )


def main() -> int:
    check()

    high_issues = [i for i in ISSUES if i[0] == "high"]
    warning_issues = [i for i in ISSUES if i[0] == "warning"]
    info_issues = [i for i in ISSUES if i[0] == "info"]

    print("═══ Design Brief Exit Check (PM Direction Gate G1) ═══")
    print()
    for level, code, detail in info_issues:
        print(f"  ℹ️  [{code}] {detail}")
    print()
    for level, code, detail in warning_issues:
        print(f"  ⚠️  [{code}] {detail}")
    print()
    for level, code, detail in high_issues:
        print(f"  ❌ [{code}] {detail}")

    print()
    print(
        f"  Total: {len(high_issues)} high, "
        f"{len(warning_issues)} warning, {len(info_issues)} info"
    )
    print()

    if high_issues:
        print(
            "❌ Design Brief exit check FAILED — resolve HIGH issues before proceeding."
        )
        return 1

    if warning_issues:
        print(
            "⚠️  Design Brief exit check PASSED with warnings — "
            "PM should review direction alignment."
        )
    else:
        print("✅ Design Brief passes exit check. Direction alignment verified.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
