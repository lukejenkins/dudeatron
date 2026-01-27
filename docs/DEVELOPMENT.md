# Development Guide

This guide covers local development setup and contribution workflows for Dudeatron.

## Local Setup

### Prerequisites

- Python 3.x
- SSH access to Catalyst 9800 WLCs and APs
- Git

### Initial Setup

```bash
# Clone this repository
git clone https://github.com/lukejenkins/dudeatron.git
cd dudeatron

# Clone the Genie fork (one level up)
cd ..
git clone https://github.com/lukejenkins/genieparser.git
cd dudeatron

# Install dependencies in editable mode
pip install -r requirements.txt

# Copy environment template and configure
cp .env.example .env
# Edit .env with your SSH credentials and device details
```

### Device Lists

- `aps.txt` - List of AP IP addresses (one per line, supports comments with #)
- `wlc.txt` - List of WLC IP addresses (one per line, supports comments with #)
- `test_aps.txt` - Test AP device list for safe development
- `test_single.txt` - Single device for targeted testing

Comment out devices or use test lists to avoid connecting to production during development.

## Genie Parser Development

### Understanding the Fork Setup

The Genie fork at `../genieparser/` is installed in **editable mode** via `requirements.txt`:

```plaintext
-e ../genieparser
```

This means any changes you make directly to the fork code are immediately active without reinstalling. This enables rapid iteration.

### Workflow: Making Parser Improvements

#### 1. Identify Parser Issues

When using Dudeatron commands, you may discover:

- Parser doesn't exist for a command
- Parser schema doesn't match actual device output
- Parser validation logic is too strict
- Parser missing optional fields

Example: `show ap summary` parser may need enhancement to handle edge cases in your environment.

#### 2. Create Feature Branch

```bash
cd ../genieparser
git checkout -b feature/enhance-show-ap-summary
```

Use descriptive branch names:

- `feature/` - New parser or significant enhancement
- `fix/` - Bug fix or validation improvement
- `docs/` - Parser documentation updates

#### 3. Locate and Modify Parser

Genie parsers for IOS-XE are in: `genieparser/src/genieparser/parsers/iosxe/show_ap.py`

For Catalyst 9800, look for parser classes like:

- `ShowApSummary` - Parses `show ap summary`
- `ShowApCdpNeighbor` - Parses `show ap cdp neighbor`
- `ShowApConfigGeneral` - Parses `show ap config general`
- `ShowApVersion` - Parses `show version` on WLC

#### 4. Understand Parser Structure

Genie parsers follow a consistent pattern:

```python
class ShowApSummary(ShowApSummary):
    """Parser for 'show ap summary' command"""

    cli_command = 'show ap summary'

    ELEMENT_SCHEMA = {
        'ap_name': str,
        'slots_count': int,
        'ap_model': str,
        'ethernet_mac': str,
        # ... more schema fields
    }

    EXPECTED_DATA_TYPES = {
        Optional('ap_name'): str,
        Optional('slots_count'): int,
        # ... more type definitions
    }

    def cli(self, *args, **kwargs):
        # Parsing logic here
        return result_dict
```

#### 5. Test Against Real Device Output

Before modifying parsers:

1. Capture actual device output
2. Save to a test file for reference
3. Create test fixtures in Genie's test directory
4. Verify parser output against expected schema

Example test creation:

```bash
# In genieparser test fixtures
genieparser/tests/iosxe/fixtures/show_ap_summary.txt
```

#### 6. Run Genie Tests

```bash
cd ../genieparser
pytest tests/iosxe/test_show_ap.py -v
```

#### 7. Test in Dudeatron Context

Before submitting upstream, verify the parser works in actual Dudeatron commands:

```bash
cd dudeatron
python dudeatron_wlc.py  # Test with real WLC
```

Confirm parsed data appears correctly in CSV output.

#### 8. Commit and Push

```bash
cd ../genieparser
git add genieparser/src/genieparser/parsers/iosxe/show_ap.py
git commit -m "Enhance ShowApSummary parser for Catalyst 9800

- Add support for additional AP status fields
- Improve validation for edge cases in location strings
- Fix regex pattern for multi-slot APs

Tested against Catalyst 9800 real device output.
Fixes issue with APs in locations with special characters."

git push origin feature/enhance-show-ap-summary
```

**Commit message guidelines:**

- First line: concise summary (50 chars max)
- Blank line
- Bullet points explaining what changed and why
- Include device model and OS version tested against
- Reference any issues or real-world problems solved

### Workflow: Contributing Upstream

#### 1. Create Pull Request

Open a PR against `CiscoTestAutomation/genieparser`:

- Base branch: `main`
- Compare branch: your feature branch
- Title: "Enhance ShowApSummary parser for Catalyst 9800"
- Description:
  - What the parser improvement does
  - Real-world use case (reference Dudeatron)
  - Testing verification
  - Device model and OS version tested

#### 2. Respond to Review

Cisco's maintainers may request:

- Additional test cases
- Documentation improvements
- Schema refinements
- Validation logic clarification

#### 3. After Merge

Once merged upstream:

```bash
cd ../genieparser
git checkout main
git pull upstream main
```

Update Dudeatron's `requirements.txt`:

```plaintext
# Change from:
-e ../genieparser

# To:
genie>=X.Y.Z
```

Then reinstall:

```bash
pip install -r requirements.txt --upgrade
```

## Dudeatron Development

### Running Commands

```bash
# Parse APs (uses test_aps.txt)
python dudeatron.py --test

# Parse WLCs (uses wlc.txt)
python dudeatron_wlc.py

# Single device
python dudeatron.py --device 192.168.1.100
```

### Logging and Output

- SSH session logs: `logs/` directory with timestamps
- CSV exports: Project root with ISO 8601-style naming
- Session bookends: `show clock` commands bracket each session for time correlation

### Adding New Commands

To parse a new command (e.g., `show ap inventory`):

1. **Verify Genie support**: Check if Genie has a parser for it

   ```bash
   cd ../genieparser
   grep -r "show ap inventory" genieparser/
   ```

2. **If parser exists**: Use it in `wlc_module.py`
3. **If parser missing**:

   - Create/enhance parser in your Genie fork
   - Test and submit PR upstream
   - Once merged, integrate into Dudeatron

4. **Add to command list** in `dudeatron_wlc.py` and `wlc_module.py`
5. **Update parsing function** to handle new command output
6. **Add to CSV export** logic in `combine_wlc_results_and_write_csv()`

## Testing

### Manual Testing

```bash
# Test single WLC
python dudeatron_wlc.py

# Verify CSV output
head output/20260105-*.csv

# Check session logs
tail -f logs/20260105-*.log
```

### Code Quality

```bash
# Check PEP 8 compliance
pip install black flake8
black --check .
flake8 .

# Auto-format code
black .
```

## Troubleshooting

### SSH Connection Issues

- Verify credentials in `.env`
- Check device accessibility: `ping <ip>`
- Increase `SSH_TIMEOUT` in `.env` if WLC is slow to respond
- Check SSH logs in `logs/` directory

### Parser Failures

- Verify Genie parser exists for the command
- Check actual device output: `ssh <device> 'show ap summary'`
- Compare against Genie test fixtures
- Submit enhancement PR to Genie if edge case found

### CSV Export Issues

- Verify parsing functions return proper dictionaries
- Check column naming consistency
- Ensure data types match schema

## Documentation Updates

When making changes:

- Update AGENTS.md for high-level architectural changes
- Update DEVELOPMENT.md (this file) for development workflow changes
- Update README.md for user-facing feature changes
- Add docstrings to new functions following Google style format

## Common Tasks

### Sync Genie Fork with Upstream

```bash
cd ../genieparser
git fetch upstream
git merge upstream/main
```

### Create Test Device List

```bash
cp wlc.txt test_wlc.txt
# Edit test_wlc.txt with non-production device IPs
```

### Analyze Parser Performance

```bash
# Time a single WLC command
time python dudeatron_wlc.py
```

### Extract Device Output for Testing

```bash
# Save raw SSH output for creating parser test fixtures
ssh -l admin <wlc_ip> 'show ap summary' > /tmp/raw_output.txt
```

## Recent Session Summary (2026-01-06)

### Accomplishments

This session completed the WLC management implementation with full Genie parser integration:

**Environment & Setup**
- Recreated `.venv` from scratch with Python 3.14
- Resolved Genie stub compatibility issues:
  - Added `declare_token()` method to `_AbstractStub` 
  - Updated `_Placeholder.__init__()` to accept variadic args for schema patterns like `Or(int, str)`
- All three Genie parsers working correctly

**Bug Fixes**
- **CDP Parser Regex**: Fixed `show ap cdp neighbors` regex to capture `neighbor_ip` from command output (was parsing 0 entries, now correctly parses 76+)
- **Radio MAC Merge**: Added `radio_mac` to Meraki data merge logic in `combine_wlc_data_to_csv()` (was being discarded during merge)
- **CSV Columns**: Removed empty columns (`capability`, `local_port`) that weren't populated by parsers

**Feature Enhancements**
- Added CLI option `-o/--output-dir` for specifying output directory
- Added `OUTPUT_DIR` configuration option in `.env`
- Output directory precedence: CLI args > .env variable > current directory

**Testing & Validation**
- Small WLC: Successfully processed 77 APs with Genie parsers
- Large WLC: Successfully processed 2,056 APs without errors (validates scalability)
- All 77 APs have valid `radio_mac` values from merged data sources

**Documentation**
- Updated [WLC_README.md](WLC_README.md) with:
  - Genie parser details and integration approach
  - Complete CSV column documentation with data sources
  - Updated troubleshooting guide with parser-specific issues
  - Configuration examples and usage patterns
  - Example CSV output showing merged data
- Updated [AGENTS.md](AGENTS.md) with comprehensive session summary

### Files Modified
- [wlc_module.py](wlc_module.py) - Fixed radio_mac merge in combine_wlc_data_to_csv()
- [dudeatron_wlc.py](dudeatron_wlc.py) - Added argparse for output directory option
- [WLC_README.md](WLC_README.md) - Comprehensive documentation overhaul
- [AGENTS.md](AGENTS.md) - Session completion summary

### Test Results
- **Output File**: `output/20260106-171253-ogden-wlc4.csv`
- **Rows**: 77 APs + 1 header = 78 total
- **Columns**: 16 (dynamically generated from all three command sources)
- **Data Quality**: All radio_mac values populated from merged sources

### Known Limitations & Future Work
- Single serial SSH connections (concurrent support planned)
- Meraki monitoring parser is custom (not in upstream Genie yet)
- Additional WLC commands not yet implemented (show version, show inventory, show ap config general)

---

For more details on project architecture, see [AGENTS.md](AGENTS.md).
