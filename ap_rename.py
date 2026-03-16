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
