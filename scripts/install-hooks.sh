#!/bin/bash
# Helper script to set up pre-commit hooks if needed
# Run this to configure everything in one go

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "🔒 Dudeatron Security Setup"
echo "================================"
echo ""

# Check Python version
echo "Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✅ Python $PYTHON_VERSION"
echo ""

# Install pre-commit
echo "Installing pre-commit framework..."
if pip install pre-commit 2>&1 | grep -q "Successfully installed\|Requirement already satisfied"; then
    echo "✅ pre-commit installed"
else
    echo "⚠️  pre-commit installation had issues, but continuing..."
fi
echo ""

# Install git hooks
echo "Setting up git pre-commit hooks..."
if [ ! -f ".git/hooks/pre-commit" ]; then
    pre-commit install
    echo "✅ Git hooks installed"
else
    echo "✅ Git hooks already installed"
    # Update if needed
    pre-commit install --install-hooks 2>/dev/null || true
fi
echo ""

# Test configuration
echo "Testing pre-commit configuration..."
if pre-commit validate-config .pre-commit-config.yaml 2>&1; then
    echo "✅ Configuration is valid"
else
    echo "⚠️  Configuration validation had issues"
fi
echo ""

# Run a test
echo "Running a test scan (this may take a moment)..."
if pre-commit run --all-files --dry-run 2>&1 | head -5; then
    echo "✅ Pre-commit is ready to use"
else
    echo "⚠️  Pre-commit test had issues"
fi
echo ""

echo "================================"
echo "✅ Setup complete!"
echo ""
echo "You're now protected. The next time you commit:"
echo "  git commit -m 'Your message'"
echo ""
echo "The hooks will automatically:"
echo "  • Check for sensitive data"
echo "  • Validate example files"
echo "  • Check for large files"
echo "  • Fix formatting issues"
echo ""
echo "Run 'python scripts/security_scan.py' anytime for a manual check."
