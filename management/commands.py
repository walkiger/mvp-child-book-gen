"""
Command implementations for starting and stopping servers
"""

import os
import sys
import time
import sqlite3
import logging
import subprocess
import signal
from pathlib import Path
import json
import traceback
import platform
import threading
import queue
from enum import Enum

try:
    from colorama import init, Fore, Style
    colorama_available = True
except ImportError:
    colorama_available = False

from .pid_utils import save_pid, get_pid, get_pid_file, is_process_running, ensure_pid_dir
from .server_utils import find_server_pid, kill_process, DEFAULT_BACKEND_PORT, DEFAULT_FRONTEND_PORT
# Import error handling from shared utilities
from utils.error_handling import ServerError, DatabaseError, ErrorSeverity, handle_error, setup_logger
# Import local error handling
from .errors import ProcessError, with_error_handling, db_error_handler
from .db_utils import init_db, run_migrations as run_db_migrations

# Setup logger
logger = setup_logger("management.commands", "logs/management.log")

# Error handling
class ErrorSeverity(Enum):
    WARNING = 1
    ERROR = 2
    CRITICAL = 3

class ServerError:
    def __init__(self, message, server, severity=ErrorSeverity.ERROR, details=None):
        self.message = message
        self.server = server
        self.severity = severity
        self.details = details

def handle_error(error, exit_app=False):
    """Handle server errors"""
    if error.severity == ErrorSeverity.WARNING:
        logger.warning(f"{error.server.upper()}: {error.message}")
        if error.details:
            logger.warning(f"Details: {error.details}")
    elif error.severity == ErrorSeverity.ERROR:
        logger.error(f"{error.server.upper()}: {error.message}")
        if error.details:
            logger.error(f"Details: {error.details}")
    elif error.severity == ErrorSeverity.CRITICAL:
        logger.critical(f"{error.server.upper()}: {error.message}")
        if error.details:
            logger.critical(f"Details: {error.details}")
        
    if exit_app:
        logger.info("Exiting due to error.")
        sys.exit(1)

# PID management
def get_pid_file(server_type):
    """Get the path to the PID file for a server type"""
    return os.path.join(os.getcwd(), f"{server_type}.pid")

def save_pid(server_type, pid):
    """Save the PID of a server process"""
    with open(get_pid_file(server_type), "w") as f:
        f.write(str(pid))

def get_pid(server_type):
    """Get the PID of a server process if it exists"""
    pid_file = get_pid_file(server_type)
    if os.path.exists(pid_file):
        try:
            with open(pid_file, "r") as f:
                pid = int(f.read().strip())
                return pid
        except (IOError, ValueError) as e:
            logger.warning(f"Could not read PID file for {server_type}: {e}")
    return None

def remove_pid_file(server_type):
    """Remove the PID file for a server"""
    pid_file = get_pid_file(server_type)
    if os.path.exists(pid_file):
        try:
            os.remove(pid_file)
        except IOError as e:
            logger.warning(f"Could not remove PID file for {server_type}: {e}")
            
def is_pid_running(pid):
    """Check if a PID is running"""
    if pid is None:
        return False
    try:
        if platform.system() == "Windows":
            # Windows implementation
            import psutil
            return psutil.pid_exists(pid)
        else:
            # UNIX implementation
            os.kill(pid, 0)
            return True
    except (ProcessLookupError, PermissionError, ModuleNotFoundError):
        return False

