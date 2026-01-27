# Dudeatron WLC - Usage Guide

## Overview

The WLC module provides functionality to connect to Cisco Catalyst 9800 Series WLCs (running IOS-XE) via SSH, execute monitoring commands, and combine the results into a unified CSV file for analysis. All parsing uses **Cisco Genie** library for production-grade structured output extraction.

## Features

- **SSH Connectivity**: Secure SSH connections to Cisco Catalyst 9800 WLC devices (IOS-XE)
- **Genie-Based Parsing**: Production-validated parsers from Cisco Genie library (v25.11+)
  - `ShowApSummary` - Structured AP summary data
  - `ShowApCdpNeighbor` - CDP neighbor relationships  
  - `ShowApMerakiMonitoringSummary` - Custom Meraki monitoring (non-standard Cisco command)
- **Command Execution**: Executes three key monitoring commands:
  - `show ap summary`
  - `show ap cdp neighbors`
  - `show ap meraki monitoring summary`
- **Session Logging**: Each SSH session is bookended with `show clock` and logged in plaintext to the `logs/` directory
- **Unified Data Merge**: Combines all three command outputs by AP name into a single CSV per WLC
- **ISO 8601 Naming**: All files follow the format `YYYYMMDD-HHMMSS-hostname.extension`
- **Configurable Output**: Specify output directory via CLI `-o` option or `OUTPUT_DIR` in `.env`

## Quick Start

### 1. Configuration

Ensure your `.env` file contains your credentials:

```bash
# SSH Connection Settings
SSH_USERNAME=your_username
SSH_PASSWORD=your_password
SSH_ENABLE_SECRET=your_enable_secret

# Connection Timeout (seconds)
SSH_TIMEOUT=30

# Note: DEVICE_TYPE is set automatically to cisco_wlc_ssh by dudeatron_wlc.py
# No need to configure it manually
```

### 2. Create WLC List

Create a `wlc.txt` file with your WLC hostnames or IP addresses (one per line):

```plaintext
# WLC Hostnames
wlc01.example.com
wlc02.example.com
192.168.1.100
```

See `wlc.txt.example` for reference.

### 3. Run the Script

```bash
python dudeatron_wlc.py
```

Optional arguments:
```bash
# Specify output directory
python dudeatron_wlc.py -o ./output
python dudeatron_wlc.py --output-dir ./my_csv_files
```

If no output directory is specified:
1. CLI argument (`-o/--output-dir`) takes precedence
2. Falls back to `OUTPUT_DIR` from `.env` if configured
3. Defaults to current directory (`.`)

## Output Files

### Session Logs

Session logs are saved to the `logs/` directory with the format:

```plaintext
YYYYMMDD-HHMMSS-hostname.log
```

Example: `20260105-143022-wlc01.example.com.log`

**Log Contents:**

- Initial `show clock` output
- `show ap summary` output
- `show ap cdp neighbors` output
- `show ap meraki monitoring summary` output
- Final `show clock` output

### CSV Files

CSV files are saved to the configured output directory with the format:

```plaintext
YYYYMMDD-HHMMSS-hostname.csv
```

Example: `20260106-171253-example-wlc4.csv`

**CSV Columns** (dynamically generated from all available fields):

From `show ap summary`:
- `ap_name` - AP hostname/name
- `ap_model` - AP model number
- `radio_mac` - Radio MAC address
- `mac_address` - Ethernet MAC address
- `slots` - Number of radio slots
- `location` - AP location string
- `country` - Country code
- `regulatory_domain` - Regulatory domain
- `ip_address` - AP IP address
- `state` - AP state (Registered, etc.)

From `show ap cdp neighbors`:
- `neighbor_name` - Connected switch hostname
- `neighbor_ip` - Connected switch IP address
- `neighbor_port` - Switch port connected to AP

From `show ap meraki monitoring summary`:
- `serial_number` - AP serial number
- `cloud_id` - Meraki cloud ID
- `meraki_status` - Meraki monitoring status

**Note:** The CSV combines all data based on AP name. APs present in one command output but not others will have empty fields for missing data. The `radio_mac` field is populated from both summary and Meraki monitoring sources (merged together).

## Module Structure

### `wlc_module.py`

Core functions for WLC operations using Genie parsers:

- `connect_and_execute_wlc_commands()` - SSH connection and command execution with `show clock` bookends for accurate timing
- `parse_show_ap_summary()` - Parse AP summary using `ShowApSummary` Genie parser; extracts 10 fields including radio_mac, mac_address, location, country, ip_address, state, etc.
- `parse_show_ap_cdp_neighbors()` - Parse CDP neighbor data using `ShowApCdpNeighbor` Genie parser; extracts 4 fields: ap_name, neighbor_name, neighbor_ip, neighbor_port
- `parse_show_ap_meraki_monitoring()` - Parse Meraki monitoring using custom `ShowApMerakiMonitoringSummary` Genie parser (non-standard Cisco command); extracts 6 fields including radio_mac, serial_number, cloud_id, status
- `combine_wlc_data_to_csv()` - Merge all three data sources by AP name, generate dynamic CSV columns, and write to file
- `process_wlc()` - High-level orchestration function to process a single WLC

