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
from typing import Optional, Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor, Future

try:
    from colorama import init, Fore, Style
    colorama_available = True
except ImportError:
    colorama_available = False

from .pid_utils import save_pid, get_pid, get_pid_file, is_process_running, ensure_pid_dir
from .server_utils import find_server_pid, kill_process, DEFAULT_BACKEND_PORT, DEFAULT_FRONTEND_PORT
# Import new error handling
from app.core.errors.management import (
    ServerError, ProcessError, CommandError, with_management_error_handling
)
from app.core.errors.base import ErrorContext, ErrorSeverity
from app.core.errors.database import DatabaseError
from .db_utils import init_db, run_migrations as run_db_migrations
from app.core.logging import setup_logger

# Setup logger only if it doesn't exist
logger = logging.getLogger("management.commands")
if not logger.handlers:
    logger = setup_logger(
        name="management.commands",
        level="INFO",
        log_file="logs/management.log"
    )

def handle_error(error, exit_app=False):
    """Handle server errors with standardized error context"""
    error_context = ErrorContext(
        source="management",
        severity=error.error_context.severity if hasattr(error, 'error_context') else ErrorSeverity.ERROR,
        timestamp=error.error_context.timestamp if hasattr(error, 'error_context') else None,
        error_id=error.error_context.error_id if hasattr(error, 'error_context') else None,
        additional_data=error.error_context.additional_data if hasattr(error, 'error_context') else {}
    )
    
    if error_context.severity == ErrorSeverity.WARNING:
        logger.warning(str(error))
    elif error_context.severity == ErrorSeverity.ERROR:
        logger.error(str(error))
    elif error_context.severity == ErrorSeverity.CRITICAL:
        logger.critical(str(error))
        
    if exit_app:
        logger.info("Exiting due to error.")
        sys.exit(1)

@with_management_error_handling
async def start_concurrent_mode(args):
    """Run both servers concurrently in the same terminal with color-coded output"""
    # Initialize colorama for cross-platform colored terminal output
    if colorama_available:
        init()
    else:
        logger.warning("colorama not installed. Output will not be color-coded.")
        logger.warning("To install: pip install colorama")
    
    # Check if servers are already running
    if get_pid("backend"):
        raise ServerError("Backend server is already running", server="backend")
    
    if get_pid("frontend"):
        raise ServerError("Frontend server is already running", server="frontend")
    
    if args.detach:
        # For detached mode, open a new terminal window
        current_dir = os.getcwd()
        venv_path = os.path.join(current_dir, '.venv')
        
        if platform.system() == "Darwin":  # macOS
            # Create the command that will run in the new terminal
            # First activate venv, then run the servers
            cmd = f"cd '{current_dir}' && "
            cmd += f"source .venv/bin/activate && "
            cmd += "python3 -m management.main start --unified-mode"  # Run without detach flag in the new terminal
            
            # Open new terminal with the command
            terminal_cmd = [
                "osascript",
                "-e",
                f'tell application "Terminal" to do script "{cmd}"'
            ]
            
            try:
                subprocess.run(terminal_cmd, check=True)
                logger.info("Servers started in a new terminal window.")
                return
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to open new terminal window: {str(e)}")
                # Fall back to regular mode if terminal creation fails
                logger.warning("Falling back to regular unified mode...")
        
        elif platform.system() == "Windows":
            # Escape any spaces in the path for Windows
            current_dir_escaped = current_dir.replace(" ", "^ ")
            venv_activate = os.path.join(current_dir_escaped, '.venv', 'Scripts', 'activate.bat')
            
            # Create the command that will run in the new terminal
            cmd = f"cd /d {current_dir_escaped} && "
            cmd += f"call {venv_activate} && "
            cmd += "python -m management.main start --unified-mode"  # Run without detach flag in the new terminal
            
            try:
                # On Windows, we use 'start' command to open a new CMD window
                subprocess.Popen(
                    f'start cmd /k "{cmd}"',
                    shell=True,
                    cwd=current_dir
                )
                logger.info("Servers started in a new terminal window.")
                return
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to open new terminal window: {str(e)}")
                # Fall back to regular mode if terminal creation fails
                logger.warning("Falling back to regular unified mode...")
        
        else:  # Linux or other Unix-like systems
            # Try to detect the available terminal emulator
            terminals = ["gnome-terminal", "xterm", "konsole"]
            terminal_found = None
            
            for term in terminals:
                try:
                    subprocess.run(["which", term], check=True, capture_output=True)
                    terminal_found = term
                    break
                except subprocess.CalledProcessError:
                    continue
            
            if terminal_found:
                # Create the command that will run in the new terminal
                cmd = f"cd '{current_dir}' && "
                cmd += f"source .venv/bin/activate && "
                cmd += "python3 -m management.main start --unified-mode"  # Run without detach flag in the new terminal
                
                try:
                    if terminal_found == "gnome-terminal":
                        subprocess.Popen(["gnome-terminal", "--", "bash", "-c", f"{cmd}; exec bash"])
                    elif terminal_found == "konsole":
                        subprocess.Popen(["konsole", "-e", f"bash -c '{cmd}; exec bash'"])
                    else:  # xterm
                        subprocess.Popen(["xterm", "-e", f"bash -c '{cmd}; exec bash'"])
                    
                    logger.info("Servers started in a new terminal window.")
                    return
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to open new terminal window: {str(e)}")
                    # Fall back to regular mode if terminal creation fails
                    logger.warning("Falling back to regular unified mode...")
            else:
                logger.warning("No suitable terminal emulator found. Falling back to regular unified mode...")
    
    # If detached mode failed or not requested, continue with regular unified mode
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

        # Set up detached process flags based on platform
        if args.detach:
            if platform.system() == "Windows":
                creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    creationflags=creationflags
                )
            else:
                # On Unix-like systems, use nohup but keep output visible
                cmd = ["nohup"] + cmd
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    preexec_fn=os.setpgrp
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
                npm_path = subprocess.check_output(["where", "npm"], shell=True).decode('utf-8').split('\n')[0].strip()
                if npm_path:
                    npm_cmd = npm_path
                    frontend_queue.put(f"[FRONTEND] Found npm at: {npm_path}")
            except Exception as e:
                frontend_queue.put(f"[FRONTEND] Warning: Could not find npm in PATH: {str(e)}")
                frontend_queue.put("[FRONTEND] Trying system default npm or using shell=True...")
        
        cmd = [npm_cmd, "run", "dev"]

        try:
            # Set up detached process flags based on platform
            if args.detach:
                if platform.system() == "Windows":
                    creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        universal_newlines=True,
                        cwd=str(frontend_dir),
                        creationflags=creationflags,
                        shell=True
                    )
                else:
                    # On Unix-like systems, use nohup but keep output visible
                    cmd = ["nohup"] + cmd
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        universal_newlines=True,
                        shell=True,
                        cwd=str(frontend_dir),
                        preexec_fn=os.setpgrp
                    )
            else:
                if platform.system() == "Windows":
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        universal_newlines=True,
                        cwd=str(frontend_dir),
                        shell=True
                    )
                else:
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        universal_newlines=True,
                        cwd=str(frontend_dir)
                    )
            
            save_pid("frontend", process.pid)
            
            try:
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
                process.terminate()
            finally:
                frontend_queue.put(None)  # Signal that this process is done

        except Exception as e:
            frontend_queue.put(f"[FRONTEND] ERROR: {str(e)}")
            frontend_queue.put(f"[FRONTEND] This may be due to npm not being in your PATH or not being installed.")
            frontend_queue.put(f"[FRONTEND] Check that you can run 'npm --version' from your terminal.")
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
    if args.detach:
        logger.info("Starting servers in detached mode (with output)...")
    else:
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
    
    # Don't remove PID files here - let stop_server handle cleanup
    if args.detach:
        logger.info("Servers will continue running in the background. Use 'python -m management.main stop' to stop them.")

