#!/usr/bin/env python
"""
Server status checker tool for the Child Book Generator MVP.

This diagnostic tool checks if the backend and frontend servers are running
and displays their status information.
"""

import os
import sys
import psutil
import argparse

# Add parent directory to path to allow importing from root modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Default configuration
PID_DIR = ".pids"


def get_pid_file(server_type):
    """Get the path to the PID file for a server type"""
    return os.path.join(PID_DIR, f"{server_type}.pid")


def get_pid(server_type, debug=False):
    """
    Get the PID of a running server process
    
    Args:
        server_type: Type of server ('backend' or 'frontend')
        debug: Whether to print debug information
        
    Returns:
        int or None: PID if found, None otherwise
    """
    pid_file = get_pid_file(server_type)
    
    if debug:
        print(f"Checking PID file: {pid_file}")
    
    if not os.path.exists(pid_file):
        if debug:
            print(f"PID file does not exist for {server_type}")
        return None
    
    try:
        with open(pid_file, 'r') as f:
            content = f.read().strip()
            
            if debug:
                print(f"PID file content: {content}")
                
            try:
                pid = int(content)
                
                if psutil.pid_exists(pid):
                    if debug:
                        print(f"Process {pid} is running")
                    return pid
                else:
                    if debug:
                        print(f"Process {pid} is not running")
                    return None
            except ValueError:
                if debug:
                    print(f"Failed to parse PID from {content}")
                return None
    except Exception as e:
        if debug:
            print(f"Error reading PID file: {e}")
        return None


def show_status(debug=False, format_json=False):
    """
    Show the status of both servers
    
    Args:
        debug: Whether to print debug information
        format_json: Whether to output in JSON format
    """
    if not debug:
        print("Checking server status...")
        
    backend_pid = get_pid("backend", debug)
    frontend_pid = get_pid("frontend", debug)
    
    if format_json:
        import json
        status = {
            "backend": {
                "running": backend_pid is not None,
                "pid": backend_pid,
                "url": "http://localhost:8080/api" if backend_pid else None
            },
            "frontend": {
                "running": frontend_pid is not None,
                "pid": frontend_pid,
                "url": "http://localhost:5173" if frontend_pid else None
            }
        }
        print(json.dumps(status, indent=2))
        return
    
    print("\nServer Status:")
    print("-" * 50)
    
    # Check backend
    if backend_pid:
        print(f"Backend server: RUNNING (PID: {backend_pid})")
        try:
            proc = psutil.Process(backend_pid)
            if debug:
                cmdline = ' '.join(proc.cmdline())
                print(f"  Command: {cmdline[:80]}")
            print(f"  URL: http://localhost:8080/api")
        except Exception as e:
            if debug:
                print(f"  Error getting process info: {e}")
    else:
        print("Backend server: STOPPED")
        
    # Check frontend
    if frontend_pid:
        print(f"Frontend server: RUNNING (PID: {frontend_pid})")
        try:
            proc = psutil.Process(frontend_pid)
            print(f"  URL: http://localhost:5173")
        except Exception as e:
            if debug:
                print(f"  Error getting process info: {e}")
    else:
        print("Frontend server: STOPPED")
    
    print("-" * 50)


def main():
    """Parse command line arguments and run the status check"""
    parser = argparse.ArgumentParser(description='Check server status')
    parser.add_argument('-d', '--debug', action='store_true',
                       help='Enable debug output')
    parser.add_argument('-j', '--json', action='store_true',
                       help='Output in JSON format')
    
    args = parser.parse_args()
    
    try:
        show_status(debug=args.debug, format_json=args.json)
    except Exception as e:
        print(f"Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 