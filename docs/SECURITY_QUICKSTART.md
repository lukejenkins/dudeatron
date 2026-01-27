# Quick Security Checklist

## Before Your First Commit

- [ ] Read [SECURITY.md](SECURITY.md) for detailed setup
- [ ] Run setup script: `bash scripts/setup-security.sh`
- [ ] Install pre-commit: `pip install pre-commit`
- [ ] Install hooks: `pre-commit install`
- [ ] Test it works: `pre-commit run --all-files`

## Before Every Commit

### Option 1: Automatic (easiest)

```bash
git commit -m "Your message"
# Hooks run automatically and block if issues found
```

### Option 2: Manual check first

```bash
python scripts/security_scan.py
# Review findings, fix issues, then commit
```

### Option 3: Full pre-commit check

```bash
pre-commit run --all-files
# Comprehensive check with all hooks
```

## Common Sensitive Data & How to Handle It

### Real Device List (aps.txt, wlc.txt)

```plaintext
❌ DON'T COMMIT:
10.1.2.100
10.1.2.101
192.168.50.10

✅ DO COMMIT (example only):
aps.txt.example:
192.168.X.Y
192.168.X.Z
```

### Credentials (.env)

```plaintext
❌ DON'T COMMIT:
SSH_PASS=MySecurePassword123

✅ DO COMMIT (.env.example only):
SSH_PASS=your_password_here
```

### Device Names/Serials

```plaintext
❌ DON'T COMMIT:
ap-office-1.example.com
FOC123456789

✅ DO COMMIT (in examples):
ap-building-A
ABC0000
```

## Anonymization Quick Reference

| Item | Real | Anonymized |
|------|------|------------|
| IP | 10.1.2.50 | 192.168.X.Y |
| MAC | 00:11:22:33:44:55 | XX:XX:XX:XX:XX:XX |
| Serial | FOC123456789 | ABC0000 |
| Hostname | ap-office-1 | ap-building-A |
| Password | MySecretPass | use .env instead |

## If Something Goes Wrong

### Commit blocked - not sure why?

```bash
# See what the check found
pre-commit run --all-files --verbose

# Then either:
# 1. Fix the data and try again
# 2. Review false positive in .secrets.baseline
```

### Need to see what files are checked?

```bash
# List all configured hooks
pre-commit run --all-files --dry-run
```

### Want to skip hooks (NOT recommended)?

```bash
# Only do this if you're absolutely certain
git commit --no-verify -m "Your message"
```

## Questions?

See [SECURITY.md](SECURITY.md) for detailed documentation.