def start_concurrent_mode(args):
    """Run both servers concurrently in the same terminal with color-coded output"""
    # Initialize colorama for cross-platform colored terminal output
    if colorama_available:
        init()
    else:
        logger.warning("colorama not installed. Output will not be color-coded.")
        logger.warning("To install: pip install colorama")
    
    # Check if servers are already running
    if get_pid("backend"):
        logger.info("Backend server is already running.")
        return
    
    if get_pid("frontend"):
        logger.info("Frontend server is already running.")
        return
    
    # Start dashboard if requested
    dashboard_thread = None
    if hasattr(args, 'with_dashboard') and args.with_dashboard:
        try:
            from .dashboard import start_dashboard
            # Start dashboard in a separate thread
            def run_dashboard():
                try:
                    # Import Flask and start the app without using signals
                    from flask import Flask
                    from .dashboard import create_dashboard_app
                    
                    # Save the dashboard PID
                    save_pid("dashboard", os.getpid())
                    
                    dashboard_port = 3001  # Define dashboard_port explicitly
                    app = create_dashboard_app(
                        backend_port=args.backend_port, 
                        frontend_port=args.frontend_port, 
                        dashboard_port=dashboard_port
                    )
                    # Run without using signal handlers
                    app.run(host='0.0.0.0', port=dashboard_port, use_reloader=False, debug=False, threaded=True)
                except Exception as e:
                    logger.error(f"Dashboard error: {str(e)}")
                finally:
                    # Clean up PID file
                    remove_pid_file("dashboard")
            
            logger.info(f"Starting dashboard on port 3001...")
            dashboard_thread = threading.Thread(target=run_dashboard)
            dashboard_thread.daemon = True
            dashboard_thread.start()
            logger.info(f"Dashboard started - visit http://localhost:3001/")
        except ImportError:
            logger.error("Flask is not installed. Cannot start dashboard.")
            logger.error("Install with: pip install flask")
    
    # Create message queues for each server's output
    backend_queue = queue.Queue()
    frontend_queue = queue.Queue()
    stop_event = threading.Event()
    
    # Function to start the backend server and capture its output
    def run_backend():
        cmd = [
            "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", str(args.backend_port)
        ]
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True, 
            bufsize=1,
            universal_newlines=True
        )
        save_pid("backend", process.pid)
        
        try:
            # Process output until the process ends or stop_event is set
            for line in iter(process.stdout.readline, ''):
                if stop_event.is_set():
                    process.terminate()
                    break
                
                if colorama_available:
                    backend_queue.put(f"{Fore.BLUE}[BACKEND] {line.rstrip()}{Style.RESET_ALL}")
                else:
                    backend_queue.put(f"[BACKEND] {line.rstrip()}")
            
            # Clean up when the process ends
            process.wait()
        except Exception as e:
            backend_queue.put(f"[BACKEND] ERROR: {str(e)}")
            process.terminate()
        finally:
            backend_queue.put(None)  # Signal that this process is done
    
    # Function to start the frontend server and capture its output
    def run_frontend():
        frontend_dir = Path("frontend").resolve()
        if not frontend_dir.exists():
            frontend_queue.put("[FRONTEND] ERROR: Frontend directory not found")
            frontend_queue.put(None)  # Signal that this process is done
            return
        
        original_dir = os.getcwd()
        os.chdir(frontend_dir)
        
        # Try to find full path to npm on Windows
        npm_cmd = "npm"
        if platform.system() == "Windows":
            try:
                # Check if npm exists in PATH
                npm_path = subprocess.check_output(["where", "npm"], shell=True).decode('utf-8').split('\n')[0].strip()
                if npm_path:
                    npm_cmd = npm_path
                    frontend_queue.put(f"[FRONTEND] Found npm at: {npm_path}")
            except Exception as e:
                frontend_queue.put(f"[FRONTEND] Warning: Could not find npm in PATH: {str(e)}")
                frontend_queue.put("[FRONTEND] Trying system default npm or using shell=True...")
        
        cmd = [npm_cmd, "run", "dev"]
        try:
            # Try with shell=True for better PATH resolution on Windows
            if platform.system() == "Windows":
                process = subprocess.Popen(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT, 
                    text=True, 
                    bufsize=1,
                    universal_newlines=True,
                    shell=True
                )
            else:
                process = subprocess.Popen(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT, 
                    text=True, 
                    bufsize=1,
                    universal_newlines=True
                )
            
            save_pid("frontend", process.pid)
            
            # Process output until the process ends or stop_event is set
            for line in iter(process.stdout.readline, ''):
                if stop_event.is_set():
                    process.terminate()
                    break
                
                if colorama_available:
                    frontend_queue.put(f"{Fore.GREEN}[FRONTEND] {line.rstrip()}{Style.RESET_ALL}")
                else:
                    frontend_queue.put(f"[FRONTEND] {line.rstrip()}")
            
            # Clean up when the process ends
            process.wait()
        except Exception as e:
            frontend_queue.put(f"[FRONTEND] ERROR: {str(e)}")
            frontend_queue.put(f"[FRONTEND] This may be due to npm not being in your PATH or not being installed.")
            frontend_queue.put(f"[FRONTEND] Check that you can run 'npm --version' from your terminal.")
            if platform.system() == "Windows":
                # Try with a direct shell command as last resort
                try:
                    frontend_queue.put("[FRONTEND] Attempting direct shell command as fallback...")
                    process = subprocess.Popen(
                        "npm run dev", 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.STDOUT, 
                        text=True, 
                        shell=True,
                        cwd=str(frontend_dir)
                    )
                    save_pid("frontend", process.pid)
                    
                    for line in iter(process.stdout.readline, ''):
                        if stop_event.is_set():
                            process.terminate()
                            break
                        
                        if colorama_available:
                            frontend_queue.put(f"{Fore.GREEN}[FRONTEND] {line.rstrip()}{Style.RESET_ALL}")
                        else:
                            frontend_queue.put(f"[FRONTEND] {line.rstrip()}")
                    
                    process.wait()
                except Exception as e2:
                    frontend_queue.put(f"[FRONTEND] ERROR with fallback method: {str(e2)}")
        finally:
            os.chdir(original_dir)
            frontend_queue.put(None)  # Signal that this process is done
    
    # Function to print messages from the queues
    def print_output():
        backend_done = False
        frontend_done = False
        
        try:
            while not (backend_done and frontend_done):
                if stop_event.is_set():
                    break
                
                # Check backend queue
                try:
                    line = backend_queue.get(block=False)
                    if line is None:
                        backend_done = True
                    else:
                        print(line, flush=True)
                except queue.Empty:
                    pass
                
                # Check frontend queue
                try:
                    line = frontend_queue.get(block=False)
                    if line is None:
                        frontend_done = True
                    else:
                        print(line, flush=True)
                except queue.Empty:
                    pass
                
                # Brief pause to prevent CPU spinning
                time.sleep(0.05)
        except KeyboardInterrupt:
            stop_event.set()
            logger.info("Stopping servers...")
    
    # Start all threads
    if colorama_available:
        logger.info(f"Starting both servers in unified terminal mode...")
        logger.info(f"Backend will be shown in {Fore.BLUE}blue{Style.RESET_ALL}, Frontend in {Fore.GREEN}green{Style.RESET_ALL}")
    else:
        logger.info(f"Starting both servers in unified terminal mode...")
        logger.info(f"Backend will be prefixed with [BACKEND], Frontend with [FRONTEND]")
    
    logger.info(f"Press Ctrl+C to stop both servers")
    
    backend_thread = threading.Thread(target=run_backend)
    frontend_thread = threading.Thread(target=run_frontend)
    output_thread = threading.Thread(target=print_output)
    
    backend_thread.daemon = True
    frontend_thread.daemon = True
    output_thread.daemon = True
    
    backend_thread.start()
    frontend_thread.start()
    output_thread.start()
    
    try:
        # Keep the main thread alive until both servers are done or user interrupts
        while (backend_thread.is_alive() or frontend_thread.is_alive()) and not stop_event.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        logger.info("Stopping all servers...")
        stop_event.set()
    
    # Wait for threads to finish
    backend_thread.join(timeout=2)
    frontend_thread.join(timeout=2)
    output_thread.join(timeout=1)
    
    # Clean up PID files
    remove_pid_file("backend")
    remove_pid_file("frontend")
    
    logger.info("All servers stopped.")

