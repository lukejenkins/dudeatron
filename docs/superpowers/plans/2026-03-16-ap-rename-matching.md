# AP Rename Matching Tool — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a tool that matches new WLC APs to historical records by CDP neighbor/port, generates IOS-XE rename commands, and updates the historical CSV with current device data.

**Architecture:** Two new files: `ap_rename.py` (reusable module with matching logic, CSV I/O, CLI command generation) and `dudeatron_rename.py` (CLI entry point with argparse). Follows the existing `wlc_module.py` / `dudeatron_wlc.py` pattern. Pure data transformation — no network access.

**Tech Stack:** Python 3.x, csv (stdlib), argparse (stdlib), typing (stdlib). No new dependencies.

**Spec:** `docs/superpowers/specs/2026-03-16-ap-rename-matching-design.md`

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `ap_rename.py` | Create | Reusable module: CSV reading, CDP lookup building, AP matching, CSV updating, CLI command generation, MAC format conversion |
| `dudeatron_rename.py` | Create | CLI entry point: argparse, orchestration, file I/O, console output |
| `tests/test_ap_rename.py` | Create | Unit tests for all `ap_rename.py` functions using anonymized data |

---

## Chunk 1: Core Module — ap_rename.py

### Task 1: MAC Address Format Conversion

The WLC CSV uses Cisco dotted format (`687d.b45c.1f10`) while the historical
CSV uses colon-separated format (`cc:6e:2a:3f:a7:90`). We need a converter.

**Files:**
- Create: `tests/test_ap_rename.py`
- Create: `ap_rename.py`

- [ ] **Step 1: Write the failing test**

In `tests/test_ap_rename.py`:

```python
"""Tests for AP rename matching module."""

from ap_rename import convert_mac_to_colon_format


def test_convert_cisco_dotted_mac():
    """Convert Cisco dotted MAC to colon-separated lowercase."""
    assert convert_mac_to_colon_format("687d.b45c.1f10") == "68:7d:b4:5c:1f:10"


def test_convert_already_colon_mac():
    """Colon-separated MACs pass through unchanged."""
    assert convert_mac_to_colon_format("aa:bb:cc:dd:ee:ff") == "aa:bb:cc:dd:ee:ff"


def test_convert_uppercase_colon_mac():
    """Uppercase colon-separated MACs are lowercased."""
    assert convert_mac_to_colon_format("AA:BB:CC:DD:EE:FF") == "aa:bb:cc:dd:ee:ff"


def test_convert_empty_mac():
    """Empty string returns empty string."""
    assert convert_mac_to_colon_format("") == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_ap_rename.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Write minimal implementation**

In `ap_rename.py`:

```python
"""AP rename matching module for Dudeatron.

This module provides functionality to match new WLC APs to historical records
using CDP neighbor/port data, generate IOS-XE rename commands, and update
historical CSV files with current device data.
"""

import re


def convert_mac_to_colon_format(mac: str) -> str:
    """Convert a MAC address to colon-separated lowercase format.

    Handles Cisco dotted format (687d.b45c.1f10) and colon-separated format.

    Args:
        mac: MAC address string in any common format.

    Returns:
        Colon-separated lowercase MAC (cc:6e:2a:3f:a7:90), or empty string
        if input is empty.
    """
    if not mac or not mac.strip():
        return ""

    # Remove all separators (dots, colons, dashes) to get raw hex
    raw_hex = re.sub(r"[.:\-]", "", mac.strip().lower())

    if len(raw_hex) != 12:
        return mac.strip().lower()

    # Insert colons every 2 characters
    return ":".join(raw_hex[i:i + 2] for i in range(0, 12, 2))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_ap_rename.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add tests/test_ap_rename.py ap_rename.py
git commit -m "feat: add MAC address format conversion for AP rename tool"
```

---

### Task 2: CDP Neighbor Name Normalization

CDP neighbor names from the WLC include FQDN suffixes (e.g.,
`switch-1.mgmt.example.edu`) while the historical CSV uses short names
(`switch-1`). We need normalization for matching.

**Files:**
- Modify: `tests/test_ap_rename.py`
- Modify: `ap_rename.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_ap_rename.py`:

```python
from ap_rename import normalize_cdp_neighbor


def test_normalize_fqdn_neighbor():
    """Strip domain suffix from FQDN."""
    assert normalize_cdp_neighbor("switch-1.mgmt.example.edu") == "switch-1"


