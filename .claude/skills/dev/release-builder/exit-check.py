#!/usr/bin/env python3
"""
Exit Check: release-builder (PM Release Gate)

Deterministic gate for release readiness. This is the final gate before
users see the product — it must be airtight.

PM Release Gate (G4) checks:
  1. All P0 features from spec are implemented
  2. Rollback plan exists
  3. Task history is complete (all phases done)
  4. Spec coverage — spec file is not empty
  5. Design brief exists (visual authority chain)
  6. Dev plan exists (phase tracking)

Hard Gate levels:
  - high:   Blocks release. Must fix before proceeding.
  - warning: Does not block release, but PM should confirm.
  - info:   Informational, for traceability.
"""

import re
import sys
from pathlib import Path

STATE_DIR = Path(".claude/state")
PROJECT_ROOT = Path(".")

ISSUES = []


def check():
    """Run all release readiness checks."""

    # ──────────────────────────────────────────
    # 1. P0 Features — All must be implemented
    # ──────────────────────────────────────────
    l2_spec = STATE_DIR / "L2-spec.md"
    if l2_spec.exists():
        spec_content = l2_spec.read_text(encoding="utf-8")

        p0_section = re.search(
            r"P0.*?(?:P1|##|$)", spec_content, re.IGNORECASE | re.DOTALL
        )
        if p0_section:
            p0_text = p0_section.group(0)
            p0_items = re.findall(r"^[-*]\s+\*\*.+?\*\*", p0_text, re.MULTILINE)
            if p0_items:
                ISSUES.append(
                    (
                        "info",
                        "p0_features_listed",
                        f"Found {len(p0_items)} P0 features in spec. "
                        f"Verify all are implemented before release.",
                    )
                )
            else:
                ISSUES.append(
                    (
                        "info",
                        "p0_section_exists",
                        "P0 section found in spec but no specific features listed.",
                    )
                )
        else:
            has_priority = re.search(
                r"P[0-2]|Must\s+Have|优先级|priority", spec_content, re.IGNORECASE
            )
            if not has_priority:
                ISSUES.append(
                    (
                        "warning",
                        "no_priority_markers",
                        "No P0/P1/P2 or priority markers found in spec. "
                        "Cannot verify which features must be in this release.",
                    )
                )

        if len(spec_content.strip()) < 200:
            ISSUES.append(
                (
                    "high",
                    "spec_too_short",
                    f"L2-spec.md is only {len(spec_content.strip())} chars. "
                    f"Cannot verify feature coverage without a meaningful spec.",
                )
            )
    else:
        ISSUES.append(
            (
                "high",
                "spec_missing",
                f"L2-spec.md not found at {l2_spec}. "
                f"Release gate requires a spec to verify feature coverage.",
            )
        )

    # ──────────────────────────────────────────
    # 2. Rollback Plan — Must exist and be confirmed
    # ──────────────────────────────────────────
    rollback_doc = PROJECT_ROOT / "ROLLBACK.md"
    l4_plan = STATE_DIR / "L4-plan.md"
    found_rollback = False

    if rollback_doc.exists():
        rollback_content = rollback_doc.read_text(encoding="utf-8")
        if len(rollback_content.strip()) > 50:
            found_rollback = True
            ISSUES.append(
                (
                    "info",
                    "rollback_plan_found",
                    "ROLLBACK.md exists at project root.",
                )
            )

    if not found_rollback and l4_plan.exists():
        plan_content = l4_plan.read_text(encoding="utf-8")
        if re.search(r"rollback|回滚|revert|回退", plan_content, re.IGNORECASE):
            found_rollback = True
            ISSUES.append(
                (
                    "info",
                    "rollback_in_plan",
                    "Rollback plan found in L4-plan.md.",
                )
            )

    if not found_rollback:
        ISSUES.append(
            (
                "high",
                "no_rollback_plan",
                "No rollback plan found. Create ROLLBACK.md at project root "
                "or add a rollback section to L4-plan.md before releasing.",
            )
        )

    # ──────────────────────────────────────────
    # 3. Task History — All phases should be complete
    # ──────────────────────────────────────────
    task_history = STATE_DIR / "task-history.yaml"
    if task_history.exists():
        hist_content = task_history.read_text(encoding="utf-8")
        incomplete = re.findall(
            r"status:\s*(?:in.progress|pending|blocked|todo)",
            hist_content,
            re.IGNORECASE,
        )
        if incomplete:
            ISSUES.append(
                (
                    "warning",
                    "incomplete_tasks",
                    f"Found {len(incomplete)} incomplete task(s) in task-history.yaml. "
                    f"Verify these are not blocking the release.",
                )
            )
        else:
            ISSUES.append(
                (
                    "info",
                    "task_history_exists",
                    "Task history found.",
                )
            )
    else:
        ISSUES.append(
            (
                "warning",
                "no_task_history",
                "task-history.yaml not found — cannot verify all tasks completed.",
            )
        )

    # ──────────────────────────────────────────
    # 4. Design Brief — Visual authority chain must exist
    # ──────────────────────────────────────────
    l3_design = STATE_DIR / "L3-design.md"
    if not l3_design.exists():
        ISSUES.append(
            (
                "warning",
                "no_design_brief",
                "L3-design.md not found. If this release includes UI changes, "
                "a design brief is required for spec compliance.",
            )
        )
    else:
        design_content = l3_design.read_text(encoding="utf-8")
        if len(design_content.strip()) < 100:
            ISSUES.append(
                (
                    "warning",
                    "design_brief_too_short",
                    "L3-design.md exists but is nearly empty. "
                    "UI changes require a design brief.",
                )
            )

    # ──────────────────────────────────────────
    # 5. Dev Plan — Phase structure must exist
    # ──────────────────────────────────────────
    if l4_plan.exists():
        plan_content = l4_plan.read_text(encoding="utf-8")
        phases = re.findall(
            r"^##\s+(?:Phase|阶段)", plan_content, re.MULTILINE | re.IGNORECASE
        )
        if phases:
            ISSUES.append(
                (
                    "info",
                    "plan_has_phases",
                    f"Found {len(phases)} phase(s) in dev plan.",
                )
            )
        else:
            ISSUES.append(
                (
                    "warning",
                    "plan_no_phases",
                    "L4-plan.md exists but no phases found. "
                    "Verify that the plan structure is correct.",
                )
            )
    else:
        ISSUES.append(
            (
                "warning",
                "no_dev_plan",
                "L4-plan.md not found. Cannot verify phase completion.",
            )
        )

    # ── 6. Release Notes ─────────────────────────────────────────────
    release_notes = PROJECT_ROOT / "RELEASE-NOTES.md"
    if release_notes.exists():
        ISSUES.append(
            (
                "info",
                "release_notes_found",
                "RELEASE-NOTES.md exists.",
            )
        )
    else:
        ISSUES.append(
            (
                "warning",
                "no_release_notes",
                "No RELEASE-NOTES.md found. Document what changed in this release.",
            )
        )


def main() -> int:
    check()

    high_issues = [i for i in ISSUES if i[0] == "high"]
    warning_issues = [i for i in ISSUES if i[0] == "warning"]
    info_issues = [i for i in ISSUES if i[0] == "info"]

    # Summary
    print("═══ PM Release Gate (G4) ═══")
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
        f"  Total: {len(high_issues)} high, {len(warning_issues)} warning, {len(info_issues)} info"
    )
    print()

    # Hard Gate: any HIGH issue blocks release
    if high_issues:
        print("❌ Release Gate FAILED — resolve HIGH issues before proceeding.")
        return 1

    if warning_issues:
        print("⚠️  Release Gate PASSED with warnings — PM should review before release.")
    else:
        print("✅ Release Gate PASSED — ready for PM sign-off (Creative Gate).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
