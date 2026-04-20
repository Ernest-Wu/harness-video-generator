#!/usr/bin/env python3
"""
Harness Health Check - Three-Domain Edition
Verify that the Harness infrastructure is intact for dev, content, and pm domains.
"""

import ast
import py_compile
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
ISSUES = []

DEV_SKILLS = [
    "product-spec-builder",
    "design-brief-builder",
    "design-maker",
    "dev-planner",
    "dev-builder",
    "bug-fixer",
    "code-review",
    "release-builder",
]

CONTENT_SKILLS = [
    "script-writer",
    "visual-designer",
    "frontend-slides",
    "tts-engine",
    "video-compositor",
]

PM_SKILLS = [
    "validation",
    "content-strategy",
    "distribution-planner",
    "content-validation",
]

STATE_FILES = [
    "L0-strategy.md",
    "L1-summary.md",
    "L2-spec.md",
    "L2-content-spec.md",
    "L3-design.md",
    "L4-plan.md",
    "L5-media.md",
    "L5-content-validation.md",
    "L6-distribution.md",
    "task-history.yaml",
]

DOC_FILES = [
    "CLAUDE.md",
    "docs/HARNESS-ARCHITECTURE.md",
    "docs/EVOLUTION-PROTOCOL.md",
    "docs/CONTENT-PIPELINE.md",
    "docs/FIGMA_MCP_SETUP.md",
]


def check_skills():
    skills_dir = ROOT / "skills"

    # Check dev skills
    for name in DEV_SKILLS:
        skill_md = skills_dir / "dev" / name / "SKILL.md"
        exit_check = skills_dir / "dev" / name / "exit-check.py"
        if not skill_md.exists():
            ISSUES.append(
                ("dev_skill_missing", f"Dev skill SKILL.md not found: {skill_md}")
            )
        if not exit_check.exists():
            ISSUES.append(
                (
                    "dev_exit_check_missing",
                    f"Dev skill exit-check.py not found: {exit_check}",
                )
            )

    # Check content skills
    for name in CONTENT_SKILLS:
        skill_md = skills_dir / "content" / name / "SKILL.md"
        exit_check = skills_dir / "content" / name / "exit-check.py"
        if not skill_md.exists():
            ISSUES.append(
                (
                    "content_skill_missing",
                    f"Content skill SKILL.md not found: {skill_md}",
                )
            )
        if not exit_check.exists():
            ISSUES.append(
                (
                    "content_exit_check_missing",
                    f"Content skill exit-check.py not found: {exit_check}",
                )
            )

    # Check pm skills
    for name in PM_SKILLS:
        skill_md = skills_dir / "pm" / name / "SKILL.md"
        exit_check = skills_dir / "pm" / name / "exit-check.py"
        if not skill_md.exists():
            ISSUES.append(
                (
                    "pm_skill_missing",
                    f"PM skill SKILL.md not found: {skill_md}",
                )
            )
        if not exit_check.exists():
            ISSUES.append(
                (
                    "pm_exit_check_missing",
                    f"PM skill exit-check.py not found: {exit_check}",
                )
            )


def check_hooks():
    hooks_dir = ROOT / "hooks"
    expected = [
        "pre-commit-check.sh",
        "stop-gate.sh",
        "content-validator.sh",
        "detect-feedback-signal.py",
        "mark-review-needed.sh",
        "feedback-analyzer.py",
    ]
    for name in expected:
        if not (hooks_dir / name).exists():
            ISSUES.append(("hook_missing", f"{hooks_dir / name} not found"))


def check_state():
    state_dir = ROOT / "state"
    if not state_dir.exists():
        ISSUES.append(("state_dir_missing", f"{state_dir} not found"))
    else:
        for name in STATE_FILES:
            if not (state_dir / name).exists():
                ISSUES.append(
                    ("state_file_missing", f"State file not found: {state_dir / name}")
                )


def check_docs():
    for doc in DOC_FILES:
        if not (ROOT / doc).exists():
            ISSUES.append(("doc_missing", f"Doc not found: {ROOT / doc}"))