def test_normalize_short_neighbor():
    """Short name passes through (lowercased)."""
    assert normalize_cdp_neighbor("SWITCH-1") == "switch-1"


def test_normalize_neighbor_whitespace():
    """Whitespace is stripped."""
    assert normalize_cdp_neighbor("  switch-1  ") == "switch-1"


def test_normalize_empty_neighbor():
    """Empty string returns empty string."""
    assert normalize_cdp_neighbor("") == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_ap_rename.py::test_normalize_fqdn_neighbor -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Write minimal implementation**

Append to `ap_rename.py`:

```python
def normalize_cdp_neighbor(name: str) -> str:
    """Normalize a CDP neighbor name for comparison.

    Strips domain suffixes and lowercases for consistent matching.
    E.g., 'switch-1.mgmt.example.edu' -> 'switch-1'

    Args:
        name: CDP neighbor name, possibly with FQDN suffix.

    Returns:
        Normalized lowercase short name, or empty string if input is empty.
    """
    if not name or not name.strip():
        return ""

    name = name.strip().lower()

    # Strip domain suffix: take everything before the first dot
    # But only if the dot-separated part looks like a domain
    # (not an IP address, which is all digits and dots)
    if "." in name and not re.match(r"^[\d.]+$", name):
        name = name.split(".")[0]

    return name
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_ap_rename.py -v`
Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add tests/test_ap_rename.py ap_rename.py
git commit -m "feat: add CDP neighbor name normalization"
```

---

### Task 3: CSV Reading Functions

**Files:**
- Modify: `tests/test_ap_rename.py`
- Modify: `ap_rename.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_ap_rename.py`:

```python
import os
import tempfile
from ap_rename import read_historical_csv, read_current_wlc_csv


def test_read_historical_csv():
    """Read a historical CSV and return list of dicts."""
    content = (
        "AP Name,MAC Address,Serial Number,Meraki Serial Number,"
        "CDP Neighbor,Port of CDP Neighbor\n"
        "ap-building-A,XX:XX:XX:XX:XX:XX,ABC0000,MERA-XXXX-0000,"
        "switch-1,TenGigabitEthernet1/0/47\n"
        "ap-building-B,,,,switch-1,TenGigabitEthernet1/0/48\n"
    )
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, encoding="utf-8"
    ) as f:
        f.write(content)
        f.flush()
        rows = read_historical_csv(f.name)

    os.unlink(f.name)

    assert len(rows) == 2
    assert rows[0]["AP Name"] == "ap-building-A"
    assert rows[0]["MAC Address"] == "XX:XX:XX:XX:XX:XX"
    assert rows[1]["AP Name"] == "ap-building-B"
    assert rows[1]["MAC Address"] == ""


def test_read_historical_csv_utf8_bom():
    """Handle Excel-produced UTF-8 BOM files."""
    content = (
        "\ufeffAP Name,CDP Neighbor,Port of CDP Neighbor\n"
        "ap-building-A,switch-1,TenGigabitEthernet1/0/47\n"
    )
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, encoding="utf-8-sig"
    ) as f:
        f.write(content)
        f.flush()
        rows = read_historical_csv(f.name)

    os.unlink(f.name)

    assert len(rows) == 1
    assert "AP Name" in rows[0]


def test_read_historical_csv_file_not_found():
    """Raise FileNotFoundError for missing file."""
    import pytest
    with pytest.raises(FileNotFoundError):
        read_historical_csv("/nonexistent/file.csv")


def test_read_current_wlc_csv():
    """Read a WLC CSV produced by dudeatron_wlc.py."""
    content = (
        "ap_name,mac_address,neighbor_name,neighbor_port,"
        "serial_number,cloud_id\n"
        "AP00XX.XXXX.0000,xxxx.xxxx.0000,switch-1.example.com,"
        "TenGigabitEthernet1/0/47,ABC0000,MERA-XXXX-0000\n"
    )
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, encoding="utf-8"
    ) as f:
        f.write(content)
        f.flush()
        rows = read_current_wlc_csv(f.name)

    os.unlink(f.name)

    assert len(rows) == 1
    assert rows[0]["ap_name"] == "AP00XX.XXXX.0000"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_ap_rename.py::test_read_historical_csv -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Write minimal implementation**

Add imports and functions to `ap_rename.py`:

