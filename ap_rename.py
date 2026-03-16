"""AP rename matching module for Dudeatron.

This module provides functionality to match new WLC APs to historical records
using CDP neighbor/port data, generate IOS-XE rename commands, and update
historical CSV files with current device data.
"""

import re


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
