"""
Main entry point for the management CLI
"""

import sys
import argparse
import traceback
import signal
import platform
import time
import threading
import logging
import asyncio

from app.core.errors.base import ErrorContext, ErrorSeverity
from app.core.errors.management import (
    ServerError, ManagementDatabaseError, CommandError, ProcessError,
    EnvironmentError, MonitoringError, with_management_error_handling, ManagementError
)
from app.core.logging import setup_logger

from .server_utils import show_status, DEFAULT_BACKEND_PORT, DEFAULT_FRONTEND_PORT
from .pid_utils import cleanup_pid_files, get_pid
from .commands import (
    start_backend, start_frontend, stop_server, restart_server,
    run_db_init, run_migrations,
    check_db_structure, explore_db_contents, dump_db_to_file,
    check_characters, check_images, 
    start_concurrent_mode
)
# Import environment management commands
from .env_commands import (
    setup_environment, show_current_env, setup_project, integrate_migrations
)
# Import monitoring commands
from .monitoring import (
    generate_monitoring_report, print_monitoring_summary, save_monitoring_report,
    continuous_monitoring
)

# Setup logger only if it doesn't exist
logger = logging.getLogger("management.main")
if not logger.handlers:
    logger = setup_logger(
        name="management.main",
        level="INFO",
        log_file="logs/management.log"
    )

@with_management_error_handling
async def setup_signal_handlers():
    """Setup signal handlers for graceful termination"""
    try:
        def signal_handler(sig, frame):
            logger.info("Operation cancelled by user.")
            sys.exit(0)
        
        # Register SIGINT (Ctrl+C) handler
        signal.signal(signal.SIGINT, signal_handler)
        
        # Register SIGTERM handler if available
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)
        
        # Register Windows-specific handler if on Windows
        if platform.system() == "Windows" and hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, signal_handler)
    except Exception as e:
        context = ErrorContext(
            source="setup_signal_handlers",
            severity=ErrorSeverity.ERROR,
            error_id="signal_handler_setup_error",
            additional_data={"error": str(e)}
        )
        raise ProcessError("Failed to set up signal handlers", context=context) from e

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Manage the Child Book Generator application."
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start servers")
    start_parser.add_argument("--backend", action="store_true", help="Start only the backend server")
    start_parser.add_argument("--frontend", action="store_true", help="Start only the frontend server")
    start_parser.add_argument(
        "--backend-port",
        type=int,
        default=8080,
        help="Port for the backend server (default: 8080)"
    )
    start_parser.add_argument(
        "--frontend-port",
        type=int,
        default=3000,
        help="Port for the frontend server (default: 3000)"
    )
    start_parser.add_argument(
        "-d", "--detach",
        action="store_true",
        help="Run in detached mode (background)"
    )
    start_parser.add_argument(
        "--unified-mode",
        action="store_true",
        help="Run both servers concurrently in a single terminal with color-coded output"
    )
    start_parser.add_argument(
        "--with-dashboard",
        action="store_true",
        help="Start the web dashboard alongside the servers"
    )
    
    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop servers")
    stop_parser.add_argument("--backend", action="store_true", help="Stop only the backend server")
    stop_parser.add_argument("--frontend", action="store_true", help="Stop only the frontend server")
    stop_parser.add_argument("--dashboard", action="store_true", help="Stop only the dashboard server")
    stop_parser.add_argument("--force", action="store_true", help="Force kill the servers")
    stop_parser.add_argument("--all", action="store_true", help="Stop all running servers")
    
    # Restart command
    restart_parser = subparsers.add_parser("restart", help="Restart servers")
    restart_parser.add_argument("--backend", action="store_true", help="Restart only the backend server")
    restart_parser.add_argument("--frontend", action="store_true", help="Restart only the frontend server")
    restart_parser.add_argument(
        "--backend-port",
        type=int,
        default=8080,
        help="Port for the backend server (default: 8080)"
    )
    restart_parser.add_argument(
        "--frontend-port",
        type=int,
        default=3000,
        help="Port for the frontend server (default: 3000)"
    )
    restart_parser.add_argument(
        "-d", "--detach",
        action="store_true",
        help="Run restarted servers in detached mode"
    )
    restart_parser.add_argument(
        "--unified-mode",
        action="store_true",
        help="Run both servers concurrently in a single terminal with color-coded output"
    )
    restart_parser.add_argument(
        "--with-dashboard",
        action="store_true",
        help="Start the web dashboard alongside the servers"
    )
    
    # Status command
    subparsers.add_parser("status", help="Show server status")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up stale PID files")
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser("dashboard", help="Start the web dashboard for managing servers")
    dashboard_parser.add_argument(
        "--port",
        type=int,
        default=3001,
        help="Port for the dashboard server (default: 3001)"
    )
    
    return parser.parse_args()

