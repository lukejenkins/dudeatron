"""WLC (Wireless LAN Controller) management module for Dudeatron.

This module provides functionality to connect to WLC devices via SSH,
execute commands, parse outputs with Genie, and combine results into CSV
format.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from genie.libs.parser.iosxe.show_ap import (
    ShowApCdpNeighbor,
    ShowApMerakiMonitoringSummary,
    ShowApSummary,
)
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException


def setup_logs_directory() -> Path:
    """Create logs directory if it doesn't exist.

    Returns:
        Path: Path object pointing to the logs directory.
    """
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    return logs_dir


def connect_and_execute_wlc_commands(
    hostname: str,
    commands: List[str],
    config: Dict[str, str]
) -> Optional[Dict[str, str]]:
    """Connect to a WLC and execute multiple commands with show clock bookends.

    Args:
        hostname: The hostname or IP address of the WLC.
        commands: List of commands to execute on the WLC.
        config: Dictionary containing SSH connection parameters.

    Returns:
        Optional[Dict[str, str]]: Dictionary mapping command to output if
            successful, None if connection failed. Keys include 'show_clock_start',
            'show_clock_end', and each command from the commands list.

    Note:
        All SSH session traffic is logged to timestamped files in the logs/
        directory. The session starts and ends with 'show clock' commands.
    """
    logs_dir = setup_logs_directory()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    # Create log filename following the ISO 8601-inspired format
    session_log_path = logs_dir / f"{timestamp}-{hostname}.log"

    device_params = {
        "device_type": config["DEVICE_TYPE"],
        "host": hostname,
        "username": config["SSH_USERNAME"],
        "password": config["SSH_PASSWORD"],
        "secret": config.get("SSH_ENABLE_SECRET", ""),
        "timeout": int(config.get("SSH_TIMEOUT", "30")),
        "session_log": str(session_log_path),
        "session_log_record_writes": True,
        "session_log_file_mode": "write",
        "global_delay_factor": 2,  # Increase delay for WLC responses
    }

    try:
        print(f"Connecting to WLC: {hostname}...")
        connection = ConnectHandler(**device_params)

        # For IOS-XE, also disable line wrapping to prevent output truncation
        if config["DEVICE_TYPE"] == "cisco_xe":
            connection.send_command("terminal width 0", expect_string=r"#")

        # Enter enable mode if secret is provided
        if device_params["secret"]:
            connection.enable()

        outputs = {}

        # Execute show clock at the start
        print(f"Executing: show clock (start)")
        outputs["show_clock_start"] = connection.send_command("show clock")

        # Execute each command
        for command in commands:
            print(f"Executing: {command}")
            # Use a longer read timeout for commands with potentially large output
            # WLCs with many APs can take a long time to return all data
            outputs[command] = connection.send_command(
                command,
                read_timeout=120,
                expect_string=r"#"
            )

        # Execute show clock at the end
        print(f"Executing: show clock (end)")
        outputs["show_clock_end"] = connection.send_command("show clock")

        connection.disconnect()
        print(f"Successfully retrieved data from {hostname}")
        print(f"Session log saved to: {session_log_path}\n")

        return outputs

    except NetmikoTimeoutException:
        print(f"ERROR: Connection timeout to {hostname}")
        return None
    except NetmikoAuthenticationException:
        print(f"ERROR: Authentication failed for {hostname}")
        return None
    except Exception as error:
        print(f"ERROR: Failed to connect to {hostname}: {str(error)}")
        return None


def _safe_parse(parser_cls, output: str, command_label: str) -> Dict[str, Any]:
    """Run a Genie parser safely, returning an empty dict on failure."""
    try:
        parser = parser_cls(device=None)
        return parser.cli(output=output)
    except Exception as exc:  # pragma: no cover - defensive logging only
        print(f"WARNING: Failed to parse {command_label}: {exc}")
        return {}


def parse_show_ap_summary(output: str) -> List[Dict[str, Any]]:
    """Parse 'show ap summary' using Genie."""
    parsed = _safe_parse(ShowApSummary, output, "show ap summary")
    ap_entries: List[Dict[str, Any]] = []

    for ap_name, data in parsed.get("ap_name", {}).items():
        ap_entries.append(
            {
                "ap_name": ap_name,
                "slots": data.get("slots_count"),
                "ap_model": data.get("ap_model"),
                "mac_address": data.get("ethernet_mac"),
                "radio_mac": data.get("radio_mac"),
                "location": data.get("location"),
                "country": data.get("country"),
                "regulatory_domain": data.get("regulatory_domain"),
                "ip_address": data.get("ap_ip_address"),
                "state": data.get("state"),
            }
        )

    return ap_entries


def parse_show_ap_cdp_neighbors(output: str) -> List[Dict[str, Any]]:
    """Parse 'show ap cdp neighbor' using Genie."""
    parsed = _safe_parse(ShowApCdpNeighbor, output, "show ap cdp neighbors")
    neighbor_entries: List[Dict[str, Any]] = []

    for ap_name, data in parsed.get("ap_name", {}).items():
        neighbor_ips = data.get("neighbor_ip_addresses") or []
        neighbor_entries.append(
            {
                "ap_name": ap_name,
                "neighbor_name": data.get("neighbor_name"),
                "neighbor_ip": neighbor_ips[0] if neighbor_ips else "",
                "neighbor_port": data.get("neighbor_port"),
            }
        )

    return neighbor_entries


def parse_show_ap_meraki_monitoring(output: str) -> List[Dict[str, Any]]:
    """Parse 'show ap meraki monitoring summary' using Genie."""
    parsed = _safe_parse(
        ShowApMerakiMonitoringSummary, output, "show ap meraki monitoring summary"
    )
    monitor = parsed.get("meraki_monitoring", {})
    aps = monitor.get("aps", {})
    entries: List[Dict[str, Any]] = []

    for ap_name, data in aps.items():
        entries.append(
            {
                "ap_name": ap_name,
                "ap_model": data.get("ap_model"),
                "radio_mac": data.get("radio_mac"),
                "mac_address": data.get("mac_address"),
                "serial_number": data.get("serial_number"),
                "cloud_id": data.get("cloud_id"),
                "meraki_status": data.get("status"),
            }
        )

    return entries


def combine_wlc_data_to_csv(
    hostname: str,
    ap_summary: List[Dict[str, str]],
    cdp_neighbors: List[Dict[str, str]],
    meraki_monitoring: List[Dict[str, str]],
    timestamp: str,
    output_dir: str = "."
) -> str:
    """Combine parsed WLC data from multiple commands into a unified CSV file.

    Args:
        hostname: The hostname or IP address of the WLC.
        ap_summary: Parsed data from 'show ap summary'.
        cdp_neighbors: Parsed data from 'show ap cdp neighbors'.
        meraki_monitoring: Parsed data from 'show ap meraki monitoring summary'.
        timestamp: Timestamp string for the filename.
        output_dir: Directory to save the CSV file (default: current directory).

    Returns:
        str: Path to the created CSV file.

    Note:
        The CSV combines data based on AP name. APs present in one dataset
        but not others will have empty fields for missing data.
    """
    # Create a master dictionary keyed by AP name
    combined_data = {}

    # Add AP summary data
    for ap in ap_summary:
        ap_name = ap["ap_name"]
        combined_data[ap_name] = ap.copy()

    # Add CDP neighbor data
    for neighbor in cdp_neighbors:
        ap_name = neighbor["ap_name"]
        if ap_name in combined_data:
            combined_data[ap_name].update({
                "neighbor_name": neighbor.get("neighbor_name", ""),
                "neighbor_ip": neighbor.get("neighbor_ip", ""),
                "neighbor_port": neighbor.get("neighbor_port", ""),
            })
        else:
            # AP found in CDP but not in summary
            combined_data[ap_name] = {
                "ap_name": ap_name,
                "neighbor_name": neighbor.get("neighbor_name", ""),
                "neighbor_ip": neighbor.get("neighbor_ip", ""),
                "neighbor_port": neighbor.get("neighbor_port", ""),
            }

    # Add Meraki monitoring data
    for meraki in meraki_monitoring:
        ap_name = meraki["ap_name"]
        if ap_name in combined_data:
            combined_data[ap_name].update({
                "radio_mac": meraki.get("radio_mac", ""),
                "serial_number": meraki.get("serial_number", ""),
                "cloud_id": meraki.get("cloud_id", ""),
                "meraki_status": meraki.get("meraki_status", ""),
            })
        else:
            # AP found in Meraki but not in summary or CDP
            combined_data[ap_name] = {
                "ap_name": ap_name,
                "serial_number": meraki.get("serial_number", ""),
                "cloud_id": meraki.get("cloud_id", ""),
                "meraki_status": meraki.get("meraki_status", ""),
            }

    # Determine all possible column headers
    all_headers = set()
    for ap_data in combined_data.values():
        all_headers.update(ap_data.keys())

    # Sort headers for consistent output (ap_name first)
    sorted_headers = ["ap_name"] + sorted(
        [h for h in all_headers if h != "ap_name"]
    )

    # Create CSV file
    csv_filename = f"{timestamp}-{hostname}.csv"
    csv_path = Path(output_dir) / csv_filename

    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=sorted_headers)
        writer.writeheader()

        # Write data sorted by AP name
        for ap_name in sorted(combined_data.keys()):
            # Fill in missing fields with empty strings
            row = {header: combined_data[ap_name].get(header, "")
                   for header in sorted_headers}
            writer.writerow(row)

    return str(csv_path)


def process_wlc(hostname: str, config: Dict[str, str]) -> Optional[str]:
    """Process a single WLC: connect, execute commands, parse, and save to CSV.

    Args:
        hostname: The hostname or IP address of the WLC.
        config: Dictionary containing SSH connection parameters.

    Returns:
        Optional[str]: Path to the generated CSV file if successful,
            None if processing failed.
    """
    commands = [
        "show ap summary",
        "show ap cdp neighbors",
        "show ap meraki monitoring summary"
    ]

    # Get timestamp for consistent naming
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    # Execute commands
    outputs = connect_and_execute_wlc_commands(hostname, commands, config)

    if not outputs:
        return None

    # Parse each command output
    print("Parsing 'show ap summary'...")
    ap_summary = parse_show_ap_summary(outputs.get("show ap summary", ""))
    print(f"Found {len(ap_summary)} APs in summary")

    print("Parsing 'show ap cdp neighbors'...")
    cdp_neighbors = parse_show_ap_cdp_neighbors(
        outputs.get("show ap cdp neighbors", "")
    )
    print(f"Found {len(cdp_neighbors)} CDP neighbor entries")

    print("Parsing 'show ap meraki monitoring summary'...")
    meraki_monitoring = parse_show_ap_meraki_monitoring(
        outputs.get("show ap meraki monitoring summary", "")
    )
    print(f"Found {len(meraki_monitoring)} Meraki monitoring entries")

    # Combine data and write to CSV
    print("Combining data and writing to CSV...")
    output_dir = config.get("OUTPUT_DIR", ".")
    csv_path = combine_wlc_data_to_csv(
        hostname,
        ap_summary,
        cdp_neighbors,
        meraki_monitoring,
        timestamp,
        output_dir
    )

    print(f"CSV file created: {csv_path}\n")

    return csv_path
