#!/usr/bin/env python
"""
Script to run database migrations.
"""
import os
import sys

# Add parent directory to path to ensure imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.migrations import run_migrations

if __name__ == "__main__":
    print("Running database migrations...")
    run_migrations()
    print("Database migrations completed successfully") 