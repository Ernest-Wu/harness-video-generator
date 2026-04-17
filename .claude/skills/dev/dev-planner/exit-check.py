#!/usr/bin/env python3
"""
Exit Check: dev-planner (PM Scope Gate G2)

Deterministic gate for dev plan rigor. Verifies plan structure,
Phase→Spec mapping, business goal alignment, and MVP boundaries.

Severity levels:
  - high:   Blocks progress. Must fix before proceeding.
  - warning: Does not block, but PM should review.
  - info:   Informational, for traceability.
"""

import re
import sys
from pathlib import Path

PLAN_PATH = Path(".claude/state/L4-plan.md")
SPEC_PATH = Path(".claude/state/L2-spec.md")

ISSUES = []


def check():
    # ── 1. Plan file must exist ────────────────────────────────
    if not PLAN_PATH.exists():
        ISSUES.append(("high", "file_missing", f"{PLAN_PATH} does not exist."))
        return

    text = PLAN_PATH.read_text(encoding="utf-8")

    # ── 2. Must have Phase sections ────────────────────────────
    phases = re.findall(r"^##\s+.*Phase.*$", text, re.MULTILINE | re.IGNORECASE)
    if len(phases) < 2:
        ISSUES.append(
            ("high", "phases_too_few", "DEV-PLAN should have at least 2 Phases.")
        )

    # ── 3. Must mention deliverables or dependencies ───────────
    if not re.search(r"deliverable|dependency|task", text, re.IGNORECASE):
        ISSUES.append(
            ("high", "plan_too_vague", "No deliverables, dependencies, or tasks found.")
        )

    # ── 4. PM Scope Gate (G2) checks ───────────────────────────
    check_phase_spec_mapping(text)


def check_phase_spec_mapping(plan_content):
    """PM Scope Gate G2: Verify Phase→Spec feature mapping and MVP boundaries.

    Reads L2-spec.md to extract prioritized features (P0/P1/P2),
    then cross-references with L4-plan.md to verify:
    1. Each Phase maps to spec features
    2. P0 features are in MVP/Phase 0
    3. Business goal alignment exists
    4. MVP boundary is confirmed
    """
    if not SPEC_PATH.exists():
        ISSUES.append(
            (
                "warning",
                "spec_not_found",
                "L2-spec.md not found. Cannot verify Phase→Spec mapping. "
                "Run product-spec-builder first.",
            )
        )
        return

    spec_content = SPEC_PATH.read_text(encoding="utf-8")

    # ── 4a. Feature-Phase Mapping check ────────────────────────
    has_feature_phase_mapping = re.search(
        r"Feature.Phase\s+Mapping|Phase.*Feature|feature.*mapping",
        plan_content,
        re.IGNORECASE,
    )

    if has_feature_phase_mapping:
        ISSUES.append(
            (
                "info",
                "feature_phase_mapping_found",
                "Feature-Phase Mapping section found in plan.",
            )
        )
    else:
        phase_sections = re.findall(
            r"^##\s+.*Phase\s*(\d+)", plan_content, re.MULTILINE | re.IGNORECASE
        )
        if phase_sections:
            ISSUES.append(
                (
                    "warning",
                    "no_feature_phase_mapping",
                    "Plan has Phase sections but no Feature-Phase Mapping. "
                    "Each Phase should reference which Spec features it delivers. "
                    "(PM Scope Gate G2: Phase↔Feature alignment required)",
                )
            )

    # ── 4b. P0 features in MVP check ──────────────────────────
    p0_features = re.findall(r"P0.*?—.*?$", spec_content, re.MULTILINE | re.IGNORECASE)
    if p0_features:
        plan_lower = plan_content.lower()
        mvp_section = re.search(
            r"MVP\s+Boundary|MVP\s+Scope|Phase\s*0|最小可行",
            plan_content,
            re.IGNORECASE,
        )
        if mvp_section:
            mvp_text = plan_content[
                mvp_section.start() : min(mvp_section.end() + 500, len(plan_content))
            ]
            p0_in_mvp = sum(
                1
                for f in p0_features
                if re.sub(r"[^\w\s]", "", f.lower()).split()[0:3]
                and any(
                    w in mvp_text.lower()
                    for w in re.sub(r"[^\w\s]", "", f.lower()).split()[:3]
                )
            )
            ISSUES.append(
                (
                    "info",
                    "p0_features_found",
                    f"Found {len(p0_features)} P0 features in spec, "
                    f"{p0_in_mvp} referenced in MVP section.",
                )
            )
        else:
            ISSUES.append(
                (
                    "warning",
                    "no_mvp_in_plan",
                    "Spec has P0 features but plan has no MVP Boundary/Phase 0 section. "
                    "P0 features must be in MVP. (PM Scope Gate G2)",
                )
            )
    else:
        has_priority = re.search(
            r"P[0-2]|优先级|priority|Must\s+Have", spec_content, re.IGNORECASE
        )
        if not has_priority:
            ISSUES.append(
                (
                    "warning",
                    "no_priority_in_spec",
                    "L2-spec.md has no priority markers (P0/P1/P2). "
                    "Cannot verify which features belong in MVP.",
                )
            )

    # ── 4c. Business Goal alignment ───────────────────────────
    has_business_goal_in_plan = re.search(
        r"业务目标|Business\s+Goal|objective|目标", plan_content, re.IGNORECASE
    )
    has_business_goal_in_spec = re.search(
        r"业务目标|Business\s+Goal|objective|目标", spec_content, re.IGNORECASE
    )

    if has_business_goal_in_plan:
        ISSUES.append(
            (
                "info",
                "business_goal_in_plan",
                "Plan references Business Goal — spec alignment traceable.",
            )
        )
    elif has_business_goal_in_spec:
        ISSUES.append(
            (
                "warning",
                "business_goal_missing_from_plan",
                "Spec has Business Goal but plan does not reference it. "
                "Each Phase should align with the business goal. (PM Scope Gate G2)",
            )
        )

    # ── 4d. Risk Flags check ───────────────────────────────────
    has_risk_flags = re.search(r"Risk\s+Flags|风险|risk", plan_content, re.IGNORECASE)
    if has_risk_flags:
        ISSUES.append(("info", "risk_flags_found", "Plan includes Risk Flags section."))
    else:
        ISSUES.append(
            (
                "warning",
                "no_risk_flags",
                "Plan has no Risk Flags section. "
                "PM should identify business and technical risks per Phase. "
                "(PM Scope Gate G2)",
            )
        )

    # ── 4e. Spec Gaps section ──────────────────────────────────
    has_spec_gaps = re.search(r"Spec\s+Gaps|GAP-|缺口", plan_content, re.IGNORECASE)
    if has_spec_gaps:
        ISSUES.append(
            (
                "info",
                "spec_gaps_section_found",
                "Plan has Spec Gaps section for tracking discovered gaps.",
            )
        )


def main() -> int:
    check()

    high_issues = [i for i in ISSUES if i[0] == "high"]
    warning_issues = [i for i in ISSUES if i[0] == "warning"]
    info_issues = [i for i in ISSUES if i[0] == "info"]

    print("═══ Dev Plan Exit Check (PM Scope Gate G2) ═══")
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
        print("❌ DEV-PLAN exit check FAILED — resolve HIGH issues before proceeding.")
        return 1

    if warning_issues:
        print(
            "⚠️  DEV-PLAN exit check PASSED with warnings — "
            "PM should review scope alignment."
        )
    else:
        print("✅ DEV-PLAN passes exit check. Scope alignment verified.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
