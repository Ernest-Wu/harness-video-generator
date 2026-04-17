#!/usr/bin/env python3
"""
Exit Check: code-review (PM Compliance Gate G3)

Deterministic gate for code review rigor. Prevents LLM reviewer leniency bias
and enforces PM compliance checks (spec coverage, scope creep, user impact).

Severity levels:
  - high:   Blocks progress. Must fix before proceeding.
  - warning: Does not block, but PM should review.
  - info:   Informational, for traceability.
"""

import re
import sys
from pathlib import Path

REVIEW_PATH = Path(".claude/state/LAST_REVIEW.md")
SPEC_PATH = Path(".claude/state/L2-spec.md")

ISSUES = []


def check():
    # ──────────────────────────────────────────
    # 1. Review file must exist
    # ──────────────────────────────────────────
    if not REVIEW_PATH.exists():
        ISSUES.append(
            (
                "high",
                "review_file_missing",
                ".claude/state/LAST_REVIEW.md does not exist. "
                "Run code-review skill first.",
            )
        )
        return

    text = REVIEW_PATH.read_text(encoding="utf-8")

    # ──────────────────────────────────────────
    # 2. Two-stage review structure
    # ──────────────────────────────────────────
    if not re.search(r"Stage\s+1", text, re.IGNORECASE):
        ISSUES.append(
            (
                "high",
                "stage1_missing",
                "Review does not contain a Stage 1 section. "
                "Every review must check spec compliance first.",
            )
        )

    if not re.search(r"Stage\s+2", text, re.IGNORECASE):
        ISSUES.append(
            (
                "warning",
                "stage2_missing",
                "Review does not contain a Stage 2 section. "
                "Code quality review is needed after spec compliance passes.",
            )
        )

    # ──────────────────────────────────────────
    # 3. Anti-leniency: must have actionable issues
    # ──────────────────────────────────────────
    action_words = [
        "should",
        "needs to",
        "missing",
        "incorrect",
        "rename",
        "refactor",
        "fix",
        "add",
        "remove",
        "consider",
        "suggest",
    ]
    if not any(w in text.lower() for w in action_words):
        ISSUES.append(
            (
                "warning",
                "review_too_lenient",
                "Review contains no actionable issues or suggestions. "
                "Leniency bias detected. Every review must find at least one "
                "concrete problem or improvement.",
            )
        )

    # ──────────────────────────────────────────
    # 4. Stage 1 HIGH must block Stage 2
    # ──────────────────────────────────────────
    stage1_high = re.search(r"Stage\s+1.*?HIGH", text, re.IGNORECASE | re.DOTALL)
    stage2_approved = re.search(
        r"Stage\s+2.*?(passed|approve)", text, re.IGNORECASE | re.DOTALL
    )
    if stage1_high and stage2_approved:
        ISSUES.append(
            (
                "high",
                "high_issue_ignored",
                "Stage 1 has HIGH issues but Stage 2 was approved. "
                "This is a PM Compliance Gate violation.",
            )
        )

    # ──────────────────────────────────────────
    # 5. Minimum review length
    # ──────────────────────────────────────────
    if len(text.strip()) < 200:
        ISSUES.append(
            (
                "high",
                "review_too_short",
                f"Review is only {len(text.strip())} chars. "
                f"A meaningful review needs at least 200 chars.",
            )
        )

    # ──────────────────────────────────────────
    # 6. PM Spec Compliance Gate (G3) checks
    # ──────────────────────────────────────────
    check_spec_compliance(text)


