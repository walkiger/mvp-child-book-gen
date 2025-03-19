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

from app.core.errors.base import ErrorContext, ErrorSeverity
from app.core.errors.management import (
    ProcessError, ServerError, with_management_error_handling
)
from app.core.errors.monitoring import (
    MonitoringError, MetricsError, LogAnalysisError,
    RouteHealthError, ServerStatusError
)
from app.core.logging import setup_logger
from .error_utils import create_error_context

from .pid_utils import get_pid, PID_DIR
from .server_utils import DEFAULT_BACKEND_PORT, DEFAULT_FRONTEND_PORT

# Setup logger only if it doesn't exist
logger = logging.getLogger("management.monitoring")
if not logger.handlers:
    logger = setup_logger(
        name="management.monitoring",
        level="INFO",
        log_file="logs/monitoring.log"
    )

# Define monitoring constants
HEALTH_CHECK_INTERVAL = 60  # seconds
RESOURCE_CHECK_INTERVAL = 30  # seconds
LOG_CHECK_INTERVAL = 120  # seconds
ERROR_THRESHOLD = 5  # Number of errors before alert
RESPONSE_TIME_THRESHOLD = 2000  # ms

class MonitoringMetrics:
    """Container for monitoring metrics"""
    def __init__(self):
        self.cpu_percent: float = 0.0
        self.memory_percent: float = 0.0
        self.disk_usage: Dict[str, float] = {}
        self.process_info: Dict[str, Any] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []

@with_management_error_handling
async def collect_metrics(pid: Optional[int] = None) -> MonitoringMetrics:
    """Collect system and process metrics
    
    Args:
        pid: Optional process ID to monitor
        
    Returns:
        MonitoringMetrics object
        
    Raises:
        MonitoringError: If metrics collection fails
    """
    try:
        metrics = MonitoringMetrics()
        
        # System metrics
        metrics.cpu_percent = psutil.cpu_percent(interval=1)
        metrics.memory_percent = psutil.virtual_memory().percent
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        metrics.disk_usage = {
            'total': disk.total / (1024 * 1024 * 1024),  # GB
            'used': disk.used / (1024 * 1024 * 1024),    # GB
            'free': disk.free / (1024 * 1024 * 1024),    # GB
            'percent': disk.percent
        }
        
        # Process metrics if PID provided
        if pid:
            try:
                process = psutil.Process(pid)
                metrics.process_info = {
                    'cpu_percent': process.cpu_percent(interval=1),
                    'memory_percent': process.memory_percent(),
                    'status': process.status(),
                    'create_time': datetime.fromtimestamp(process.create_time()).isoformat(),
                    'threads': len(process.threads())
                }
            except psutil.NoSuchProcess:
                error_ctx = create_error_context(
                    operation='collect_metrics',
                    source='monitoring',
                    additional_info={'pid': pid}
                )
                raise MonitoringError(
                    message=f"Process with PID {pid} not found",
                    error_code="MON-PROC-NOT-FOUND-001",
                    context=error_ctx
                )
            except psutil.AccessDenied:
                error_ctx = create_error_context(
                    operation='collect_metrics',
                    source='monitoring',
                    additional_info={'pid': pid}
                )
                raise MonitoringError(
                    message=f"Access denied to process with PID {pid}",
                    error_code="MON-ACCESS-DENIED-001",
                    context=error_ctx
                )
        
        return metrics
        
    except Exception as e:
        error_ctx = create_error_context(
            operation='collect_metrics',
            source='monitoring',
            additional_info={'original_error': str(e)}
        )
        raise MonitoringError(
            message=f"Failed to collect monitoring metrics: {str(e)}",
            error_code="MON-COLLECT-FAIL-001",
            context=error_ctx
        )

