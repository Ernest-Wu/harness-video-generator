#!/usr/bin/env python3
"""
Exit Check: frontend-slides (Content Domain)
Deterministic gate verifying HTML slides output quality.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from _utils.exit_check_base import add_issue, print_and_exit, ensure_project_root

SLIDES_PATH = Path("slides-preview.html")
DESIGN_SPEC_PATH = Path(".claude/state/L3-design.md")


def check():
    # ── HARD GATE: slides-preview.html must exist and be valid HTML ──
    if not SLIDES_PATH.exists():
        add_issue(
            "file_missing",
            f"{SLIDES_PATH} does not exist. frontend-slides must produce this file.",
            level="high",
        )
        return

    html_content = SLIDES_PATH.read_text(encoding="utf-8")

    if not (
        html_content.strip().startswith("<")
        or "<html" in html_content.lower()[:500]
        or "<!doctype" in html_content.lower()[:500]
    ):
        add_issue(
            "invalid_html",
            f"{SLIDES_PATH} does not appear to be valid HTML.",
            level="high",
        )

    # ── HARD GATE: Must contain slide structure ──
    has_sections = bool(re.search(r"<section[^>]*class", html_content, re.IGNORECASE))
    has_divs = bool(re.search(r"<div[^>]*class.*slide", html_content, re.IGNORECASE))
    if not has_sections and not has_divs:
        add_issue(
            "no_slide_structure",
            f"{SLIDES_PATH} contains no slide structure. "
            "Must have <section> or <div> elements with slide classes.",
            level="high",
        )

    # ── HARD GATE: Must contain CSS styling ──
    has_style_tag = "<style" in html_content.lower()
    has_css_vars = "--primary" in html_content or "--bg" in html_content
    has_inline_style = "style=" in html_content.lower()
    if not has_style_tag and not has_css_vars and not has_inline_style:
        add_issue(
            "no_styling",
            f"{SLIDES_PATH} contains no CSS styling. "
            "Slides must have visual design applied.",
            level="high",
        )

    # ── WARNING: Check referenced images ──
    img_refs = re.findall(
        r'(?:src|href)=["\']([^"\']+\.(?:png|jpg|jpeg|webp|svg|gif))["\']',
        html_content,
        re.IGNORECASE,
    )
    for img_ref in img_refs:
        img_path = Path(img_ref)
        if not img_path.is_absolute():
            img_path = Path(".") / img_ref
        if not img_path.exists():
            add_issue(
                "image_missing",
                f"Referenced image not found: {img_ref}",
                level="warning",
            )

    # ── HARD GATE: L3-design.md must exist with Mood and Style ──
    if not DESIGN_SPEC_PATH.exists():
        add_issue(
            "design_spec_missing",
            f"{DESIGN_SPEC_PATH} does not exist. "
            "Mood and Style selection must be recorded.",
            level="high",
        )
    else:
        content = DESIGN_SPEC_PATH.read_text(encoding="utf-8")
        if not re.search(r"Mood\s*[:：]\s*\S+", content, re.IGNORECASE):
            add_issue(
                "design_spec_missing_mood",
                f"{DESIGN_SPEC_PATH} must specify Mood with a non-empty value.",
                level="high",
            )
        if not re.search(r"Style\s*[:：]\s*\S+", content, re.IGNORECASE):
            add_issue(
                "design_spec_missing_style",
                f"{DESIGN_SPEC_PATH} must specify Style with a non-empty value.",
                level="high",
            )


def main() -> int:
    ensure_project_root()
    check()
    print_and_exit("frontend-slides")


if __name__ == "__main__":
    raise SystemExit(main())
