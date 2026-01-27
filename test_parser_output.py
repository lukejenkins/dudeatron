"""Test script to see what fields Genie parsers actually return."""

import json
from pathlib import Path

from genie.libs.parser.iosxe.show_ap import (
    ShowApCdpNeighbor,
    ShowApMerakiMonitoringSummary,
    ShowApSummary,
)


def test_parser(log_file: str):
    """Parse log file and display what each parser returns."""
    with open(log_file, "r") as f:
        log_content = f.read()
    
    # Extract show ap summary output
    summary_start = log_content.find("show ap summary\n")
    summary_end = log_content.find("ogden-wlc4#show ap cdp")
    if summary_start != -1 and summary_end != -1:
        summary_output = log_content[summary_start:summary_end].split("\n", 2)[2]
        print("=" * 80)
        print("SHOW AP SUMMARY - First AP parsed data:")
        print("=" * 80)
        parser = ShowApSummary(device=None)
        parsed = parser.cli(output=summary_output)
        first_ap = list(parsed.get("ap_name", {}).items())[0] if parsed.get("ap_name") else None
        if first_ap:
            print(f"\nAP Name: {first_ap[0]}")
            print(f"Available fields: {json.dumps(first_ap[1], indent=2)}")
    
    # Extract show ap cdp neighbors output
    cdp_start = log_content.find("show ap cdp neighbors\n")
    cdp_end = log_content.find("ogden-wlc4#show ap meraki")
    if cdp_start != -1 and cdp_end != -1:
        cdp_output = log_content[cdp_start:cdp_end].split("\n", 2)[2]
        print("\n" + "=" * 80)
        print("SHOW AP CDP NEIGHBORS - Parsed data:")
        print("=" * 80)
        parser = ShowApCdpNeighbor(device=None)
        parsed = parser.cli(output=cdp_output)
        print(f"Number of APs with CDP data: {len(parsed.get('ap_name', {}))}")
        first_ap = list(parsed.get("ap_name", {}).items())[0] if parsed.get("ap_name") else None
        if first_ap:
            print(f"\nFirst AP Name: {first_ap[0]}")
            print(f"Available fields: {json.dumps(first_ap[1], indent=2)}")
        else:
            print("No CDP data parsed")
    
    # Extract show ap meraki monitoring summary output
    meraki_start = log_content.find("show ap meraki monitoring summary\n")
    meraki_end = log_content.find("ogden-wlc4#show clock\n", meraki_start)
    if meraki_start != -1 and meraki_end != -1:
        meraki_output = log_content[meraki_start:meraki_end].split("\n", 2)[2]
        print("\n" + "=" * 80)
        print("SHOW AP MERAKI MONITORING - First AP parsed data:")
        print("=" * 80)
        parser = ShowApMerakiMonitoringSummary(device=None)
        parsed = parser.cli(output=meraki_output)
        aps = parsed.get("meraki_monitoring", {}).get("aps", {})
        first_ap = list(aps.items())[0] if aps else None
        if first_ap:
            print(f"\nAP Name: {first_ap[0]}")
            print(f"Available fields: {json.dumps(first_ap[1], indent=2)}")


if __name__ == "__main__":
    log_file = "logs/20260106-163814-ogden-wlc4.log"
    test_parser(log_file)
