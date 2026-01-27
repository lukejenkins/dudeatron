# Documentation Index - Dudeatron Project

## Quick Navigation

| Document | Purpose | Audience | Best For |
|----------|---------|----------|----------|
| **[QUICKSTART.md](../QUICKSTART.md)** ⭐ | Get running in 5 minutes | New users | First-time setup |
| **[WLC_README.md](WLC_README.md)** | Complete WLC module guide | All users | Daily usage reference |
| **[AGENTS.md](../AGENTS.md)** | Project architecture & guidelines | Developers | Understanding design |
| **[DEVELOPMENT.md](DEVELOPMENT.md)** | Dev environment & workflows | Contributors | Contributing code |
| **[SESSION_SUMMARY.md](../AGENT-Notes/SESSION_SUMMARY.md)** | Latest session accomplishments | Project managers | Status overview |
| **[CLEANUP_CHECKLIST.md](../AGENT-Notes/CLEANUP_CHECKLIST.md)** | Session verification checklist | QA/Lead | Completion verification |
| **[README.md](../README.md)** | Project overview | Everyone | Project context |

## By Use Case

### 👤 I want to use the WLC tool
1. Start with [QUICKSTART.md](../QUICKSTART.md) for installation
2. Reference [WLC_README.md](WLC_README.md) for features and options
3. Check troubleshooting section in [WLC_README.md](WLC_README.md) if issues arise

### 🏗️ I want to understand the architecture
1. Read [README.md](../README.md) for project overview
2. Review [AGENTS.md](../AGENTS.md) for technical details and patterns
3. Check [DEVELOPMENT.md](DEVELOPMENT.md) for codebase organization

### 💻 I want to contribute code
1. Read [DEVELOPMENT.md](DEVELOPMENT.md) for setup instructions
2. Review [AGENTS.md](../AGENTS.md) for coding standards
3. Reference [SESSION_SUMMARY.md](../AGENT-Notes/SESSION_SUMMARY.md) for recent work

### 📋 I want to verify session completion
1. Review [SESSION_SUMMARY.md](../AGENT-Notes/SESSION_SUMMARY.md) for accomplishments
2. Check [CLEANUP_CHECKLIST.md](../AGENT-Notes/CLEANUP_CHECKLIST.md) for verification
3. Reference [AGENTS.md](../AGENTS.md) for detailed session notes

## Documentation by Topic

### Installation & Setup
- [QUICKSTART.md](../QUICKSTART.md) - Step-by-step installation
- [DEVELOPMENT.md](DEVELOPMENT.md) - Development environment setup
- [WLC_README.md](WLC_README.md) - Configuration reference

### Usage & Reference
- [QUICKSTART.md](../QUICKSTART.md) - Basic usage examples
- [WLC_README.md](WLC_README.md) - Complete feature documentation
- [WLC_README.md](WLC_README.md) - Troubleshooting guide

### Architecture & Design
- [AGENTS.md](../AGENTS.md) - System architecture and patterns
- [AGENTS.md](../AGENTS.md) - AI assistant guidelines
- [DEVELOPMENT.md](DEVELOPMENT.md) - Codebase structure

### Development & Contributing
- [DEVELOPMENT.md](DEVELOPMENT.md) - Development workflow
- [AGENTS.md](../AGENTS.md) - Coding standards and conventions
- [AGENTS.md](../AGENTS.md) - Genie parser development guide

### Project Status & Planning
- [SESSION_SUMMARY.md](../AGENT-Notes/SESSION_SUMMARY.md) - Latest session work
- [CLEANUP_CHECKLIST.md](../AGENT-Notes/CLEANUP_CHECKLIST.md) - Completion verification
- [AGENTS.md](../AGENTS.md) - Next steps and roadmap

## File Structure

