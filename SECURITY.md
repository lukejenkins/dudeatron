# Dudeatron Security Pre-Commit Setup Guide

This guide helps you set up security checks to prevent committing sensitive information (credentials, IP addresses, device names, serial numbers, etc.).

## What's Protected

The pre-commit hooks will detect and prevent committing:

- **Credentials**: Passwords, API keys, SSH keys, tokens
- **Network Data**: Real IP addresses, MAC addresses, DNS hostnames
- **Device Info**: Serial numbers, Meraki IDs, device names
- **High-Entropy Strings**: Potential secrets/tokens

## Setup Instructions

### 1. Install pre-commit framework

```bash
pip install pre-commit
```

This installs the pre-commit framework globally or in your virtual environment.

### 2. Initialize the git hooks

From the project root:

```bash
pre-commit install
```

This sets up git hooks that run automatically before each commit.

### 3. Test the installation

Run a check on all files:

```bash
pre-commit run --all-files
```

You should see checks for:

- Sensitive data patterns
- Large files
- Merge conflicts
- Example file anonymization
- YAML/JSON syntax

## How It Works

### Automatic (on every commit)

When you run `git commit`, the hooks automatically:

1. ✅ Check for sensitive patterns (IPs, MACs, serials, etc.)
2. ✅ Validate example files use anonymized data
3. ✅ Catch accidental large file commits
4. ✅ Detect merge conflicts
5. ✅ Fix trailing whitespace

If issues are found, the commit is blocked until you fix them.

### Manual checks

Run anytime with:

```bash
# Check all files
pre-commit run --all-files

# Check only staged files
pre-commit run

# Check specific file
pre-commit run --files path/to/file.txt
```

## Anonymization Standards

Use these formats for example and test files:

| Data Type | Anonymized Format | Examples |
|-----------|-------------------|----------|
| **IPv4 Address** | `192.168.X.Y` or `10.0.0.X` | `192.168.1.1` → `192.168.X.Y` |
| **MAC Address** | `XX:XX:XX:XX:XX:XX` | `00:11:22:33:44:55` → `XX:XX:XX:XX:XX:XX` |
| **Serial Number** | `ABC0000`, `ABC0001`, etc. | `FOC12345678` → `ABC0000` |
| **Hostname/Device** | `device-1`, `ap-building-A` | `ap-office-1.example.com` → `ap-building-A` |
| **Meraki ID** | `meraki-device-1` | `L18-12345-00000` → `meraki-device-1` |
| **Domain Name** | `example.com` or `test.com` | Keep as is for examples |

### Good Example Files

**aps.txt.example** ✅

```plaintext
192.168.X.Y
192.168.X.Z
10.0.0.X
```

**wlc.txt.example** ✅

```plaintext
# WLC controllers
10.0.0.X
10.0.0.Y
```

### Bad Example Files

**aps.txt.example** ❌

```plaintext
10.1.1.50
10.1.1.51
172.20.1.10
```

## For Real Device Lists

Put actual device information in files that are `.gitignore`d:

```bash
# File: .gitignore
aps.txt      # Your actual AP list
wlc.txt      # Your actual WLC list
```

Then commit only the example versions:

- `aps.txt.example` (anonymized)
- `wlc.txt.example` (anonymized)

## For Credentials

Always use `.env` for credentials and configuration:

```bash
# File: .env (NEVER COMMIT)
SSH_USER=admin
SSH_PASS=MySecurePassword123
ENABLE_PASSWORD=AnotherSecret

# File: .env.example (SAFE TO COMMIT)
SSH_USER=admin_user
SSH_PASS=your_password_here
ENABLE_PASSWORD=your_enable_password
```

Make sure `.env` is in `.gitignore`:

```plaintext
.env
.envrc
```

## Debugging Failed Checks

### If a check fails

1. **Read the output carefully** - it shows which file and what pattern matched
2. **Verify it's real data** - might be a false positive
3. **Fix the data** - anonymize or remove it
4. **Try committing again**

### If it's a false positive

Edit `.secrets.baseline` to whitelist the pattern:

```bash
pre-commit run detect-secrets -- --update-baseline
```

This creates/updates `.secrets.baseline` with acceptable patterns.

### To bypass a check (not recommended)

```bash
# Skip pre-commit hooks for this commit ONLY
git commit --no-verify -m "Your message"
```

**Note**: Only use this if you're absolutely certain there's no sensitive data.

## Common Issues

### "Command not found: pre-commit"

Ensure pre-commit is installed:

```bash
pip install pre-commit
# OR
pip install --user pre-commit
```

Then run:

```bash
pre-commit install
```

### Hooks not running automatically

Check they're installed:

```bash
ls -la .git/hooks/pre-commit
# Should exist and be executable
```

Reinstall if needed:

```bash
pre-commit uninstall
pre-commit install
```

### My commit is blocked but data looks anonymized

The patterns are conservative to be safe. If it's a legitimate false positive:

1. Make sure it matches the anonymization standards above
2. Update `.secrets.baseline`
3. Or check if you accidentally used a real format

## Manual Security Scan

For a comprehensive scan anytime:

```bash
python scripts/security_scan.py
```

This scans key project files and shows findings.

## GitHub Secret Scanning

When you push to GitHub, GitHub automatically scans for common secrets (AWS keys, GitHub tokens, etc.). If anything is detected:

1. GitHub will notify you
2. Remove it from your repository
3. Consider it compromised - rotate it immediately
4. Use the GitHub UI to remove sensitive commits from history if needed

## Files Excluded from Checks

The following are intentionally skipped (whitelisted):

- `.secrets.baseline` - used by detect-secrets
- `.pre-commit-config.yaml` - configuration file
- Virtual environments (`venv/`, `.venv/`)
- Caches and build files (`__pycache__/`, `dist/`)
- This guide (`SECURITY.md`)

## Questions?

Refer to:

- [pre-commit documentation](https://pre-commit.com/)
- [detect-secrets documentation](https://github.com/Yelp/detect-secrets)
- Project: [AGENTS.md](AGENTS.md)