@with_management_error_handling
async def generate_monitoring_report(
    metrics: MonitoringMetrics,
    report_file: Optional[str] = None
) -> Dict[str, Any]:
    """Generate a monitoring report from collected metrics
    
    Args:
        metrics: Collected monitoring metrics
        report_file: Optional file to save report to
        
    Returns:
        Dictionary containing the report data
        
    Raises:
        MonitoringError: If report generation fails
    """
    try:
        report = {
            'timestamp': datetime.now().isoformat(),
            'system': {
                'cpu_percent': metrics.cpu_percent,
                'memory_percent': metrics.memory_percent,
                'disk_usage': metrics.disk_usage
            },
            'process': metrics.process_info if metrics.process_info else None,
            'warnings': metrics.warnings,
            'errors': metrics.errors
        }
        
        if report_file:
            try:
                with open(report_file, 'w') as f:
                    json.dump(report, f, indent=2)
            except IOError as e:
                error_ctx = create_error_context(
                    operation='generate_monitoring_report',
                    source='monitoring',
                    additional_info={'report_file': report_file}
                )
                raise MonitoringError(
                    message=f"Failed to save monitoring report: {str(e)}",
                    error_code="MON-SAVE-FAIL-001",
                    context=error_ctx
                )
        
        return report
        
    except Exception as e:
        error_ctx = create_error_context(
            operation='generate_monitoring_report',
            source='monitoring',
            additional_info={'original_error': str(e)}
        )
        raise MonitoringError(
            message=f"Failed to generate monitoring report: {str(e)}",
            error_code="MON-GEN-FAIL-001",
            context=error_ctx
        )

@with_management_error_handling
async def print_monitoring_summary(metrics: MonitoringMetrics):
    """Print a summary of monitoring metrics to console
    
    Args:
        metrics: Collected monitoring metrics
    """
    print("\nMONITORING SUMMARY")
    print("=" * 50)
    print(f"CPU Usage: {metrics.cpu_percent}%")
    print(f"Memory Usage: {metrics.memory_percent}%")
    print(f"Disk Usage: {metrics.disk_usage['percent']}%")
    
    if metrics.process_info:
        print("\nProcess Information:")
        print(f"  CPU Usage: {metrics.process_info['cpu_percent']}%")
        print(f"  Memory Usage: {metrics.process_info['memory_percent']}%")
        print(f"  Status: {metrics.process_info['status']}")
        print(f"  Threads: {metrics.process_info['threads']}")
    
    if metrics.warnings:
        print("\nWarnings:")
        for warning in metrics.warnings:
            print(f"  - {warning}")
    
    if metrics.errors:
        print("\nErrors:")
        for error in metrics.errors:
            print(f"  - {error}")

@with_management_error_handling
async def continuous_monitoring(
    pid: Optional[int] = None,
    interval: int = 60,
    report_dir: str = "monitoring_reports"
):
    """Continuously monitor system and process metrics
    
    Args:
        pid: Optional process ID to monitor
        interval: Monitoring interval in seconds
        report_dir: Directory to save monitoring reports
    """
    try:
        # Ensure report directory exists
        os.makedirs(report_dir, exist_ok=True)
        
        print(f"Starting continuous monitoring (Ctrl+C to stop)")
        print(f"Monitoring interval: {interval} seconds")
        print(f"Reports directory: {report_dir}")
        
        while True:
            try:
                metrics = await collect_metrics(pid)
                
                # Generate report filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                report_file = os.path.join(report_dir, f"monitoring_report_{timestamp}.json")
                
                # Generate and save report
                await generate_monitoring_report(metrics, report_file)
                
                # Print summary
                await print_monitoring_summary(metrics)
                
                # Wait for next interval
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print("\nMonitoring stopped by user")
                break
                
    except Exception as e:
        error_ctx = create_error_context(
            operation='continuous_monitoring',
            source='monitoring',
            additional_info={
                'pid': pid,
                'interval': interval,
                'report_dir': report_dir
            }
        )
        raise MonitoringError(
            message=f"Continuous monitoring failed: {str(e)}",
            error_code="MON-CONTINUOUS-FAIL-001",
            context=error_ctx
        )

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


@with_management_error_handling
def monitor_backend(port: int = DEFAULT_BACKEND_PORT) -> ServerMetrics:
    """
    Monitor the backend server
    
    Args:
        port: Backend server port
        
    Returns:
        ServerMetrics: Server metrics object
    """
    try:
        metrics = ServerMetrics("backend")
        
        # Update process metrics
        metrics.update_process_metrics()
        
        # Check server health - use the root endpoint directly
        health_url = f"http://localhost:{port}/"
        metrics.check_health(health_url)
        
        return metrics
    except Exception as e:
        error_context = ErrorContext(
            source="monitor_backend",
            severity=ErrorSeverity.ERROR,
            error_id="backend_monitoring_error",
            additional_data={
                "error": str(e),
                "port": port
            }
        )
        raise MonitoringError("Failed to monitor backend server", error_context) from e


