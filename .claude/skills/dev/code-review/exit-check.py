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

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from _utils.exit_check_base import add_issue, print_and_exit

REVIEW_PATH = Path(".claude/state/LAST_REVIEW.md")
SPEC_PATH = Path(".claude/state/L2-spec.md")


def check():
    # ── 1. Review file must exist ──
    if not REVIEW_PATH.exists():
        add_issue(
            "review_file_missing",
            ".claude/state/LAST_REVIEW.md does not exist. "
            "Run code-review skill first.",
            level="high",
        )
        return

    text = REVIEW_PATH.read_text(encoding="utf-8")

    # ── 2. Two-stage review structure ──
    if not re.search(r"Stage\s+1", text, re.IGNORECASE):
        add_issue(
            "stage1_missing",
            "Review does not contain a Stage 1 section. "
            "Every review must check spec compliance first.",
            level="high",
        )

    if not re.search(r"Stage\s+2", text, re.IGNORECASE):
        add_issue(
            "stage2_missing",
            "Review does not contain a Stage 2 section. "
            "Code quality review is needed after spec compliance passes.",
            level="warning",
        )

    # ── 3. Anti-leniency: must have actionable issues ──
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
        add_issue(
            "review_too_lenient",
            "Review contains no actionable issues or suggestions. "
            "Leniency bias detected. Every review must find at least one "
            "concrete problem or improvement.",
            level="warning",
        )

    # ── 4. Multi-dimensional action word verification ──
    # Strong reviews use diverse action words, not just "should"
    diverse_actions = ["must", "needs to", "fix", "refactor", "rename", "add", "remove"]
    found_diverse = [w for w in diverse_actions if w in text.lower()]
    if "should" in text.lower() and len(found_diverse) < 2:
        add_issue(
            "review_action_words_limited",
            "Review relies heavily on 'should' with limited variety of action words. "
            "Stronger reviews use must/needs to/fix/refactor/rename/etc.",
            level="info",
        )

    # ── 5. Stage 1 HIGH must block Stage 2 ──
    stage1_match = re.search(
        r"Stage\s+1(.*?)(?=Stage\s+2|$)", text, re.IGNORECASE | re.DOTALL
    )
    stage1_has_high = False
    if stage1_match:
        stage1_text = stage1_match.group(1)
        in_code_block = False
        for line in stage1_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block or stripped.startswith("#"):
                continue
            if re.search(r"\bHIGH\b", stripped, re.IGNORECASE):
                stage1_has_high = True
                break
    stage2_approved = re.search(
        r"Stage\s+2.*?(passed|approve)", text, re.IGNORECASE | re.DOTALL
    )
    if stage1_has_high and stage2_approved:
        add_issue(
            "high_issue_ignored",
            "Stage 1 has HIGH issues but Stage 2 was approved. "
            "This is a PM Compliance Gate violation.",
            level="high",
        )

    # ── 6. Minimum review length ──
    if len(text.strip()) < 200:
        add_issue(
            "review_too_short",
            f"Review is only {len(text.strip())} chars. "
            f"A meaningful review needs at least 200 chars.",
            level="high",
        )

    # ── 7. Structured validation: template fields ──
    # Check for checklist / verification structure
    has_checklist = bool(re.search(r"[-*]\s+\[[x ]\]", text))
    has_verification = bool(
        re.search(
            r"(fully implemented|partially|missing|extra scope|not found|verified)",
            text,
            re.IGNORECASE,
        )
    )
    if not has_checklist and not has_verification:
        add_issue(
            "review_no_verification_structure",
            "Review lacks structured verification "
            "(checklist or implementation status per item).",
            level="warning",
        )

    # ── 8. Code location reference ──
    has_code_location = bool(
        re.search(
            r"(?:\w+\.\w+:\d+|line\s+\d+|@\w+/\w+|`[^`]+:\d+`|\b\w+\.(?:py|js|ts|jsx|tsx|go|rs|java)\b)",
            text,
            re.IGNORECASE,
        )
    )
    if not has_code_location:
        add_issue(
            "review_no_code_location",
            "Review does not reference specific code locations "
            "(file:line, line N, or file paths).",
            level="warning",
        )

    # ── 9. Spec Gap type detection ──
    has_spec_gap_section = bool(re.search(r"(Spec\s+Gap|GAP-\d+)", text, re.IGNORECASE))
    if has_spec_gap_section:
        gap_types = re.findall(r"\bType\s*[:\-=]?\s*([A-E])\b", text)
        if not gap_types:
            gap_types = re.findall(r"\*\*Type\*\*.*?(A|B|C|D|E)", text)
        if not gap_types:
            add_issue(
                "spec_gap_unclassified",
                "Spec Gap mentioned but not classified with A-E type. "
                "SKILL.md requires Type A/B/C/D/E classification for every gap.",
                level="warning",
            )

    # ── 10. PM Spec Compliance Gate (G3) checks ──
    check_spec_compliance(text)


