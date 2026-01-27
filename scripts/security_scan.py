#!/usr/bin/env python3
"""
Manual security scan script for the dudeatron project.

Run this before committing to catch any sensitive data that might have slipped through.
Usage: python scripts/security_scan.py [--fix]
"""

import re
import sys
import subprocess
from pathlib import Path
from typing import Optional, Set

# Import centralized patterns
from security_patterns import APPROVED_ANON, SENSITIVE_PATTERNS, SKIP_FILES


def is_rfc1918(ip: str) -> bool:
    """Check if IP is in private RFC 1918 range."""
    parts = ip.split(".")
    if len(parts) != 4:
        return False

    try:
        octet1 = int(parts[0])
        octet2 = int(parts[1])

        # 10.0.0.0 – 10.255.255.255
        if octet1 == 10:
            return True
        # 172.16.0.0 – 172.31.255.255
        if octet1 == 172 and 16 <= octet2 <= 31:
            return True
        # 192.168.0.0 – 192.168.255.255
        if octet1 == 192 and octet2 == 168:
            return True
    except ValueError:
        pass

    return False


def is_approved_anonymized(text: str) -> bool:
    """Check if text is in an approved anonymized format."""
    for pattern in APPROVED_ANON:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def is_gitignored(filepath: Path, repo_root: Path) -> bool:
    """Check if a file is in .gitignore."""
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", str(filepath)],
            cwd=repo_root,
            capture_output=True,
        )
        return result.returncode == 0
    except Exception:
        return False


def scan_file(filepath: Path, repo_root: Optional[Path] = None) -> dict:
    """Scan a file for sensitive data."""
    results = {
        "findings": [],
        "warnings": [],
        "path": str(filepath),
        "gitignored": False,
    }

    if not filepath.exists():
        return results
    
    # Skip files in skip list
    if filepath.name in SKIP_FILES:
        return results
    
    # Check if file is gitignored
    if repo_root and is_gitignored(filepath, repo_root):
        results["gitignored"] = True
        # Still scan but mark as gitignored

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        results["warnings"].append(f"Could not read: {e}")
        return results

    for check_name, check_info in SENSITIVE_PATTERNS.items():
        pattern = check_info["pattern"]
        description = check_info["description"]

        for match in re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE):
            matched_text = match.group(0)

            # Skip approved anonymized patterns
            if is_approved_anonymized(matched_text):
                continue

            # Skip RFC 1918 private IPs
            if check_name == "ip_non_rfc1918" and is_rfc1918(matched_text):
                continue

            line_num = content[: match.start()].count("\n") + 1

            results["findings"].append(
                {
                    "line": line_num,
                    "type": description,
                    "text": matched_text[:60],
                    "check": check_name,
                }
            )

    return results


def main():
    """Run security scan on project."""
    print("🔒 Dudeatron Security Scan\n")

    repo_root = Path(__file__).parent.parent
    all_clean = True
    total_findings = 0
    gitignored_findings = 0
    scanned_count = 0
    skipped_count = 0

    # Directories to skip
    skip_dirs = {'.git', '__pycache__', '.venv', 'venv', 'node_modules', '.pytest_cache'}

    # Scan all files recursively
    print("Scanning all files (excluding .gitignored)...\n")
    for file_path in repo_root.rglob("*"):
        # Skip directories
        if file_path.is_dir():
            continue
        
        # Skip if in a directory we want to ignore
        if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
            continue
        
        # Check if gitignored first
        if is_gitignored(file_path, repo_root):
            skipped_count += 1
            continue
        
        scanned_count += 1
        results = scan_file(file_path, repo_root)

        if results["findings"]:
            all_clean = False
            total_findings += len(results["findings"])

            rel_path = file_path.relative_to(repo_root)
            print(f"\n⚠️  {rel_path}:")
            for finding in results["findings"]:
                print(
                    f"   Line {finding['line']}: {finding['type']}: "
                    f"{finding['text']}"
                )

    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Scanned {scanned_count} files, skipped {skipped_count} .gitignored files")
    
    if all_clean:
        print("✅ No sensitive data detected in tracked files!")
        print("\nNext steps:")
        print("1. Run 'pre-commit run --all-files' for comprehensive checks")
        print("2. Commit with confidence!")
        print("\nNote: Files in .gitignore are automatically protected.")
        return 0
    else:
        print(f"❌ Found {total_findings} potential security issues in tracked files")
        print("\nNext steps:")
        print("1. Review each finding above")
        print("2. Replace with anonymized versions:")
        print("   - IPs: 192.168.X.Y or 10.0.0.X")
        print("   - MACs: XX:XX:XX:XX:XX:XX")
        print("   - Serials: ABC0000, ABC0001, etc.")
        print("3. Move production data to files in .gitignore")
        return 1


if __name__ == "__main__":
    sys.exit(main())
