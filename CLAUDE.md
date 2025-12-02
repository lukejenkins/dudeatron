# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dudeatron is a wireless network management tool designed to help manage APs and WLCs via SSH. The project uses Python with netmiko for SSH connectivity and python-dotenv for configuration management.

**Status**: Active development with working core functionality. The tool successfully connects to network devices via SSH, executes commands, parses output, and logs sessions. Currently managing 75+ production APs.

## Tech Stack

- Python 3.x
- netmiko (SSH connectivity for network devices)
- python-dotenv (environment configuration)

## Project Structure

- `dudeatron.py` - Main application script (362 lines, functional architecture)
- `aps.txt` - Production device list (75+ IP addresses)
- `test_aps.txt`, `test_single.txt` - Test device lists
- `aps.txt.example` - Example format for device lists
- `.env` - Configuration file (SSH credentials, device type, timeout)
- `.env.example` - Configuration template
- `logs/` - SSH session logs directory (timestamped log files)
- `requirements.txt` - Python dependencies

## Code Style & Standards

All Python code must adhere to PEP 8 with these specifications:

- **Line length**: maximum 88 characters (Black default)
- **Indentation**: 4 spaces, no tabs
- **Naming conventions**:
  - `snake_case` for variables, functions, methods, modules
  - `PascalCase` for classes
  - `UPPER_CASE` for constants
  - Private attributes/methods prefixed with underscore (`_private_method`)
- **String quotes**: prefer double quotes (`"`)
- **Docstrings**: Google style format for all modules, classes, and functions (PEP 257)
- **Type annotations**: Use the `typing` module (e.g., `List[str]`, `Dict[str, int]`)

## Programming Patterns

- Use functional and declarative programming patterns; avoid classes where possible
- Prefer iteration and modularization over code duplication
- Use descriptive variable names with auxiliary verbs (e.g., `is_loading`, `has_error`)
- Break down complex functions into smaller, more manageable functions
- Write code with clear variable names and explanatory comments for non-obvious logic
- Avoid shorthand syntax and complex patterns
- Add defensive coding patterns and clear error handling
- Include validation for user inputs and explicit type checking
- Handle edge cases and write clear exception handling

## Implementation Approach

- Provide full implementations rather than partial snippets
- Include import statements, required dependencies, and initialization code
- Suggest simpler solutions first, then offer more optimized versions with explanations of trade-offs
- When suggesting fixes for errors, explain the root cause and how the solution addresses it
- Write concise, efficient, and idiomatic code that is also easily understandable

## Current Implementation

The core script (`dudeatron.py`) provides:

- SSH connectivity to network devices (APs and WLCs)
- Configuration management via `.env` file with interactive credential prompting
- Device list processing from text files (with comment support)
- SSH session logging with timestamped log files in `logs/` directory
- Command execution and output parsing
- Graceful error handling for timeouts and authentication failures

**Implemented Commands**:
- `show version` - Parses software version, model, serial number, uptime, and build time

**Planned Commands**:

**APs**:
- `show inventory`

**WLCs**:
- `show inventory`
- `show ap summary`
- `show ap summary load-info`
- `show ap uptime`
- `show ap name $AP_NAME config general`
- `show ap name $AP_NAME ethernet statistics`
- `show ap cdp neighbors`

## Future Architecture

Planned features include:

- Multiple simultaneous SSH connections
- Data export to multiple formats (JSON, time series DB, Prometheus, CSV)
- Integration with Cisco DNA Center and netbox for equipment inventory
- AP replacement project management with Asana integration
