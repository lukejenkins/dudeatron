# dudeatron

A buddy to help me manage my wireless network.

I hope you find something here to be useful.

## Platform Specification

**This tool is designed for Catalyst 9800 Series WLCs running IOS-XE.** It does not support legacy AireOS controllers. All WLC connections use the `cisco_xe` device type.

## Features

- [ ] Add support for SSHing to APs and then running & parsing the following commands:
  - [ ] `show version` Parsing the following fields:
    - [ ] AP Name
    - [ ] Model
    - [ ] Serial Number
    - [ ] Base ethernet MAC Address
    - [ ] Software Version (AP Running Image)
    - [ ] Primary Boot Image
    - [ ] Secondary Boot Image
    - [ ] Uptime
    - [ ] Last reload time
    - [ ] Last reload reason
    - [ ] Primary Boot Image Hash
    - [ ] Secondary Boot Image Hash
    - [ ] Radio FW version
    - [ ] QC_IMAGE_VERSION_STRING
    - [ ] NSS FW version
    - [ ] Cloud ID
  - [ ] `show inventory`
- [ ] Add support for SSHing to WLCs and then running & parsing the following commands:
  - [ ] `show version`
  - [ ] `show inventory`
  - [ ] `show ap summary`
  - [ ] `show ap summary load-info`
  - [ ] `show ap uptime`
  - [ ] `show ap name $AP_NAME config general`
  - [ ] `show ap name $AP_NAME ethernet statistics`
  - [ ] `show ap cdp neighbors`
  - [ ] `show ap meraki monitoring summary`
- [ ] Implement `python-dotenv` for configuration management
- [ ] Add data output to the following
  - [ ] Data output to json files
  - [ ] Data output to a time series database
  - [ ] Data output to Prometheus
  - [ ] Data output to CSV files with comprehensive data flattening
- [ ] Add example visualizations using Grafana
- [ ] Add support for multiple SSH connections at once
- [ ] Add support for pulling equiptment lists (e.g. APs, WLCs) from Cisco DNA Center
- [ ] Add support for pulling equiptment lists (e.g. APs, WLCs) from netbox
- [ ] Help with AP replacement projects
  - [ ] Keep track of AP to switchport relationships
  - [ ] As APs get replaced, generate code snippets to configure APs
    - [ ] Set AP name
    - [ ] Set Primary Controller
    - [ ] Add AP to location ( ap location name $BuildingCode-location )
    - [ ] Set AP height
  - [ ] Update project status in Asana
  - [ ] Generate config archives
    - [ ] `show ap name $AP_NAME config general`
    - [ ] `show ap name $AP_NAME ethernet statistics`
    - [ ] `show ap name $AP_NAME cdp neighbors`
    - [ ] `show ap meraki monitoring summary`
    - [ ] `show ap name $AP_NAME inventory`

  ## Possible Future Features

  - Add pytest-based test runner (e.g., simple `make test` or tox) and wire into CI
  - Expand parser coverage tests with additional sample logs (e.g., show version, show inventory)
  - Add lightweight unit tests around helper utilities in `wlc_module.py`
  - A TUI user interface for selecting devices and commands to run

## AI Disclosure

**Here there be robots!** I *think* they are friendly, but they might just be very good at pretending. You might be a fool if you use this project for anything other than as an example of how silly it can be to use AI to code with.

> This project was developed with the assistance of language models from companies such as OpenAI and Anthropic, which provided suggestions and code snippets to enhance the functionality and efficiency of the tools. The models were used to generate code, documentation, distraction, moral support, moral turpitude, and explanations for various components of the project.

## Project Structure

