#!/usr/bin/env python3
"""
Feedback Analyzer — Steering Loop automation.

Scans .claude/feedback/ directory, groups feedback entries by (skill, type),
and reports graduated candidates based on domain thresholds.

Pure stdlib — zero external dependencies.

Usage:
    python3 .claude/hooks/feedback-analyzer.py
"""

import re
from collections import Counter
from pathlib import Path

# Domain thresholds for graduation
THRESHOLDS = {
    "dev": 3,
    "pm": 2,
    "content": 5,
}

# Skill → domain mapping (fallback: infer from skill directory)
SKILL_DOMAIN = {
    "product-spec-builder": "dev",
    "design-brief-builder": "dev",
    "design-maker": "dev",
    "dev-planner": "dev",
    "dev-builder": "dev",
    "bug-fixer": "dev",
    "code-review": "dev",
    "release-builder": "dev",
    "script-writer": "content",
    "visual-designer": "content",
    "frontend-slides": "content",
    "tts-engine": "content",
    "video-compositor": "content",
    "validation": "pm",
    "content-strategy": "pm",
    "distribution-planner": "pm",
    "content-validation": "pm",
}


def parse_frontmatter(text: str) -> dict:
    """Extract YAML frontmatter key-value pairs from markdown text."""
    meta = {}
    match = re.search(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return meta
    for line in match.group(1).splitlines():
        line = line.strip()
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta


def infer_skill_type_from_filename(path: Path) -> tuple[str, str]:
    """Try to extract skill and type from filename like YYYY-MM-DD_skill-type.md."""
    name = path.stem
    m = re.match(r"\d{4}-\d{2}-\d{2}_(.+)", name)
    if m:
        remainder = m.group(1)
        # Try to match known skill names first (longest match)
        for skill in sorted(SKILL_DOMAIN.keys(), key=len, reverse=True):
            for sep in ("_", "-"):
                prefix = skill + sep
                if remainder.startswith(prefix):
                    return skill, remainder[len(prefix):]
        # Fallback: naive split
        for sep in ("_", "-"):
            if sep in remainder:
                parts = remainder.rsplit(sep, 1)
                if len(parts) == 2:
                    return parts[0], parts[1]
    return name, "general"


def infer_skill_type_from_content(text: str) -> tuple[str, str]:
    """Try to extract skill and type from first markdown heading."""
    for line in text.splitlines()[:10]:
        m = re.search(r"#+\s+Feedback\s*[:：]\s*(\S+)[\s/]+(\S+)", line, re.IGNORECASE)
        if m:
            return m.group(1), m.group(2)
    return "", ""


def get_domain(skill: str) -> str:
    """Return domain for a skill name."""
    if skill in SKILL_DOMAIN:
        return SKILL_DOMAIN[skill]
    # Fallback: check if skill name matches known prefixes
    if skill.startswith(("dev-", "code-", "bug-", "release-", "design-")):
        return "dev"
    if skill in ("script-writer", "visual-designer", "frontend-slides", "tts-engine", "video-compositor"):
        return "content"
    return "pm"


def main() -> int:
    feedback_dir = Path(".claude/feedback")
    if not feedback_dir.exists():
        print("❌ Feedback directory not found: .claude/feedback")
        return 1

    entries = []
    for path in sorted(feedback_dir.glob("*.md")):
        if path.name == "FEEDBACK-INDEX.md":
            continue
        text = path.read_text(encoding="utf-8")
        meta = parse_frontmatter(text)

        skill = meta.get("skill", "")
        ftype = meta.get("type", "")

        if not skill:
            skill, ftype = infer_skill_type_from_content(text)
        if not skill:
            skill, ftype = infer_skill_type_from_filename(path)
        if not ftype:
            ftype = "general"

        entries.append((skill, ftype, path.name))

    if not entries:
        print("═══ Feedback Analysis ═══\n")
        print("No feedback entries found.")
        print("\nTo add feedback, create a file in .claude/feedback/ with YAML frontmatter:")
        print("""
---
skill: tts-engine
type: voice-quality
---

Your feedback description here.
""")
        return 0

    counts = Counter((e[0], e[1]) for e in entries)
    graduated = []
    active = []

    for (skill, ftype), count in counts.most_common():
        domain = get_domain(skill)
        threshold = THRESHOLDS.get(domain, 3)
        if count >= threshold:
            graduated.append((skill, ftype, count, domain, threshold))
        else:
            active.append((skill, ftype, count, domain, threshold))

    print("═══ Feedback Analysis ═══\n")
    print(f"Scanned: {len(entries)} feedback file(s)\n")

    if graduated:
        print("🎓 Graduated (ready for proposal):\n")
        for skill, ftype, count, domain, threshold in graduated:
            print(
                f"  {skill} / {ftype} = {count} "
                f"({domain} threshold: {threshold})"
            )
        print()

    if active:
        print("📊 Active (below threshold):\n")
        for skill, ftype, count, domain, threshold in active:
            print(
                f"  {skill} / {ftype} = {count} "
                f"({domain} threshold: {threshold})"
            )
        print()

    if not graduated:
        print("No graduated feedback yet. Keep collecting!\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
