# AP Rename Matching Tool — Design Spec

## Purpose

After upgrading APs on a WLC, new APs join with default names. This tool matches
new APs to their historical records using CDP neighbor/port as the match key,
then generates IOS-XE CLI commands for renaming and verification.

## Architecture

Two new files following the existing `dudeatron_wlc.py` / `wlc_module.py` pattern:

- **`ap_rename.py`** — reusable module with matching logic, CSV updating, and
  command generation
- **`dudeatron_rename.py`** — CLI entry point that orchestrates the pipeline

## Workflow

```
Step 1: Run existing dudeatron_wlc.py → produces current-state CSV in output/
Step 2: Run dudeatron_rename.py with historical CSV + current CSV
        → produces updated CSV + CLI commands file
```

## Data Flow

```
Historical CSV (user spreadsheet, in output/)
         |
   dudeatron_rename.py
         |
   Reads current WLC CSV (from dudeatron_wlc.py output)
         |
   ap_rename.py: match by (CDP Neighbor, Port)
         |
   +-------------+----------------------+
   | Updated CSV  | CLI Commands (.txt)  |
   | (filled in   | - Verification cmds  |
   |  MAC, serial,|   for already-renamed|
   |  meraki SN)  | - Rename cmds for    |
   +-------------+   newly matched APs   |
                  +----------------------+
```

## Module: ap_rename.py

### Functions

#### `read_historical_csv(file_path: str) -> List[Dict[str, str]]`

Read the historical CSV mapping file. Returns list of row dicts preserving all
original columns. Handles both `utf-8` and `utf-8-sig` encoding (the BOM
variant that Excel produces).

#### `read_current_wlc_csv(file_path: str) -> List[Dict[str, str]]`