### `dudeatron_wlc.py`

Main entry point script that:

1. Parses command-line arguments (including `-o/--output-dir`)
2. Loads configuration from `.env`
3. Prompts for missing credentials via interactive prompts
4. Reads WLC hostnames from `wlc.txt` (skips comments and blank lines)
5. Creates output directory if needed (respects OUTPUT_DIR from .env or CLI)
6. Processes each WLC sequentially using Genie parsers
7. Displays summary statistics with completion status

## Error Handling

The script handles common connection issues:

- **Connection Timeout**: Displays error message and continues to next WLC
- **Authentication Failure**: Reports authentication errors clearly
- **Missing Files**: Provides helpful error messages about missing configuration or hostname files
- **Parsing Errors**: Continues processing even if some commands fail or return unexpected output

## Tips

1. **Device Type**: The device type is automatically set to `cisco_xe` by the script - this is correct for Catalyst 9800 WLCs running IOS-XE
2. **Testing**: Start with a single WLC in `wlc.txt` to verify connectivity
3. **Credentials**: If credentials are missing from `.env`, the script will prompt interactively. Enable secret can be skipped (Enter) if not needed
4. **Timeout**: Increase `SSH_TIMEOUT` in `.env` if working with slow or remote WLCs (default: 30 seconds)
5. **Logs**: Check the `logs/` directory for full session transcripts if parsing issues occur
6. **Output Directory**: Use `-o` CLI option for quick one-off output locations, or set `OUTPUT_DIR` in `.env` for consistent behavior
7. **Scale Testing**: Script successfully processes WLCs with 2,000+ APs; larger deployments may need concurrent connections (planned feature)

## Troubleshooting

### "Authentication failed"

- Verify `SSH_USERNAME` and `SSH_PASSWORD` in `.env`
- Check that the credentials have proper access to the WLC
- Ensure no trailing whitespace in `.env` values

### "Connection timeout"

- Verify network connectivity to the WLC
- Increase `SSH_TIMEOUT` in `.env` (default: 30 seconds)
- Check firewall rules allow SSH (port 22) to the WLC

### Empty CSV columns

- Some WLCs may not support all commands (e.g., Meraki monitoring may not be enabled)
- Verify the command syntax is supported on your WLC version and model
- Check the session log in `logs/` to see the actual command output

### Parser errors

- WLC output format may vary by Catalyst model and IOS-XE version
- Check the session log (`logs/TIMESTAMP-hostname.log`) for the actual command output
- Genie parsers are validated against Catalyst 9800 standard output formats
- For non-standard output, custom regex patterns in `parse_show_ap_*()` functions may need adjustment

### CSV file location issues

- Verify output directory is writable: Check permissions on the directory specified by `-o` or `OUTPUT_DIR`
- If using relative path (e.g., `./output`), ensure it exists or script will create it
- Check `wlc.txt` is in the correct location and is readable

### Genie Parser Import Errors

- Ensure `.venv` is activated: `source .venv/bin/activate` (macOS/Linux)
- Verify requirements installed: `pip install -e ../genieparser -e .`
- Check genieparser fork is cloned: `git clone https://github.com/lukejenkins/genieparser.git ../genieparser`

## Genie Parser Integration Details

This project uses a custom fork of Cisco Genie for production-grade output parsing:

- **Fork Location**: `../genieparser` (lukejenkins/genieparser)
- **Meraki Parser**: Custom `ShowApMerakiMonitoringSummary` class added for non-standard Cisco command
- **Development**: The fork is installed in editable mode (`-e ../genieparser`) for rapid iteration
- **Stubs**: Custom minimal stubs in `genieparser/src/genie/` reduce pyATS dependency

### Example CSV Output

Sample output from `show ap summary`, `show ap cdp neighbors`, and `show ap meraki monitoring summary` merged together:

```csv
ap_name,ap_model,radio_mac,mac_address,slots,location,country,ip_address,state,neighbor_name,neighbor_ip,neighbor_port,serial_number,cloud_id,meraki_status
canary-ap4,9130AXI,687d.b45f.73a0,687d.b45f.73a0,2,Fab A,UK,10.6.33.106,Registered,switch-01,10.1.1.1,Gi1/0/1,ABC123,cloud-456,online
et-101-ap1,9130AXI,f0d8.05f5.33c0,f0d8.05f5.33c0,2,Fab B,UK,10.6.32.146,Registered,switch-02,10.1.1.2,Gi1/0/2,DEF456,cloud-789,online
```

## Future Enhancements

- Concurrent connections to multiple WLCs (improve processing speed for large deployments)
- Additional WLC commands (`show version`, `show inventory`, `show ap config general`, etc.)
- JSON output format option
- Integration with time-series databases (Prometheus, InfluxDB, etc.)
- Diff comparison between multiple runs
- Contribute Meraki monitoring parser upstream to CiscoTestAutomation/genieparser
- AP replacement project management integration (Asana/Jira)

## See Also

- [AGENTS.md](AGENTS.md) - Project documentation and AI assistant guidelines
- [README.md](README.md) - Main project README
- `.env.example` - Configuration template