```
dudeatron/
├── Documentation
│   ├── README.md ..................... Project overview
│   ├── QUICKSTART.md ................. Installation & basic usage
│   ├── AGENTS.md ..................... Architecture & guidelines
│   ├── docs/
│   │   ├── WLC_README.md ............. Feature reference & troubleshooting
│   │   ├── DEVELOPMENT.md ............ Dev setup & workflows
│   │   ├── DOCUMENTATION_INDEX.md .... This file
│   │   ├── SECURITY.md ............... Security setup guide
│   │   ├── SECURITY_QUICKSTART.md .... Security quick reference
│   │   ├── SECURITY_SETUP.md ......... Security configuration details
│   │   └── SECURITY_COMPLETE.md ...... Security overview
│   └── AGENT-Notes/
│       ├── SESSION_SUMMARY.md ........ Session accomplishments
│       ├── CLEANUP_CHECKLIST.md ...... Completion verification
│       └── SETUP_SUMMARY.txt ......... Security setup summary
│
├── Core Application
│   ├── dudeatron.py ................. AP management tool
│   ├── dudeatron_wlc.py ............ WLC management (CLI entry point)
│   └── wlc_module.py ............... WLC implementation (Genie parsers)
│
├── Configuration
│   ├── .env ......................... Runtime configuration (user-specific)
│   ├── .env.example ................ Configuration template
│   ├── wlc.txt ..................... WLC hostnames/IPs
│   ├── wlc.txt.example ............ WLC example format
│   ├── aps.txt ..................... AP hostnames/IPs
│   └── aps.txt.example ............ AP example format
│
├── Output
│   ├── output/ ..................... CSV exports (dynamically generated)
│   │   └── 20260106-171253-ogden-wlc4.csv
│   └── logs/ ....................... Session logs (timestamped)
│       └── 20260106/
│
└── Dependencies
    └── requirements.txt ............ Python package versions
```

## Key Concepts

### Genie Parser Integration
- All command parsing uses Cisco Genie library (v25.11+)
- Three parsers integrated: ShowApSummary, ShowApCdpNeighbor, ShowApMerakiMonitoringSummary
- Custom Meraki monitoring parser for non-standard Cisco command
- See: [AGENTS.md](AGENTS.md) - "Genie Parser Development" section

### Data Merge Strategy
- All three command outputs merged by AP name
- Dynamic CSV columns generated from all available fields
- Radio MAC field populated from both summary and Meraki sources
- See: [WLC_README.md](WLC_README.md) - "CSV Columns" section

### Output Configuration
- Output directory via CLI: `python dudeatron_wlc.py -o ./output`
- Or via environment: `OUTPUT_DIR=./output` in .env
- Or default to current directory
- See: [QUICKSTART.md](QUICKSTART.md) - "Configuration" section

## Recent Session (2026-01-06)

**What Was Done**:
- Fixed radio_mac field merge from Meraki parser
- Fixed CDP neighbor IP address parsing
- Added CLI output directory option
- Updated all documentation

**Files Changed**:
- `wlc_module.py` - Added radio_mac to merge logic
- `dudeatron_wlc.py` - Added argparse for output directory
- `WLC_README.md` - Complete documentation overhaul
- `AGENTS.md` - Session completion summary
- `DEVELOPMENT.md` - Session summary added

**Test Results**:
- ✅ 77 APs processed successfully (small WLC)
- ✅ 2,056 APs processed successfully (large WLC)
- ✅ All radio_mac values populated in CSV

See [SESSION_SUMMARY.md](../AGENT-Notes/SESSION_SUMMARY.md) for details.

## Support & Help

### Common Questions

**Q: How do I get started?**  
A: See [QUICKSTART.md](../QUICKSTART.md)

**Q: How do I use the WLC tool?**  
A: See [WLC_README.md](WLC_README.md)

**Q: How do I set up development environment?**  
A: See [DEVELOPMENT.md](DEVELOPMENT.md)

**Q: What's in the CSV output?**  
A: See [WLC_README.md](WLC_README.md) - "CSV Columns" section

**Q: Why is my output going to the wrong directory?**  
A: Check precedence in [QUICKSTART.md](../QUICKSTART.md) - "Usage" section

**Q: How do I contribute?**  
A: See [DEVELOPMENT.md](DEVELOPMENT.md) and [AGENTS.md](../AGENTS.md)

## Document Maintenance

All documentation is maintained in Markdown format and should be updated when:
- New features are added
- Bugs are fixed
- Architecture changes
- Session work is completed

Current documentation is current as of: **January 6, 2026**

---

**Project**: Dudeatron - Wireless Network Management Tool  
**Status**: Production Ready  
**Last Updated**: January 6, 2026, 5:20 PM
