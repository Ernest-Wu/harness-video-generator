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

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from _utils.exit_check_base import add_issue, print_and_exit, ensure_project_root

PLAN_PATH = Path(".claude/state/L4-plan.md")
SPEC_PATH = Path(".claude/state/L2-spec.md")


def check():
    # ── 1. Plan file must exist ────────────────────────────────
    if not PLAN_PATH.exists():
        add_issue("file_missing", f"{PLAN_PATH} does not exist.", level="high")
        return

    text = PLAN_PATH.read_text(encoding="utf-8")

    # ── 2. Must have Phase sections ────────────────────────────
    phases = re.findall(r"^##\s+.*Phase.*$", text, re.MULTILINE | re.IGNORECASE)
    if len(phases) < 2:
        add_issue(
            "phases_too_few",
            "DEV-PLAN should have at least 2 Phases.",
            level="high",
        )

    # ── 3. Must mention deliverables or dependencies ───────────
    if not re.search(r"deliverable|dependency|task", text, re.IGNORECASE):
        add_issue(
            "plan_too_vague",
            "No deliverables, dependencies, or tasks found.",
            level="high",
        )

    # ── 4. PM Scope Gate (G2) checks ───────────────────────────
    check_phase_spec_mapping(text)


def extract_p0_features(spec_content: str) -> list[str]:
    """Extract P0 feature names from L2-spec.md."""
    p0_match = re.search(
        r"(?:###|##)\s*P0.*?\n(.*?)(?=(?:###|##)\s*(?:P1|P2|Scope|References)|\Z)",
        spec_content,
        re.DOTALL | re.IGNORECASE,
    )
    if not p0_match:
        return []

    p0_section = p0_match.group(1)
    items = re.findall(r"^(?:[-*]|\d+\.)\s+(.*?)$", p0_section, re.MULTILINE)
    features = []
    for item in items:
        name = re.split(r"[—:：]", item)[0].strip()
        if name:
            features.append(name)
    return features


def check_p0_in_phase0(p0_features: list[str], plan_content: str) -> list[str]:
    """Check which P0 features are not referenced in Phase 0 / MVP section."""
    mvp_match = re.search(
        r"(?:###|##)\s*(?:Phase\s*0|MVP|最小可行).*?\n(.*?)(?=(?:###|##)\s*(?:Phase\s*1|Risk|References)|\Z)",
        plan_content,
        re.DOTALL | re.IGNORECASE,
    )
    if not mvp_match:
        return p0_features

    mvp_text = mvp_match.group(1).lower()
    missing = []
    for feature in p0_features:
        words = re.sub(r"[^\w\s]", "", feature.lower()).split()
        significant = [w for w in words if len(w) >= 2]
        if significant and not any(w in mvp_text for w in significant[:3]):
            missing.append(feature)
    return missing


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
        add_issue(
            "spec_not_found",
            "L2-spec.md not found. Cannot verify Phase→Spec mapping. "
            "Run product-spec-builder first.",
            level="warning",
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
        add_issue(
            "feature_phase_mapping_found",
            "Feature-Phase Mapping section found in plan.",
            level="info",
        )
    else:
        phase_sections = re.findall(
            r"^##\s+.*Phase\s*(\d+)", plan_content, re.MULTILINE | re.IGNORECASE
        )
        if phase_sections:
            add_issue(
                "no_feature_phase_mapping",
                "Plan has Phase sections but no Feature-Phase Mapping. "
                "Each Phase should reference which Spec features it delivers. "
                "(PM Scope Gate G2: Phase↔Feature alignment required)",
                level="warning",
            )

    # ── 4b. P0 features in MVP / Phase 0 coverage check ───────
    p0_features = extract_p0_features(spec_content)
    if p0_features:
        missing = check_p0_in_phase0(p0_features, plan_content)
        if missing:
            add_issue(
                "p0_feature_not_in_phase0",
                f"{len(missing)} P0 feature(s) not referenced in Phase 0 / MVP: "
                f"{', '.join(missing[:3])}{'...' if len(missing) > 3 else ''}. "
                f"All P0 features must be mapped to Phase 0. (PM Scope Gate G2)",
                level="high",
            )
        else:
            add_issue(
                "p0_features_in_phase0",
                f"All {len(p0_features)} P0 features are referenced in Phase 0 / MVP.",
                level="info",
            )
    else:
        has_priority = re.search(
            r"P[0-2]|优先级|priority|Must\s+Have", spec_content, re.IGNORECASE
        )
        if not has_priority:
            add_issue(
                "no_priority_in_spec",
                "L2-spec.md has no priority markers (P0/P1/P2). "
                "Cannot verify which features belong in MVP.",
                level="warning",
            )

    # ── 4c. Business Goal alignment ───────────────────────────
    has_business_goal_in_plan = re.search(
        r"业务目标|Business\s+Goal|objective|目标", plan_content, re.IGNORECASE
    )
    has_business_goal_in_spec = re.search(
        r"业务目标|Business\s+Goal|objective|目标", spec_content, re.IGNORECASE
    )

    if has_business_goal_in_plan:
        add_issue(
            "business_goal_in_plan",
            "Plan references Business Goal — spec alignment traceable.",
            level="info",
        )
    elif has_business_goal_in_spec:
        add_issue(
            "business_goal_missing_from_plan",
            "Spec has Business Goal but plan does not reference it. "
            "Each Phase should align with the business goal. (PM Scope Gate G2)",
            level="warning",
        )

    # ── 4d. Risk Flags check ───────────────────────────────────
    has_risk_flags = re.search(r"Risk\s+Flags|风险|risk", plan_content, re.IGNORECASE)
    if has_risk_flags:
        add_issue("risk_flags_found", "Plan includes Risk Flags section.", level="info")
    else:
        add_issue(
            "no_risk_flags",
            "Plan has no Risk Flags section. "
            "PM should identify business and technical risks per Phase. "
            "(PM Scope Gate G2)",
            level="warning",
        )

    # ── 4e. Spec Gaps section ──────────────────────────────────
    has_spec_gaps = re.search(r"Spec\s+Gaps|GAP-|缺口", plan_content, re.IGNORECASE)
    if has_spec_gaps:
        add_issue(
            "spec_gaps_section_found",
            "Plan has Spec Gaps section for tracking discovered gaps.",
            level="info",
        )


def main() -> int:
    ensure_project_root()
    check()
    print_and_exit("Dev Plan")


if __name__ == "__main__":
    raise SystemExit(main())
