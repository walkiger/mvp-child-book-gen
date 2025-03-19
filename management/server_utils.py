"""
Server utilities for managing server processes
"""

import os
import sys
import signal
import psutil
import platform
import time
import socket
import subprocess
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
from uuid import uuid4

from app.core.errors.base import ErrorContext, ErrorSeverity
from app.core.errors.management import (
    ServerError,
    ProcessError,
    with_management_error_handling
)
from app.core.logging import setup_logger

from .pid_utils import get_pid, save_pid, is_process_running

# Setup logger only if it doesn't exist
logger = logging.getLogger("management.server_utils")
if not logger.handlers:
    logger = setup_logger(
        name="management.server_utils",
        level="INFO",
        log_file="logs/management.log"
    )

# Default ports
DEFAULT_BACKEND_PORT = 8080
DEFAULT_FRONTEND_PORT = 3000

async def is_port_in_use(port: int) -> bool:
    """Check if a port is in use by any process"""
    try:
        # Try socket connection first
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                result = s.connect_ex(('localhost', port))
                if result == 0:
                    return True
        except:
            pass
            
        # Try HTTP request as fallback for web servers
        try:
            import urllib.request
            urllib.request.urlopen(f"http://localhost:{port}", timeout=0.5)
            return True
        except:
            pass
            
        # Try platform-specific commands as last resort
        if platform.system() == "Windows":
            try:
                output = subprocess.check_output(
                    f"netstat -ano | findstr :{port}", 
                    shell=True, 
                    stderr=subprocess.DEVNULL
                ).decode('utf-8')
                return len(output.strip()) > 0
            except:
                pass
                
        return False
        
    except Exception as e:
        raise ServerError(
            message=f"Failed to check if port {port} is in use",
            context=ErrorContext(
                source="management.server_utils.is_port_in_use",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={
                    "port": port,
                    "error": str(e)
                }
            )
        )

@with_management_error_handling
async def show_status():
    """Show the status of all servers"""
    try:
        # Get backend server status
        backend_pid = get_pid("backend")
        backend_port = DEFAULT_BACKEND_PORT
        
        # Get frontend server status
        frontend_pid = get_pid("frontend")
        frontend_port = DEFAULT_FRONTEND_PORT
        
        # Get dashboard status
        dashboard_pid = get_pid("dashboard")
        
        # Build status message
        status_lines = []
        
        # Check backend status
        if backend_pid and is_process_running(backend_pid):
            status_lines.append(f"Backend server is running (PID: {backend_pid}).")
        else:
            # Check if process is running on port
            port_pid = find_server_pid("backend")
            if port_pid:
                status_lines.append(f"Backend server is running (PID: {port_pid}).")
                # Update PID file if needed
                if port_pid != backend_pid:
                    save_pid("backend", port_pid)
            else:
                status_lines.append("Backend server is not running.")
            
        # Check frontend status
        if frontend_pid and is_process_running(frontend_pid):
            status_lines.append(f"Frontend server is running (PID: {frontend_pid}).")
        else:
            # Check if process is running on port
            port_pid = find_server_pid("frontend")
            if port_pid:
                status_lines.append(f"Frontend server is running (PID: {port_pid}).")
                # Update PID file if needed
                if port_pid != frontend_pid:
                    save_pid("frontend", port_pid)
            else:
                status_lines.append("Frontend server is not running.")
            
        # Check dashboard status
        if dashboard_pid and is_process_running(dashboard_pid):
            status_lines.append(f"Dashboard server is running (PID: {dashboard_pid}).")
        else:
            status_lines.append("Dashboard server is not running.")
        
        # Log all status lines at once
        for line in status_lines:
            logger.info(line)
            
        return True
    except Exception as e:
        raise ServerError(
            message=f"Failed to check server status: {str(e)}",
            context=ErrorContext(
                source="management.server_utils.show_status",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"error": str(e)}
            )
        )

