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

from .server_utils import show_status, DEFAULT_BACKEND_PORT, DEFAULT_FRONTEND_PORT
from .pid_utils import cleanup_pid_files
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
# Import from shared utils
from utils.error_handling import (
    BaseError, ServerError, DatabaseError, ConfigError,
    ErrorSeverity, handle_error, setup_logger
)
# Import from local errors
from .errors import ProcessError

# Setup logger
logger = setup_logger("management.main", "logs/management.log")

def setup_signal_handlers():
    """Setup signal handlers for graceful termination"""
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
        "--use-ide-terminal",
        action="store_true",
        help="Show commands to run in separate IDE terminal tabs"
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
    stop_parser.add_argument(
        "--backend",
        action="store_true",
        dest="backend_only",
        help="Stop only the backend server"
    )
    stop_parser.add_argument(
        "--frontend",
        action="store_true",
        dest="frontend_only",
        help="Stop only the frontend server"
    )
    stop_parser.add_argument(
        "--dashboard",
        action="store_true",
        dest="dashboard_only",
        help="Stop only the dashboard server"
    )
    stop_parser.add_argument(
        "--force",
        action="store_true",
        help="Force kill the servers"
    )
    
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
        "--use-ide-terminal",
        action="store_true",
        help="Show commands to run in separate IDE terminal tabs"
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
    dashboard_parser.add_argument(
        "--backend-port",
        type=int,
        default=8080,
        help="Port for the backend server (default: 8080)"
    )
    dashboard_parser.add_argument(
        "--frontend-port",
        type=int,
        default=3000,
        help="Port for the frontend server (default: 3000)"
    )
    
    # Init DB command
    subparsers.add_parser("init-db", help="Initialize the database")
    
    # Run migrations command
    subparsers.add_parser("migrate", help="Run database migrations")
    
    # Database structure check command
    db_check_parser = subparsers.add_parser("db-check", help="Check database structure")
    db_check_parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Path to the database file (default: storybook.db in current directory)"
    )
    db_check_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show verbose output"
    )
    
    # Database explore command
    db_explore_parser = subparsers.add_parser("db-explore", help="Explore database contents")
    db_explore_parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Path to the database file (default: storybook.db in current directory)"
    )
    
    # Database dump command
    db_dump_parser = subparsers.add_parser("db-dump", help="Dump database structure and contents to a file")
    db_dump_parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Path to the database file (default: storybook.db in current directory)"
    )
    db_dump_parser.add_argument(
        "--output",
        type=str,
        default="db_dump.txt",
        help="Path to the output file (default: db_dump.txt)"
    )
    
    # Character inspection command
    char_check_parser = subparsers.add_parser("check-characters", help="Check character information in the database")
    char_check_parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Path to the database file (default: storybook.db in current directory)"
    )
    
    # Image inspection command
    image_check_parser = subparsers.add_parser("check-images", help="Check image information in the database")
    image_check_parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Path to the database file (default: storybook.db in current directory)"
    )
    
    # Environment management commands
    env_parser = subparsers.add_parser("env", help="Manage environment variables")
    env_subparsers = env_parser.add_subparsers(dest="env_command", help="Environment command")
    
    # Setup environment variables
    env_setup_parser = env_subparsers.add_parser("setup", help="Setup or update environment variables")
    env_setup_parser.add_argument("--auto", action="store_true", help="Automatically create .env file without user interaction")
    
    # Show environment variables
    env_subparsers.add_parser("show", help="Display current environment variables")
    
    # Project setup command
    subparsers.add_parser("setup-project", help="Set up the project environment (virtualenv, dependencies, alembic)")
    
    # Integrate migrations command
    subparsers.add_parser("integrate-migrations", help="Integrate existing migrations with Alembic")
    
    # Monitoring command
    monitor_parser = subparsers.add_parser("monitor", help="Monitor server health and performance")
    monitor_parser.add_argument("--save", action="store_true", help="Save the monitoring report to a file")
    monitor_parser.add_argument("--output", type=str, help="Path to output file (default: auto-generated)")
    monitor_parser.add_argument("--backend-port", type=int, default=DEFAULT_BACKEND_PORT, help="Backend server port")
    monitor_parser.add_argument("--frontend-port", type=int, default=DEFAULT_FRONTEND_PORT, help="Frontend server port")
    monitor_parser.add_argument("--continuous", action="store_true", help="Run continuous monitoring")
    monitor_parser.add_argument("--interval", type=int, default=60, help="Interval between checks in seconds (default: 60)")
    monitor_parser.add_argument("--duration", type=int, default=0, help="Total monitoring duration in seconds (0 for infinite)")
    
    return parser.parse_args()