Read the current WLC CSV produced by `dudeatron_wlc.py`. Returns list of row
dicts. Uses `utf-8` encoding (matching `wlc_module.py`'s write encoding).

#### `build_cdp_lookup(rows: List[Dict[str, str]], neighbor_key: str, port_key: str) -> Dict[Tuple[str, str], Dict[str, str]]`

Build a lookup dictionary keyed by `(cdp_neighbor, port)` from a list of row
dicts. Parameters specify which column names to use as keys (since historical
and current CSVs may have different column names).

**Key normalization**: CDP neighbor names are compared case-insensitively and
with any trailing domain suffix stripped (e.g., `Switch1.example.com` →
`switch1`). Port names are compared case-insensitively with whitespace trimmed.

If duplicate keys are encountered, warn to stderr and keep the first occurrence.

#### `match_aps(historical: List[Dict[str, str]], current_lookup: Dict[Tuple[str, str], Dict[str, str]]) -> Tuple[List[Dict], List[Dict], List[Dict]]`

Match historical records against current WLC data by CDP neighbor + port.

Returns three lists:
- **already_renamed** — historical AP name matches current AP name
  (case-insensitive comparison)
- **needs_rename** — current AP has a different/default name
- **unmatched** — no current AP found on that port; dicts contain only
  historical fields (no `current_ap_name` key)

Each dict in the `already_renamed` and `needs_rename` lists contains:
- All fields from the historical row (original keys preserved)
- `current_ap_name` — the AP's current name on the WLC
- `current_mac_address` — ethernet MAC from `show ap summary`
- `current_serial_number` — Cisco serial from `show ap meraki monitoring summary`
- `current_meraki_serial` — Cloud ID from `show ap meraki monitoring summary`

Each dict in the `unmatched` list contains only the original historical fields.

#### `update_historical_csv(historical_rows: List[Dict[str, str]], matched: List[Dict], output_path: str) -> str`

Write an updated version of the historical CSV. The `matched` parameter is the
concatenation of `already_renamed + needs_rename` from `match_aps` — i.e., all
entries that were successfully matched to current WLC data.

For each matched entry, updates these historical columns if the historical value
is empty:
- `MAC Address` ← `current_mac_address`
- `Serial Number` ← `current_serial_number`
- `Meraki Serial Number` ← `current_meraki_serial`

Preserves all original columns and column order. Uses `utf-8` encoding.

Returns path to the updated CSV file.

#### `generate_cli_commands(already_renamed: List[Dict], needs_rename: List[Dict], unmatched: List[Dict]) -> str`

Generate and return a string containing IOS-XE WLC CLI commands organized in
sections. The caller (`dudeatron_rename.py`) writes this string to the output
file.

Sections:

1. **Verification commands** for already-renamed APs:
   `show ap name <ap-name> config general`

2. **Rename commands** for newly matched APs:
   `ap name <current-default-name> name <desired-name>`

3. **Post-rename verification** commands:
   `show ap summary | include <desired-name>`

4. **Unmatched APs** as IOS comments noting expected CDP neighbor/port:
   `! <ap-name> expected on <neighbor> <port> — not found`

## Entry Point: dudeatron_rename.py

### CLI Arguments

```
python dudeatron_rename.py --historical <path> --current <path> [-o <output-dir>]
```

- `--historical` — path to the user's historical CSV file
- `--current` — path to the CSV produced by `dudeatron_wlc.py`
- `-o` / `--output-dir` — directory for output files (default: `output/`)

### WLC Hostname in Output Filenames

The WLC hostname is extracted from the `--current` CSV filename, which follows
the `YYYYMMDD-HHMMSS-<hostname>.csv` naming convention established by
`wlc_module.py`. The hostname is the portion after the second `-` and before
`.csv`.

### Output Files

All output goes to gitignored `output/` directory:

- `YYYYMMDD-HHMMSS-<wlc>-rename-commands.txt` — pasteable CLI commands
- `YYYYMMDD-HHMMSS-<wlc>-updated-aps.csv` — updated historical CSV with new data

### Column Mapping

The historical CSV and current WLC CSV use different column names. The mapping:

| Historical CSV Column  | Current WLC CSV Column | Source Command                        |
|------------------------|------------------------|---------------------------------------|
| `CDP Neighbor`         | `neighbor_name`        | `show ap cdp neighbors`               |
| `Port of CDP Neighbor` | `neighbor_port`        | `show ap cdp neighbors`               |
| `AP Name`              | `ap_name`              | `show ap summary`                     |
| `MAC Address`          | `mac_address`          | `show ap summary` (ethernet MAC)      |
| `Serial Number`        | `serial_number`        | `show ap meraki monitoring summary`   |
| `Meraki Serial Number` | `cloud_id`             | `show ap meraki monitoring summary`   |

**Note on MAC address source**: The `mac_address` field in the current WLC CSV
comes from `parse_show_ap_summary` (the `ethernet_mac` field from
`show ap summary`). The meraki parser also extracts a `mac_address`, but
`combine_wlc_data_to_csv` does not forward it. The AP summary ethernet MAC is
the authoritative source.

### Match Classification

For each historical row:

1. Look up `(CDP Neighbor, Port of CDP Neighbor)` in the current data lookup
   (using normalized keys — see `build_cdp_lookup`)
2. If no match found → **unmatched** (AP not currently on the WLC on that port)
3. If match found and `current_ap_name` matches `historical AP Name`
   (case-insensitive) → **already_renamed**
4. If match found and names differ → **needs_rename**

## Error Handling

- Missing or unreadable CSV files: clear error message with expected format
- No matches found: warn but still produce output files
- Duplicate CDP neighbor + port in either dataset: warn to stderr and use first
  occurrence (duplicates in practice would indicate a data issue worth
  investigating)

## Testing

- Can be tested with anonymized sample CSVs (using `192.168.X.Y` IPs,
  `XX:XX:XX:XX:XX:XX` MACs, `ABC0000` serials per project conventions)
- Matching logic is pure data transformation — no network access needed for
  unit tests

## Security Considerations

- All input/output files should remain in gitignored directories (`output/`)
- No real device data should appear in committed code, tests, or docs
- The tool generates CLI commands for the user to paste — it never connects to
  the WLC itself
