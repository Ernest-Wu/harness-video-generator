#!/usr/bin/env python3
"""
Exit Check: design-maker
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from _utils.exit_check_base import add_issue, print_and_exit

DATA_PATH = Path(".claude/state/L5-design-data.yaml")


def check():
    if not DATA_PATH.exists():
        add_issue("file_missing", f"{DATA_PATH} does not exist.")
        return

    text = DATA_PATH.read_text(encoding="utf-8")

    # Must reference a source and at least one page
    if not re.search(r"source:\s*(figma|pencil|json|yaml)", text, re.IGNORECASE):
        add_issue("source_missing", "No design source (figma/pencil/json/yaml) found.")

    if not re.search(r"pages?:", text, re.IGNORECASE):
        add_issue("pages_missing", "No pages list found. Design deliverable must name the screens/components it covers.")


def main() -> int:
    check()
    print_and_exit("design-maker")


if __name__ == "__main__":
    raise SystemExit(main())