@with_management_error_handling
def find_server_pid(server_type):
    """Find a server PID by looking for processes using the expected ports
    
    Uses the most effective method for each platform to detect processes
    listening on ports - psutil for cross-platform support and
    platform-specific commands as needed.
    """
    try:
        # Determine which port to check based on server type
        if server_type == "backend":
            port = DEFAULT_BACKEND_PORT
        else:  # frontend
            port = DEFAULT_FRONTEND_PORT
        
        # Check for special marker PIDs used for Windows external windows
        pid = get_pid(server_type)
        if pid:
            # Special handling for Windows servers running in separate windows
            if server_type == "frontend" and pid == 99999:
                return pid
            if server_type == "backend" and pid == 88888:
                return pid
            
            # For regular PIDs, verify process is still running
            if is_process_running(pid):
                return pid

        # On Windows, use netstat (reliable and commonly available)
        if platform.system() == "Windows":
            try:
                netstat_cmd = f"netstat -ano | findstr :{port} | findstr LISTENING"
                output = subprocess.check_output(
                    netstat_cmd,
                    shell=True,
                    stderr=subprocess.DEVNULL
                ).decode('utf-8', errors='ignore')

                for line in output.strip().split('\n'):
                    if line.strip():
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            try:
                                pid = int(parts[-1])
                                if is_process_running(pid):
                                    save_pid(server_type, pid)
                                    return pid
                            except (ValueError, IndexError):
                                continue
                
                # No process found listening on the port
                return None
            except subprocess.CalledProcessError:
                # Command failed, likely no process on that port
                return None
                
        # On Unix-like systems, use lsof (preferred) or psutil as fallback
        else:
            try:
                # Use lsof on Unix-like systems (very reliable)
                lsof_cmd = f"lsof -i :{port} -sTCP:LISTEN -t"
                output = subprocess.check_output(
                    lsof_cmd,
                    shell=True,
                    stderr=subprocess.DEVNULL
                ).decode('utf-8', errors='ignore')
                
                if output.strip():
                    pid = int(output.strip().split('\n')[0])
                    if is_process_running(pid):
                        save_pid(server_type, pid)
                        return pid
                        
                # No process found with lsof
                return None
            except (subprocess.CalledProcessError, ValueError):
                # Fallback to psutil if lsof fails or isn't available
                try:
                    for conn in psutil.net_connections(kind='inet'):
                        if conn.laddr.port == port and conn.status == 'LISTEN':
                            pid = conn.pid
                            if is_process_running(pid):
                                save_pid(server_type, pid)
                                return pid
                except (psutil.AccessDenied, psutil.Error):
                    pass
                    
                # No process found
                return None
                
    except Exception as e:
        raise ServerError(
            message=f"Failed to find {server_type} server PID",
            context=ErrorContext(
                source="management.server_utils.find_server_pid",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={
                    "server_type": server_type,
                    "error": str(e)
                }
            )
        )

@with_management_error_handling
def kill_process(pid: int) -> bool:
    """Kill a process by its PID.
    
    Args:
        pid: Process ID to kill
        
    Returns:
        bool: True if process was killed or doesn't exist, False if process couldn't be killed
    """
    try:
        # Don't kill marker PIDs
        if pid in [99999, 88888]:
            return False

        # Check if process exists
        if not psutil.pid_exists(pid):
            return True  # Process doesn't exist, consider it "killed"

        try:
            process = psutil.Process(pid)
            
            # Try graceful shutdown first
            logger.info(f"Attempting graceful shutdown of process {pid}")
            process.terminate()
            
            try:
                process.wait(timeout=5)  # Wait up to 5 seconds for graceful shutdown
                return True
            except psutil.TimeoutExpired:
                # Graceful shutdown timed out, force kill
                logger.warning(f"Graceful shutdown timed out for process {pid}, forcing kill")
                process.kill()
                return True

        except psutil.NoSuchProcess:
            return True  # Process doesn't exist anymore
        except psutil.AccessDenied:
            # Try platform-specific force kill for privileged processes
            try:
                if platform.system() == "Windows":
                    subprocess.run(
                        ["taskkill", "/F", "/PID", str(pid)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                else:
                    os.kill(pid, signal.SIGKILL)
                return True
            except (subprocess.SubprocessError, OSError) as e:
                raise ProcessError(
                    message=f"Process {pid} could not be killed",
                    context=ErrorContext(
                        source="management.server_utils.kill_process",
                        severity=ErrorSeverity.ERROR,
                        timestamp=datetime.now(UTC),
                        error_id=str(uuid4()),
                        additional_data={
                            "pid": pid,
                            "error": str(e)
                        }
                    )
                )
        except Exception as e:
            raise ProcessError(
                message=f"Error killing process {pid}",
                context=ErrorContext(
                    source="management.server_utils.kill_process",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "pid": pid,
                        "error": str(e)
                    }
                )
            )
            
    except Exception as e:
        raise ProcessError(
            message=f"Error killing process {pid}",
            context=ErrorContext(
                source="management.server_utils.kill_process",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={
                    "pid": pid,
                    "error": str(e)
                }
            )
        ) 