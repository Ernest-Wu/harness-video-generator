#!/usr/bin/env python3
"""
Skill Router - Match user intent to the best Skill.
Supports three-domain routing: dev/, content/, and pm/
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

SKILLS_DIR = Path(__file__).parent / "skills"


def parse_skill_triggers(path: Path) -> list[str]:
    """Extract triggers list from SKILL.md YAML frontmatter using regex."""
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return []
    parts = content.split("---", 2)
    if len(parts) < 3:
        return []
    frontmatter = parts[1]
    match = re.search(r'^triggers:\s*\[(.*?)\]', frontmatter, re.MULTILINE | re.DOTALL)
    if not match:
        return []
    items = match.group(1)
    triggers = []
    for item in items.split(","):
        item = item.strip().strip('"').strip("'")
        if item:
            triggers.append(item)
    return triggers


def build_skill_index() -> list[dict]:
    """Dynamically build skill index from filesystem."""
    index = []
    domains = ["dev", "content", "pm"]
    for domain in domains:
        domain_path = SKILLS_DIR / domain
        if not domain_path.exists():
            continue
        for item in domain_path.iterdir():
            if item.is_dir() and item.name != "_utils":
                skill_md = item / "SKILL.md"
                triggers = parse_skill_triggers(skill_md) if skill_md.exists() else []
                index.append({
                    "name": f"{domain}/{item.name}",
                    "triggers": triggers,
                    "domain": domain,
                })
    return index


def route(query: str, domain: Optional[str] = None) -> list[str]:
    """Route a user query to the best Skill(s).

    Args:
        query: User intent description
        domain: Optional domain filter ('dev', 'content', or 'pm')
    """
    index = build_skill_index()
    query_lower = query.lower()
    # Tokenize query for exact-word matching bonus
    query_tokens = set(re.findall(r"[a-z0-9\u4e00-\u9fff]+", query_lower))
    scores = []
    for skill in index:
        if domain and skill["domain"] != domain:
            continue
        score = 0
        for t in skill["triggers"]:
            t_lower = t.lower()
            if t_lower in query_lower:
                # Base score for substring match
                score += 1
                # Bonus for exact token match (reduces false positives)
                if t_lower in query_tokens:
                    score += 1
        if score > 0:
            scores.append((score, skill["name"], skill["domain"]))
    scores.sort(reverse=True)
    return [name for _, name, _ in scores[:3]]


def main() -> int:
    parser = argparse.ArgumentParser(description="Route user query to best Skill(s)")
    parser.add_argument("query", help="User intent description")
    parser.add_argument(
        "--domain",
        choices=["dev", "content", "pm"],
        help="Restrict routing to a specific domain",
    )
    args = parser.parse_args()

    matches = route(args.query, args.domain)
    if not matches:
        print("⚠ No strong Skill match found.")
        print(
            "  Consider specifying a domain with --domain dev, --domain content, or --domain pm."
        )
        print("  Or rephrase your query with more specific keywords.")
        return 1

    print("Top matches:")
    for m in matches:
        skill_dir = SKILLS_DIR / m
        exists = "✓" if skill_dir.exists() else "✗"
        print(f"  {exists} {m}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
