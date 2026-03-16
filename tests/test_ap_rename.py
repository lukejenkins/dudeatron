"""Tests for AP rename matching module."""

import os
import tempfile

import pytest

from ap_rename import (
    build_cdp_lookup,
    convert_mac_to_colon_format,
    match_aps,
    normalize_cdp_neighbor,
    read_current_wlc_csv,
    read_historical_csv,
)


def test_convert_cisco_dotted_mac():
    """Convert Cisco dotted MAC to colon-separated lowercase."""
    assert (
        convert_mac_to_colon_format("687d.b45c.1f10")
        == "68:7d:b4:5c:1f:10"
    )


def test_convert_already_colon_mac():
    """Colon-separated MACs pass through unchanged."""
    assert (
        convert_mac_to_colon_format("aa:bb:cc:dd:ee:ff")
        == "aa:bb:cc:dd:ee:ff"
    )


def test_convert_uppercase_colon_mac():
    """Uppercase colon-separated MACs are lowercased."""
    assert (
        convert_mac_to_colon_format("AA:BB:CC:DD:EE:FF")
        == "aa:bb:cc:dd:ee:ff"
    )


def test_convert_empty_mac():
    """Empty string returns empty string."""
    assert convert_mac_to_colon_format("") == ""


def test_normalize_fqdn_neighbor():
    """Strip domain suffix from FQDN."""
    assert (
        normalize_cdp_neighbor("switch-1.mgmt.example.edu")
        == "switch-1"
    )


def test_normalize_short_neighbor():
    """Short name passes through (lowercased)."""
    assert normalize_cdp_neighbor("SWITCH-1") == "switch-1"


def test_normalize_neighbor_whitespace():
    """Whitespace is stripped."""
    assert normalize_cdp_neighbor("  switch-1  ") == "switch-1"


def test_normalize_empty_neighbor():
    """Empty string returns empty string."""
    assert normalize_cdp_neighbor("") == ""


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
        "AP Name,CDP Neighbor,Port of CDP Neighbor\n"
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
    assert (
        lookup[("switch-1", "tengigabitethernet1/0/47")]["ap_name"]
        == "AP00XX.XXXX.0000"
    )


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
    already, needs, unmatched = match_aps(
        historical, current_lookup
    )

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
    already, needs, unmatched = match_aps(
        historical, current_lookup
    )

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
    already, needs, unmatched = match_aps(
        historical, current_lookup
    )

    assert len(already) == 0
    assert len(needs) == 0
    assert len(unmatched) == 1
    assert "current_ap_name" not in unmatched[0]