def check_spec_compliance(review_content):
    """PM Compliance Gate G3: Verify spec coverage and detect scope creep."""
    if not SPEC_PATH.exists():
        add_issue(
            "spec_not_found",
            "L2-spec.md not found. Cannot verify spec compliance. "
            "Run product-spec-builder first.",
            level="warning",
        )
        return

    spec_content = SPEC_PATH.read_text(encoding="utf-8")

    if len(spec_content.strip()) < 100:
        add_issue(
            "spec_too_short",
            f"L2-spec.md is only {len(spec_content.strip())} chars. "
            f"Cannot extract meaningful spec items for compliance check.",
            level="warning",
        )
        return

    # ── 10a. Spec item verification coverage ──
    spec_items = re.findall(r"^[-*]\s+\*\*(.+?)\*\*", spec_content, re.MULTILINE)

    if spec_items and len(spec_items) >= 3:
        unverified = []
        for item in spec_items[:30]:
            item_key = re.sub(r"[^\w\s]", "", item.lower()).strip()
            review_lower = review_content.lower()
            item_words = [w for w in item_key.split() if len(w) > 2]
            if item_words:
                matched_words = sum(1 for w in item_words if w in review_lower)
                coverage_ratio = matched_words / len(item_words)
                if coverage_ratio < 0.5:
                    unverified.append(item)

        if unverified and len(unverified) >= len(spec_items) * 0.3:
            add_issue(
                "spec_items_not_verified",
                f"{len(unverified)} of {len(spec_items)} spec items appear "
                f"unverified in review. Missing: "
                f"{', '.join(unverified[:5])}"
                f"{'...' if len(unverified) > 5 else ''}. "
                f"Stage 1 must verify each spec item.",
                level="warning",
            )

    # ── 10b. Scope creep detection ──
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
            add_issue(
                "potential_scope_creep",
                "Review mentions scope beyond spec — "
                "PM should confirm whether to accept, reject, or defer. "
                "(Spec Gap Protocol: classify as A/B/C/D/E)",
                level="warning",
            )
            break

    # ── 10c. HIGH issue user impact assessment ──
    stage1_match = re.search(
        r"Stage\s+1(.*?)(?=Stage\s+2|$)",
        review_content,
        re.IGNORECASE | re.DOTALL,
    )
    if stage1_match:
        stage1_text = stage1_match.group(1)
        # Find lines containing "HIGH" (issue markers), excluding code blocks and headings
        in_code_block = False
        high_lines = []
        for line in stage1_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
            if stripped.startswith("#"):
                continue
            if re.search(r"\bHIGH\b", stripped, re.IGNORECASE):
                high_lines.append(stripped)
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
                add_issue(
                    "high_issue_no_user_impact",
                    f"HIGH issue without user impact assessment: "
                    f"{line[:80]}... — PM Compliance Gate requires "
                    f"user impact for every HIGH issue.",
                    level="info",
                )


def main() -> int:
    check()
    print_and_exit("Code Review")


if __name__ == "__main__":
    raise SystemExit(main())
