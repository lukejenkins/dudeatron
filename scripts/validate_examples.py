#!/usr/bin/env python3
"""
Validate that example files use properly anonymized data.

Checks that example and template files use standardized anonymization:
- IPs: 192.168.X.Y, 10.0.0.X, etc.
- MACs: XX:XX:XX:XX:XX:XX
- Serials: ABC0000, ABC0001, etc.
- Hostnames: device-X, ap-building-Y, etc.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Import centralized patterns
from security_patterns import APPROVED_ANON as APPROVED_PATTERNS, FORBIDDEN_IN_EXAMPLES

# Map FORBIDDEN_IN_EXAMPLES to the tuple format expected by this script
FORBIDDEN_PATTERNS = {
    name: (info["pattern"], info["description"])
    for name, info in FORBIDDEN_IN_EXAMPLES.items()
}


def is_approved_anonymization(text: str) -> bool:
    """Check if text is approved anonymized format."""
    for pattern in APPROVED_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def validate_file(filepath: str) -> Tuple[bool, List[str]]:
    """
    Validate an example file uses proper anonymization.

    Returns: (is_valid, issues)
    """
    path = Path(filepath)

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return False, [f"Could not read file: {e}"]

    issues = []

    for pattern_name, (pattern, description) in FORBIDDEN_PATTERNS.items():
        matches = re.finditer(pattern, content, re.IGNORECASE)

        for match in matches:
            matched_text = match.group(0)

            # Allow if it's already in an approved format
            if is_approved_anonymization(matched_text):
                continue

            line_num = content[: match.start()].count("\n") + 1
            issues.append(
                f"  Line {line_num}: {description}\n"
                f"    Found: {matched_text}"
            )

    return len(issues) == 0, issues


def main():
    """Validate all provided example files."""
    if len(sys.argv) < 2:
        print("Usage: validate_examples.py <file1> [file2] ...")
        sys.exit(0)

    all_valid = True
    all_issues = []

    for filepath in sys.argv[1:]:
        is_valid, issues = validate_file(filepath)

        if not is_valid:
            all_valid = False
            all_issues.append(f"\n{filepath}:")
            all_issues.extend(issues)

    if not all_valid:
        print("❌ Example files contain real data:\n")
        print("\n".join(all_issues))
        print(
            "\n⚠️  Example and template files should only contain "
            "anonymized data (192.168.X.Y, ABC0000, XX:XX:XX:XX:XX:XX, etc.)"
        )
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
