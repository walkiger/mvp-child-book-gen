"""
PID file utilities for managing server processes
"""

import os
import psutil
import platform
from pathlib import Path
from typing import Optional, List
import time
import logging

from app.core.errors.base import ErrorContext, ErrorSeverity
from app.core.errors.management import (
    ProcessError,
    with_management_error_handling
)
from app.core.logging import setup_logger

# Setup logger
logger = setup_logger(
    name="management.pid_utils",
    level="INFO",
    log_file="logs/management.log"
)

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
PID_DIR = PROJECT_ROOT / ".pids"

@with_management_error_handling
def ensure_pid_dir():
    """Ensure the PID directory exists"""
    PID_DIR.mkdir(exist_ok=True)

def get_pid_file(server_type: str) -> Path:
    """Get the path to a PID file"""
    ensure_pid_dir()
    return PID_DIR / f"{server_type}.pid"

def is_process_running(pid: int) -> bool:
    """Check if a process is running"""
    try:
        # Special handling for marker PIDs
        if pid in [99999, 88888]:
            return True
            
        process = psutil.Process(pid)
        return process.is_running()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False

@with_management_error_handling
def save_pid(server_type: str, pid: int):
    """Save a PID to file"""
    pid_file = get_pid_file(server_type)
    with open(pid_file, 'w') as f:
        f.write(str(pid))

@with_management_error_handling
def get_pid(server_type: str) -> Optional[int]:
    """Get a PID from file if it exists"""
    pid_file = get_pid_file(server_type)
    if pid_file.exists():
        try:
            with open(pid_file) as f:
                return int(f.read().strip())
        except (ValueError, IOError):
            return None
    return None

@with_management_error_handling
async def cleanup_pid_files():
    """Clean up stale PID files"""
    try:
        ensure_pid_dir()
        cleaned = 0
        
        for pid_file in PID_DIR.glob("*.pid"):
            try:
                server_type = pid_file.stem
                pid = get_pid(server_type)
                
                if pid is None:
                    pid_file.unlink()
                    cleaned += 1
                    logger.info(f"Removed invalid PID file: {pid_file}")
                    continue
                    
                if not is_process_running(pid):
                    pid_file.unlink()
                    cleaned += 1
                    logger.info(f"Removed stale PID file for {server_type} (PID: {pid})")
                    
            except Exception as e:
                logger.warning(f"Error cleaning up {pid_file}: {e}")
                
        logger.info(f"Cleaned up {cleaned} stale PID files")
        return cleaned
        
    except Exception as e:
        error_context = ErrorContext(
            source="cleanup_pid_files",
            severity=ErrorSeverity.ERROR,
            error_id="pid_cleanup_error",
            additional_data={"error": str(e)}
        )
        raise ProcessError("Failed to clean up PID files", context=error_context)

@with_management_error_handling
def get_all_pid_files() -> List[str]:
    """Get a list of all PID files"""
    try:
        pid_dir = ensure_pid_dir()
        if not os.path.exists(pid_dir):
            return []
            
        return [os.path.join(pid_dir, f) for f in os.listdir(pid_dir) if f.endswith('.pid')]
    except Exception as e:
        error_context = ErrorContext(
            source="get_all_pid_files",
            severity=ErrorSeverity.ERROR,
            error_id="pid_list_error",
            additional_data={"error": str(e)}
        )
        raise ProcessError("Failed to list PID files", error_context) from e 