```python
import csv
from pathlib import Path
from typing import Dict, List, Tuple


def read_historical_csv(file_path: str) -> List[Dict[str, str]]:
    """Read the historical CSV mapping file.

    Handles both utf-8 and utf-8-sig encoding (Excel BOM).

    Args:
        file_path: Path to the historical CSV file.

    Returns:
        List of row dictionaries preserving all original columns.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Historical CSV not found: {file_path}")

    # Try utf-8-sig first (handles BOM), falls back gracefully for plain utf-8
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def read_current_wlc_csv(file_path: str) -> List[Dict[str, str]]:
    """Read the current WLC CSV produced by dudeatron_wlc.py.

    Args:
        file_path: Path to the WLC CSV file.

    Returns:
        List of row dictionaries.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"WLC CSV not found: {file_path}")

    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_ap_rename.py -v`
Expected: 12 passed

- [ ] **Step 5: Commit**

```bash
git add tests/test_ap_rename.py ap_rename.py
git commit -m "feat: add CSV reading functions for historical and WLC data"
```

---

### Task 4: CDP Lookup Builder

**Files:**
- Modify: `tests/test_ap_rename.py`
- Modify: `ap_rename.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_ap_rename.py`:

```python
from ap_rename import build_cdp_lookup


def test_build_cdp_lookup_basic():
    """Build lookup keyed by normalized (neighbor, port)."""
    rows = [
        {
            "ap_name": "AP00XX.XXXX.0000",
            "neighbor_name": "switch-1.example.com",
            "neighbor_port": "TenGigabitEthernet1/0/47",
        },
        {
            "ap_name": "AP00XX.XXXX.0001",
            "neighbor_name": "switch-1.example.com",
            "neighbor_port": "TenGigabitEthernet1/0/48",
        },
    ]
    lookup = build_cdp_lookup(rows, "neighbor_name", "neighbor_port")

    assert ("switch-1", "tengigabitethernet1/0/47") in lookup
    assert lookup[("switch-1", "tengigabitethernet1/0/47")]["ap_name"] == "AP00XX.XXXX.0000"


def test_build_cdp_lookup_duplicate_warns(capsys):
    """Duplicate keys warn to stderr and keep first."""
    rows = [
        {
            "ap_name": "first-ap",
            "neighbor_name": "switch-1",
            "neighbor_port": "Te1/0/47",
        },
        {
            "ap_name": "second-ap",
            "neighbor_name": "switch-1",
            "neighbor_port": "Te1/0/47",
        },
    ]
    lookup = build_cdp_lookup(rows, "neighbor_name", "neighbor_port")

    assert lookup[("switch-1", "te1/0/47")]["ap_name"] == "first-ap"
    captured = capsys.readouterr()
    assert "WARNING" in captured.err or "WARNING" in captured.out
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_ap_rename.py::test_build_cdp_lookup_basic -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Write minimal implementation**

Add to `ap_rename.py`:

```python
import sys


def build_cdp_lookup(
    rows: List[Dict[str, str]],
    neighbor_key: str,
    port_key: str
) -> Dict[Tuple[str, str], Dict[str, str]]:
    """Build a lookup dictionary keyed by normalized (cdp_neighbor, port).

    Args:
        rows: List of row dicts from a CSV file.
        neighbor_key: Column name for the CDP neighbor field.
        port_key: Column name for the port field.

    Returns:
        Dictionary mapping (normalized_neighbor, normalized_port) to row dict.
        If duplicates exist, warns and keeps the first occurrence.
    """
    lookup: Dict[Tuple[str, str], Dict[str, str]] = {}

    for row in rows:
        neighbor = normalize_cdp_neighbor(row.get(neighbor_key, ""))
        port = row.get(port_key, "").strip().lower()

        if not neighbor or not port:
            continue

        key = (neighbor, port)

        if key in lookup:
            print(
                f"WARNING: Duplicate CDP key {key}, keeping first "
                f"('{lookup[key].get('ap_name', 'unknown')}'), "
                f"skipping '{row.get('ap_name', row.get('AP Name', 'unknown'))}'",
                file=sys.stderr,
            )
            continue

        lookup[key] = row

    return lookup
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_ap_rename.py -v`
Expected: 14 passed

- [ ] **Step 5: Commit**

```bash
git add tests/test_ap_rename.py ap_rename.py
git commit -m "feat: add CDP lookup builder with normalization"
```

---

### Task 5: AP Matching Logic

**Files:**
- Modify: `tests/test_ap_rename.py`
- Modify: `ap_rename.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_ap_rename.py`:

```python
from ap_rename import match_aps