@with_management_error_handling
async def main():
    """Main entry point for the CLI"""
    try:
        # Setup signal handlers
        await setup_signal_handlers()
        
        # Parse command line arguments
        args = parse_args()
        
        if not args.command:
            print("No command specified. Use --help for usage information.")
            return
        
        # Handle commands
        if args.command == "start":
            if args.unified_mode:
                await start_concurrent_mode(args)
            else:
                if not args.backend and not args.frontend:
                    # Start both by default
                    args.backend = args.frontend = True
                
                if args.backend:
                    await start_backend(args)
                
                if args.frontend:
                    await start_frontend(args)
                
                if args.with_dashboard:
                    await start_dashboard(args)
        
        elif args.command == "stop":
            try:
                if args.all or (not args.backend and not args.frontend and not args.dashboard):
                    # Stop all servers
                    if get_pid("backend"):
                        await stop_server("backend", force=args.force)
                    if get_pid("frontend"):
                        await stop_server("frontend", force=args.force)
                    if get_pid("dashboard"):
                        await stop_server("dashboard", force=args.force)
                else:
                    # Stop specific servers
                    if args.backend and get_pid("backend"):
                        await stop_server("backend", force=args.force)
                    if args.frontend and get_pid("frontend"):
                        await stop_server("frontend", force=args.force)
                    if args.dashboard and get_pid("dashboard"):
                        await stop_server("dashboard", force=args.force)
            except Exception as e:
                error_context = ErrorContext(
                    source="main",
                    severity=ErrorSeverity.ERROR,
                    error_id="cli_execution_error",
                    additional_data={
                        "error": str(e),
                        "command": "stop",
                        "traceback": traceback.format_exc()
                    }
                )
                raise ProcessError("CLI execution failed", context=error_context) from e
        
        elif args.command == "restart":
            if args.unified_mode:
                await stop_server("backend", force=True)
                await stop_server("frontend", force=True)
                if args.with_dashboard:
                    await stop_server("dashboard", force=True)
                time.sleep(1)  # Give servers time to stop
                await start_concurrent_mode(args)
            else:
                if not args.backend and not args.frontend:
                    # Restart both by default
                    args.backend = args.frontend = True
                
                if args.backend:
                    await restart_server(
                        "backend",
                        port=args.backend_port,
                        detach=args.detach,
                        use_ide_terminal=args.use_ide_terminal
                    )
                
                if args.frontend:
                    await restart_server(
                        "frontend",
                        port=args.frontend_port,
                        detach=args.detach,
                        use_ide_terminal=args.use_ide_terminal
                    )
                
                if args.with_dashboard:
                    await restart_server(
                        "dashboard",
                        port=3001,
                        detach=args.detach,
                        use_ide_terminal=args.use_ide_terminal
                    )
        
        elif args.command == "status":
            # Show status is already decorated with error handling
            await show_status()
            return True
        
        elif args.command == "cleanup":
            await cleanup_pid_files()
        
        elif args.command == "init-db":
            await run_db_init()
        
        elif args.command == "migrate":
            await run_migrations()
        
        elif args.command == "db-check":
            await check_db_structure(args.db_path, args.verbose)
        
        elif args.command == "db-explore":
            await explore_db_contents(args.db_path)
        
        elif args.command == "db-dump":
            await dump_db_to_file(args.db_path, args.output)
        
        elif args.command == "check-characters":
            await check_characters(args.db_path)
        
        elif args.command == "check-images":
            await check_images(args.db_path)
        
        elif args.command == "env":
            if args.env_command == "setup":
                return await setup_environment(auto_mode=args.auto)
            elif args.env_command == "show":
                return await show_current_env()
            elif args.env_command == "init":
                return await setup_project()
            elif args.env_command == "migrate":
                return await integrate_migrations()
            else:
                logger.error(f"Unknown environment command: {args.env_command}")
                return False
        
        elif args.command == "monitor":
            if args.save:
                report = await generate_monitoring_report()
                await save_monitoring_report(report, args.output)
            elif args.continuous:
                await continuous_monitoring(
                    interval=args.interval,
                    output=args.output,
                    duration=args.duration
                )
            else:
                report = await generate_monitoring_report()
                await print_monitoring_summary(report)
        
        elif args.command == "dashboard":
            # Import the dashboard module
            try:
                from .dashboard import start_dashboard
                await start_dashboard(
                    port=args.port,
                    backend_port=args.backend_port,
                    frontend_port=args.frontend_port
                )
            except ImportError as e:
                logger.error(f"Failed to import dashboard module: {e}")
                logger.error("Please make sure Flask is installed with 'pip install flask'")
                return 1
            except KeyboardInterrupt:
                logger.info("Dashboard stopped by user")
                return 0
            except Exception as e:
                logger.error(f"Failed to start dashboard: {e}")
                traceback.print_exc()
                return 1
        
        else:
            context = ErrorContext(
                source="main",
                severity=ErrorSeverity.ERROR,
                error_id="invalid_command",
                additional_data={"command": args.command}
            )
            raise CommandError("Please specify a command. Use -h for help.", context=context)
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        context = ErrorContext(
            source="main",
            severity=ErrorSeverity.ERROR,
            error_id="cli_execution_error",
            additional_data={
                "error": str(e),
                "command": args.command if 'args' in locals() and hasattr(args, 'command') else None,
                "traceback": traceback.format_exc()
            }
        )
        raise ProcessError("CLI execution failed", context=context) from e

if __name__ == "__main__":
    asyncio.run(main()) 