# Diagnostic and Utility Tools

This directory contains diagnostic and utility tools for the Child Book Generator MVP.

## Available Tools

### Server Status Checker

`check_server_status.py` - Checks if the backend and frontend servers are running and displays their status.

#### Usage

```bash
# Basic usage
python tools/check_server_status.py

# With debug output
python tools/check_server_status.py --debug

# Output in JSON format
python tools/check_server_status.py --json
```

## Future Tools

Additional diagnostic and utility tools will be added to this directory as they are developed. If you create a new tool, please add it to this README.

## Guidelines for Creating Tools

When creating new diagnostic or utility tools:

1. Include clear documentation and command-line help
2. Use consistent argument parsing with argparse
3. Include debug/verbose options
4. Consider adding JSON output for integration with other tools
5. Update this README with usage information 