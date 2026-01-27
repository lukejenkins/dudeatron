#!/usr/bin/env python3
"""
Pre-commit hook to detect sensitive data patterns.

Scans files for common sensitive information including:
- IP addresses (non-RFC 1918)
- Real MAC addresses
- Serial numbers
- Meraki IDs
- DNS entries
- Device names that look real
- High-entropy strings (potential passwords/API keys)
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Import centralized patterns
from security_patterns import APPROVED_ANON as WHITELIST_PATTERNS, SENSITIVE_PATTERNS, SKIP_FILES

# Map SENSITIVE_PATTERNS to the tuple format expected by this script
PATTERNS = {
    name: (info["pattern"], info["description"])
    for name, info in SENSITIVE_PATTERNS.items()
}


def is_whitelisted(text: str, pattern: str) -> bool:
    """Check if text matches a whitelisted pattern."""
    for whitelist_pattern in WHITELIST_PATTERNS:
        if re.search(whitelist_pattern, text, re.IGNORECASE):
            return True
    return False


def check_file(filepath: str) -> Tuple[bool, List[str]]:
    """
    Check a file for sensitive data patterns.

    Returns: (is_clean, issues)
    """
    path = Path(filepath)

    # Skip certain files
    if path.name in SKIP_FILES:
        return True, []

    # Skip binary files
    if path.suffix in {".png", ".jpg", ".jpeg", ".gif", ".pyc", ".o", ".so"}:
        return True, []

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        return True, []  # If we can't read it, skip it

    issues = []

    for pattern_name, (pattern, description) in PATTERNS.items():
        matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)

        for match in matches:
            matched_text = match.group(0)

            # Skip whitelisted matches
            if is_whitelisted(matched_text, pattern):
                continue

            # Calculate line number
            line_num = content[: match.start()].count("\n") + 1

            issues.append(
                f"  Line {line_num}: {description}\n"
                f"    Matched: {matched_text[:60]}"
                f"{'...' if len(matched_text) > 60 else ''}"
            )

    return len(issues) == 0, issues


def main():
    """Check all provided files for sensitive data."""
    if len(sys.argv) < 2:
        print("Usage: check_sensitive_data.py <file1> [file2] ...")
        sys.exit(0)

    all_clean = True
    all_issues = []

    for filepath in sys.argv[1:]:
        is_clean, issues = check_file(filepath)

        if not is_clean:
            all_clean = False
            all_issues.append(f"\n{filepath}:")
            all_issues.extend(issues)

    if not all_clean:
        print("❌ Sensitive data detected:\n")
        print("\n".join(all_issues))
        print(
            "\n⚠️  Please anonymize sensitive data or add to "
            ".secrets.baseline if this is a false positive."
        )
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