def start_backend(args):
    """Start the backend server"""
    # Check if already running
    if get_pid("backend"):
        logger.info("Backend server is already running.")
        return

    logger.info(f"Starting backend server on port {args.backend_port}...")
    
    # Construct the command
    cmd = [
        "uvicorn", 
        "app.main:app", 
        "--reload", 
        "--host", "0.0.0.0", 
        "--port", str(args.backend_port)
    ]
    
    # Start the process (regular mode)
    try:
        if args.detach:
            # Detached mode - redirect output to log file
            os.makedirs("logs", exist_ok=True)
            log_file = os.path.join("logs", "backend.log")
            
            with open(log_file, 'a') as log:
                kwargs = {}
                if platform.system() == "Windows":
                    kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
                
                process = subprocess.Popen(
                    cmd,
                    stdout=log,
                    stderr=log,
                    **kwargs
                )
                
            save_pid("backend", process.pid)
            logger.info(f"Backend server started in detached mode (PID: {process.pid}).")
            logger.info(f"Logs are being written to {log_file}")
            
        elif args.use_ide_terminal:
            # For IDE terminal integration - display commands for IDE terminal tabs
            logger.info("\n========== TERMINAL 1: BACKEND SERVER ==========")
            logger.info("Open a terminal tab in your IDE and run this command:")
            
            # Format the command
            cmd_str = " ".join([f'"{c}"' if ' ' in str(c) else str(c) for c in cmd])
            
            # Show command in an easy-to-copy format
            logger.info("-----------------------------------------------")
            logger.info(f"{cmd_str}")
            logger.info("-----------------------------------------------")
            logger.info(f"After starting, access backend at http://localhost:{args.backend_port}/api")
            logger.info("==================================================\n")
            
            return
        else:
            # Interactive mode - use a separate window on Windows
            if platform.system() == "Windows":
                # For Windows, open in a new terminal window
                cmd_str = " ".join([f'"{c}"' if ' ' in str(c) else str(c) for c in cmd])
                window_title = "Backend Server - Child Book Generator"
                
                # Open a new terminal window with the command
                logger.info("Starting backend server in a new terminal window...")
                os.system(f'start "Backend Server" cmd /k "title {window_title} && {cmd_str}"')
                
                # Save a special marker PID - we can't get the actual PID but use a marker
                save_pid("backend", 88888)
                logger.info("Backend server started in a separate window.")
                logger.info(f"Access backend at http://localhost:{args.backend_port}/api")
            else:
                # Regular behavior for non-Windows platforms
                process = subprocess.Popen(cmd)
                save_pid("backend", process.pid)
                logger.info(f"Backend server started (PID: {process.pid}).")
                
                # If not starting the frontend, wait for the backend
                if not args.frontend:
                    try:
                        process.wait()
                    except KeyboardInterrupt:
                        process.terminate()
                        logger.info("Backend server stopped.")
    except (subprocess.SubprocessError, OSError) as e:
        error = ServerError(f"Failed to start backend server", "backend", 
                          ErrorSeverity.ERROR, str(e))
        handle_error(error, exit_app=True)

