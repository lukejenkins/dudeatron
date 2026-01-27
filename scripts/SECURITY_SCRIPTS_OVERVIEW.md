# Security Scripts Overview

This document describes the security scanning infrastructure and confirms all scripts are synchronized.

## Centralized Pattern Management

**All security patterns are now managed in a single file: `security_patterns.py`**

This centralized approach ensures:
- ✅ All scripts use identical patterns
- ✅ No risk of patterns getting out of sync
- ✅ Easy to validate and update approved patterns
- ✅ Single source of truth for all security checks

## Scripts and Their Roles

### 1. `check_sensitive_data.py` (Pre-commit Hook)
- **Trigger**: Automatically runs on `git commit`
- **Scope**: Only scans files being committed (staged files)
- **Purpose**: Block commits containing sensitive data patterns
- **Configuration**: Called by `.pre-commit-config.yaml`

### 2. `validate_examples.py` (Pre-commit Hook)
- **Trigger**: Automatically runs on `git commit` for `.example` files
- **Scope**: Only files matching `*.example` or `example.*` pattern
- **Purpose**: Ensure example files use anonymized data (allow RFC1918 IPs, block public IPs)
- **Configuration**: Called by `.pre-commit-config.yaml`

### 3. `security_scan.py` (Manual Tool)
- **Trigger**: Manual execution (`python scripts/security_scan.py`)
- **Scope**: All files in repository (excludes .gitignored files)
- **Purpose**: Comprehensive security audit before commits
- **Use Case**: Final check to catch any sensitive data in the working tree

## Shared Pattern Configuration

All three scripts import from `security_patterns.py` which defines:

### Approved Anonymization Patterns (APPROVED_ANON)
- RFC1918 IPs: `10.*`, `172.16-31.*`, `192.168.*`
- Placeholder IPs: `192.168.X.Y`, `10.0.0.X`
- RFC 5737 TEST-NET IPs: `203.0.113.*`, `198.51.100.*` (documentation use)
- Common DNS examples: `8.8.8.8`, `1.1.1.1`
- Anonymized MACs: `XX:XX:XX:XX:XX:XX`, `00:11:22:33:44:55`
- Anonymized Serials: `ABC####`, `FOC123456789`, `FOC12345678`
- Example credentials: `your_username`, `your_password`, `your_enable_secret`
- Config examples: `PASSWORD=your_password`, `SECRET=your_enable_secret`
- Documentation hostnames: `example.com`, `test.com`, `github.com`, `pre-commit.com`
- Device patterns: `device-#`, `ap-*`, `wlc-#`

### Detected Sensitive Patterns
- Public IP addresses (non-RFC1918)
- Real MAC addresses (non-XX:XX:XX:XX:XX:XX format)
- Device serial numbers (Cisco format: ABC#####)
- Meraki device IDs
- DNS hostnames with specific TLDs
- Hardcoded passwords (`password=`, `secret=`, etc.)
- API keys and tokens
- SSH private keys
- Username assignments

## Testing Status

✅ **All security scripts tested and passing:**

```bash
# Pre-commit hooks
$ pre-commit run --all-files
Detect secrets...........................................................Passed
check for added large files..............................................Passed
check for merge conflicts................................................Passed
check yaml...............................................................Passed
fix end of files.........................................................Passed
trim trailing whitespace.................................................Passed
Check for sensitive patterns.............................................Passed
Validate example files are anonymized....................................Passed

# Manual security scan
$ python scripts/security_scan.py
📊 Scanned 40 files, skipped 390 .gitignored files
✅ No sensitive data detected in tracked files!
```

## Usage Workflow

### During Development
1. Edit files as normal
2. When ready to commit: `git add <files>`
3. Run `git commit -m "message"`
4. Pre-commit hooks automatically run
5. If hooks pass, commit succeeds
6. If hooks fail, fix issues and retry

### Before Major Commits
1. Run manual comprehensive scan: `python scripts/security_scan.py`
2. Review any findings
3. Fix issues or add to whitelist if false positive
4. Run pre-commit: `pre-commit run --all-files`
5. Commit when clean

## Protected Files (.gitignore)

These files are automatically excluded from commits and contain production data:
- `aps.txt` - Production AP list
- `wlc.txt` - Production WLC list
- `.env` - SSH credentials and configuration
- `logs/*` - SSH session logs
- `output/*` - Generated CSV files with device data

## False Positive Management

**IMPORTANT: All pattern changes are now made in `security_patterns.py` only.**

If a pattern is flagged incorrectly:

1. **Edit `security_patterns.py`**: Add the pattern to `APPROVED_ANON` set
2. **Test all scripts**: Run both `python scripts/security_scan.py` and `pre-commit run --all-files`
3. **Document the reason**: Add a comment explaining why the pattern is approved

The centralized approach ensures all three scripts (check_sensitive_data.py, validate_examples.py, and security_scan.py) automatically use the updated patterns.

**Never add patterns directly to individual scripts** - they all import from security_patterns.py.

Last synchronized: 2026-01-05
