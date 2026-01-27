"""Test CDP neighbor parsing to debug the issue."""

from genie.libs.parser.iosxe.show_ap import ShowApCdpNeighbor
import re

# Read actual output from log
with open("logs/20260106-170010-ogden-wlc4.log", "r") as f:
    log_content = f.read()

# Extract show ap cdp neighbors output
cdp_start = log_content.find("show ap cdp neighbors\n")
cdp_end = log_content.find("ogden-wlc4#show ap meraki")
cdp_output = log_content[cdp_start:cdp_end].split("\n", 2)[2]

print("First 1000 chars of raw output:")
print(repr(cdp_output[:1000]))
print("\n" + "="*80 + "\n")

# Try parsing
parser = ShowApCdpNeighbor(device=None)
parsed = parser.cli(output=cdp_output)

print(f"Parsed result keys: {parsed.keys()}")
print(f"AP CDP neighbor count: {parsed.get('ap_cdp_neighbor_count')}")
print(f"Number of APs parsed: {len(parsed.get('ap_name', {}))}")
print(f"First few AP names: {list(parsed.get('ap_name', {}).keys())[:5]}")

# Now test the regex directly on actual lines
print("\n" + "="*80 + "\n")
print("Testing regex on actual output lines:\n")

neighbor_info_pattern = re.compile(
    r"^(?P<ap_name>\S+)\s+(?P<ap_ip>\d+\.\d+\.\d+\.\d+)\s+(?P<neighbor_name>\S+)\s+(?P<neighbor_port>\S+)$")

for i, line in enumerate(cdp_output.splitlines()):
    line = line.strip()
    if line and not line.startswith('Number') and not line.startswith('AP Name') and not line.startswith('-') and not line.startswith('Neighbor IP'):
        match = neighbor_info_pattern.match(line)
        if match and i < 50:  # Show first few matches
            print(f"Line {i}: MATCHED - {line[:80]}")
            print(f"  Groups: {match.groupdict()}\n")
        elif i < 50:
            print(f"Line {i}: NO MATCH - {repr(line[:80])}")
