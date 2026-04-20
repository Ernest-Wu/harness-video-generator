#!/usr/bin/env python3
"""
Exit Check: visual-designer (Content Domain)
Deterministic gate verifying HTML slides output quality.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from _utils.exit_check_base import add_issue, print_and_exit, ensure_project_root

SLIDES_PATH = Path("slides-preview.html")
DESIGN_SPEC_PATH = Path(".claude/state/L3-design.md")
SCENES_PATH = Path("scenes.json")


def check():
    # 1. slides-preview.html must exist and be valid HTML
    if not SLIDES_PATH.exists():
        add_issue(
            "file_missing",
            f"{SLIDES_PATH} does not exist. visual-designer must produce this file.",
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
            f"{SLIDES_PATH} does not appear to be valid HTML. Must contain <!DOCTYPE html>, <html>, or start with an HTML tag.",
            level="high",
        )

    # 2. Must contain data-beat-at attributes
    if "data-beat-at" not in html_content:
        add_issue(
            "missing_beat_attributes",
            f"{SLIDES_PATH} contains no 'data-beat-at' attributes. Visual beats from scenes.json must be injected into HTML elements.",
            level="high",
        )

    # 3. Must contain platform override CSS
    has_platform_css = any(
        marker in html_content
        for marker in [
            "--platform-aspect",
            "9:16",
            "16:9",
            "4:5",
            "platform-override",
            "aspect-ratio",
        ]
    )
    if not has_platform_css:
        add_issue(
            "missing_platform_css",
            f"{SLIDES_PATH} missing platform override CSS. Must include aspect ratio variables for the target platform.",
            level="high",
        )

    # 4. Check referenced image files exist
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
            add_issue("image_missing", f"Referenced image not found: {img_ref}", level="high")

    # 5. L3-design.md must exist with Mood and Style
    if not DESIGN_SPEC_PATH.exists():
        add_issue(
            "design_spec_missing",
            f"{DESIGN_SPEC_PATH} does not exist. Visual design spec is required for downstream TTS.",
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
    print_and_exit("visual-designer")


if __name__ == "__main__":
    raise SystemExit(main())