@with_management_error_handling
async def start_backend(args):
    """Start the backend server"""
    if get_pid("backend"):
        raise ServerError("Backend server is already running", server="backend")

    logger.info(f"Starting backend server on port {args.backend_port}...")
    
    # Construct the command
    cmd = [
        "uvicorn", 
        "app.main:app", 
        "--reload", 
        "--host", "0.0.0.0", 
        "--port", str(args.backend_port)
    ]
    
    try:
        # Set up detached process flags based on platform
        if args.detach:
            if platform.system() == "Windows":
                creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=creationflags
                )
            else:
                # On Unix-like systems, use nohup and redirect output
                cmd = ["nohup"] + cmd + [">/dev/null", "2>&1", "&"]
                process = subprocess.Popen(
                    " ".join(cmd),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    shell=True,
                    preexec_fn=os.setpgrp
                )
            save_pid("backend", process.pid)
            logger.info(f"Backend server started in detached mode (PID: {process.pid}).")
        else:
            process = subprocess.Popen(cmd)
            save_pid("backend", process.pid)
            logger.info(f"Backend server started (PID: {process.pid}).")
            
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

@with_management_error_handling
async def start_frontend(args):
    """Start the frontend server"""
    if get_pid("frontend"):
        raise ServerError("Frontend server is already running", server="frontend")
    
    frontend_dir = Path("frontend").resolve()
    if not frontend_dir.exists():
        raise ServerError("Frontend directory not found", server="frontend")
    
    logger.info(f"Starting frontend server...")
    
    # Try to find full path to npm on Windows
    npm_cmd = "npm"
    if platform.system() == "Windows":
        try:
            # Check if npm exists in PATH
            npm_path = subprocess.check_output(["where", "npm"], shell=True).decode('utf-8').split('\n')[0].strip()
            if npm_path:
                npm_cmd = npm_path
                logger.info(f"Found npm at: {npm_path}")
        except Exception as e:
            logger.warning(f"Could not find npm in PATH: {str(e)}")
            logger.warning("Trying system default npm or using shell=True...")
    
    cmd = [npm_cmd, "run", "dev"]
    
    try:
        # Set up detached process flags based on platform
        if args.detach:
            if platform.system() == "Windows":
                creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    cwd=str(frontend_dir),
                    creationflags=creationflags,
                    shell=True
                )
            else:
                # On Unix-like systems, use nohup and redirect output
                cmd = ["nohup"] + cmd + [">/dev/null", "2>&1", "&"]
                process = subprocess.Popen(
                    " ".join(cmd),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    shell=True,
                    cwd=str(frontend_dir),
                    preexec_fn=os.setpgrp
                )
            save_pid("frontend", process.pid)
            logger.info(f"Frontend server started in detached mode (PID: {process.pid}).")
        else:
            if platform.system() == "Windows":
                process = subprocess.Popen(
                    cmd,
                    cwd=str(frontend_dir),
                    shell=True
                )
            else:
                process = subprocess.Popen(
                    cmd,
                    cwd=str(frontend_dir)
                )
            save_pid("frontend", process.pid)
            logger.info(f"Frontend server started (PID: {process.pid}).")
            
            if not args.backend:
                try:
                    process.wait()
                except KeyboardInterrupt:
                    process.terminate()
                    logger.info("Frontend server stopped.")
    except (subprocess.SubprocessError, OSError) as e:
        error = ServerError(f"Failed to start frontend server: {str(e)}", "frontend", 
                          ErrorSeverity.ERROR)
        handle_error(error, exit_app=True)

