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
        help=(
            "Path to historical CSV file with desired AP names "
            "and CDP data"
        ),
    )
    parser.add_argument(
        "--current",
        type=str,
        required=True,
        help=(
            "Path to current WLC CSV file produced by "
            "dudeatron_wlc.py"
        ),
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
        print(
            f"  Found {len(historical_rows)} historical AP entries"
        )

        print(f"Reading current WLC CSV: {args.current}")
        current_rows = read_current_wlc_csv(args.current)
        print(
            f"  Found {len(current_rows)} current AP entries"
        )
        print()

        # Build lookup from current WLC data
        current_lookup = build_cdp_lookup(
            current_rows, "neighbor_name", "neighbor_port"
        )
        print(
            f"Built CDP lookup with {len(current_lookup)} "
            f"unique entries"
        )
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
            output_dir
            / f"{timestamp}-{wlc_hostname}-updated-aps.csv"
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