def test_match_aps_already_renamed():
    """AP with matching name classified as already_renamed."""
    historical = [
        {
            "AP Name": "ap-building-A",
            "CDP Neighbor": "switch-1",
            "Port of CDP Neighbor": "TenGigabitEthernet1/0/47",
        }
    ]
    current_lookup = {
        ("switch-1", "tengigabitethernet1/0/47"): {
            "ap_name": "ap-building-A",
            "mac_address": "xxxx.xxxx.0000",
            "serial_number": "ABC0000",
            "cloud_id": "MERA-XXXX-0000",
        }
    }
    already, needs, unmatched = match_aps(historical, current_lookup)

    assert len(already) == 1
    assert len(needs) == 0
    assert len(unmatched) == 0
    assert already[0]["current_ap_name"] == "ap-building-A"
    assert already[0]["current_mac_address"] == "xx:xx:xx:xx:00:00"


def test_match_aps_needs_rename():
    """AP with different name classified as needs_rename."""
    historical = [
        {
            "AP Name": "ap-building-B",
            "CDP Neighbor": "switch-1",
            "Port of CDP Neighbor": "TenGigabitEthernet1/0/48",
        }
    ]
    current_lookup = {
        ("switch-1", "tengigabitethernet1/0/48"): {
            "ap_name": "AP00XX.XXXX.0001",
            "mac_address": "xxxx.xxxx.0001",
            "serial_number": "ABC0001",
            "cloud_id": "MERA-XXXX-0001",
        }
    }
    already, needs, unmatched = match_aps(historical, current_lookup)

    assert len(already) == 0
    assert len(needs) == 1
    assert len(unmatched) == 0
    assert needs[0]["AP Name"] == "ap-building-B"
    assert needs[0]["current_ap_name"] == "AP00XX.XXXX.0001"


def test_match_aps_unmatched():
    """AP with no current match classified as unmatched."""
    historical = [
        {
            "AP Name": "ap-building-C",
            "CDP Neighbor": "switch-2",
            "Port of CDP Neighbor": "TenGigabitEthernet2/0/47",
        }
    ]
    current_lookup = {}
    already, needs, unmatched = match_aps(historical, current_lookup)

    assert len(already) == 0
    assert len(needs) == 0
    assert len(unmatched) == 1
    assert "current_ap_name" not in unmatched[0]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_ap_rename.py::test_match_aps_already_renamed -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Write minimal implementation**

Add to `ap_rename.py`:

```python
def match_aps(
    historical: List[Dict[str, str]],
    current_lookup: Dict[Tuple[str, str], Dict[str, str]]
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Match historical AP records against current WLC data by CDP neighbor/port.

    Args:
        historical: List of historical CSV row dicts.
        current_lookup: Lookup dict from build_cdp_lookup keyed by
            normalized (neighbor, port).

    Returns:
        Tuple of (already_renamed, needs_rename, unmatched) lists.
        Matched entries include current_ap_name, current_mac_address,
        current_serial_number, and current_meraki_serial fields.
        Unmatched entries contain only historical fields.
    """
    already_renamed: List[Dict] = []
    needs_rename: List[Dict] = []
    unmatched: List[Dict] = []

    for row in historical:
        neighbor = normalize_cdp_neighbor(row.get("CDP Neighbor", ""))
        port = row.get("Port of CDP Neighbor", "").strip().lower()

        if not neighbor or not port:
            unmatched.append(dict(row))
            continue

        key = (neighbor, port)
        current = current_lookup.get(key)

        if current is None:
            unmatched.append(dict(row))
            continue

        # Build the matched entry with all historical fields plus current data
        entry = dict(row)
        entry["current_ap_name"] = current.get("ap_name", "")
        entry["current_mac_address"] = convert_mac_to_colon_format(
            current.get("mac_address", "")
        )
        entry["current_serial_number"] = current.get("serial_number", "")
        entry["current_meraki_serial"] = current.get("cloud_id", "")

        # Compare AP names case-insensitively
        historical_name = row.get("AP Name", "").strip().lower()
        current_name = current.get("ap_name", "").strip().lower()

        if historical_name == current_name:
            already_renamed.append(entry)
        else:
            needs_rename.append(entry)

    return already_renamed, needs_rename, unmatched
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_ap_rename.py -v`
Expected: 17 passed

- [ ] **Step 5: Commit**

```bash
git add tests/test_ap_rename.py ap_rename.py
git commit -m "feat: add AP matching logic by CDP neighbor/port"
```

---