def start_frontend(args):
    """Start the frontend server"""
    # Check if already running
    if get_pid("frontend"):
        logger.info("Frontend server is already running.")
        return

    logger.info(f"Starting frontend server on port {args.frontend_port}...")
    
    # Change to the frontend directory
    frontend_dir = Path("frontend").resolve()
    
    if not frontend_dir.exists():
        error = ServerError(f"Frontend directory not found at {frontend_dir}", "frontend", 
                          ErrorSeverity.ERROR)
        handle_error(error, exit_app=True)
    
    # Remember current directory to restore later
    original_dir = os.getcwd()
    
    # Regular operation when not using separate terminals
    os.chdir(frontend_dir)
    
    # Check for package.json
    if not os.path.exists("package.json"):
        os.chdir(original_dir)
        error = ServerError("No package.json found in frontend directory", "frontend", 
                          ErrorSeverity.ERROR, 
                          f"This doesn't appear to be a valid Node.js project directory: {frontend_dir}")
        handle_error(error, exit_app=True)
    
    # Try to find full paths to executables on Windows
    npm_path = "npm"
    yarn_path = "yarn"
    
    if platform.system() == "Windows":
        try:
            npm_path = subprocess.check_output(["where", "npm"], shell=True).decode('utf-8').split('\n')[0].strip()
            logger.info(f"Found npm at: {npm_path}")
        except Exception as e:
            logger.warning(f"Could not find npm: {str(e)}")
            
        try:
            yarn_path = subprocess.check_output(["where", "yarn"], shell=True).decode('utf-8').split('\n')[0].strip()
            logger.info(f"Found yarn at: {yarn_path}")
        except Exception as e:
            logger.warning(f"Could not find yarn: {str(e)}")
    
    # Determine if we're using npm or yarn
    use_yarn = os.path.exists("yarn.lock")

    # For IDE terminal mode
    if args.use_ide_terminal:
        # For IDE terminal integration - display commands for IDE terminal tabs
        logger.info("\n========== TERMINAL 2: FRONTEND SERVER ==========")
        logger.info("Open another terminal tab in your IDE and run this command:")
        
        # Format the command based on npm or yarn
        if use_yarn:
            cmd_str = f'cd "{frontend_dir}" && yarn dev'
        else:
            cmd_str = f'cd "{frontend_dir}" && npm run dev'
        
        # Show command in an easy-to-copy format
        logger.info("-----------------------------------------------")
        logger.info(f"{cmd_str}")
        logger.info("-----------------------------------------------")
        logger.info(f"After starting, access frontend at http://localhost:{args.frontend_port}")
        logger.info("==================================================\n")
        
        # Return to original directory
        os.chdir(original_dir)
        return

    # For Windows, use a direct shell command
    if platform.system() == "Windows":
        try:
            # Change back to original directory right away before starting the new process
            os.chdir(original_dir)
            
            # Format the command for Windows CMD
            if use_yarn:
                cmd = f'cd "{frontend_dir}" && "{yarn_path}" dev'
            else:
                cmd = f'cd "{frontend_dir}" && "{npm_path}" run dev'
                
            logger.info(f"Command for frontend: {cmd}")
            
            if args.detach:
                # Detached mode - redirect output to log file
                os.makedirs("logs", exist_ok=True)
                log_file = os.path.join("logs", "frontend.log")
                
                with open(log_file, 'a') as log:
                    process = subprocess.Popen(
                        ["start", "cmd", "/c", cmd],
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                
                # We can't get the actual PID of the cmd window, but we can save a placeholder
                save_pid("frontend", 99999)
                logger.info("Frontend server started in detached mode.")
                logger.info(f"Logs are being written to {log_file}")
            else:
                # Interactive mode - open in a new terminal window
                window_title = "Frontend Server - Child Book Generator"
                logger.info("Starting frontend server in a new terminal window...")
                
                # The /K flag keeps the window open after the command executes
                os.system(f'start "Frontend Server" cmd /k "title {window_title} && {cmd}"')
                
                # Save a special marker PID - we can't get the actual PID in this case
                save_pid("frontend", 99999)
                logger.info("Frontend server started in a separate window.")
                logger.info(f"Access frontend at http://localhost:{args.frontend_port}")
            
            return
        except Exception as e:
            logger.error(f"Failed to start frontend using shell command: {str(e)}")
            # Fall back to regular method

    # Construct the command (for non-Windows platforms or fallback)
    if use_yarn:
        cmd = ["yarn", "dev"]
    else:
        cmd = ["npm", "run", "dev"]
        
    # Start the process
    try:
        if args.detach:
            # Detached mode - redirect output to log file
            os.makedirs("logs", exist_ok=True)
            log_file = os.path.join(original_dir, "logs", "frontend.log")
            
            with open(log_file, 'a') as log:
                process = subprocess.Popen(
                    cmd,
                    stdout=log,
                    stderr=log
                )
                
            save_pid("frontend", process.pid)
            logger.info(f"Frontend server started in detached mode (PID: {process.pid}).")
            logger.info(f"Logs are being written to {log_file}")
        else:
            # Interactive mode
            process = subprocess.Popen(cmd)
            save_pid("frontend", process.pid)
            logger.info(f"Frontend server started (PID: {process.pid}).")
            
            # If not starting the backend, wait for the frontend
            if not args.backend:
                try:
                    process.wait()
                except KeyboardInterrupt:
                    process.terminate()
                    logger.info("Frontend server stopped.")
    except (subprocess.SubprocessError, OSError) as e:
        error = ServerError(f"Failed to start frontend server", "frontend", 
                          ErrorSeverity.ERROR, str(e))
        handle_error(error, exit_app=True)
    finally:
        # Restore original directory
        os.chdir(original_dir)

@with_error_handling(context="Server Stop", exit_on_error=True)
def stop_server(server_type, force=False):
    """Stop a server by finding and killing its process"""
    # Find the server PID
    pid = find_server_pid(server_type)
    
    if not pid:
        logger.info(f"{server_type.capitalize()} server is not running.")
        return
    
    # Special handling for frontend running in an external window on Windows
    if server_type == "frontend" and pid == 99999:
        logger.info("Frontend server is running in an external window.")
        logger.info("Please close the frontend server window manually.")
        
        # Clean up PID file
        pid_file = get_pid_file(server_type)
        if os.path.exists(pid_file):
            try:
                os.remove(pid_file)
                logger.info("Removed frontend PID marker file.")
            except OSError as e:
                logger.warning(f"Failed to remove PID file: {str(e)}")
        return
    
    # Special handling for backend running in an external window on Windows
    if server_type == "backend" and pid == 88888:
        logger.info("Backend server is running in an external window.")
        logger.info("Please close the backend server window manually.")
        
        # Clean up PID file
        pid_file = get_pid_file(server_type)
        if os.path.exists(pid_file):
            try:
                os.remove(pid_file)
                logger.info("Removed backend PID marker file.")
            except OSError as e:
                logger.warning(f"Failed to remove PID file: {str(e)}")
        return
    
    logger.info(f"Stopping {server_type} server (PID: {pid})...")
    
    try:
        # Attempt to kill the process
        success = kill_process(pid)
        
        if success:
            logger.info(f"{server_type.capitalize()} server stopped.")
            
            # Clean up PID file if kill was successful
            pid_file = get_pid_file(server_type)
            if os.path.exists(pid_file):
                try:
                    os.remove(pid_file)
                except OSError as e:
                    logger.warning(f"Failed to remove PID file: {str(e)}")
        else:
            raise ServerError(f"Failed to stop server", server_type, 
                            ErrorSeverity.ERROR,
                            f"Process {pid} could not be terminated")
    except Exception as e:
        raise ServerError(f"Error stopping server", server_type, 
                        ErrorSeverity.ERROR, str(e))

@with_error_handling(context="Server Restart", exit_on_error=True)
def restart_server(server_type, args):
    """Restart a server by stopping and starting it"""
    logger.info(f"Restarting {server_type} server...")
    
    # Stop the server
    stop_server(server_type)
    
    # Brief pause to ensure processes are fully terminated
    time.sleep(1)
    
    # Start the server based on type
    if server_type == "backend":
        start_backend(args)
    elif server_type == "frontend":
        start_frontend(args)
    else:
        raise ValueError(f"Unknown server type: {server_type}")
        
    logger.info(f"{server_type.capitalize()} server restarted.")

@with_error_handling(context="Database Init", exit_on_error=False)
def run_db_init():
    """Initialize the database schema"""
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully.")
        return True
    except Exception as e:
        raise DatabaseError("Failed to initialize database", 
                          severity=ErrorSeverity.ERROR, 
                          details=str(e))
        return False

@with_error_handling(context="Database Migrations", exit_on_error=False)
def run_migrations():
    """Run database migrations"""
    try:
        logger.info("Running database migrations...")
        run_db_migrations()
        logger.info("Database migrations completed successfully.")
        return True
    except Exception as e:
        raise DatabaseError("Failed to run database migrations", 
                          severity=ErrorSeverity.ERROR, 
                          details=str(e))
        return False

@with_error_handling(context="Database Structure Check", exit_on_error=True)
def check_db_structure(db_path=None, verbose=False):
    """Check the database structure"""
    try:
        from .db_inspection import check_db_structure as inspect_structure
        
        logger.info("Checking database structure...")
        try:
            result = inspect_structure(db_path)
            logger.info("Database structure check completed.")
            return True
        except FileNotFoundError as e:
            db_file = db_path or "storybook.db"
            raise DatabaseError(f"Failed to check database structure - {str(e)}", 
                             db_path=db_file,
                             severity=ErrorSeverity.ERROR)
            return False
    except ImportError:
        raise DatabaseError("Failed to import db_inspection module", 
                          severity=ErrorSeverity.ERROR)
        return False

@with_error_handling(context="Database Exploration", exit_on_error=False)
def explore_db_contents(db_path=None):
    """Explore the database contents"""
    try:
        from .db_inspection import explore_db_contents as explore_contents
        
        logger.info("Exploring database contents...")
        result = explore_contents(db_path)
        
        if result is False:
            db_file = db_path or "storybook.db"
            raise DatabaseError(f"Database file not found or empty", 
                             db_path=db_file,
                             severity=ErrorSeverity.ERROR)
            return False
                             
        logger.info("Database exploration completed.")
        return True
    except ImportError:
        raise DatabaseError("Failed to import db_inspection module", 
                          severity=ErrorSeverity.ERROR)
        return False
    except Exception as e:
        raise DatabaseError("Failed to explore database contents", 
                          db_path=db_path,
                          severity=ErrorSeverity.ERROR, 
                          details=str(e))
        return False

@with_error_handling(context="Database Dump", exit_on_error=False)
def dump_db_to_file(db_path=None, output_file="db_dump.txt"):
    """Dump the database contents to a file"""
    try:
        from .db_inspection import dump_db_to_file as dump_database
        
        logger.info(f"Dumping database to {output_file}...")
        result = dump_database(db_path, output_file)
        
        if result is False:
            db_file = db_path or "storybook.db"
            raise DatabaseError(f"Database file not found or could not be dumped", 
                             db_path=db_file,
                             severity=ErrorSeverity.ERROR)
            return False
                             
        logger.info("Database dump completed.")
        return True
    except ImportError:
        raise DatabaseError("Failed to import db_inspection module", 
                          severity=ErrorSeverity.ERROR)
    except Exception as e:
        raise DatabaseError("Failed to dump database", 
                          db_path=db_path,
                          severity=ErrorSeverity.ERROR, 
                          details=str(e))
        return False

@with_error_handling(context="Character Check", exit_on_error=False)
def check_characters(db_path=None):
    """Check character information in the database"""
    try:
        from .content_inspection import check_characters as inspect_chars
        
        logger.info("Checking character information...")
        result = inspect_chars(db_path)
        
        if result is False:
            db_file = db_path or "storybook.db"
            raise DatabaseError(f"Database file not found or no character data available", 
                             db_path=db_file,
                             severity=ErrorSeverity.ERROR)
            return False
                             
        logger.info("Character check completed.")
        return True
    except ImportError:
        raise DatabaseError("Failed to import content_inspection module", 
                          severity=ErrorSeverity.ERROR)
        return False
    except Exception as e:
        raise DatabaseError("Failed to check character information", 
                          db_path=db_path,
                          severity=ErrorSeverity.ERROR, 
                          details=str(e))
        return False

@with_error_handling(context="Image Check", exit_on_error=False)
def check_images(db_path=None):
    """Check image information in the database"""
    try:
        from .content_inspection import check_images as inspect_images
        
        logger.info("Checking image information...")
        result = inspect_images(db_path)
        
        if result is False:
            db_file = db_path or "storybook.db"
            raise DatabaseError(f"Database file not found or no image data available", 
                             db_path=db_file,
                             severity=ErrorSeverity.ERROR)
            return False
                             
        logger.info("Image check completed.")
        return True
    except ImportError:
        raise DatabaseError("Failed to import content_inspection module", 
                          severity=ErrorSeverity.ERROR)
        return False
    except Exception as e:
        raise DatabaseError("Failed to check image information", 
                          db_path=db_path,
                          severity=ErrorSeverity.ERROR, 
                          details=str(e))
        return False 