```
dudeatron/
├── Core Scripts
│   ├── dudeatron.py              # AP management (netmiko SSH, CLI parsing)
│   ├── dudeatron_wlc.py          # WLC management with Genie parsers
│   └── wlc_module.py             # WLC-specific functions (SSH, parsing, CSV export)
│
├── Configuration
│   ├── .env                      # SSH credentials, device type, timeout (create from .env.example)
│   ├── .pre-commit-config.yaml   # Security pre-commit hooks configuration
│   ├── .secrets.baseline         # Secrets detection baseline
│   └── requirements.txt          # Python dependencies
│
├── Device Lists
│   ├── aps.txt                   # Production AP device list
│   ├── wlc.txt                   # Production WLC device list
│   ├── test_aps.txt              # Test AP device list
│   ├── test_single.txt           # Single test device
│   └── *.example                 # Configuration templates
│
├── Documentation
│   ├── README.md                 # This file
│   ├── AGENTS.md                 # **START HERE** - AI agent guidelines and project overview
│   ├── QUICKSTART.md             # Quick start guide for basic operations
│   ├── CLAUDE.md                 # Pointer to AGENTS.md (for Claude AI)
│   ├── GEMINI.md                 # Pointer to AGENTS.md (for Gemini AI)
│   ├── docs/                     # Detailed documentation
│   │   ├── WLC_README.md         # WLC management detailed documentation
│   │   ├── DEVELOPMENT.md        # Development guidelines and current status
│   │   ├── SECURITY.md           # Security setup and pre-commit framework
│   │   ├── SECURITY_QUICKSTART.md # Quick reference for security setup
│   │   ├── SECURITY_SETUP.md     # Security configuration details
│   │   ├── SECURITY_COMPLETE.md  # Security overview
│   │   └── DOCUMENTATION_INDEX.md # Navigation hub for all docs
│   └── AGENT-Notes/              # Session documentation
│       ├── SESSION_SUMMARY.md    # Latest session quick summary
│       ├── CLEANUP_CHECKLIST.md  # Session completion checklist
│       └── SETUP_SUMMARY.txt     # Security setup summary
│
├── scripts/ (Security and utility scripts)
│   ├── install-hooks.sh          # One-command pre-commit setup
│   ├── check_sensitive_data.py   # Pattern detector for sensitive data
│   ├── validate_examples.py      # Validates example files
│   ├── security_scan.py          # Manual security scanner
│   └── security_patterns.py      # Centralized pattern definitions
│
├── tests/ (Test and debugging scripts)
│   ├── install-hooks.sh          # One-command pre-commit setup
│   ├── check_sensitive_data.py   # Pattern detector for sensitive data
│   ├── validate_examples.py      # Validates example files
│   ├── security_scan.py          # Manual security scanner
│   ├── security_patterns.py      # Centralized pattern definitions
│   └── README.md                 # SECURITY folder guide
│
├── tests/ (Test and debugging scripts)
│   ├── test_parser_output.py     # Verifies Genie parser field extraction
│   ├── test_cdp_parsing.py       # Debugs CDP neighbor parsing
│   ├── __init__.py               # Test package initialization
│   └── README.md                 # Test suite documentation
│
├── logs/                         # SSH session logs (timestamped by date)
│   └── YYYYMMDD/
│       └── YYYYMMDD-HHMMSS-hostname.log
│
└── output/                       # Generated CSV files
    └── YYYYMMDD-HHMMSS-hostname.csv
```

## Getting Started

**First time?** Start here:
1. Read [AGENTS.md](AGENTS.md) for project overview and guidelines
2. Follow [QUICKSTART.md](QUICKSTART.md) for basic setup
3. See [WLC_README.md](docs/WLC_README.md) for WLC-specific operations

**For security setup:**
- See [SECURITY_QUICKSTART.md](docs/SECURITY_QUICKSTART.md) for quick reference
- Run `bash SECURITY/install-hooks.sh` to enable pre-commit protection

**For development:**
- Check [DEVELOPMENT.md](docs/DEVELOPMENT.md) for current status and guidelines
- Review session notes in `AGENT-Notes/` directory for historical context

## AI Agents

**Operational guidance for all AI agents is centralized in [AGENTS.md](AGENTS.md).**

Before starting work, please read [AGENTS.md](AGENTS.md) for:
- Project overview and architecture
- Code style and naming conventions
- Security guidelines and data handling
- Session documentation procedures
- TODO tracking and progress updates

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