## Chunk 2: Output Generation and CLI Entry Point

### Task 6: CLI Command Generation

**Files:**
- Modify: `tests/test_ap_rename.py`
- Modify: `ap_rename.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_ap_rename.py`:

```python
from ap_rename import generate_cli_commands


def test_generate_cli_commands_rename():
    """Generate rename commands for needs_rename APs."""
    needs_rename = [
        {
            "AP Name": "ap-building-A",
            "current_ap_name": "AP00XX.XXXX.0000",
        }
    ]
    output = generate_cli_commands([], needs_rename, [])

    assert "ap name AP00XX.XXXX.0000 name ap-building-A" in output


def test_generate_cli_commands_verify():
    """Generate verification commands for already-renamed APs."""
    already_renamed = [
        {
            "AP Name": "ap-building-B",
            "current_ap_name": "ap-building-B",
        }
    ]
    output = generate_cli_commands(already_renamed, [], [])

    assert "show ap name ap-building-B config general" in output


def test_generate_cli_commands_unmatched():
    """Generate comments for unmatched APs."""
    unmatched = [
        {
            "AP Name": "ap-building-C",
            "CDP Neighbor": "switch-2",
            "Port of CDP Neighbor": "TenGigabitEthernet2/0/47",
        }
    ]
    output = generate_cli_commands([], [], unmatched)

    assert "ap-building-C" in output
    assert "switch-2" in output
    assert "TenGigabitEthernet2/0/47" in output


def test_generate_cli_commands_post_rename_verify():
    """Generate post-rename verification commands."""
    needs_rename = [
        {
            "AP Name": "ap-building-A",
            "current_ap_name": "AP00XX.XXXX.0000",
        }
    ]
    output = generate_cli_commands([], needs_rename, [])

    assert "show ap summary | include ap-building-A" in output
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_ap_rename.py::test_generate_cli_commands_rename -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Write minimal implementation**

Add to `ap_rename.py`:

```python
def generate_cli_commands(
    already_renamed: List[Dict],
    needs_rename: List[Dict],
    unmatched: List[Dict]
) -> str:
    """Generate IOS-XE WLC CLI commands for verification and renaming.

    Returns a string containing pasteable CLI commands organized in sections.
    The caller writes this to the output file.

    Args:
        already_renamed: APs whose names already match (verify only).
        needs_rename: APs that need renaming (current name differs).
        unmatched: APs with no current match (informational comments).

    Returns:
        Multi-line string of CLI commands with section headers as IOS comments.
    """
    lines: List[str] = []

    # Section 1: Verification of already-renamed APs
    if already_renamed:
        lines.append("! ====== VERIFICATION COMMANDS (already renamed) ======")
        for ap in already_renamed:
            ap_name = ap.get("AP Name", ap.get("current_ap_name", ""))
            lines.append(f"show ap name {ap_name} config general")
        lines.append("")

    # Section 2: Rename commands
    if needs_rename:
        lines.append("! ====== RENAME COMMANDS ======")
        for ap in needs_rename:
            current_name = ap["current_ap_name"]
            desired_name = ap["AP Name"]
            lines.append(f"ap name {current_name} name {desired_name}")
        lines.append("")

    # Section 3: Post-rename verification
    if needs_rename:
        lines.append("! ====== VERIFICATION AFTER RENAME ======")
        for ap in needs_rename:
            desired_name = ap["AP Name"]
            lines.append(f"show ap summary | include {desired_name}")
        lines.append("")

    # Section 4: Unmatched APs
    if unmatched:
        lines.append(
            "! ====== UNMATCHED APs "
            "(no current AP found on expected port) ======"
        )
        for ap in unmatched:
            ap_name = ap.get("AP Name", "unknown")
            neighbor = ap.get("CDP Neighbor", "unknown")
            port = ap.get("Port of CDP Neighbor", "unknown")
            lines.append(
                f"! {ap_name} expected on {neighbor} {port} — not found"
            )
        lines.append("")

    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_ap_rename.py -v`
Expected: 21 passed

- [ ] **Step 5: Commit**

```bash
git add tests/test_ap_rename.py ap_rename.py
git commit -m "feat: add CLI command generation for AP renaming"
```

---

### Task 7: CSV Update Function

**Files:**
- Modify: `tests/test_ap_rename.py`
- Modify: `ap_rename.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_ap_rename.py`:

```python
from ap_rename import update_historical_csv