def check_spec_compliance(review_content):
    """PM Compliance Gate G3: Verify spec coverage and detect scope creep.

    Reads L2-spec.md to extract feature items, then cross-references
    with the review to verify each item has a verification result.
    Also detects scope creep and checks HIGH issues for user impact.
    """
    if not SPEC_PATH.exists():
        ISSUES.append(
            (
                "warning",
                "spec_not_found",
                "L2-spec.md not found. Cannot verify spec compliance. "
                "Run product-spec-builder first.",
            )
        )
        return

    spec_content = SPEC_PATH.read_text(encoding="utf-8")

    if len(spec_content.strip()) < 100:
        ISSUES.append(
            (
                "warning",
                "spec_too_short",
                f"L2-spec.md is only {len(spec_content.strip())} chars. "
                f"Cannot extract meaningful spec items for compliance check.",
            )
        )
        return

    # ── 6a. Spec item verification coverage ──────────────────────
    # Extract feature items from L2-spec (bullet points with bold names)
    # Pattern matches: "- **Feature Name**: description" or "- *Feature Name*"
    spec_items = re.findall(r"^[-*]\s+\*\*(.+?)\*\*", spec_content, re.MULTILINE)

    if spec_items and len(spec_items) >= 3:
        # Check how many spec items are referenced in the review
        unverified = []
        for item in spec_items[:30]:  # limit to first 30 to avoid noise
            # Normalize item name for matching (remove punctuation, lowercase)
            item_key = re.sub(r"[^\w\s]", "", item.lower()).strip()
            # Check if review mentions this feature
            review_lower = review_content.lower()
            # Split item into words and check if at least 2 key words appear
            item_words = [w for w in item_key.split() if len(w) > 2]
            if item_words:
                matched_words = sum(1 for w in item_words if w in review_lower)
                coverage_ratio = matched_words / len(item_words)
                if coverage_ratio < 0.5:
                    unverified.append(item)

        if unverified and len(unverified) >= len(spec_items) * 0.3:
            ISSUES.append(
                (
                    "warning",
                    "spec_items_not_verified",
                    f"{len(unverified)} of {len(spec_items)} spec items appear "
                    f"unverified in review. Missing: "
                    f"{', '.join(unverified[:5])}"
                    f"{'...' if len(unverified) > 5 else ''}. "
                    f"Stage 1 must verify each spec item.",
                )
            )

    # ── 6b. Scope creep detection ───────────────────────────────
    scope_creep_patterns = [
        r"[Ee]xtra\s+[Ss]cope",
        r"超出规格",
        r"额外功能",
        r"[Bb]eyond\s+[Ss]pec",
        r"[Nn]ot\s+in\s+[Ss]pec",
        r"[Aa]dditional\s+feature",
        r"[Ss]cope\s+creep",
    ]
    for pattern in scope_creep_patterns:
        if re.search(pattern, review_content):
            ISSUES.append(
                (
                    "warning",
                    "potential_scope_creep",
                    "Review mentions scope beyond spec — "
                    "PM should confirm whether to accept, reject, or defer. "
                    "(Spec Gap Protocol: classify as A/B/C/D/E)",
                )
            )
            break  # only one scope creep warning needed

    # ── 6c. HIGH issue user impact assessment ────────────────────
    # Find Stage 1 section for HIGH issue analysis
    stage1_match = re.search(
        r"Stage\s+1(.*?)(?=Stage\s+2|$)",
        review_content,
        re.IGNORECASE | re.DOTALL,
    )
    if stage1_match:
        stage1_text = stage1_match.group(1)
        # Find lines containing "HIGH" (issue markers)
        high_lines = [
            line.strip()
            for line in stage1_text.splitlines()
            if re.search(r"\bHIGH\b", line, re.IGNORECASE)
        ]
        for line in high_lines:
            impact_keywords = [
                r"user\s+impact",
                r"用户影响",
                r"[Uu]ser",
                r"[Ff]rontend",
                r"UX",
                r"customer",
                r"客户",
            ]
            has_impact = any(
                re.search(kw, line, re.IGNORECASE) for kw in impact_keywords
            )
            if not has_impact:
                ISSUES.append(
                    (
                        "info",
                        "high_issue_no_user_impact",
                        f"HIGH issue without user impact assessment: "
                        f"{line[:80]}... — PM Compliance Gate requires "
                        f"user impact for every HIGH issue.",
                    )
                )


def main() -> int:
    check()

    high_issues = [i for i in ISSUES if i[0] == "high"]
    warning_issues = [i for i in ISSUES if i[0] == "warning"]
    info_issues = [i for i in ISSUES if i[0] == "info"]

    # Summary
    print("═══ Code Review Exit Check (PM Compliance Gate G3) ═══")
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

    # Hard Gate: any HIGH issue blocks review
    if high_issues:
        print(
            "❌ Code review exit check FAILED — resolve HIGH issues before proceeding."
        )
        return 1

    if warning_issues:
        print(
            "⚠️  Code review exit check PASSED with warnings — "
            "PM should review before proceeding."
        )
    else:
        print(
            "✅ Code review exit check passed. "
            "Review meets minimum rigor and spec compliance."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
