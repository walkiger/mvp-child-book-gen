"""
Monitoring utilities for the Child Book Generator MVP.

This module provides functions for monitoring server health, performance,
and logs, as well as utilities for visualizing monitoring data.
"""

import os
import sys
import time
import datetime
import requests
import json
import platform
import psutil
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
from .pid_utils import get_pid, PID_DIR
from .server_utils import DEFAULT_BACKEND_PORT, DEFAULT_FRONTEND_PORT
from utils.error_handling import ProcessError, ServerError, setup_logger

# Setup logger
logger = setup_logger("management.monitoring", "logs/monitoring.log")

# Define monitoring constants
HEALTH_CHECK_INTERVAL = 60  # seconds
RESOURCE_CHECK_INTERVAL = 30  # seconds
LOG_CHECK_INTERVAL = 120  # seconds
ERROR_THRESHOLD = 5  # Number of errors before alert
RESPONSE_TIME_THRESHOLD = 2000  # ms

class ServerMetrics:
    """Class to store and manage server metrics"""
    
    def __init__(self, server_type: str, pid: int = None):
        """
        Initialize server metrics
        
        Args:
            server_type: Type of server (backend or frontend)
            pid: Process ID of the server
        """
        self.server_type = server_type
        self.pid = pid
        self.cpu_usage = []
        self.memory_usage = []
        self.disk_usage = []
        self.response_times = []
        self.error_count = 0
        self.last_checked = None
        self.status = "Unknown"
        self.uptime = 0
        self.start_time = None
    
    def update_process_metrics(self) -> bool:
        """
        Update process-related metrics (CPU, memory)
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.pid:
            self.pid = get_pid(self.server_type)
            
        if not self.pid:
            logger.warning(f"No PID found for {self.server_type} server")
            self.status = "Not running"
            return False
            
        try:
            process = psutil.Process(self.pid)
            
            # Get metrics
            cpu = process.cpu_percent(interval=0.5)
            memory = process.memory_info().rss / (1024 * 1024)  # Convert to MB
            
            # Store metrics
            self.cpu_usage.append((datetime.datetime.now(), cpu))
            self.memory_usage.append((datetime.datetime.now(), memory))
            
            # Limit history to keep memory usage reasonable
            if len(self.cpu_usage) > 100:
                self.cpu_usage.pop(0)
            if len(self.memory_usage) > 100:
                self.memory_usage.pop(0)
                
            # Update status
            self.status = "Running"
            
            # Update uptime
            if not self.start_time:
                self.start_time = process.create_time()
            self.uptime = time.time() - self.start_time
            
            self.last_checked = datetime.datetime.now()
            return True
        
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            logger.warning(f"Process with PID {self.pid} not accessible or no longer exists")
            self.status = "Not accessible"
            return False
        except Exception as e:
            logger.error(f"Error updating process metrics for {self.server_type}: {str(e)}")
            return False
    
    def check_health(self, url: str) -> bool:
        """
        Check server health by making a request to the given URL
        
        Args:
            url: URL to check
            
        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            start_time = time.time()
            response = requests.get(url, timeout=5)
            end_time = time.time()
            
            # Calculate response time in ms
            response_time = (end_time - start_time) * 1000
            
            # Store response time
            self.response_times.append((datetime.datetime.now(), response_time))
            
            # Limit history
            if len(self.response_times) > 100:
                self.response_times.pop(0)
                
            if response.status_code < 400:
                self.status = "Healthy"
                return True
            else:
                self.status = f"Unhealthy (HTTP {response.status_code})"
                self.error_count += 1
                return False
                
        except requests.RequestException as e:
            logger.error(f"Health check failed for {url}: {str(e)}")
            self.status = "Unreachable"
            self.error_count += 1
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert metrics to a dictionary for reporting
        
        Returns:
            dict: Dictionary of metrics
        """
        # Calculate averages if data exists
        avg_cpu = sum([cpu for _, cpu in self.cpu_usage[-5:]]) / max(len(self.cpu_usage[-5:]), 1) if self.cpu_usage else 0
        avg_memory = sum([mem for _, mem in self.memory_usage[-5:]]) / max(len(self.memory_usage[-5:]), 1) if self.memory_usage else 0
        avg_response = sum([resp for _, resp in self.response_times[-5:]]) / max(len(self.response_times[-5:]), 1) if self.response_times else 0
        
        # Format uptime
        uptime_str = str(datetime.timedelta(seconds=int(self.uptime))) if self.uptime else "N/A"
        
        return {
            "server_type": self.server_type,
            "pid": self.pid,
            "status": self.status,
            "uptime": uptime_str,
            "avg_cpu_percent": round(avg_cpu, 2),
            "avg_memory_mb": round(avg_memory, 2),
            "avg_response_ms": round(avg_response, 2),
            "error_count": self.error_count,
            "last_checked": self.last_checked.strftime("%Y-%m-%d %H:%M:%S") if self.last_checked else "Never"
        }


def monitor_backend(port: int = DEFAULT_BACKEND_PORT) -> ServerMetrics:
    """
    Monitor the backend server
    
    Args:
        port: Backend server port
        
    Returns:
        ServerMetrics: Server metrics object
    """
    metrics = ServerMetrics("backend")
    
    # Update process metrics
    metrics.update_process_metrics()
    
    # Check server health - use the root endpoint directly
    health_url = f"http://localhost:{port}/"
    metrics.check_health(health_url)
    
    return metrics


def monitor_frontend(port: int = DEFAULT_FRONTEND_PORT) -> ServerMetrics:
    """
    Monitor the frontend server
    
    Args:
        port: Frontend server port
        
    Returns:
        ServerMetrics: Server metrics object
    """
    metrics = ServerMetrics("frontend")
    
    # Update process metrics
    metrics.update_process_metrics()
    
    # Check server health
    health_url = f"http://localhost:{port}"
    metrics.check_health(health_url)
    
    return metrics


def check_disk_usage(path: str = ".") -> Dict[str, Union[float, str]]:
    """
    Check disk usage for the given path
    
    Args:
        path: Path to check
        
    Returns:
        dict: Dictionary with disk usage information
    """
    try:
        usage = psutil.disk_usage(path)
        return {
            "total_gb": round(usage.total / (1024**3), 2),
            "used_gb": round(usage.used / (1024**3), 2),
            "free_gb": round(usage.free / (1024**3), 2),
            "percent_used": usage.percent
        }
    except Exception as e:
        logger.error(f"Error checking disk usage: {str(e)}")
        return {
            "error": str(e)
        }


def check_system_resources() -> Dict[str, Any]:
    """
    Check system-wide resource usage
    
    Returns:
        dict: Dictionary with system resource information
    """
    try:
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            "disk_usage": check_disk_usage()
        }
    except Exception as e:
        logger.error(f"Error checking system resources: {str(e)}")
        return {
            "error": str(e)
        }


def analyze_logs(log_file: str, lines: int = 100) -> Dict[str, Any]:
    """
    Analyze logs to extract error information
    
    Args:
        log_file: Path to log file
        lines: Number of lines to analyze
        
    Returns:
        dict: Dictionary with log analysis information
    """
    if not os.path.exists(log_file):
        return {"error": f"Log file not found: {log_file}"}
    
    try:
        # Use platform-specific command to get last N lines
        if platform.system() == "Windows":
            result = subprocess.run(
                ["powershell", "-Command", f"Get-Content -Path '{log_file}' -Tail {lines}"], 
                capture_output=True, 
                text=True, 
                check=False
            )
            log_data = result.stdout
        else:  # Linux/Mac
            result = subprocess.run(
                ["tail", f"-{lines}", log_file], 
                capture_output=True, 
                text=True, 
                check=False
            )
            log_data = result.stdout
        
        # Count error levels
        error_count = log_data.count("ERROR")
        warning_count = log_data.count("WARNING")
        info_count = log_data.count("INFO")
        
        # Extract the most recent errors
        errors = []
        for line in log_data.splitlines():
            if "ERROR" in line:
                errors.append(line)
                if len(errors) >= 5:  # Limit to 5 most recent errors
                    break
        
        return {
            "error_count": error_count,
            "warning_count": warning_count,
            "info_count": info_count,
            "recent_errors": errors
        }
    except Exception as e:
        logger.error(f"Error analyzing logs: {str(e)}")
        return {"error": str(e)}


def generate_monitoring_report() -> Dict[str, Any]:
    """
    Generate a comprehensive monitoring report
    
    Returns:
        dict: Dictionary with monitoring information
    """
    report = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "system": {
            "hostname": platform.node(),
            "os": f"{platform.system()} {platform.release()}",
            "resources": check_system_resources()
        },
        "servers": {
            "backend": monitor_backend().to_dict(),
            "frontend": monitor_frontend().to_dict()
        },
        "logs": {
            "app": analyze_logs("logs/app.log"),
            "management": analyze_logs("logs/management.log"),
            "backend": analyze_logs("logs/backend.log"),
            "frontend": analyze_logs("logs/frontend.log")
        }
    }
    
    return report


def save_monitoring_report(report: Dict[str, Any], output_file: str = "monitoring_report.json") -> str:
    """
    Save monitoring report to a file
    
    Args:
        report: Monitoring report dictionary
        output_file: File to save the report to
        
    Returns:
        str: Path to the saved report
    """
    try:
        # Ensure the monitoring directory exists
        os.makedirs("monitoring", exist_ok=True)
        
        # Generate a timestamp-based filename if not provided
        if output_file == "monitoring_report.json":
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"monitoring/report_{timestamp}.json"
        
        # Save the report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"Monitoring report saved to {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"Error saving monitoring report: {str(e)}")
        return ""


def print_monitoring_summary(report: Dict[str, Any]) -> None:
    """
    Print a summary of the monitoring report to the console
    
    Args:
        report: Monitoring report dictionary
    """
    print("\n===== MONITORING SUMMARY =====")
    print(f"Time: {report['timestamp']}")
    print(f"System: {report['system']['hostname']} ({report['system']['os']})")
    
    print("\n--- SERVERS ---")
    
    # Backend server
    backend = report['servers']['backend']
    print(f"Backend: {backend['status']} (PID: {backend['pid']})")
    print(f"  Uptime: {backend['uptime']}")
    print(f"  CPU: {backend['avg_cpu_percent']}%, Memory: {backend['avg_memory_mb']} MB")
    print(f"  Response Time: {backend['avg_response_ms']} ms")
    
    # Frontend server
    frontend = report['servers']['frontend']
    print(f"Frontend: {frontend['status']} (PID: {frontend['pid']})")
    print(f"  Uptime: {frontend['uptime']}")
    print(f"  CPU: {frontend['avg_cpu_percent']}%, Memory: {frontend['avg_memory_mb']} MB")
    print(f"  Response Time: {frontend['avg_response_ms']} ms")
    
    print("\n--- SYSTEM RESOURCES ---")
    resources = report['system']['resources']
    print(f"CPU: {resources['cpu_percent']}%")
    print(f"Memory: {resources['memory_percent']}% (Available: {resources['memory_available_gb']} GB)")
    disk = resources['disk_usage']
    print(f"Disk: {disk['percent_used']}% used ({disk['used_gb']} GB / {disk['total_gb']} GB)")
    
    print("\n--- LOGS SUMMARY ---")
    for log_name, log_data in report['logs'].items():
        if "error" in log_data:
            print(f"{log_name}: Error - {log_data['error']}")
        else:
            print(f"{log_name}: {log_data['error_count']} errors, {log_data['warning_count']} warnings")
    
    # Alert on issues
    print("\n--- ALERTS ---")
    alerts = []
    
    # Check server status
    if backend['status'] != "Healthy" and backend['status'] != "Running":
        alerts.append(f"Backend server is {backend['status']}")
    if frontend['status'] != "Healthy" and frontend['status'] != "Running":
        alerts.append(f"Frontend server is {frontend['status']}")
    
    # Check response times
    if backend['avg_response_ms'] > RESPONSE_TIME_THRESHOLD:
        alerts.append(f"Backend response time is high: {backend['avg_response_ms']} ms")
    
    # Check error counts
    for log_name, log_data in report['logs'].items():
        if "error_count" in log_data and log_data['error_count'] >= ERROR_THRESHOLD:
            alerts.append(f"{log_name} log has {log_data['error_count']} errors")
    
    # Display alerts or all-clear
    if alerts:
        for alert in alerts:
            print(f"⚠️ ALERT: {alert}")
    else:
        print("✅ All systems operating normally")
    
    print("\n===============================")


def continuous_monitoring(interval: int = 60, duration: int = 0, save_reports: bool = True) -> None:
    """
    Run continuous monitoring with a specified interval
    
    Args:
        interval: Time between checks in seconds
        duration: Total monitoring duration in seconds (0 for infinite)
        save_reports: Whether to save reports to disk
    """
    start_time = time.time()
    count = 0
    
    try:
        while True:
            count += 1
            current_time = time.time()
            elapsed = current_time - start_time
            
            # Generate and display report
            logger.info(f"Running monitoring check #{count} (elapsed: {int(elapsed)}s)")
            report = generate_monitoring_report()
            print_monitoring_summary(report)
            
            # Save report if requested
            if save_reports:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"monitoring/report_{timestamp}.json"
                save_monitoring_report(report, output_file)
            
            # Check if we've hit the duration limit
            if duration > 0 and elapsed >= duration:
                logger.info(f"Monitoring completed after {int(elapsed)} seconds ({count} checks)")
                break
                
            # Sleep until next check
            logger.info(f"Next check in {interval} seconds. Press Ctrl+C to stop monitoring.")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        logger.info(f"Monitoring stopped by user after {int(time.time() - start_time)} seconds ({count} checks)")
        print("\nMonitoring stopped by user.") 