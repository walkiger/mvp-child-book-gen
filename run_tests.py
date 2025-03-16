#!/usr/bin/env python
"""
Test runner for the Child Book Generator MVP.

This script runs the test suite using pytest and provides options for
different test configurations.
"""

import os
import sys
import argparse
import subprocess
import platform


def run_tests(args):
    """
    Run the test suite with the specified options.
    
    Args:
        args: Command line arguments
    
    Returns:
        int: Exit code from pytest
    """
    # Build the pytest command
    cmd = ['pytest']
    
    # Add verbosity
    if args.verbose:
        cmd.append('-v')
    elif args.quiet:
        cmd.append('-q')
    
    # Add test discovery options
    if args.keyword:
        cmd.extend(['-k', args.keyword])
    
    if args.xvs:
        cmd.append('-xvs')
    
    # Add test output options
    if args.show_locals:
        cmd.append('-l')
    
    # Add failure reporting options
    if args.fail_fast:
        cmd.append('-x')
    
    # Add coverage if requested
    if args.coverage:
        cmd.extend(['--cov=management', '--cov=app'])
        
        # Coverage report format
        if args.html_cov:
            cmd.append('--cov-report=html')
        else:
            cmd.append('--cov-report=term')
    
    # Add warnings handling
    if args.disable_warnings:
        cmd.append('-p no:warnings')
    
    # Enable asyncio support
    cmd.append('--asyncio-mode=strict')
    
    # Add tests to run
    if args.test_path:
        cmd.append(args.test_path)
    else:
        cmd.append('tests/')
    
    # Add additional args
    if args.pytest_args:
        cmd.extend(args.pytest_args)
    
    # Print command with colorized output if available
    cmd_str = ' '.join(cmd)
    if hasattr(platform, "system") and platform.system() != "Windows":
        print(f"\033[1;34mRunning: {cmd_str}\033[0m")
    else:
        print(f"Running: {cmd_str}")
    
    # Set environment variables for testing
    test_env = os.environ.copy()
    test_env["TESTING"] = "1"
    test_env["SECRET_KEY"] = "test_secret_key"
    test_env["OPENAI_API_KEY"] = "test_openai_key"
    
    # Run pytest
    result = subprocess.run(cmd, env=test_env)
    return result.returncode


def main():
    """Main function to parse arguments and run tests."""
    parser = argparse.ArgumentParser(description='Run the test suite')
    
    # Test discovery options
    parser.add_argument('-k', '--keyword', 
                        help='Only run tests that match the given substring expression')
    parser.add_argument('test_path', nargs='?',
                        help='Path to specific test or test directory')
    
    # Output options
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='Decrease verbosity')
    parser.add_argument('-l', '--show-locals', action='store_true',
                        help='Show local variables in tracebacks')
    parser.add_argument('--xvs', action='store_true',
                        help='Exit instantly on first error, with verbose output')
    
    # Behavior options
    parser.add_argument('-x', '--fail-fast', action='store_true',
                        help='Exit instantly on first error')
    parser.add_argument('--disable-warnings', action='store_true',
                        help='Disable pytest warnings')
    
    # Coverage options
    parser.add_argument('-c', '--coverage', action='store_true',
                        help='Generate test coverage report')
    parser.add_argument('--html-cov', action='store_true',
                        help='Generate HTML coverage report')
    
    # Pass arbitrary arguments to pytest
    parser.add_argument('pytest_args', nargs='*', 
                        help='Additional arguments to pass to pytest')
    
    args = parser.parse_args()
    
    # Check for incompatible options
    if args.verbose and args.quiet:
        parser.error("Cannot use both --verbose and --quiet")
    
    # Ensure required packages are installed
    try:
        import pytest
        import pytest_asyncio
    except ImportError:
        print("Missing required packages. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio", "pytest-cov", "httpx"])
        print("Required packages installed. Continuing...")
    
    sys.exit(run_tests(args))


if __name__ == '__main__':
    main() 