@with_management_error_handling
def monitor_frontend(port: int = DEFAULT_FRONTEND_PORT) -> ServerMetrics:
    """
    Monitor the frontend server
    
    Args:
        port: Frontend server port
        
    Returns:
        ServerMetrics: Server metrics object
    """
    try:
        metrics = ServerMetrics("frontend")
        
        # Update process metrics
        metrics.update_process_metrics()
        
        # Check server health
        health_url = f"http://localhost:{port}"
        metrics.check_health(health_url)
        
        return metrics
    except Exception as e:
        error_context = ErrorContext(
            source="monitor_frontend",
            severity=ErrorSeverity.ERROR,
            error_id="frontend_monitoring_error",
            additional_data={
                "error": str(e),
                "port": port
            }
        )
        raise MonitoringError("Failed to monitor frontend server", error_context) from e


@with_management_error_handling
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
        error_context = ErrorContext(
            source="check_disk_usage",
            severity=ErrorSeverity.ERROR,
            error_id="disk_usage_error",
            additional_data={
                "error": str(e),
                "path": path
            }
        )
        raise MonitoringError("Failed to check disk usage", error_context) from e


@with_management_error_handling
def check_system_resources() -> Dict[str, Any]:
    """
    Check system-wide resource usage
    
    Returns:
        dict: Dictionary with system resource information
    """
    try:
        return {
            "cpu": {
                "percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count(),
                "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            },
            "memory": {
                "total": round(psutil.virtual_memory().total / (1024**3), 2),  # GB
                "available": round(psutil.virtual_memory().available / (1024**3), 2),  # GB
                "percent": psutil.virtual_memory().percent
            },
            "disk": check_disk_usage(),
            "network": {
                "bytes_sent": psutil.net_io_counters().bytes_sent,
                "bytes_recv": psutil.net_io_counters().bytes_recv,
                "packets_sent": psutil.net_io_counters().packets_sent,
                "packets_recv": psutil.net_io_counters().packets_recv,
                "errin": psutil.net_io_counters().errin,
                "errout": psutil.net_io_counters().errout
            }
        }
    except Exception as e:
        error_context = ErrorContext(
            source="check_system_resources",
            severity=ErrorSeverity.ERROR,
            error_id="system_resources_error",
            additional_data={"error": str(e)}
        )
        raise MonitoringError("Failed to check system resources", error_context) from e


@with_management_error_handling
def analyze_logs(log_file: str, lines: int = 100) -> Dict[str, Any]:
    """
    Analyze the last N lines of a log file
    
    Args:
        log_file: Path to log file
        lines: Number of lines to analyze
        
    Returns:
        dict: Dictionary with log analysis information
    """
    try:
        if not os.path.exists(log_file):
            error_context = ErrorContext(
                source="analyze_logs",
                severity=ErrorSeverity.ERROR,
                error_id="log_file_not_found",
                additional_data={
                    "log_file": log_file
                }
            )
            raise MonitoringError(f"Log file not found: {log_file}", error_context)
        
        # Read last N lines
        with open(log_file, 'r') as f:
            # Use a list to store lines for analysis
            log_lines = []
            for line in f:
                log_lines.append(line)
                if len(log_lines) > lines:
                    log_lines.pop(0)
        
        # Analyze lines
        error_count = 0
        warning_count = 0
        info_count = 0
        debug_count = 0
        
        for line in log_lines:
            if "ERROR" in line:
                error_count += 1
            elif "WARNING" in line:
                warning_count += 1
            elif "INFO" in line:
                info_count += 1
            elif "DEBUG" in line:
                debug_count += 1
        
        return {
            "file": log_file,
            "lines_analyzed": len(log_lines),
            "error_count": error_count,
            "warning_count": warning_count,
            "info_count": info_count,
            "debug_count": debug_count,
            "last_error": next((line for line in reversed(log_lines) if "ERROR" in line), None),
            "last_warning": next((line for line in reversed(log_lines) if "WARNING" in line), None)
        }
    except Exception as e:
        error_context = ErrorContext(
            source="analyze_logs",
            severity=ErrorSeverity.ERROR,
            error_id="log_analysis_error",
            additional_data={
                "error": str(e),
                "log_file": log_file,
                "lines": lines
            }
        )
        raise MonitoringError("Failed to analyze logs", error_context) from e


@with_management_error_handling
def generate_monitoring_report() -> Dict[str, Any]:
    """
    Generate a comprehensive monitoring report
    
    Returns:
        dict: Dictionary with monitoring information
    """
    try:
        # Monitor servers
        backend_metrics = monitor_backend()
        frontend_metrics = monitor_frontend()
        
        # Check system resources
        system_resources = check_system_resources()
        
        # Analyze logs
        log_analysis = {
            "backend": analyze_logs("logs/backend.log"),
            "frontend": analyze_logs("logs/frontend.log"),
            "management": analyze_logs("logs/management.log")
        }
        
        # Compile report
        report = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "servers": {
                "backend": backend_metrics.to_dict(),
                "frontend": frontend_metrics.to_dict()
            },
            "system": system_resources,
            "logs": log_analysis
        }
        
        return report
    except Exception as e:
        error_context = ErrorContext(
            source="generate_monitoring_report",
            severity=ErrorSeverity.ERROR,
            error_id="monitoring_report_error",
            additional_data={"error": str(e)}
        )
        raise MonitoringError("Failed to generate monitoring report", error_context) from e


