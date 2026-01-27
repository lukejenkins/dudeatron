"""
Centralized security patterns for all security scanning scripts.

This module provides shared pattern definitions for:
- check_sensitive_data.py (pre-commit hook)
- validate_examples.py (pre-commit hook for examples)
- security_scan.py (manual comprehensive scan)

All pattern changes should be made here to keep all scripts synchronized.
"""

# Approved anonymization patterns and false positives
# These are safe to use in documentation and example files
APPROVED_ANON = {
    # Placeholder IPs
    r"192\.168\.X\.Y",
    r"10\.0\.0\.X",
    # RFC1918 private IP ranges (production-appropriate for internal networks)
    r"(?:10|172\.(?:1[6-9]|2[0-9]|3[01])|192\.168)\.",
    r"\d+\.\d+\.\d+\.\d+\.example",
    # RFC 5737 TEST-NET documentation IPs
    r"8\.8\.8\.8",
    r"1\.1\.1\.1",
    r"203\.0\.113\.",  # TEST-NET-3 (198.51.100.0/24, 203.0.113.0/24)
    r"198\.51\.100\.",  # TEST-NET-2
    # Anonymized MAC addresses
    r"XX:XX:XX:XX:XX:XX",
    r"xx:xx:xx:xx:xx:xx",
    r"00:11:22:33:44:55",  # Example MAC in docs
    # Anonymized serials (ABC#### format)
    r"ABC\d{4,}",
    r"FOC123456789",  # Example serial in docs
    r"FOC12345678",   # Example serial in docs
    # URLs in documentation
    r"https?://",
    # Test/example domains
    r"example\.com",
    r"test\.com",
    r"localhost",
    # GitHub templated secrets / tokens in workflows
    r"\$\{\{[^}]+\}\}",
    r"token:\s*'write'",
    r"api_key:\s*'\$\{\{",
    r"TOKEN:\s*'\$\{\{",
    # Common service hostnames present in docs/config
    r"github\.com",
    r"ghcr\.io",
    r"python-poetry\.org",
    r"pdm-project\.org",
    r"abstra\.io",
    r"docs\.cursor\.com",
    # Example placeholders
    r"your_username",
    r"your_password",
    r"your_enable_secret",
    r"Password:\s*\"",
    r"Password:\s*\"\)",  # Password prompt string in code
    r"PASSWORD=your_password",  # Example config
    r"SECRET=your_enable_secret",  # Example config
    r"PASSWORD=AnotherSecret",  # Example in docs
    r"PASSWORD=your_enable_password",  # Example in docs
    r"USER=admin",  # Example in docs
    r"USER=admin_user",  # Example in docs
    # Hostnames in documentation
    r"pre-commit\.com",  # Documentation reference
    r"internal\.myco\.com",  # Example hostname in docs
    # Pattern markers in documentation
    r"password=`,",  # Code example marker
    r"secret=`,",  # Code example marker
    # Timestamped filenames used as examples
    r"\d{8}-\d{6}-[a-z0-9\-]+",
    # Device naming patterns
    r"(?i)device-\d+",
    r"(?i)ap-[\w\-]+",
    r"(?i)wlc-\d+",
}

# Sensitive data patterns to detect
# These patterns identify potentially sensitive information
SENSITIVE_PATTERNS = {
    "ip_non_rfc1918": {
        "pattern": (
            r"(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
            r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
        ),
        "description": "Non-RFC 1918 IP address",
    },
    "mac_address": {
        "pattern": r"(?i)(?:[0-9a-f]{2}[:\-]){5}(?:[0-9a-f]{2})",
        "description": "MAC address",
    },
    "serial_number": {
        "pattern": r"(?i)\b[A-Z]{3}\d{5,}\b",
        "description": "Device serial number",
    },
    "password": {
        "pattern": r"(?i)(?:password|passwd|pwd|secret)\s*[=:]\s*['\"]?([^\s'\"]+)",
        "description": "Hardcoded password",
    },
    "meraki_id": {
        "pattern": r"(?i)\b(?=[a-z0-9\-]*\d)(?:[a-z0-9]{4,10}-){2,3}[a-z0-9]{4,10}\b",
        "description": "Potential Meraki device ID",
    },
    "hostname_dns": {
        "pattern": (
            r"(?i)\b[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?\."
            r"(?:[a-z0-9\-]{1,63}\.)?"
            r"(?:com|net|org|io|gov|edu|co|uk|us|ca|ai|app|dev|cloud|local)\b"
        ),
        "description": "DNS hostname or domain",
    },
    "api_key_pattern": {
        "pattern": r"(?i)(?:api[_-]?key|token)\s*[=:]\s*['\"]?([^\s'\"]+)['\"]?",
        "description": "Potential API key or token",
    },
    "ssh_key": {
        "pattern": r"-----BEGIN (?:RSA|DSA|EC|OPENSSH) PRIVATE KEY",
        "description": "Private SSH key",
    },
    "username_pattern": {
        "pattern": r"(?i)(?:username|user)\s*[=:]\s*['\"]?([a-zA-Z0-9._\-]+)['\"]?",
        "description": "Potential username assignment",
    },
}

# Forbidden patterns for example files
# Example files should not contain real public IPs or MAC addresses
FORBIDDEN_IN_EXAMPLES = {
    "public_ip": {
        "pattern": (
            r"(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
            r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
            r"(?!(?:\.X\.Y|\.example))"
            r"(?!\s)"
            r"(?!"
            r"(?:10\.|192\.168\.|172\.(?:1[6-9]|2[0-9]|3[01])\.)"
            r")"
        ),
        "description": "Public IP address (examples should use RFC1918 or 192.168.X.Y)",
    },
    "real_mac": {
        "pattern": r"(?<![xX:])(?:[0-9a-f]{2}[:\-]){5}(?:[0-9a-f]{2})(?![xXx])",
        "description": "Real MAC address (use XX:XX:XX:XX:XX:XX)",
    },
}

# Files to skip in security scanning
SKIP_FILES = {
    "security_index.py",
    "security_patterns.py",
    "check_sensitive_data.py",
    "validate_examples.py",
    "security_scan.py",
    ".secrets.baseline",
    ".pre-commit-config.yaml",
}
