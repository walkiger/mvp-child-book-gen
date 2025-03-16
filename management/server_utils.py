"""
Server utilities for detecting and managing server processes
"""

import os
import sys
import time
import subprocess
import signal
import platform
import psutil
import socket

from .pid_utils import get_pid, save_pid, is_process_running
from .errors import ServerError, ProcessError, ErrorSeverity, handle_error, setup_logger

# Setup logger
logger = setup_logger()

# Configuration
DEFAULT_BACKEND_PORT = 8080
DEFAULT_FRONTEND_PORT = 3000

def find_server_pid(server_type):
    """Find a server PID by looking for processes using the expected ports
    
    Uses the most effective method for each platform to detect processes
    listening on ports - psutil for cross-platform support and
    platform-specific commands as needed.
    """
    
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

def kill_process(pid):
    """Kill a process reliably using the most effective method for each platform"""
    # For special marker PIDs, just clean up the PID file
    if pid in [88888, 99999]:
        logger.info(f"Process {pid} is a marker for an external window - cannot terminate directly")
        return False
        
    # Try psutil first (cross-platform and reliable)
    try:
        process = psutil.Process(pid)
        
        # Try graceful termination first
        process.terminate()
        
        # Wait briefly for termination
        try:
            process.wait(timeout=2)
        except psutil.TimeoutExpired:
            # Force kill if still running after timeout
            logger.debug(f"Process {pid} did not terminate gracefully, forcing kill")
            process.kill()
            
        # Check if process is gone    
        time.sleep(0.5)  # Brief pause to let OS update process list
        return not psutil.pid_exists(pid)
        
    except psutil.NoSuchProcess:
        # Process already gone
        return True
    
    except psutil.AccessDenied:
        # Try platform-specific approach if psutil fails due to permissions
        logger.warning(f"Access denied when terminating process {pid}, trying platform-specific method")
        
        if platform.system() == "Windows":
            # On Windows, use taskkill (requires admin rights for some processes)
            try:
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
                time.sleep(0.5)
                return not psutil.pid_exists(pid)
            except Exception as e:
                error = ProcessError(f"Could not kill process using taskkill", pid, 
                                    ErrorSeverity.ERROR, str(e))
                handle_error(error)
                return False
        else:
            # On Unix, use kill command
            try:
                os.kill(pid, signal.SIGKILL)
                time.sleep(0.5)
                return not psutil.pid_exists(pid)
            except Exception as e:
                error = ProcessError(f"Could not kill process", pid, 
                                    ErrorSeverity.ERROR, str(e))
                handle_error(error)
                return False
    
    except Exception as e:
        # Handle any other exceptions
        error = ProcessError(f"Error killing process", pid, ErrorSeverity.ERROR, str(e))
        handle_error(error)
        return False

def is_port_in_use(port):
    """Check if a port is in use by any process"""
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

def show_status():
    """Show the status of all servers"""
    from .pid_utils import get_pid, is_process_running
    
    # Check if unified mode might be running
    unified_mode_possible = False
    
    # Get backend server status
    backend_pid = get_pid("backend")
    backend_port = DEFAULT_BACKEND_PORT
    backend_running_by_pid = backend_pid and is_process_running(backend_pid)
    backend_running_by_port = is_port_in_use(backend_port)
    
    if backend_running_by_pid:
        logger.info(f"Backend server is running (PID: {backend_pid}).")
    elif backend_running_by_port:
        logger.info(f"Backend server is running on port {backend_port} (separate window or process).")
        unified_mode_possible = True
    else:
        logger.info("Backend server is not running.")
    
    # Get frontend server status
    frontend_pid = get_pid("frontend")
    frontend_port = DEFAULT_FRONTEND_PORT
    frontend_running_by_pid = frontend_pid and is_process_running(frontend_pid)
    frontend_running_by_port = is_port_in_use(frontend_port)
    
    if frontend_running_by_pid:
        logger.info(f"Frontend server is running (PID: {frontend_pid}).")
    elif frontend_running_by_port:
        logger.info(f"Frontend server is running on port {frontend_port} (separate window or process).")
        unified_mode_possible = True
    else:
        logger.info("Frontend server is not running.")
        
    # Get dashboard server status
    dashboard_pid = get_pid("dashboard")
    dashboard_port = 3001  # Default dashboard port
    dashboard_running_by_pid = dashboard_pid and is_process_running(dashboard_pid)
    dashboard_running_by_port = is_port_in_use(dashboard_port)
    
    if dashboard_running_by_pid:
        logger.info(f"Dashboard server is running (PID: {dashboard_pid}).")
    elif dashboard_running_by_port:
        logger.info(f"Dashboard server is running on port {dashboard_port} (separate window or process).")
        unified_mode_possible = True
    else:
        logger.info("Dashboard server is not running.")
        
    # Add a hint if unified mode is suspected
    if unified_mode_possible:
        logger.info("\nNote: Some servers appear to be running in separate windows or processes.")
        logger.info("PIDs may not be available for servers started in separate windows.") 