def test_update_csv_fills_empty_fields():
    """Fill in MAC/serial/meraki for matched APs with empty fields."""
    historical_rows = [
        {
            "AP Name": "ap-building-A",
            "MAC Address": "",
            "Serial Number": "",
            "Meraki Serial Number": "",
            "CDP Neighbor": "switch-1",
            "Port of CDP Neighbor": "TenGigabitEthernet1/0/47",
        },
    ]
    matched = [
        {
            "AP Name": "ap-building-A",
            "MAC Address": "",
            "Serial Number": "",
            "Meraki Serial Number": "",
            "CDP Neighbor": "switch-1",
            "Port of CDP Neighbor": "TenGigabitEthernet1/0/47",
            "current_ap_name": "AP00XX.XXXX.0000",
            "current_mac_address": "xx:xx:xx:xx:00:00",
            "current_serial_number": "ABC0000",
            "current_meraki_serial": "MERA-XXXX-0000",
        },
    ]

    with tempfile.NamedTemporaryFile(
        suffix=".csv", delete=False, mode="w"
    ) as f:
        output_path = f.name

    result_path = update_historical_csv(
        historical_rows, matched, output_path
    )

    updated = read_historical_csv(result_path)
    os.unlink(result_path)

    assert updated[0]["MAC Address"] == "xx:xx:xx:xx:00:00"
    assert updated[0]["Serial Number"] == "ABC0000"
    assert updated[0]["Meraki Serial Number"] == "MERA-XXXX-0000"


def test_update_csv_preserves_existing_fields():
    """Do not overwrite existing MAC/serial values."""
    historical_rows = [
        {
            "AP Name": "ap-building-A",
            "MAC Address": "aa:bb:cc:dd:ee:ff",
            "Serial Number": "EXISTING1",
            "Meraki Serial Number": "EXIST-MERA-0000",
            "CDP Neighbor": "switch-1",
            "Port of CDP Neighbor": "TenGigabitEthernet1/0/47",
        },
    ]
    matched = [
        {
            "AP Name": "ap-building-A",
            "MAC Address": "aa:bb:cc:dd:ee:ff",
            "Serial Number": "EXISTING1",
            "Meraki Serial Number": "EXIST-MERA-0000",
            "CDP Neighbor": "switch-1",
            "Port of CDP Neighbor": "TenGigabitEthernet1/0/47",
            "current_ap_name": "ap-building-A",
            "current_mac_address": "xx:xx:xx:xx:99:99",
            "current_serial_number": "NEW0000",
            "current_meraki_serial": "NEW-MERA-0000",
        },
    ]

    with tempfile.NamedTemporaryFile(
        suffix=".csv", delete=False, mode="w"
    ) as f:
        output_path = f.name

    result_path = update_historical_csv(
        historical_rows, matched, output_path
    )

    updated = read_historical_csv(result_path)
    os.unlink(result_path)

    # Existing values should NOT be overwritten
    assert updated[0]["MAC Address"] == "aa:bb:cc:dd:ee:ff"
    assert updated[0]["Serial Number"] == "EXISTING1"
    assert updated[0]["Meraki Serial Number"] == "EXIST-MERA-0000"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_ap_rename.py::test_update_csv_fills_empty_fields -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Write minimal implementation**

Add to `ap_rename.py`:

```python
def update_historical_csv(
    historical_rows: List[Dict[str, str]],
    matched: List[Dict],
    output_path: str
) -> str:
    """Write an updated historical CSV with data filled in from matched APs.

    Updates MAC Address, Serial Number, and Meraki Serial Number for matched
    entries only when the historical value is empty. Preserves all original
    columns and column order.

    Args:
        historical_rows: Original historical CSV rows (list of dicts).
        matched: Concatenation of already_renamed + needs_rename from match_aps.
        output_path: Path to write the updated CSV file.

    Returns:
        Path to the written CSV file.
    """
    # Build a lookup from matched entries keyed by AP Name
    match_lookup: Dict[str, Dict] = {}
    for entry in matched:
        ap_name = entry.get("AP Name", "")
        if ap_name:
            match_lookup[ap_name] = entry

    # Get column order from the first row
    if not historical_rows:
        return output_path

    fieldnames = list(historical_rows[0].keys())

    # Update rows in place
    updated_rows: List[Dict[str, str]] = []
    for row in historical_rows:
        updated_row = dict(row)
        ap_name = row.get("AP Name", "")
        match = match_lookup.get(ap_name)

        if match:
            # Only fill in empty fields
            if not updated_row.get("MAC Address", "").strip():
                updated_row["MAC Address"] = match.get(
                    "current_mac_address", ""
                )
            if not updated_row.get("Serial Number", "").strip():
                updated_row["Serial Number"] = match.get(
                    "current_serial_number", ""
                )
            if not updated_row.get("Meraki Serial Number", "").strip():
                updated_row["Meraki Serial Number"] = match.get(
                    "current_meraki_serial", ""
                )

        updated_rows.append(updated_row)

    # Write the updated CSV
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)

    return output_path
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_ap_rename.py -v`
Expected: 23 passed