@with_management_error_handling
async def stop_server(server_type, force=False):
    """Stop a server by type"""
    pid = get_pid(server_type)
    if not pid:
        raise ProcessError(f"{server_type.title()} server is not running", pid=pid)
    
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
            
            # Only remove PID file if process is no longer running
            if not is_process_running(pid):
                pid_file = get_pid_file(server_type)
                if os.path.exists(pid_file):
                    try:
                        os.remove(pid_file)
                    except OSError as e:
                        logger.warning(f"Failed to remove PID file: {str(e)}")
            else:
                logger.info(f"{server_type.capitalize()} server is still running in unified mode.")
        else:
            raise ServerError(f"Failed to stop server", server_type, 
                            ErrorSeverity.ERROR,
                            f"Process {pid} could not be terminated")
    except Exception as e:
        raise ServerError(f"Error stopping server", server_type, 
                        ErrorSeverity.ERROR, str(e))

@with_management_error_handling
async def restart_server(server_type, args):
    """Restart a server by type"""
    await stop_server(server_type)
    if server_type == "backend":
        await start_backend(args)
    else:
        await start_frontend(args)

@with_management_error_handling
async def run_db_init():
    """Initialize the database"""
    try:
        from .db_utils import init_db
        init_db()  # init_db is synchronous, so no await needed
    except Exception as e:
        raise DatabaseError(
            "Failed to initialize database",
            error_code="DATABASE-INITIALIZATION-FAILURE-001",
            context=ErrorContext(
                source="run_db_init",
                severity=ErrorSeverity.ERROR,
                additional_data={"error": str(e)}
            )
        )

@with_management_error_handling
async def run_migrations():
    """Run database migrations"""
    try:
        from .db_utils import run_migrations as run_db_migrations
        run_db_migrations()  # synchronous function, no await needed
    except Exception as e:
        raise DatabaseError(
            "Failed to run migrations",
            error_code="DATABASE-MIGRATION-FAILURE-001",
            context=ErrorContext(
                source="run_migrations",
                severity=ErrorSeverity.ERROR,
                additional_data={"error": str(e)}
            )
        )

@with_management_error_handling
async def check_db_structure(db_path=None, verbose=False):
    """Check database structure"""
    if not db_path:
        raise DatabaseError(
            "Database path not provided",
            error_code="DATABASE-CHECK-MISSING-PATH-001",
            context=ErrorContext(
                source="check_db_structure",
                severity=ErrorSeverity.ERROR,
                additional_data={}
            )
        )

    try:
        from .db_inspection import check_db_structure as inspect_structure
        
        logger.info("Checking database structure...")
        try:
            result = inspect_structure(db_path)
            logger.info("Database structure check completed.")
            return True
        except FileNotFoundError as e:
            db_file = db_path or "storybook.db"
            raise DatabaseError(
                f"Failed to check database structure - {str(e)}",
                error_code="DATABASE-CHECK-FILE-NOT-FOUND-001",
                context=ErrorContext(
                    source="check_db_structure",
                    severity=ErrorSeverity.ERROR,
                    additional_data={"db_path": db_file}
                )
            )
    except ImportError:
        raise DatabaseError(
            "Failed to import db_inspection module",
            error_code="DATABASE-CHECK-IMPORT-ERROR-001",
            context=ErrorContext(
                source="check_db_structure",
                severity=ErrorSeverity.ERROR,
                additional_data={}
            )
        )

@with_management_error_handling
async def explore_db_contents(db_path=None):
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

@with_management_error_handling
async def dump_db_to_file(db_path=None, output_file="db_dump.txt"):
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

@with_management_error_handling
async def check_characters(db_path=None):
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

@with_management_error_handling
async def check_images(db_path=None):
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