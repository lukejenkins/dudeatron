#!/bin/bash
#
# Pre-commit checklist and setup script for dudeatron
# Run this once to set up security checks, then before each commit to verify
#

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

echo "🔒 Dudeatron Security Setup Checklist"
echo "=================================="
echo ""

# Check 1: pre-commit installed
echo "[1/6] Checking pre-commit installation..."
if ! command -v pre-commit &> /dev/null; then
    echo "❌ pre-commit not found. Install it:"
    echo "   pip install pre-commit"
    exit 1
fi
echo "✅ pre-commit is installed: $(pre-commit --version)"
echo ""

# Check 2: git hooks installed
echo "[2/6] Checking git hooks..."
if [ -f ".git/hooks/pre-commit" ]; then
    echo "✅ Pre-commit hook is installed"
else
    echo "⚠️  Pre-commit hook not installed yet. Run:"
    echo "   pre-commit install"
    PRE_COMMIT_INSTALL_NEEDED=1
fi
echo ""

# Check 3: Configuration files exist
echo "[3/6] Checking configuration files..."
FILES_TO_CHECK=(
    ".pre-commit-config.yaml"
    ".secrets.baseline"
    "docs/SECURITY.md"
    "scripts/check_sensitive_data.py"
    "scripts/validate_examples.py"
    "scripts/security_scan.py"
)

for file in "${FILES_TO_CHECK[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (missing)"
        exit 1
    fi
done
echo ""

# Check 4: .gitignore has sensitive files
echo "[4/6] Checking .gitignore for sensitive files..."
SENSITIVE_PATTERNS=(
    "^.env$"
    "^aps\.txt$"
    "^wlc\.txt$"
    "^logs/"
)

for pattern in "${SENSITIVE_PATTERNS[@]}"; do
    if grep -q "$pattern" .gitignore 2>/dev/null; then
        echo "✅ $pattern in .gitignore"
    else
        echo "⚠️  $pattern may not be in .gitignore"
    fi
done
echo ""

# Check 5: Example files are anonymized
echo "[5/6] Checking example files for anonymization..."
EXAMPLE_FILES=(
    "aps.txt.example"
    "wlc.txt.example"
)

for file in "${EXAMPLE_FILES[@]}"; do
    if [ -f "$file" ]; then
        if grep -q '192\.168\.X\.Y\|10\.0\.0\.X\|ABC[0-9]\|XX:XX:XX' "$file"; then
            echo "✅ $file appears to be anonymized"
        else
            echo "⚠️  $file may contain real data - review it"
        fi
    fi
done
echo ""

# Check 6: Run initial scan
echo "[6/6] Running security scan..."
python scripts/security_scan.py
SCAN_RESULT=$?

echo ""
echo "=================================="
echo ""

if [ $SCAN_RESULT -eq 0 ]; then
    echo "✅ All checks passed!"
    echo ""
    echo "Next steps:"
    echo "1. If pre-commit hook needed installation, run: pre-commit install"
    echo "2. Review docs/SECURITY.md for detailed setup and usage"
    echo "3. You're ready to commit safely!"
else
    echo "⚠️  Some findings detected in security scan"
    echo ""
    echo "Review the output above and:"
    echo "1. Fix any sensitive data in your files"
    echo "2. Run this script again to verify"
    exit 1
fi
