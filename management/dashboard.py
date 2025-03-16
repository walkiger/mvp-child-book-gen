"""
Simple web dashboard for managing development servers.
"""
import os
import sys
import subprocess
import threading
import time
import logging
import json
from pathlib import Path

try:
    from flask import Flask, render_template_string, jsonify, request
    flask_available = True
except ImportError:
    flask_available = False

from .pid_utils import get_pid, is_process_running
from .commands import remove_pid_file

# Setup logging
logger = logging.getLogger("dashboard")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)

# HTML template for the dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Dev Server Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.5;
            margin: 0;
            padding: 0;
            color: #333;
            background: #f5f5f5;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 1rem;
        }
        .header {
            background: #4a90e2;
            color: white;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        .header h1 {
            margin: 0;
            font-size: 1.5rem;
        }
        .card {
            background: white;
            border-radius: 4px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
            overflow: hidden;
        }
        .card-header {
            padding: 1rem;
            background: #f9f9f9;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .card-header h2 {
            margin: 0;
            font-size: 1.2rem;
        }
        .card-body {
            padding: 1rem;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1rem;
        }
        .status {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.875rem;
            font-weight: 500;
        }
        .status-running {
            background: #48c774;
            color: white;
        }
        .status-stopped {
            background: #e25c4a;
            color: white;
        }
        .button {
            display: inline-block;
            background: #4a90e2;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            font-size: 0.875rem;
            cursor: pointer;
            text-decoration: none;
        }
        .button:hover {
            background: #3a80d2;
        }
        .button-danger {
            background: #e25c4a;
        }
        .button-danger:hover {
            background: #d24c3a;
        }
        .button-group {
            display: flex;
            gap: 0.5rem;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        table th, table td {
            text-align: left;
            padding: 0.5rem;
            border-bottom: 1px solid #eee;
        }
        table th {
            font-weight: 500;
            color: #666;
        }
        .refresh {
            font-size: 0.875rem;
            color: #666;
            text-align: center;
            margin-top: 1rem;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1>Development Server Dashboard</h1>
        </div>
    </div>
    
    <div class="container">
        <div class="card">
            <div class="card-header">
                <h2>Server Control</h2>
                <div class="button-group">
                    <a href="/" class="button">Refresh</a>
                    <a href="/start-all" class="button">Start All</a>
                    <a href="/stop-all" class="button button-danger">Stop All</a>
                </div>
            </div>
            <div class="card-body">
                <div class="grid">
                    <div>
                        <h3>Backend Server</h3>
                        <table>
                            <tr>
                                <th>Status</th>
                                <td>
                                    {% if backend_running %}
                                    <span class="status status-running">Running</span>
                                    {% else %}
                                    <span class="status status-stopped">Stopped</span>
                                    {% endif %}
                                </td>
                            </tr>
                            <tr>
                                <th>PID</th>
                                <td>{{ backend_pid or 'N/A' }}</td>
                            </tr>
                            <tr>
                                <th>Port</th>
                                <td>{{ backend_port }}</td>
                            </tr>
                            <tr>
                                <th>Actions</th>
                                <td>
                                    <div class="button-group">
                                        {% if not backend_running %}
                                        <a href="/start/backend" class="button">Start</a>
                                        {% else %}
                                        <a href="/stop/backend" class="button button-danger">Stop</a>
                                        {% endif %}
                                        <a href="http://localhost:{{ backend_port }}/api" target="_blank" class="button">Open API</a>
                                    </div>
                                </td>
                            </tr>
                        </table>
                    </div>
                    
                    <div>
                        <h3>Frontend Server</h3>
                        <table>
                            <tr>
                                <th>Status</th>
                                <td>
                                    {% if frontend_running %}
                                    <span class="status status-running">Running</span>
                                    {% else %}
                                    <span class="status status-stopped">Stopped</span>
                                    {% endif %}
                                </td>
                            </tr>
                            <tr>
                                <th>PID</th>
                                <td>{{ frontend_pid or 'N/A' }}</td>
                            </tr>
                            <tr>
                                <th>Port</th>
                                <td>{{ frontend_port }}</td>
                            </tr>
                            <tr>
                                <th>Actions</th>
                                <td>
                                    <div class="button-group">
                                        {% if not frontend_running %}
                                        <a href="/start/frontend" class="button">Start</a>
                                        {% else %}
                                        <a href="/stop/frontend" class="button button-danger">Stop</a>
                                        {% endif %}
                                        <a href="http://localhost:{{ frontend_port }}" target="_blank" class="button">Open App</a>
                                    </div>
                                </td>
                            </tr>
                        </table>
                    </div>
                    
                    <div>
                        <h3>Dashboard Server</h3>
                        <table>
                            <tr>
                                <th>Status</th>
                                <td>
                                    <span class="status status-running">Running</span>
                                </td>
                            </tr>
                            <tr>
                                <th>PID</th>
                                <td>{{ dashboard_pid or 'N/A' }}</td>
                            </tr>
                            <tr>
                                <th>Port</th>
                                <td>{{ dashboard_port }}</td>
                            </tr>
                            <tr>
                                <th>Actions</th>
                                <td>
                                    <div class="button-group">
                                        <a href="http://localhost:{{ dashboard_port }}" target="_blank" class="button">Refresh</a>
                                    </div>
                                </td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <h2>System Info</h2>
            </div>
            <div class="card-body">
                <table>
                    <tr>
                        <th>Project Directory</th>
                        <td>{{ project_dir }}</td>
                    </tr>
                    <tr>
                        <th>Python Version</th>
                        <td>{{ python_version }}</td>
                    </tr>
                    <tr>
                        <th>Node Version</th>
                        <td>{{ node_version }}</td>
                    </tr>
                    <tr>
                        <th>Operating System</th>
                        <td>{{ os_info }}</td>
                    </tr>
                </table>
            </div>
        </div>
        
        <div class="refresh">
            Last updated: {{ current_time }}
        </div>
    </div>
</body>
</html>
"""

def get_system_info():
    """Get system information for display"""
    import platform
    import datetime
    
    # Get Python version
    python_version = sys.version.split()[0]
    
    # Get Node.js version
    try:
        node_version = subprocess.check_output(["node", "--version"], text=True).strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        node_version = "Not found"
    
    # Get OS info
    os_info = platform.platform()
    
    # Current time
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Project directory
    project_dir = os.getcwd()
    
    return {
        "python_version": python_version,
        "node_version": node_version,
        "os_info": os_info,
        "current_time": current_time,
        "project_dir": project_dir
    }

def create_dashboard_app(backend_port=8080, frontend_port=3000, dashboard_port=3001):
    """Create the Flask dashboard app without starting it"""
    if not flask_available:
        logger.error("Flask is not installed. Please install it with 'pip install flask'")
        logger.error("Once installed, run 'python manage.py dashboard' again")
        return None
    
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        """Dashboard home page"""
        # Get server status
        backend_pid = get_pid("backend")
        frontend_pid = get_pid("frontend")
        dashboard_pid = get_pid("dashboard")
        
        backend_running = backend_pid is not None and is_process_running(backend_pid)
        frontend_running = frontend_pid is not None and is_process_running(frontend_pid)
        
        # Get system info
        system_info = get_system_info()
        
        # Render template
        return render_template_string(
            DASHBOARD_HTML, 
            backend_running=backend_running,
            frontend_running=frontend_running,
            backend_pid=backend_pid,
            frontend_pid=frontend_pid,
            dashboard_pid=os.getpid(),  # Current process ID
            backend_port=backend_port,
            frontend_port=frontend_port,
            dashboard_port=dashboard_port,  # Use dashboard_port from outer scope
            **system_info
        )
    
    # Add all the other routes
    add_routes(app, backend_port, frontend_port)
    
    return app

def add_routes(app, backend_port, frontend_port):
    """Add all routes to the Flask app"""
    @app.route('/start/<server>')
    def start_server(server):
        """Start a server"""
        if server == "backend":
            # Start backend server
            cmd = [
                "uvicorn",
                "app.main:app",
                "--reload",
                "--host", "0.0.0.0",
                "--port", str(backend_port)
            ]
            
            # Start the process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # Save PID
            from .pid_utils import save_pid
            save_pid("backend", process.pid)
            
            logger.info(f"Started backend server (PID: {process.pid})")
        
        elif server == "frontend":
            # Start frontend server
            frontend_dir = Path("frontend").resolve()
            if not frontend_dir.exists():
                return "Frontend directory not found", 404
            
            # Change to frontend directory
            original_dir = os.getcwd()
            os.chdir(frontend_dir)
            
            # Start the process
            cmd = ["npm", "run", "dev"]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # Save PID
            from .pid_utils import save_pid
            save_pid("frontend", process.pid)
            
            # Return to original directory
            os.chdir(original_dir)
            
            logger.info(f"Started frontend server (PID: {process.pid})")
        
        return {"status": "started"}, 302, {"Location": "/"}
    
    @app.route('/stop/<server>')
    def stop_server(server):
        """Stop a server"""
        from .commands import stop_server as cmd_stop_server
        cmd_stop_server(server)
        return {"status": "stopped"}, 302, {"Location": "/"}
    
    @app.route('/start-all')
    def start_all():
        """Start all servers"""
        # Start backend
        start_server("backend")
        
        # Start frontend
        start_server("frontend")
        
        return {"status": "started"}, 302, {"Location": "/"}
    
    @app.route('/stop-all')
    def stop_all():
        """Stop all servers"""
        from .commands import stop_server as cmd_stop_server
        
        # Stop backend
        cmd_stop_server("backend")
        
        # Stop frontend
        cmd_stop_server("frontend")
        
        return {"status": "stopped"}, 302, {"Location": "/"}
    
    return app

def start_dashboard(port=3001, backend_port=8080, frontend_port=3000):
    """Start the web dashboard"""
    if not flask_available:
        logger.error("Flask is not installed. Please install it with 'pip install flask'")
        logger.error("Once installed, run 'python manage.py dashboard' again")
        return
    
    # Add a message about the unified mode
    logger.info("Starting dashboard on port 3001...")
    logger.info("In unified terminal mode, the dashboard will not have colored output")
    logger.info("Backend will be shown in blue, Frontend in green")
    logger.info("For color-coded dashboard logs, run the dashboard separately")
    
    # Save the dashboard PID
    from .pid_utils import save_pid
    save_pid("dashboard", os.getpid())
    
    # Create and run the app
    app = create_dashboard_app(backend_port, frontend_port, port)
    if app:
        logger.info(f"Starting dashboard on http://localhost:{port}")
        logger.info("Press Ctrl+C to stop")
        try:
            app.run(host='0.0.0.0', port=port, debug=True)
        finally:
            # Clean up PID file when stopping
            remove_pid_file("dashboard") 