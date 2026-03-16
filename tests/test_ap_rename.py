"""Tests for AP rename matching module."""

from ap_rename import convert_mac_to_colon_format, normalize_cdp_neighbor


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
