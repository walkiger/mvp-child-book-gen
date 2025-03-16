#!/usr/bin/env python3
"""
Management script for the Child Book Generator MVP.

This script provides a command-line interface for managing the application,
including starting and stopping servers, managing the database, setting up
the environment, and more.
"""

import sys
from management import main

if __name__ == "__main__":
    sys.exit(main()) 