- [ ] **Step 5: Commit**

```bash
git add tests/test_ap_rename.py ap_rename.py
git commit -m "feat: add historical CSV update function"
```

---

### Task 8: WLC Hostname Extraction Helper

**Files:**
- Modify: `tests/test_ap_rename.py`
- Modify: `ap_rename.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_ap_rename.py`:

```python
from ap_rename import extract_wlc_hostname


def test_extract_wlc_hostname_from_csv_path():
    """Extract hostname from WLC CSV filename."""
    assert extract_wlc_hostname(
        "output/20260106-170800-ogden-wlc4.csv"
    ) == "ogden-wlc4"


def test_extract_wlc_hostname_nested_path():
    """Handle nested directory paths."""
    assert extract_wlc_hostname(
        "/home/user/output/20260316-143022-device-1.csv"
    ) == "device-1"


def test_extract_wlc_hostname_fallback():
    """Fall back to 'unknown' for unexpected formats."""
    assert extract_wlc_hostname("random-file.csv") == "unknown"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_ap_rename.py::test_extract_wlc_hostname_from_csv_path -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Write minimal implementation**

Add to `ap_rename.py`:

```python
def extract_wlc_hostname(csv_path: str) -> str:
    """Extract the WLC hostname from a dudeatron_wlc.py CSV filename.

    The CSV filename format is: YYYYMMDD-HHMMSS-<hostname>.csv
    The hostname is everything after the second hyphen and before .csv.

    Args:
        csv_path: Path to the WLC CSV file.

    Returns:
        WLC hostname string, or 'unknown' if format is not recognized.
    """
    filename = Path(csv_path).stem  # Remove .csv extension

    # Split on '-' and rejoin everything after the timestamp
    # Format: YYYYMMDD-HHMMSS-<hostname>
    parts = filename.split("-")

    # Need at least 3 parts: date, time, hostname
    if len(parts) < 3:
        return "unknown"

    # Verify first two parts look like a timestamp (YYYYMMDD, HHMMSS)
    if not (len(parts[0]) == 8 and parts[0].isdigit()
            and len(parts[1]) == 6 and parts[1].isdigit()):
        return "unknown"

    # Everything after the timestamp is the hostname
    return "-".join(parts[2:])
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_ap_rename.py -v`
Expected: 26 passed

- [ ] **Step 5: Commit**

```bash
git add tests/test_ap_rename.py ap_rename.py
git commit -m "feat: add WLC hostname extraction from CSV filename"
```

---

### Task 9: CLI Entry Point — dudeatron_rename.py

**Files:**
- Create: `dudeatron_rename.py`

- [ ] **Step 1: Write the entry point**

Create `dudeatron_rename.py`:

```python
"""Dudeatron Rename - AP rename matching tool.

Matches new WLC APs to historical records using CDP neighbor/port data,
generates IOS-XE rename commands, and updates the historical CSV.

Usage:
    python dudeatron_rename.py --historical <path> --current <path> [-o <dir>]

Example:
    python dudeatron_rename.py \\
        --historical output/historical-aps.csv \\
        --current output/20260316-143022-wlc-1.csv
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from ap_rename import (
    build_cdp_lookup,
    extract_wlc_hostname,
    generate_cli_commands,
    match_aps,
    read_current_wlc_csv,
    read_historical_csv,
    update_historical_csv,
)


def main() -> None:
    """Main execution function for AP rename matching."""
    parser = argparse.ArgumentParser(
        description="Dudeatron Rename - AP Rename Matching Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--historical",
        type=str,
        required=True,
        help="Path to historical CSV file with desired AP names and CDP data",
    )
    parser.add_argument(
        "--current",
        type=str,
        required=True,
        help="Path to current WLC CSV file produced by dudeatron_wlc.py",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default="output",
        help="Directory for output files (default: output/)",
    )
    args = parser.parse_args()

    print("Dudeatron Rename - AP Rename Matching Tool")
    print("=" * 70)
    print()

    try:
        # Read input files
        print(f"Reading historical CSV: {args.historical}")
        historical_rows = read_historical_csv(args.historical)
        print(f"  Found {len(historical_rows)} historical AP entries")

        print(f"Reading current WLC CSV: {args.current}")
        current_rows = read_current_wlc_csv(args.current)
        print(f"  Found {len(current_rows)} current AP entries")
        print()

        # Build lookup from current WLC data
        current_lookup = build_cdp_lookup(
            current_rows, "neighbor_name", "neighbor_port"
        )
        print(f"Built CDP lookup with {len(current_lookup)} unique entries")
        print()

        # Match APs
        already_renamed, needs_rename, unmatched = match_aps(
            historical_rows, current_lookup
        )
        print("Match results:")
        print(f"  Already renamed: {len(already_renamed)}")
        print(f"  Needs rename:    {len(needs_rename)}")
        print(f"  Unmatched:       {len(unmatched)}")
        print()

        # Warn if no matches found
        total_matched = len(already_renamed) + len(needs_rename)
        if total_matched == 0:
            print(
                "WARNING: No APs matched between historical "
                "and current data. Check that CDP neighbor "
                "names and ports align between the two CSVs.",
                file=sys.stderr,
            )
            print()

        # Prepare output
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        wlc_hostname = extract_wlc_hostname(args.current)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        # Generate and write CLI commands
        cli_commands = generate_cli_commands(
            already_renamed, needs_rename, unmatched
        )
        commands_filename = (
            f"{timestamp}-{wlc_hostname}-rename-commands.txt"
        )
        commands_path = output_dir / commands_filename
        with open(commands_path, "w", encoding="utf-8") as f:
            f.write(cli_commands)
        print(f"CLI commands written to: {commands_path}")

        # Print commands to console too
        print()
        print("=" * 70)
        print("CLI COMMANDS")
        print("=" * 70)
        print(cli_commands)

        # Update historical CSV
        matched = already_renamed + needs_rename
        updated_csv_path = (
            output_dir / f"{timestamp}-{wlc_hostname}-updated-aps.csv"
        )
        update_historical_csv(
            historical_rows, matched, str(updated_csv_path)
        )
        print(f"Updated CSV written to: {updated_csv_path}")
        print()
        print("Done!")

    except FileNotFoundError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
    except Exception as error:
        print(f"FATAL ERROR: {error}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify it runs with --help**

Run: `python dudeatron_rename.py --help`
Expected: Usage message showing `--historical`, `--current`, `-o` arguments

- [ ] **Step 3: Commit**

```bash
git add dudeatron_rename.py
git commit -m "feat: add CLI entry point for AP rename matching"
```

---

### Task 10: End-to-End Manual Verification

This task is a manual verification step using real devices — no code changes.
All real device data stays in gitignored directories (`output/`, `wlc.txt`).

- [ ] **Step 1: Ensure WLC hostname is in wlc.txt**

Verify or create `wlc.txt` with the target WLC IP or hostname.
Note: `wlc.txt` is gitignored — safe for real data.

- [ ] **Step 2: Run dudeatron_wlc.py to collect current data**

Run: `python dudeatron_wlc.py -o output/`

This connects to the WLC via SSH, collects `show ap summary`,
`show ap cdp neighbors`, and `show ap meraki monitoring summary`, and writes
a CSV to `output/YYYYMMDD-HHMMSS-<wlc-hostname>.csv`.

Expected: CSV file created in `output/` directory.

- [ ] **Step 3: Run dudeatron_rename.py with both CSVs**

Run:
```bash
python dudeatron_rename.py \
    --historical output/<historical-csv>.csv \
    --current output/<the-csv-from-step-2>.csv
```

Expected: Console output showing match results, CLI commands printed to screen,
and two output files created in `output/`.

- [ ] **Step 4: Review the generated CLI commands**

Open the `*-rename-commands.txt` file and verify:
- Verification commands for already-renamed APs look correct
- Rename commands map the right default names to the right desired names
- Unmatched APs are flagged with their expected CDP neighbor/port

- [ ] **Step 5: Review the updated CSV**

Open the `*-updated-aps.csv` file and verify:
- Previously empty MAC/serial/meraki fields are now filled in for matched APs
- Existing values were not overwritten
- All original columns are preserved

- [ ] **Step 6: No commit needed**

This is a manual verification step — no code changes to commit.
