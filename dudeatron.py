"""Dudeatron - Wireless network management tool for APs and WLCs.

This module provides functionality to connect to network devices via SSH,
execute commands, and parse the output for network management purposes.
"""

import os
import sys
import getpass
from typing import Dict, List, Optional, Any
from pathlib import Path

from dotenv import load_dotenv
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException


def load_environment_config() -> Dict[str, str]:
    """Load configuration from environment variables.

    Returns:
        Dict[str, str]: Dictionary containing SSH connection parameters.
            Missing credentials will be set to empty strings and can be
            prompted for at runtime.

    Raises:
        ValueError: If DEVICE_TYPE environment variable is missing.
    """
    load_dotenv()

    config = {}

    # Only DEVICE_TYPE is strictly required
    device_type = os.getenv("DEVICE_TYPE")
    if device_type is None:
        raise ValueError(
            "Missing required environment variable: DEVICE_TYPE"
        )
    config["DEVICE_TYPE"] = device_type

    # Credentials are optional - will prompt if missing
    config["SSH_USERNAME"] = os.getenv("SSH_USERNAME", "")
    config["SSH_PASSWORD"] = os.getenv("SSH_PASSWORD", "")
    config["SSH_ENABLE_SECRET"] = os.getenv("SSH_ENABLE_SECRET", "")
    config["SSH_TIMEOUT"] = os.getenv("SSH_TIMEOUT", "30")

    return config


def prompt_for_credentials(config: Dict[str, str]) -> None:
    """Prompt user for missing credentials interactively.

    Args:
        config: Configuration dictionary to update with prompted credentials.
            This dictionary is modified in place.

    Note:
        Passwords and secrets are entered securely using getpass (no echo).
    """
    print("Some credentials are missing from .env file")
    print("Please provide the following information:\n")

    if not config["SSH_USERNAME"]:
        config["SSH_USERNAME"] = input("SSH Username: ").strip()
        if not config["SSH_USERNAME"]:
            raise ValueError("Username cannot be empty")

    if not config["SSH_PASSWORD"]:
        config["SSH_PASSWORD"] = getpass.getpass("SSH Password: ")
        if not config["SSH_PASSWORD"]:
            raise ValueError("Password cannot be empty")

    if not config["SSH_ENABLE_SECRET"]:
        response = input("Enable secret (press Enter to skip): ")
        config["SSH_ENABLE_SECRET"] = response.strip()

    print()


