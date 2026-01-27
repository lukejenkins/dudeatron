# Quick Start Guide - Dudeatron WLC

## Installation (First Time)

```bash
# Clone repositories
git clone https://github.com/lukejenkins/dudeatron.git
cd dudeatron
cd ..
git clone https://github.com/lukejenkins/genieparser.git
cd dudeatron

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Configuration

### 1. Create `.env` file
```bash
cp .env.example .env

# Edit .env with your credentials:
SSH_USERNAME=admin
SSH_PASSWORD=your_password
SSH_ENABLE_SECRET=enable_password  # optional
SSH_TIMEOUT=30
OUTPUT_DIR=./output  # optional
```

### 2. Create device list
```bash
# Create wlc.txt with your WLC hostnames/IPs (one per line)
cat > wlc.txt << EOF
wlc01.example.com
wlc02.example.com
192.168.1.100
EOF
```

## Usage

### Basic Usage
```bash
source .venv/bin/activate
python dudeatron_wlc.py
```

### With Custom Output Directory
```bash
python dudeatron_wlc.py -o ./my_data
python dudeatron_wlc.py --output-dir /tmp/wlc_export
```

### Using Environment Variable
```bash
# Set in .env:
OUTPUT_DIR=/path/to/output

# Then run normally:
python dudeatron_wlc.py
```

## Output

### CSV File Format
- **Name**: `YYYYMMDD-HHMMSS-hostname.csv`
- **Location**: Specified by `-o`, `OUTPUT_DIR`, or current directory
- **Contents**: Merged data from 3 commands (show ap summary, show ap cdp neighbors, show ap meraki monitoring summary)

### Session Log Format
- **Name**: `YYYYMMDD-HHMMSS-hostname.log`
- **Location**: `logs/` directory
- **Contents**: Complete SSH session transcript for debugging

## Available Data Fields

### From `show ap summary`
- AP name, model, radio MAC, ethernet MAC, slots
- Location, country, regulatory domain, IP address, state

### From `show ap cdp neighbors`  
- Neighbor switch name, IP address, port

### From `show ap meraki monitoring summary`
- Serial number, cloud ID, Meraki status

## Troubleshooting

### "ModuleNotFoundError: No module named 'dotenv'"
```bash
# Activate virtual environment
source .venv/bin/activate
```

### "Connection timeout"
```bash
# Increase timeout in .env
SSH_TIMEOUT=60
```

### "Authentication failed"
- Verify SSH_USERNAME and SSH_PASSWORD in `.env`
- Check credentials have WLC access
- No trailing whitespace in `.env` values

### "Parser errors in logs"
- Check session log: `logs/TIMESTAMP-hostname.log`
- Look for actual command output format
- Genie parsers expect Catalyst 9800 standard format

## Examples

### Process single WLC with CSV output
```bash
# wlc.txt contains only one entry
echo "wlc01.example.com" > wlc.txt
python dudeatron_wlc.py -o ./output/wlc01
```

### Process multiple WLCs in batch
```bash
# wlc.txt contains all WLCs
cat > wlc.txt << EOF
wlc01.example.com
wlc02.example.com
wlc03.example.com
EOF

python dudeatron_wlc.py -o ./output
# Results in: output/20260106-xxxxxx-wlc01.example.com.csv, etc.
```

### Using environment variable for consistent output
```bash
# .env file
OUTPUT_DIR=/data/wlc_exports

# Create directory if needed
mkdir -p /data/wlc_exports

# Run multiple times - all outputs go to same place
python dudeatron_wlc.py
```

## Performance Notes

- **Small WLC** (< 100 APs): ~30 seconds
- **Medium WLC** (100-500 APs): ~60 seconds  
- **Large WLC** (1000+ APs): 2-5 minutes
- **Extra Large WLC** (2000+ APs): 5-10 minutes

*Times depend on network latency and WLC processing speed*

## What Gets Merged

The script automatically merges data from all three commands **by AP name**:

```
show ap summary       show ap cdp neighbors     show ap meraki monitoring summary
    ↓                        ↓                              ↓
  AP data ───────────────────────────────────────────> Single CSV row per AP
  (summary)          (network info)                  (cloud monitoring)
```

## CSV Column Order

The CSV contains all available fields, organized roughly as:

1. AP Identity: ap_name, ap_model, mac_address, radio_mac, slots
2. Location: location, country, regulatory_domain
3. Network: ip_address, state
4. CDP Neighbors: neighbor_name, neighbor_ip, neighbor_port
5. Meraki: serial_number, cloud_id, meraki_status

## Next Steps

- See [WLC_README.md](docs/WLC_README.md) for detailed documentation
- Check [DEVELOPMENT.md](docs/DEVELOPMENT.md) for development setup
- View [SESSION_SUMMARY.md](AGENT-Notes/SESSION_SUMMARY.md) for recent updates
- Refer to [AGENTS.md](AGENTS.md) for project architecture

---

**Status**: Production Ready  
**Last Updated**: January 6, 2026  
**Tested Against**: Catalyst 9800 with IOS-XE
