"""
Tests for database utilities
"""
import os
import sqlite3
from pathlib import Path
import pytest
from unittest.mock import patch

# Import is handled by conftest.py, so we don't need the sys.path modification

from management.db_utils import init_db, run_migrations
from utils.error_handling import DatabaseError


def test_init_db(temp_db_path):
    """Test database initialization using the temp_db_path fixture"""
    # Initialize the test database
    db_path = init_db(temp_db_path)
    assert db_path == temp_db_path
    
    # Verify that the database has the expected tables
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    
    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    expected_tables = [
        'migrations', 'users', 'stories', 'pages', 
        'characters', 'settings', 'images'
    ]
    
    for table in expected_tables:
        assert table in tables, f"Table {table} not found in database"
    
    conn.close()


def test_run_migrations_no_dir(temp_db_path, monkeypatch, temp_dir):
    """Test running migrations when no migrations directory exists"""
    # Initialize the test database
    init_db(temp_db_path)
    
    # Create a temporary directory structure without migrations
    temp_app_dir = os.path.join(temp_dir, "app")
    temp_db_dir = os.path.join(temp_app_dir, "database")
    os.makedirs(temp_db_dir, exist_ok=True)
    
    # Use pytest's monkeypatch instead of unittest.mock.patch
    monkeypatch.setattr('os.getcwd', lambda: temp_dir)
    
    # Run migrations (should return False since no migrations directory exists)
    result = run_migrations(temp_db_path)
    assert result is False 