def main():
    """Main function to run the CLI"""
    # Setup signal handlers for graceful termination
    setup_signal_handlers()
    
    try:
        args = parse_args()
        
        if args.command == "start":
            # Start handler
            def start_handler(args):
                if args.unified_mode:
                    # Run both servers in unified mode
                    start_concurrent_mode(args)
                else:
                    # Default behavior - start backend and frontend separately
                    if not args.frontend:  # If --frontend is not specified, start backend
                        start_backend(args)
                    
                    if not args.backend:  # If --backend is not specified, start frontend
                        start_frontend(args)
                    
                    # Start dashboard if requested (in separate terminal mode)
                    if args.with_dashboard:
                        try:
                            from .dashboard import start_dashboard
                            # Start dashboard in a separate thread
                            dashboard_port = args.port if hasattr(args, 'port') else 3001
                            dashboard_thread = threading.Thread(
                                target=start_dashboard,
                                args=(dashboard_port, args.backend_port, args.frontend_port)
                            )
                            dashboard_thread.daemon = True
                            dashboard_thread.start()
                            logger.info(f"Dashboard started - visit http://localhost:{dashboard_port}/")
                            
                            # Keep the main thread alive
                            while dashboard_thread.is_alive():
                                time.sleep(0.5)
                        except ImportError:
                            logger.error("Flask is not installed. Cannot start dashboard.")
                            logger.error("Install with: pip install flask")
                        except KeyboardInterrupt:
                            logger.info("Dashboard stopped by user.")
                            return
                
            start_handler(args)
            
        elif args.command == "stop":
            # Determine which servers to stop and handle interrupts properly
            try:
                if args.backend_only:
                    stop_server("backend")
                elif args.frontend_only:
                    stop_server("frontend")
                elif args.dashboard_only:
                    stop_server("dashboard")
                else:
                    stop_server("backend")
                    stop_server("frontend")
                    stop_server("dashboard")
            except KeyboardInterrupt:
                logger.info("Stop operation cancelled by user.")
                return
                
        elif args.command == "restart":
            # Determine which servers to restart
            restart_backend_server = not args.frontend
            restart_frontend_server = not args.backend
            
            # Add convenience properties for the start functions
            args.backend = restart_backend_server
            args.frontend = restart_frontend_server
            
            # Stop running servers first
            if restart_backend_server:
                stop_server("backend")
            
            if restart_frontend_server:
                stop_server("frontend")
            
            # Small delay to ensure ports are freed
            time.sleep(1)
            
            # Run cleanup to remove any stale PID files
            cleanup_pid_files()
            
            # Now start the servers again
            if args.unified_mode:
                # Run both servers in unified mode
                start_concurrent_mode(args)
            else:
                # Default behavior - start backend and frontend separately
                if restart_backend_server:
                    start_backend(args)
                
                if restart_frontend_server:
                    start_frontend(args)
                
                # Start dashboard if requested (in separate terminal mode)
                if args.with_dashboard:
                    try:
                        from .dashboard import start_dashboard
                        # Start dashboard in a separate thread
                        dashboard_port = args.port if hasattr(args, 'port') else 3001
                        dashboard_thread = threading.Thread(
                            target=start_dashboard,
                            args=(dashboard_port, args.backend_port, args.frontend_port)
                        )
                        dashboard_thread.daemon = True
                        dashboard_thread.start()
                        logger.info(f"Dashboard started - visit http://localhost:{dashboard_port}/")
                        
                        # Keep the main thread alive
                        while dashboard_thread.is_alive():
                            time.sleep(0.5)
                    except ImportError:
                        logger.error("Flask is not installed. Cannot start dashboard.")
                        logger.error("Install with: pip install flask")
                    except KeyboardInterrupt:
                        logger.info("Dashboard stopped by user.")
                        return
                
        elif args.command == "status":
            show_status()
                
        elif args.command == "cleanup":
            cleanup_pid_files()
            
        elif args.command == "init-db":
            run_db_init()
            
        elif args.command == "migrate":
            run_migrations()
            
        elif args.command == "db-check":
            try:
                check_db_structure(args.db_path, args.verbose)
            except FileNotFoundError as e:
                print(f"ERROR: Database '{args.db_path or 'storybook.db'}': {str(e)}")
                sys.exit(1)
            
        elif args.command == "db-explore":
            explore_db_contents(args.db_path)
            
        elif args.command == "db-dump":
            dump_db_to_file(args.db_path, args.output)
            
        elif args.command == "check-characters":
            check_characters(args.db_path)
            
        elif args.command == "check-images":
            check_images(args.db_path)
            
        # Environment management commands
        elif args.command == "env":
            if args.env_command == "setup":
                setup_environment(auto_mode=getattr(args, 'auto', False))
            elif args.env_command == "show":
                show_current_env()
            else:
                print("Usage: python manage.py env [setup|show]")
                
        # Project setup command
        elif args.command == "setup-project":
            setup_project()
            
        # Integrate migrations command
        elif args.command == "integrate-migrations":
            integrate_migrations()
            
        # Monitoring command
        elif args.command == "monitor":
            # Check if continuous monitoring is requested
            if args.continuous:
                logger.info(f"Starting continuous monitoring (interval: {args.interval}s, duration: {args.duration if args.duration > 0 else 'infinite'}s)")
                continuous_monitoring(
                    interval=args.interval,
                    duration=args.duration,
                    save_reports=args.save
                )
            else:
                # Generate single monitoring report
                report = generate_monitoring_report()
                
                # Print summary to console
                print_monitoring_summary(report)
                
                # Save report if requested
                if args.save:
                    output_file = args.output if args.output else "monitoring_report.json"
                    save_path = save_monitoring_report(report, output_file)
                    if save_path:
                        logger.info(f"Monitoring report saved to {save_path}")
                    else:
                        logger.error("Failed to save monitoring report")
                        return 1
                
        # Dashboard command
        elif args.command == "dashboard":
            # Import the dashboard module
            try:
                from .dashboard import start_dashboard
                start_dashboard(
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
                import traceback
                traceback.print_exc()
                return 1
            
        else:
            error = ConfigError("Please specify a command. Use -h for help.", severity=ErrorSeverity.ERROR)
            handle_error(error, exit_app=True)
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        # Use our error handling system
        if isinstance(e, BaseError):
            handle_error(e, exit_app=True)
        else:
            # Convert generic exceptions to BaseError
            error = BaseError(str(e), ErrorSeverity.ERROR, traceback.format_exc())
            handle_error(error, exit_app=True)

if __name__ == "__main__":
    main() 