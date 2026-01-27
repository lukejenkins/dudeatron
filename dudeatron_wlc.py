"""Dudeatron WLC - Wireless LAN Controller management tool.

This script connects to WLC devices via SSH, executes monitoring commands,
and combines the output into a unified CSV file for analysis.
"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from dudeatron import (
    load_environment_config,
    prompt_for_credentials,
    read_hostnames_from_file,
)
from wlc_module import process_wlc


def main() -> None:
    """Main execution function for WLC operations.

    Loads configuration, reads WLC hostnames, connects to each WLC,
    executes monitoring commands (show ap summary, show ap cdp neighbors,
    show ap meraki monitoring summary), and combines results into CSV files.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Dudeatron WLC - Wireless LAN Controller Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        help="Directory for CSV output files (default: current directory or OUTPUT_DIR from .env)",
    )
    args = parser.parse_args()

    print("Dudeatron WLC - Wireless LAN Controller Management Tool")
    print("=" * 70)
    print()

    try:
        # Load configuration from .env file
        config = load_environment_config()

        # Override DEVICE_TYPE for WLC operations
        # Use cisco_xe for IOS-XE based WLCs (Catalyst 9800 series)
        # Use cisco_wlc_ssh for AireOS based WLCs (older 5520/8540 series)
        config["DEVICE_TYPE"] = "cisco_xe"

        # Set output directory from CLI args, .env, or default to current directory
        output_dir = args.output_dir or config.get("OUTPUT_DIR", ".")
        output_path = Path(output_dir)
        
        # Create output directory if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)
        config["OUTPUT_DIR"] = str(output_path)

        print("Configuration loaded successfully")
        print(f"Device type set to: {config['DEVICE_TYPE']}")
        print(f"Output directory: {config['OUTPUT_DIR']}")
        print()

        # Prompt for missing credentials
        if not config["SSH_USERNAME"] or not config["SSH_PASSWORD"]:
            prompt_for_credentials(config)

        # Read WLC hostnames from file
        # You can create a separate wlc.txt file or use the existing aps.txt
        wlc_file = "wlc.txt"

        # Check if wlc.txt exists, otherwise fall back to aps.txt
        if not Path(wlc_file).exists():
            print(f"'{wlc_file}' not found, using 'aps.txt' instead")
            wlc_file = "aps.txt"

        wlc_hostnames = read_hostnames_from_file(wlc_file)
        print(f"Found {len(wlc_hostnames)} WLC(s) to process")
        print()

        # Process each WLC
        successful = 0
        failed = 0

        for hostname in wlc_hostnames:
            print(f"{'=' * 70}")
            print(f"Processing WLC: {hostname}")
            print(f"{'=' * 70}")

            csv_path = process_wlc(hostname, config)

            if csv_path:
                successful += 1
            else:
                failed += 1
                print(f"Failed to process {hostname}\n")

        # Summary
        print(f"{'=' * 70}")
        print("Processing Summary")
        print(f"{'=' * 70}")
        print(f"Total WLCs: {len(wlc_hostnames)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print()

        if successful > 0:
            print(f"CSV files have been saved to: {config['OUTPUT_DIR']}")
            print("Session logs have been saved to: logs/")

        print("\nProcessing complete!")

    except FileNotFoundError as error:
        print(f"ERROR: {error}")
        print("\nPlease create 'wlc.txt' or 'aps.txt' with WLC hostnames.")
        print("Format: one hostname or IP address per line.")
        sys.exit(1)
    except ValueError as error:
        print(f"ERROR: {error}")
        print("\nPlease check your .env file configuration.")
        print("See '.env.example' for the expected format.")
        sys.exit(1)
    except Exception as error:
        print(f"FATAL ERROR: {error}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
