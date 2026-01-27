#!/usr/bin/env python3
"""
Index of security documentation and tools.
Helps navigate all the security resources.
"""

SECURITY_RESOURCES = {
    "Quick Start": {
        "description": "Get started in 30 seconds",
        "files": [
            ("SECURITY_COMPLETE.md", "Full setup summary and next steps"),
            ("SECURITY_QUICKSTART.md", "Quick reference card for common tasks"),
        ],
        "commands": [
            ("bash scripts/install-hooks.sh", "Easiest one-command setup"),
            ("python scripts/security_scan.py", "Manual security check anytime"),
        ]
    },
    
    "Setup & Installation": {
        "description": "For initial setup and configuration",
        "files": [
            ("SECURITY.md", "Comprehensive setup guide with troubleshooting"),
            ("SECURITY_SETUP.md", "What was created and why"),
            (".pre-commit-config.yaml", "Pre-commit hooks configuration"),
            (".secrets.baseline", "Secrets detection baseline"),
        ],
        "commands": [
            ("pre-commit install", "Install git hooks (must run once)"),
            ("bash scripts/setup-security.sh", "Verify setup with checklist"),
            ("bash scripts/install-hooks.sh", "Complete setup helper"),
        ]
    },
    
    "Using Security Checks": {
        "description": "How to use the checks in your workflow",
        "commands": [
            ("git commit -m 'message'", "Auto-checked by pre-commit hooks"),
            ("python scripts/security_scan.py", "Manual scan before committing"),
            ("pre-commit run --all-files", "Comprehensive hook check"),
            ("pre-commit run --dry-run", "See what would be checked"),
        ]
    },
    
    "Security Tools": {
        "description": "Individual security check tools",
        "scripts": [
            ("scripts/install-hooks.sh", "One-command setup"),
            ("scripts/check_sensitive_data.py", "Detect IP/MAC/serial/etc patterns"),
            ("scripts/validate_examples.py", "Ensure example files are anonymized"),
            ("scripts/security_scan.py", "Manual comprehensive scanner"),
            ("scripts/setup-security.sh", "Setup verification checklist"),
        ]
    },
    
    "What's Protected": {
        "description": "What sensitive data will be blocked",
        "patterns": [
            ("Public IP addresses", "Non-RFC 1918 addresses (allows 192.168.X.Y, 10.0.0.X)"),
            ("MAC addresses", "Physical device identifiers"),
            ("Device serial numbers", "Hardware identifiers"),
            ("Passwords & API keys", "Credentials and secrets"),
            ("SSH private keys", "Authentication keys"),
            ("Cloud IDs", "Cloud service identifiers"),
            ("Meraki device IDs", "Meraki device identifiers"),
            ("Hostnames & DNS", "Device and domain names"),
            ("Large files", "Files > 1MB"),
        ]
    },
    
    "Anonymization Standards": {
        "description": "How to properly anonymize data in examples",
        "standards": [
            ("IP Address", "192.168.X.Y or 10.0.0.X", "10.1.50.100 → 192.168.X.Y"),
            ("MAC Address", "XX:XX:XX:XX:XX:XX", "00:11:22:33:44:55 → XX:XX:XX:XX:XX:XX"),
            ("Serial Number", "ABC0000, ABC0001, etc.", "FOC123456789 → ABC0000"),
            ("Hostname", "ap-building-A, device-1", "ap-office-1 → ap-building-A"),
            ("Domain", "example.com or test.com", "internal.myco.com → example.com"),
        ]
    },
    
    "Troubleshooting": {
        "description": "Common issues and solutions",
        "issues": [
            ("Hooks not running", "pre-commit uninstall && pre-commit install"),
            ("False positive detected", "pre-commit run detect-secrets -- --update-baseline"),
            ("Pre-commit not installed", "pip install pre-commit"),
            ("Need to skip checks", "git commit --no-verify (NOT recommended)"),
        ]
    }
}


def print_index():
    """Print the security index."""
    print("\n" + "="*70)
    print("🔒 DUDEATRON SECURITY - RESOURCE INDEX")
    print("="*70 + "\n")
    
    for section, content in SECURITY_RESOURCES.items():
        print(f"📌 {section}")
        print(f"   {content.get('description', '')}\n")
        
        # Files
        if "files" in content:
            print("   Files:")
            for file, desc in content["files"]:
                print(f"     • {file:<40} {desc}")
            print()
        
        # Scripts
        if "scripts" in content:
            print("   Scripts:")
            for script, desc in content["scripts"]:
                print(f"     • {script:<40} {desc}")
            print()
        
        # Commands
        if "commands" in content:
            print("   Commands:")
            for cmd, desc in content["commands"]:
                print(f"     $ {cmd:<38} {desc}")
            print()
        
        # Patterns
        if "patterns" in content:
            for pattern, desc in content["patterns"]:
                print(f"     • {pattern:<40} {desc}")
            print()
        
        # Standards
        if "standards" in content:
            for data_type, format_str, example in content["standards"]:
                print(f"     • {data_type:<15} → {format_str:<25} ({example})")
            print()
        
        # Issues
        if "issues" in content:
            for issue, solution in content["issues"]:
                print(f"     • {issue:<30} → {solution}")
            print()
        
        print()
    
    print("="*70)
    print("Get started: bash scripts/install-hooks.sh")
    print("="*70 + "\n")


if __name__ == "__main__":
    print_index()