def check_syntax():
    """T7: Verify all .py files compile and all .sh files pass bash -n."""
    # Python files
    py_files = list((ROOT / "skills").rglob("*.py"))
    py_files.extend((ROOT / "hooks").glob("*.py"))
    py_files.append(ROOT / "router.py")
    py_files.append(ROOT / "check-harness.py")
    for py_file in py_files:
        try:
            py_compile.compile(str(py_file), doraise=True)
        except py_compile.PyCompileError as e:
            ISSUES.append(("syntax_error", f"{py_file}: {e}"))

    # Bash files
    hooks_dir = ROOT / "hooks"
    for sh_file in hooks_dir.glob("*.sh"):
        result = subprocess.run(
            ["bash", "-n", str(sh_file)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            ISSUES.append(
                ("hook_syntax_error", f"{sh_file}: {result.stderr.strip()}")
            )


def check_skill_frontmatter():
    """T8: Verify all SKILL.md files contain basic frontmatter."""
    skills_dir = ROOT / "skills"
    for skill_md in skills_dir.rglob("SKILL.md"):
        content = skill_md.read_text(encoding="utf-8")
        if not content.startswith("---"):
            ISSUES.append(
                ("skill_frontmatter_missing", f"{skill_md} missing YAML frontmatter")
            )
        elif "name:" not in content or "description:" not in content:
            ISSUES.append(
                (
                    "skill_frontmatter_incomplete",
                    f"{skill_md} frontmatter missing name or description",
                )
            )


def check_state_schema():
    """T10: Verify existing state files are non-empty and have structure."""
    state_dir = ROOT / "state"
    if not state_dir.exists():
        return
    for name in STATE_FILES:
        path = state_dir / name
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            ISSUES.append(("state_file_empty", f"State file is empty: {path}"))
        elif path.suffix == ".md":
            if not re.search(r"^#\s+", content, re.MULTILINE):
                ISSUES.append(
                    ("state_file_no_heading", f"State file missing Markdown heading: {path}")
                )


def check_exit_check_format():
    """T11: Verify all exit-check.py scripts use _utils/exit_check_base."""
    skills_dir = ROOT / "skills"
    for exit_check in skills_dir.rglob("exit-check.py"):
        source = exit_check.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            ISSUES.append(
                ("exit_check_ast_error", f"{exit_check}: syntax error - {e}")
            )
            continue

        uses_base = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "_utils.exit_check_base":
                        uses_base = True
            elif isinstance(node, ast.ImportFrom):
                if node.module == "_utils.exit_check_base":
                    uses_base = True
                elif node.module == "_utils":
                    for alias in node.names:
                        if alias.name == "exit_check_base":
                            uses_base = True

        if not uses_base:
            ISSUES.append(
                (
                    "exit_check_not_using_base",
                    f"{exit_check} does not import from _utils.exit_check_base",
                )
            )


def check_add_issue_level():
    """T12: Verify all add_issue calls explicitly declare level.

    Note: Calls via **kwargs (e.g., add_issue(**kwargs)) are not supported
    and would be flagged as missing level. Use explicit keyword arguments.
    """
    skills_dir = ROOT / "skills"
    for exit_check in skills_dir.rglob("exit-check.py"):
        source = exit_check.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "add_issue":
                    # add_issue requires 3 args: code, detail, level
                    # After removing default, all calls must have level
                    has_level = False
                    # Check positional args (3rd arg is level)
                    if len(node.args) >= 3:
                        has_level = True
                    # Check keyword args
                    for kw in node.keywords:
                        if kw.arg == "level":
                            has_level = True
                            break
                    if not has_level:
                        ISSUES.append(
                            (
                                "exit_check_level_implicit",
                                f"{exit_check}: add_issue call missing explicit level= argument",
                            )
                        )


def check_print_and_exit():
    """T13: Verify all exit-check.py scripts call print_and_exit inside main()."""
    skills_dir = ROOT / "skills"
    for exit_check in skills_dir.rglob("exit-check.py"):
        source = exit_check.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue

        has_print_and_exit = False
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "main":
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        func = child.func
                        if isinstance(func, ast.Name) and func.id == "print_and_exit":
                            has_print_and_exit = True
                            break
                break

        if not has_print_and_exit:
            ISSUES.append(
                (
                    "exit_check_no_print_and_exit",
                    f"{exit_check} main() does not call print_and_exit()",
                )
            )


def check_skill_coverage():
    """T14: Rough alignment between SKILL.md Exit-Check Criteria and exit-check.py add_issue calls."""
    skills_dir = ROOT / "skills"
    for skill_md in skills_dir.rglob("SKILL.md"):
        content = skill_md.read_text(encoding="utf-8")
        exit_check = skill_md.parent / "exit-check.py"
        if not exit_check.exists():
            continue

        # Count criteria items in Exit-Check Criteria section
        criteria_count = 0
        match = re.search(
            r"## Exit-Check Criteria\s*\n+(.*?)(?=\n## |\Z)",
            content,
            re.DOTALL,
        )
        if match:
            section = match.group(1)
            # Count numbered list items (e.g., "1.", "2.") and bullet items ("-", "*")
            criteria_count = len(
                re.findall(r"^\s*(?:\d+\.|[\-*])\s+", section, re.MULTILINE)
            )

        # Count add_issue calls in exit-check.py
        ec_source = exit_check.read_text(encoding="utf-8")
        try:
            tree = ast.parse(ec_source)
        except SyntaxError:
            continue
        issue_count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "add_issue":
                    issue_count += 1

        # Heuristic: if exit-check has fewer than 50% of criteria items, flag it
        if criteria_count > 0 and issue_count < criteria_count * 0.5:
            ISSUES.append(
                (
                    "skill_coverage_low",
                    f"{skill_md.parent.name}: {issue_count} add_issue calls but "
                    f"{criteria_count} Exit-Check Criteria items. "
                    f"Coverage below 50% — verify exit-check aligns with SKILL.md.",
                )
            )


def check_state_cross_reference():
    """T15: Verify L2-spec.md and L4-plan.md Business Goal consistency."""
    state_dir = ROOT / "state"
    l2 = state_dir / "L2-spec.md"
    l4 = state_dir / "L4-plan.md"

    if not l2.exists() or not l4.exists():
        return

    l2_content = l2.read_text(encoding="utf-8")
    l4_content = l4.read_text(encoding="utf-8")

    l2_has_bg = "## Business Goal" in l2_content
    l4_has_bg = "## Business Goal" in l4_content

    if l2_has_bg != l4_has_bg:
        ISSUES.append(
            (
                "state_business_goal_mismatch",
                f"L2-spec.md {'has' if l2_has_bg else 'lacks'} '## Business Goal' but "
                f"L4-plan.md {'has' if l4_has_bg else 'lacks'} it. "
                f"Cross-file consistency required.",
            )
        )


def main() -> int:
    check_skills()
    check_hooks()
    check_state()
    check_docs()
    check_syntax()
    check_skill_frontmatter()
    check_state_schema()
    check_exit_check_format()
    check_add_issue_level()
    check_print_and_exit()
    check_skill_coverage()
    check_state_cross_reference()

    if not ISSUES:
        print(
            "✅ Harness health check passed. All three domains (dev/, content/, pm/) are intact."
        )
        return 0

    print("❌ Harness health issues detected:\n")
    for code, detail in ISSUES:
        print(f"  [{code}] {detail}")
    print()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
