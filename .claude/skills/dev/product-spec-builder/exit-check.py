#!/usr/bin/env python3
"""
Exit Check: product-spec-builder
Deterministic compliance checker for Product Spec outputs.
"""

import re
import sys
from pathlib import Path

SPEC_PATH = Path(".claude/state/L2-spec.md")

REQUIRED_SECTIONS = [
    ("problem", r"Problem\s+Statement|问题陈述|背景"),
    ("user", r"Target\s+User|目标用户|用户画像"),
    ("features", r"Core\s+Features|核心功能|功能列表"),
    ("metrics", r"Success\s+Metrics|成功指标|验收标准|Metrics"),
    ("scope", r"Scope|范围|In\s+Scope|Out\s+of\s+Scope"),
]

QUANTIFIER_RE = re.compile(
    r"\d+%?|\d+\s*(days?|weeks?|months?|hours?|minutes?)"
    r"|提升|降低|减少|增加|baseline|target|from\s+\d",
    re.IGNORECASE,
)

ISSUES = []


def check():
    if not SPEC_PATH.exists():
        ISSUES.append(("high", "file_missing", f"{SPEC_PATH} does not exist."))
        return

    text = SPEC_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()

    # 1. Required sections
    for code, pattern in REQUIRED_SECTIONS:
        if not any(
            re.search(rf"^##\s+.*{pattern}.*$", line, re.IGNORECASE) for line in lines
        ):
            ISSUES.append(
                (
                    "high",
                    f"section_missing:{code}",
                    f"Missing required section matching: {pattern}. "
                    f"Downstream Agents will have no execution baseline.",
                )
            )

    # 2. Metrics must be quantified
    metrics_section = extract_section(
        text, r"Success\s+Metrics|成功指标|验收标准|Metrics"
    )
    if metrics_section and not QUANTIFIER_RE.search(metrics_section):
        ISSUES.append(
            (
                "high",
                "metrics_not_quantified",
                "Success Metrics contains no numbers, percentages, or time units. "
                "'Improve productivity' is not a metric. 'Increase weekly output from 2000 to 2500 words within 30 days' is.",
            )
        )

    # 3. Scope must have Out-of-Scope
    scope_section = extract_section(text, r"Scope|范围")
    if scope_section:
        if not re.search(
            r"Out\s+of\s+[Ss]cope|不在范围|排除|Not\s+included",
            scope_section,
            re.IGNORECASE,
        ):
            ISSUES.append(
                (
                    "high",
                    "scope_boundary_missing",
                    "No explicit Out-of-Scope found. Scope creep is guaranteed.",
                )
            )

    # 4. Length check
    body = text.split("---", 2)[-1] if text.startswith("---") else text
    if len(body.strip()) < 400:
        ISSUES.append(
            (
                "high",
                "spec_too_short",
                f"Body is only {len(body.strip())} chars. A usable spec needs at least 400 chars to constrain downstream Agents.",
            )
        )

    # 5. Must not be marketing fluff
    fluff_words = [
        "revolutionize",
        "disrupt",
        "leverage",
        "synergy",
        "transform",
        "ecosystem",
    ]
    found_fluff = [w for w in fluff_words if w.lower() in body.lower()]
    if found_fluff:
        ISSUES.append(
            (
                "warning",
                "marketing_fluff_detected",
                f"Spec contains buzzwords: {', '.join(found_fluff)}. This is an execution contract, not a pitch deck.",
            )
        )

    # ── PM Decision Quality Checks (warning level) ─────────────
    check_decision_quality(text)


def check_decision_quality(spec_content):
    warnings = []

    if not re.search(
        r"P[0-2]|优先级|priority|MVP|Must Have", spec_content, re.IGNORECASE
    ):
        warnings.append(
            (
                "features_not_prioritized",
                "Core Features lack priority ranking (P0/P1/P2 or Must/Should/Nice). "
                "Without prioritization, downstream Agents cannot distinguish MVP from nice-to-have.",
            )
        )

    if not re.search(r"假设|assumption|hypothesis", spec_content, re.IGNORECASE):
        warnings.append(
            (
                "no_stated_assumptions",
                "Spec has no stated assumptions. Consider using discovery-interview-prep "
                "to validate key assumptions before committing to implementation.",
            )
        )

    if not re.search(
        r"MVP|最小可行|v1|phase.?0|Must Have", spec_content, re.IGNORECASE
    ):
        warnings.append(
            (
                "no_mvp_boundary",
                "No MVP boundary defined. Which features must ship in Phase 0? "
                "Without this, scope creep is guaranteed.",
            )
        )

    if not re.search(
        r"业务目标|business.goal|Business Goal|objective|OKR",
        spec_content,
        re.IGNORECASE,
    ):
        warnings.append(
            (
                "no_business_goal",
                "Spec lacks a Business Goal link. Success Metrics should tie to company strategy, "
                "not just product-level numbers.",
            )
        )

    # Warnings don't block, but they surface PM decision gaps
    for code, detail in warnings:
        ISSUES.append(("warning", code, detail))


def extract_section(text: str, pattern: str) -> str | None:
    non_capturing = re.sub(r"\((?!\?)", "(?:", pattern)
    regex = re.compile(
        rf"^##\s+.*{non_capturing}.*$\n?(.*?)(?=^##\s|\Z)",
        re.MULTILINE | re.IGNORECASE | re.DOTALL,
    )
    match = regex.search(text)
    return match.group(1) if match else None


def main() -> int:
    check()

    high_issues = [i for i in ISSUES if i[0] == "high"]
    warning_issues = [i for i in ISSUES if i[0] == "warning"]
    info_issues = [i for i in ISSUES if i[0] == "info"]
    legacy_issues = [
        i
        for i in ISSUES
        if isinstance(i[0], str) and i[0] not in ("high", "warning", "info")
    ]

    print("═══ Product Spec Exit Check (PM Discovery Gate G0) ═══")
    print()
    for level, code, detail in info_issues:
        print(f"  ℹ️  [{code}] {detail}")
    print()
    for level, code, detail in warning_issues:
        print(f"  ⚠️  [{code}] {detail}")
    print()
    for code, detail in legacy_issues:
        print(f"  ❌ [{code}] {detail}")
    for level, code, detail in high_issues:
        print(f"  ❌ [{code}] {detail}")

    print()
    blocking = high_issues + legacy_issues
    total_info = len(info_issues)
    total_warning = len(warning_issues)
    total_blocking = len(blocking)
    print(
        f"  Total: {total_blocking} blocking, {total_warning} warning, {total_info} info"
    )
    print()

    if blocking:
        print(
            "❌ Product Spec exit check FAILED — "
            "resolve blocking issues before proceeding."
        )
        return 1

    if warning_issues:
        print(
            "⚠️  Product Spec exit check PASSED with warnings — "
            "PM should review decision quality."
        )
    else:
        print("✅ Product Spec passes exit check. Decision-ready baseline.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
