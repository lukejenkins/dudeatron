"""AP rename matching module for Dudeatron.

This module provides functionality to match new WLC APs to historical records
using CDP neighbor/port data, generate IOS-XE rename commands, and update
historical CSV files with current device data.
"""

import csv
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def convert_mac_to_colon_format(mac: str) -> str:
    """Convert a MAC address to colon-separated lowercase format.

    Handles Cisco dotted format (687d.b45c.1f10) and colon-separated
    format.

    Args:
        mac: MAC address string in any common format.

    Returns:
        Colon-separated lowercase MAC (aa:bb:cc:dd:ee:ff), or empty
        string if input is empty.
    """
    if not mac or not mac.strip():
        return ""

    # Remove all separators (dots, colons, dashes) to get raw hex
    raw_hex = re.sub(r"[.:\-]", "", mac.strip().lower())

    if len(raw_hex) != 12:
        return mac.strip().lower()

    # Insert colons every 2 characters
    return ":".join(raw_hex[i : i + 2] for i in range(0, 12, 2))


def normalize_cdp_neighbor(name: str) -> str:
    """Normalize a CDP neighbor name for comparison.

    Strips domain suffixes and lowercases for consistent matching.
    E.g., 'switch-1.mgmt.example.edu' -> 'switch-1'

    Args:
        name: CDP neighbor name, possibly with FQDN suffix.

    Returns:
        Normalized lowercase short name, or empty string if input
        is empty.
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
        raise FileNotFoundError(
            f"Historical CSV not found: {file_path}"
        )

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


def build_cdp_lookup(
    rows: List[Dict[str, str]],
    neighbor_key: str,
    port_key: str,
) -> Dict[Tuple[str, str], Dict[str, str]]:
    """Build a lookup dictionary keyed by normalized (cdp_neighbor, port).

    Args:
        rows: List of row dicts from a CSV file.
        neighbor_key: Column name for the CDP neighbor field.
        port_key: Column name for the port field.

    Returns:
        Dictionary mapping (normalized_neighbor, normalized_port) to
        row dict. If duplicates exist, warns and keeps first occurrence.
    """
    lookup: Dict[Tuple[str, str], Dict[str, str]] = {}

    for row in rows:
        neighbor = normalize_cdp_neighbor(
            row.get(neighbor_key, "")
        )
        port = row.get(port_key, "").strip().lower()

        if not neighbor or not port:
            continue

        key = (neighbor, port)

        if key in lookup:
            existing_name = lookup[key].get("ap_name", "unknown")
            new_name = row.get(
                "ap_name", row.get("AP Name", "unknown")
            )
            print(
                f"WARNING: Duplicate CDP key {key}, "
                f"keeping first ('{existing_name}'), "
                f"skipping '{new_name}'",
                file=sys.stderr,
            )
            continue

        lookup[key] = row

    return lookup


def match_aps(
    historical: List[Dict[str, str]],
    current_lookup: Dict[Tuple[str, str], Dict[str, str]],
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Match historical AP records against current WLC data.

    Matches by CDP neighbor + port.

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
        neighbor = normalize_cdp_neighbor(
            row.get("CDP Neighbor", "")
        )
        port = row.get(
            "Port of CDP Neighbor", ""
        ).strip().lower()

        if not neighbor or not port:
            unmatched.append(dict(row))
            continue

        key = (neighbor, port)
        current = current_lookup.get(key)

        if current is None:
            unmatched.append(dict(row))
            continue

        # Build matched entry with historical + current data
        entry = dict(row)
        entry["current_ap_name"] = current.get("ap_name", "")
        entry["current_mac_address"] = convert_mac_to_colon_format(
            current.get("mac_address", "")
        )
        entry["current_serial_number"] = current.get(
            "serial_number", ""
        )
        entry["current_meraki_serial"] = current.get(
            "cloud_id", ""
        )

        # Compare AP names case-insensitively
        historical_name = row.get("AP Name", "").strip().lower()
        current_name = current.get("ap_name", "").strip().lower()

        if historical_name == current_name:
            already_renamed.append(entry)
        else:
            needs_rename.append(entry)

    return already_renamed, needs_rename, unmatched


def generate_cli_commands(
    already_renamed: List[Dict],
    needs_rename: List[Dict],
    unmatched: List[Dict],
) -> str:
    """Generate IOS-XE WLC CLI commands for verification and renaming.

    Returns a string containing pasteable CLI commands organized in
    sections. The caller writes this to the output file.

    Args:
        already_renamed: APs whose names already match (verify only).
        needs_rename: APs that need renaming (current name differs).
        unmatched: APs with no current match (informational comments).

    Returns:
        Multi-line string of CLI commands with section headers as
        IOS comments.
    """
    lines: List[str] = []

    # Section 1: Verification of already-renamed APs
    if already_renamed:
        lines.append(
            "! ====== VERIFICATION COMMANDS "
            "(already renamed) ======"
        )
        for ap in already_renamed:
            ap_name = ap.get(
                "AP Name", ap.get("current_ap_name", "")
            )
            lines.append(
                f"show ap name {ap_name} config general"
            )
        lines.append("")

    # Section 2: Rename commands
    if needs_rename:
        lines.append("! ====== RENAME COMMANDS ======")
        for ap in needs_rename:
            current_name = ap["current_ap_name"]
            desired_name = ap["AP Name"]
            lines.append(
                f"ap name {current_name} name {desired_name}"
            )
        lines.append("")

    # Section 3: Post-rename verification
    if needs_rename:
        lines.append(
            "! ====== VERIFICATION AFTER RENAME ======"
        )
        for ap in needs_rename:
            desired_name = ap["AP Name"]
            lines.append(
                f"show ap summary | include {desired_name}"
            )
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
            port = ap.get(
                "Port of CDP Neighbor", "unknown"
            )
            lines.append(
                f"! {ap_name} expected on "
                f"{neighbor} {port} — not found"
            )
        lines.append("")

    return "\n".join(lines)


def update_historical_csv(
    historical_rows: List[Dict[str, str]],
    matched: List[Dict],
    output_path: str,
) -> str:
    """Write an updated historical CSV with data from matched APs.

    Updates MAC Address, Serial Number, and Meraki Serial Number for
    matched entries only when the historical value is empty. Preserves
    all original columns and column order.

    Args:
        historical_rows: Original historical CSV rows (list of dicts).
        matched: Concatenation of already_renamed + needs_rename
            from match_aps.
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

    # Update rows
    updated_rows: List[Dict[str, str]] = []
    for row in historical_rows:
        updated_row = dict(row)
        ap_name = row.get("AP Name", "")
        match = match_lookup.get(ap_name)

        if match:
            # Only fill in empty fields
            if not updated_row.get(
                "MAC Address", ""
            ).strip():
                updated_row["MAC Address"] = match.get(
                    "current_mac_address", ""
                )
            if not updated_row.get(
                "Serial Number", ""
            ).strip():
                updated_row["Serial Number"] = match.get(
                    "current_serial_number", ""
                )
            if not updated_row.get(
                "Meraki Serial Number", ""
            ).strip():
                updated_row["Meraki Serial Number"] = (
                    match.get("current_meraki_serial", "")
                )

        updated_rows.append(updated_row)

    # Write the updated CSV
    with open(
        output_path, "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)

    return output_path
