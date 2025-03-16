"""
PID file utilities for managing server processes
"""

import os
import psutil
import platform
from pathlib import Path
from typing import Optional, List
import time

from .errors import ProcessError, ErrorSeverity, handle_error, setup_logger, with_error_handling

# Setup logger
logger = setup_logger()

# Configuration
PID_DIR = ".pids"

@with_error_handling(context="PID Directory")
def ensure_pid_dir():
    """Ensure the PID directory exists"""
    try:
        pid_dir = Path(PID_DIR)
        pid_dir.mkdir(exist_ok=True)
        return str(pid_dir)
    except OSError as e:
        raise ProcessError(f"Failed to create PID directory", 
                         severity=ErrorSeverity.ERROR, 
                         details=str(e))

def get_pid_file(server_type):
    """Get the path to the PID file for a server type"""
    pid_dir = ensure_pid_dir()
    return os.path.join(pid_dir, f"{server_type}.pid")

def is_process_running(pid):
    """Check if a process with the given PID is running"""
    try:
        # Special handling for marker PIDs
        if pid == 99999 or pid == 88888:
            return True
            
        # Special handling for locked PID files
        if pid == -1:
            return True
        
        # Check if the process exists
        process = psutil.Process(pid)
        
        # Check if the process is a zombie or has terminated
        if process.status() == psutil.STATUS_ZOMBIE:
            return False
            
        return True
    except psutil.NoSuchProcess:
        return False
    except psutil.AccessDenied:
        # If we can't access the process, it probably exists
        return True
    except Exception:
        return False

@with_error_handling(context="PID Save")
def save_pid(server_type, pid):
    """Save the PID of a server process"""
    try:
        pid_file = get_pid_file(server_type)
        
        # On Windows, try with a .new suffix if the original file is locked
        if platform.system() == "Windows":
            try:
                with open(pid_file, 'w') as f:
                    f.write(str(pid))
            except OSError as e:
                # If the file is locked, try with a temporary file
                if e.errno == 13 or "[WinError 32]" in str(e):  # Permission denied or file in use
                    alternate_pid_file = f"{pid_file}.new"
                    with open(alternate_pid_file, 'w') as f:
                        f.write(str(pid))
                    logger.debug(f"Saved PID {pid} for {server_type} server to alternate file {alternate_pid_file}")
                    return
                else:
                    raise
        else:
            # Non-Windows systems
            with open(pid_file, 'w') as f:
                f.write(str(pid))
                
        logger.debug(f"Saved PID {pid} for {server_type} server")
    except OSError as e:
        raise ProcessError(f"Failed to save PID file for {server_type} server", 
                         pid=pid, 
                         severity=ErrorSeverity.ERROR, 
                         details=str(e))

@with_error_handling(context="PID Retrieval")
def get_pid(server_type):
    """Get the PID of a running server process"""
    pid_file = get_pid_file(server_type)
    alternate_pid_file = f"{pid_file}.new"
    
    # On Windows, check alternate file first if it exists
    if platform.system() == "Windows" and os.path.exists(alternate_pid_file):
        try:
            with open(alternate_pid_file, 'r') as f:
                content = f.read().strip()
                try:
                    pid = int(content)
                    # For special marker PIDs like 99999, always return them
                    if pid == 99999:
                        return pid
                    
                    if is_process_running(pid):
                        return pid
                    else:
                        # Clean up stale PID file
                        logger.debug(f"Process {pid} for {server_type} server is not running, removing alternate PID file")
                        try:
                            os.remove(alternate_pid_file)
                        except OSError:
                            pass
                except ValueError:
                    # Clean up invalid PID file
                    logger.warning(f"Invalid PID in alternate file for {server_type} server, removing file")
                    try:
                        os.remove(alternate_pid_file)
                    except OSError:
                        pass
        except OSError as e:
            logger.warning(f"Error reading alternate PID file for {server_type} server: {str(e)}")
    
    # Check standard PID file
    if not os.path.exists(pid_file):
        return None
    
    try:
        with open(pid_file, 'r') as f:
            content = f.read().strip()
            try:
                pid = int(content)
                if is_process_running(pid):
                    return pid
                else:
                    # Clean up stale PID file
                    logger.debug(f"Process {pid} for {server_type} server is not running, removing PID file")
                    os.remove(pid_file)
                    return None
            except ValueError:
                # Clean up invalid PID file
                logger.warning(f"Invalid PID in file for {server_type} server, removing file")
                try:
                    os.remove(pid_file)
                except OSError as e:
                    logger.debug(f"Failed to remove invalid PID file: {str(e)}")
                return None
    except (ValueError, OSError) as e:
        # Clean up invalid PID file
        logger.warning(f"Error reading PID file for {server_type} server: {str(e)}")
        try:
            os.remove(pid_file)
        except OSError:
            pass
        return None

@with_error_handling(context="PID Cleanup")
def cleanup_pid_files():
    """Clean up stale PID files"""
    pid_files = get_all_pid_files()
    
    for pid_file in pid_files:
        try:
            # If file is locked (in use), try to wait a bit and retry a few times
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Try to remove the file
                    os.remove(pid_file)
                    logger.info(f"Removed PID file: {pid_file}")
                    break
                except PermissionError:
                    if attempt < max_retries - 1:
                        logger.info(f"PID file is locked, waiting to retry: {pid_file}")
                        time.sleep(1)  # Wait before retrying
                    else:
                        logger.warning(f"Could not remove locked PID file after {max_retries} attempts: {pid_file}")
                except Exception as e:
                    logger.warning(f"Error removing PID file {pid_file}: {str(e)}")
                    break
        except Exception as e:
            logger.warning(f"Error processing PID file {pid_file}: {str(e)}")
    
    # Try to recreate an empty PID directory
    ensure_pid_dir()

def get_all_pid_files() -> List[str]:
    """Get a list of all PID files"""
    pid_dir = ensure_pid_dir()
    if not os.path.exists(pid_dir):
        return []
        
    return [os.path.join(pid_dir, f) for f in os.listdir(pid_dir) if f.endswith('.pid')] 