def read_hostnames_from_file(file_path: str) -> List[str]:
    """Read hostnames from a text file.

    Args:
        file_path: Path to the file containing hostnames (one per line).

    Returns:
        List[str]: List of hostnames/IP addresses.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the file is empty or contains no valid hostnames.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Hostnames file not found: {file_path}")

    hostnames = []

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            # Strip whitespace and skip empty lines and comments
            stripped_line = line.strip()
            if stripped_line and not stripped_line.startswith("#"):
                hostnames.append(stripped_line)

    if not hostnames:
        raise ValueError(f"No valid hostnames found in file: {file_path}")

    return hostnames


def connect_and_execute_command(
    hostname: str,
    command: str,
    config: Dict[str, str]
) -> Optional[str]:
    """Connect to a network device and execute a command.

    Args:
        hostname: The hostname or IP address of the device.
        command: The command to execute on the device.
        config: Dictionary containing SSH connection parameters.

    Returns:
        Optional[str]: Command output if successful, None if connection failed.
    """
    device_params = {
        "device_type": config["DEVICE_TYPE"],
        "host": hostname,
        "username": config["SSH_USERNAME"],
        "password": config["SSH_PASSWORD"],
        "secret": config.get("SSH_ENABLE_SECRET", ""),
        "timeout": int(config.get("SSH_TIMEOUT", "30")),
    }

    try:
        print(f"Connecting to {hostname}...")
        connection = ConnectHandler(**device_params)

        # Enter enable mode if secret is provided
        if device_params["secret"]:
            connection.enable()

        print(f"Executing command: {command}")
        output = connection.send_command(command)

        connection.disconnect()
        print(f"Successfully retrieved data from {hostname}\n")

        return output

    except NetmikoTimeoutException:
        print(f"ERROR: Connection timeout to {hostname}")
        return None
    except NetmikoAuthenticationException:
        print(f"ERROR: Authentication failed for {hostname}")
        return None
    except Exception as error:
        print(f"ERROR: Failed to connect to {hostname}: {str(error)}")
        return None


def parse_show_version(output: str) -> Dict[str, Any]:
    """Parse the output of 'show version' command.

    Args:
        output: Raw output from the 'show version' command.

    Returns:
        Dict[str, Any]: Parsed version information containing:
            - software_version: Software version string
            - model: Device model
            - serial_number: Device serial number
            - uptime: System uptime
            - build_time: Build/compilation time
            - raw_output: Complete raw output

    Note:
        This is a basic parser that extracts common fields.
        May need adjustment based on specific device types and output formats.
    """
    parsed_data = {
        "software_version": None,
        "model": None,
        "serial_number": None,
        "uptime": None,
        "build_time": None,
        "raw_output": output
    }

    lines = output.split("\n")

    for line in lines:
        line_lower = line.lower()

        # Extract software version (common patterns)
        if "version" in line_lower and parsed_data["software_version"] is None:
            if "cisco ios" in line_lower or "ios xe" in line_lower:
                parsed_data["software_version"] = line.strip()

        # Extract model information
        if "model" in line_lower or "pid:" in line_lower:
            if parsed_data["model"] is None:
                parsed_data["model"] = line.strip()

        # Extract serial number
        if "serial" in line_lower or "sn:" in line_lower:
            if parsed_data["serial_number"] is None:
                parsed_data["serial_number"] = line.strip()

        # Extract uptime
        if "uptime" in line_lower:
            if parsed_data["uptime"] is None:
                parsed_data["uptime"] = line.strip()

        # Extract build time
        if "compiled" in line_lower:
            if parsed_data["build_time"] is None:
                parsed_data["build_time"] = line.strip()

    return parsed_data


def display_parsed_data(hostname: str, parsed_data: Dict[str, Any]) -> None:
    """Display parsed device information in a readable format.

    Args:
        hostname: The hostname or IP address of the device.
        parsed_data: Dictionary containing parsed device information.
    """
    print(f"\n{'=' * 70}")
    print(f"Device: {hostname}")
    print(f"{'=' * 70}")

    if parsed_data["software_version"]:
        print(f"Software Version: {parsed_data['software_version']}")
    else:
        print("Software Version: Not found")

    if parsed_data["model"]:
        print(f"Model: {parsed_data['model']}")
    else:
        print("Model: Not found")

    if parsed_data["serial_number"]:
        print(f"Serial Number: {parsed_data['serial_number']}")
    else:
        print("Serial Number: Not found")

    if parsed_data["uptime"]:
        print(f"Uptime: {parsed_data['uptime']}")
    else:
        print("Uptime: Not found")

    if parsed_data["build_time"]:
        print(f"Build Time: {parsed_data['build_time']}")
    else:
        print("Build Time: Not found")

    print(f"{'=' * 70}\n")


def main() -> None:
    """Main execution function for Dudeatron.

    Loads configuration, reads hostnames, connects to devices,
    executes 'show version' command, and displays parsed results.
    """
    print("Dudeatron - Network Device Management Tool")
    print("=" * 70)
    print()

    try:
        # Load configuration from .env file
        config = load_environment_config()
        print("Configuration loaded successfully")
        print()

        # Prompt for missing credentials
        if not config["SSH_USERNAME"] or not config["SSH_PASSWORD"]:
            prompt_for_credentials(config)

        # Read hostnames from file
        hostnames_file = "aps.txt"
        hostnames = read_hostnames_from_file(hostnames_file)
        print(f"Found {len(hostnames)} device(s) to process")
        print()

        # Process each device
        for hostname in hostnames:
            output = connect_and_execute_command(
                hostname=hostname,
                command="show version",
                config=config
            )

            if output:
                parsed_data = parse_show_version(output)
                display_parsed_data(hostname, parsed_data)
            else:
                print(f"Skipping {hostname} due to connection failure\n")

        print("Processing complete!")

    except FileNotFoundError as error:
        print(f"ERROR: {error}")
        print(f"\nPlease create '{hostnames_file}' with device hostnames.")
        print(f"See 'aps.txt.example' for the expected format.")
        sys.exit(1)
    except ValueError as error:
        print(f"ERROR: {error}")
        print("\nPlease check your .env file configuration.")
        print("See '.env.example' for the expected format.")
        sys.exit(1)
    except Exception as error:
        print(f"FATAL ERROR: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