@with_management_error_handling
def save_monitoring_report(report: Dict[str, Any], output_file: str = "monitoring_report.json") -> str:
    """
    Save monitoring report to a file
    
    Args:
        report: Monitoring report dictionary
        output_file: Output file path
        
    Returns:
        str: Path to saved file
    """
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Save report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return output_file
    except Exception as e:
        error_context = ErrorContext(
            source="save_monitoring_report",
            severity=ErrorSeverity.ERROR,
            error_id="report_save_error",
            additional_data={
                "error": str(e),
                "output_file": output_file
            }
        )
        raise MonitoringError("Failed to save monitoring report", error_context) from e


@with_management_error_handling
def print_monitoring_summary(report: Dict[str, Any]) -> None:
    """
    Print a human-readable summary of the monitoring report
    
    Args:
        report: Monitoring report dictionary
    """
    try:
        print("\n=== Monitoring Report Summary ===")
        print(f"Generated at: {report['timestamp']}\n")
        
        # Server status
        print("Server Status:")
        for server_type, metrics in report['servers'].items():
            print(f"  {server_type.title()}:")
            print(f"    Status: {metrics['status']}")
            print(f"    PID: {metrics['pid']}")
            print(f"    Uptime: {metrics['uptime']}")
            print(f"    CPU Usage: {metrics['avg_cpu_percent']}%")
            print(f"    Memory Usage: {metrics['avg_memory_mb']} MB")
            print(f"    Response Time: {metrics['avg_response_ms']} ms")
            print(f"    Error Count: {metrics['error_count']}")
        
        # System resources
        print("\nSystem Resources:")
        print(f"  CPU Usage: {report['system']['cpu']['percent']}%")
        print(f"  Memory Usage: {report['system']['memory']['percent']}%")
        print(f"  Disk Usage: {report['system']['disk']['percent_used']}%")
        
        # Log summary
        print("\nLog Summary:")
        for log_type, analysis in report['logs'].items():
            print(f"  {log_type.title()}:")
            print(f"    Errors: {analysis['error_count']}")
            print(f"    Warnings: {analysis['warning_count']}")
            if analysis['last_error']:
                print(f"    Last Error: {analysis['last_error'].strip()}")
    except Exception as e:
        error_context = ErrorContext(
            source="print_monitoring_summary",
            severity=ErrorSeverity.ERROR,
            error_id="summary_print_error",
            additional_data={"error": str(e)}
        )
        raise MonitoringError("Failed to print monitoring summary", error_context) from e 