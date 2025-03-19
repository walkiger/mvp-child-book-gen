"""
API endpoints for system monitoring and dashboard data.
Provides access to system metrics, server status, and logs for the monitoring dashboard.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from typing import Dict, List, Any, Optional, Set
import datetime
import httpx
import asyncio
import time
import logging
from datetime import UTC
from uuid import uuid4

from app.core.auth import get_current_admin_user
from app.database.models import User
from app.core.logging import setup_logger
from management.monitoring import (
    generate_monitoring_report, monitor_backend, monitor_frontend,
    check_system_resources, analyze_logs
)
from app.core.errors.monitoring import (
    MonitoringError,
    MetricsError,
    LogAnalysisError,
    RouteHealthError,
    ServerStatusError
)
from app.core.errors.base import ErrorContext, ErrorSeverity
from app.core.errors.api import with_api_error_handling

# Setup logger
logger = setup_logger(
    name="app.api.monitoring",
    level="INFO",
    log_file="logs/api.log"
)

# Create router without prefix (will be mounted at /api/v1/monitoring)
router = APIRouter(
    tags=["monitoring"],
    responses={404: {"description": "Not found"}},
)

# Store historical data in memory (in production, consider using a database)
historical_data = {
    "system": [],
    "backend": [],
    "frontend": [],
    "logs": []
}

# Maximum number of data points to store
MAX_HISTORY_LENGTH = 100

# Store route health check data
route_health_data = {
    "routes": {},
    "last_check": None
}

def create_monitoring_error_context(
    operation: str,
    error: Exception,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    additional_data: Optional[Dict[str, Any]] = None
) -> ErrorContext:
    """Create a standardized error context for monitoring operations."""
    return ErrorContext(
        source=f"api.monitoring.{operation}",
        severity=severity,
        timestamp=datetime.datetime.now(UTC),
        error_id=str(uuid4()),
        additional_data={
            "error_type": error.__class__.__name__,
            "error_message": str(error),
            **(additional_data or {})
        }
    )

@router.get("/current", response_model=Dict[str, Any])
@with_api_error_handling
async def get_current_metrics(current_user: User = Depends(get_current_admin_user)):
    """
    Get current system metrics, server status, and logs.
    Requires authentication.
    """
    try:
        # Generate monitoring report
        report = generate_monitoring_report()
        return report
    except Exception as e:
        error_context = create_monitoring_error_context(
            operation="get_current_metrics",
            error=e,
            additional_data={"user_id": current_user.id}
        )
        logger.error(
            f"Failed to generate monitoring report: {str(e)}",
            extra={"error_context": error_context.dict()}
        )
        raise MetricsError(
            message="Failed to generate monitoring report",
            error_code="MON-METRICS-001",
            context=error_context
        ) from e

@router.get("/system", response_model=Dict[str, Any])
@with_api_error_handling
async def get_system_metrics(current_user: User = Depends(get_current_admin_user)):
    """
    Get current system resource metrics (CPU, memory, disk).
    Requires authentication.
    """
    try:
        # Get system resources
        system_resources = check_system_resources()
        
        # Add timestamp
        system_resources["timestamp"] = datetime.datetime.now(UTC).isoformat()
        
        # Store in historical data
        historical_data["system"].append(system_resources)
        
        # Trim historical data if needed
        if len(historical_data["system"]) > MAX_HISTORY_LENGTH:
            historical_data["system"].pop(0)
        
        return system_resources
    except Exception as e:
        error_context = create_monitoring_error_context(
            operation="get_system_metrics",
            error=e,
            additional_data={
                "user_id": current_user.id,
                "historical_data_length": len(historical_data["system"])
            }
        )
        logger.error(
            f"Failed to get system metrics: {str(e)}",
            extra={"error_context": error_context.dict()}
        )
        raise MetricsError(
            message="Failed to retrieve system metrics",
            error_code="MON-METRICS-002",
            context=error_context
        ) from e

@router.get("/server-status", response_model=Dict[str, Any])
@with_api_error_handling
async def get_server_status(current_user: User = Depends(get_current_admin_user)):
    """
    Get current status of backend and frontend servers.
    Requires authentication.
    """
    try:
        # Monitor backend and frontend
        backend_status = await monitor_backend()
        frontend_status = await monitor_frontend()
        
        # Add timestamp
        timestamp = datetime.datetime.now(UTC).isoformat()
        status = {
            "backend": backend_status,
            "frontend": frontend_status,
            "timestamp": timestamp
        }
        
        # Store in historical data
        historical_data["backend"].append(backend_status)
        historical_data["frontend"].append(frontend_status)
        
        # Trim historical data if needed
        if len(historical_data["backend"]) > MAX_HISTORY_LENGTH:
            historical_data["backend"].pop(0)
        if len(historical_data["frontend"]) > MAX_HISTORY_LENGTH:
            historical_data["frontend"].pop(0)
        
        return status
    except Exception as e:
        error_context = create_monitoring_error_context(
            operation="get_server_status",
            error=e,
            additional_data={
                "user_id": current_user.id,
                "backend_history_length": len(historical_data["backend"]),
                "frontend_history_length": len(historical_data["frontend"])
            }
        )
        logger.error(
            f"Failed to get server status: {str(e)}",
            extra={"error_context": error_context.dict()}
        )
        raise ServerStatusError(
            message="Failed to retrieve server status",
            error_code="MON-SERVER-001",
            context=error_context
        ) from e

@router.get("/logs", response_model=Dict[str, Any])
@with_api_error_handling
async def get_logs(
    current_user: User = Depends(get_current_admin_user),
    log_type: str = "",
    limit: int = 100
):
    """
    Get system logs with optional filtering.
    Requires authentication.
    
    Args:
        log_type: Type of logs to retrieve (empty string for all types)
        limit: Maximum number of log entries to return (default 100)
        current_user: Current authenticated admin user
    """
    try:
        # Analyze logs
        logs = analyze_logs(log_type=log_type if log_type else None, limit=limit)
        
        # Add timestamp
        timestamp = datetime.datetime.now(UTC).isoformat()
        log_data = {
            "logs": logs,
            "timestamp": timestamp,
            "type": log_type if log_type else None,
            "limit": limit
        }
        
        # Store in historical data
        historical_data["logs"].append({
            "timestamp": timestamp,
            "count": len(logs),
            "type": log_type if log_type else None
        })
        
        # Trim historical data if needed
        if len(historical_data["logs"]) > MAX_HISTORY_LENGTH:
            historical_data["logs"].pop(0)
        
        return log_data
    except Exception as e:
        error_context = create_monitoring_error_context(
            operation="get_logs",
            error=e,
            additional_data={
                "user_id": current_user.id,
                "log_type": log_type,
                "limit": limit,
                "logs_history_length": len(historical_data["logs"])
            }
        )
        logger.error(
            f"Failed to retrieve logs: {str(e)}",
            extra={"error_context": error_context.dict()}
        )
        raise LogAnalysisError(
            message="Failed to retrieve system logs",
            error_code="MON-LOGS-001",
            context=error_context
        ) from e

@router.get("/history/system", response_model=List[Dict[str, Any]])
@with_api_error_handling
async def get_system_history(
    limit: int = 20,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get historical system metrics.
    Limit parameter controls how many data points to return.
    Requires authentication.
    """
    try:
        if limit < 1:
            error_context = ErrorContext(
                source="api.monitoring.get_system_history",
                severity=ErrorSeverity.WARNING,
                timestamp=datetime.datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"limit": limit}
            )
            raise MonitoringError(
                message="Limit must be greater than 0",
                error_code="MON-HIST-003",
                context=error_context
            )
        return historical_data["system"][-limit:]
    except MonitoringError:
        raise
    except Exception as e:
        error_context = create_monitoring_error_context(
            operation="get_system_history",
            error=e,
            additional_data={
                "user_id": current_user.id,
                "limit": limit,
                "history_length": len(historical_data["system"])
            }
        )
        raise MonitoringError(
            message="Failed to get system history",
            error_code="MON-HIST-004",
            context=error_context
        ) from e

@router.get("/history/server/{server_type}", response_model=List[Dict[str, Any]])
@with_api_error_handling
async def get_server_history(
    server_type: str,
    limit: int = 20,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get historical server metrics for a specific server type.
    Server type can be 'backend' or 'frontend'.
    Limit parameter controls how many data points to return.
    Requires authentication.
    """
    try:
        if server_type not in ["backend", "frontend"]:
            error_context = ErrorContext(
                source="api.monitoring.get_server_history",
                severity=ErrorSeverity.WARNING,
                timestamp=datetime.datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={
                    "server_type": server_type,
                    "valid_types": ["backend", "frontend"]
                }
            )
            raise MonitoringError(
                message="Invalid server type",
                error_code="MON-HIST-001",
                context=error_context,
                details={"valid_types": ["backend", "frontend"]}
            )
        
        if limit < 1:
            error_context = ErrorContext(
                source="api.monitoring.get_server_history",
                severity=ErrorSeverity.WARNING,
                timestamp=datetime.datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"limit": limit}
            )
            raise MonitoringError(
                message="Limit must be greater than 0",
                error_code="MON-HIST-003",
                context=error_context
            )
        
        return historical_data[server_type][-limit:]
    except MonitoringError:
        raise
    except Exception as e:
        error_context = create_monitoring_error_context(
            operation="get_server_history",
            error=e,
            additional_data={
                "server_type": server_type,
                "limit": limit,
                "history_length": len(historical_data.get(server_type, []))
            }
        )
        raise MonitoringError(
            message="Failed to get server history",
            error_code="MON-HIST-002",
            context=error_context
        ) from e

@router.post("/refresh", response_model=Dict[str, str])
@with_api_error_handling
async def refresh_metrics(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Refresh all metrics in the background.
    Returns immediately but triggers data collection.
    Requires authentication.
    """
    try:
        # Add tasks to refresh metrics in the background
        background_tasks.add_task(get_system_metrics, current_user)
        background_tasks.add_task(get_server_status, current_user)
        background_tasks.add_task(get_logs, None, 100)
        
        return {"status": "Refresh started in background"}
    except Exception as e:
        error_context = create_monitoring_error_context(
            operation="refresh_metrics",
            error=e,
            additional_data={"user_id": current_user.id}
        )
        raise MonitoringError(
            message="Failed to start metrics refresh",
            error_code="MON-REFRESH-001",
            context=error_context
        ) from e

@router.get("/routes", response_model=Dict[str, Any])
@with_api_error_handling
async def get_route_health(current_user: User = Depends(get_current_admin_user)):
    """
    Get health status of all registered API routes.
    Requires authentication.
    """
    try:
        return {
            "timestamp": datetime.datetime.now(UTC).isoformat(),
            "last_check": route_health_data["last_check"],
            "routes": route_health_data["routes"]
        }
    except Exception as e:
        error_context = create_monitoring_error_context(
            operation="get_route_health",
            error=e,
            additional_data={
                "user_id": current_user.id,
                "last_check": route_health_data.get("last_check")
            }
        )
        raise RouteHealthError(
            message="Failed to get route health data",
            error_code="MON-ROUTE-001",
            context=error_context
        ) from e

@router.post("/check-routes", response_model=Dict[str, str])
@with_api_error_handling
async def check_all_routes(
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Trigger a health check of all registered API routes.
    Runs in the background and updates route_health_data.
    Requires authentication.
    """
    try:
        # Start route health check in the background
        background_tasks.add_task(
            _check_all_routes,
            base_url=str(request.base_url)
        )
        
        return {"status": "Route health check started in background"}
    except Exception as e:
        error_context = create_monitoring_error_context(
            operation="check_all_routes",
            error=e,
            additional_data={
                "user_id": current_user.id,
                "base_url": str(request.base_url)
            }
        )
        raise RouteHealthError(
            message="Failed to start route health check",
            error_code="MON-ROUTE-002",
            context=error_context
        ) from e

async def _check_all_routes(base_url: str):
    """
    Check health of all registered API routes by making requests to them.
    Updates route_health_data with the results.
    """
    try:
        # Get the main FastAPI app to access all routes
        from app.main import app
        
        # Find all API routes (excluding monitoring routes to avoid recursion)
        api_routes = []
        for route in app.routes:
            if hasattr(route, "path") and route.path.startswith("/api/") and not route.path.startswith("/api/monitoring"):
                api_routes.append({
                    "path": route.path,
                    "methods": list(route.methods) if hasattr(route, "methods") else ["GET"]
                })
        
        # Initialize results
        results = {}
        
        # Create async client for making requests
        async with httpx.AsyncClient() as client:
            for route_info in api_routes:
                path = route_info["path"]
                methods = route_info["methods"]
                
                for method in methods:
                    if method not in ["GET", "HEAD"]:
                        # Skip non-GET methods as they require request bodies
                        continue
                    
                    # Construct full URL
                    url = f"{base_url.rstrip('/')}{path}"
                    
                    # Test the endpoint
                    try:
                        start_time = time.time()
                        response = await client.request(
                            method,
                            url,
                            follow_redirects=True,
                            timeout=5.0
                        )
                        end_time = time.time()
                        
                        # Calculate response time in ms
                        response_time = (end_time - start_time) * 1000
                        
                        # Store result
                        route_key = f"{method} {path}"
                        results[route_key] = {
                            "status_code": response.status_code,
                            "response_time_ms": round(response_time, 2),
                            "healthy": 200 <= response.status_code < 400,
                            "last_checked": datetime.datetime.now(UTC).isoformat()
                        }
                    except Exception as e:
                        # Handle request errors
                        route_key = f"{method} {path}"
                        results[route_key] = {
                            "status_code": None,
                            "response_time_ms": None,
                            "healthy": False,
                            "error": str(e),
                            "last_checked": datetime.datetime.now(UTC).isoformat()
                        }
        
        # Update the global route health data
        route_health_data["routes"] = results
        route_health_data["last_check"] = datetime.datetime.now(UTC).isoformat()
    except Exception as e:
        error_context = ErrorContext(
            source="api.monitoring._check_all_routes",
            severity=ErrorSeverity.ERROR,
            timestamp=datetime.datetime.now(UTC),
            error_id=str(uuid4()),
            additional_data={
                "base_url": base_url,
                "error": str(e)
            }
        )
        logger.error(
            f"Failed to check all routes: {str(e)}",
            extra={"error_context": error_context.dict()}
        )

@router.get("/health")
@with_api_error_handling
async def health_check():
    """
    Health check endpoint that returns the API status.
    This endpoint is public and does not require authentication.
    """
    try:
        return {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": datetime.datetime.now(UTC).isoformat()
        }
    except Exception as e:
        error_context = create_monitoring_error_context(
            operation="health_check",
            error=e
        )
        raise MonitoringError(
            message="Health check failed",
            error_code="MON-HEALTH-001",
            context=error_context
        ) from e

@router.get("/route-health", response_model=Dict[str, Any])
@with_api_error_handling
async def check_route_health(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Check health of all API routes.
    Requires authentication.
    """
    try:
        # Get all registered routes
        routes = [
            route for route in router.routes
            if route.path != "/route-health"  # Exclude this endpoint
        ]
        
        results = {}
        for route in routes:
            try:
                # Prepare test request
                url = f"http://localhost:8000{route.path}"
                async with httpx.AsyncClient() as client:
                    response = await client.request(
                        route.methods[0],  # Use first allowed method
                        url,
                        timeout=5.0
                    )
                results[route.path] = {
                    "status": response.status_code,
                    "latency": response.elapsed.total_seconds(),
                    "timestamp": datetime.datetime.now(UTC).isoformat()
                }
            except Exception as e:
                results[route.path] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.datetime.now(UTC).isoformat()
                }
        
        # Update route health data
        route_health_data["routes"].update(results)
        route_health_data["last_check"] = datetime.datetime.now(UTC).isoformat()
        
        return route_health_data
    except Exception as e:
        error_context = create_monitoring_error_context(
            operation="check_route_health",
            error=e,
            additional_data={
                "user_id": current_user.id,
                "routes_checked": len(router.routes),
                "last_check": route_health_data["last_check"]
            }
        )
        logger.error(
            f"Failed to check route health: {str(e)}",
            extra={"error_context": error_context.dict()}
        )
        raise RouteHealthError(
            message="Failed to check route health",
            error_code="MON-ROUTE-001",
            context=error_context
        ) from e

@router.post("/clear-history", response_model=Dict[str, str])
@with_api_error_handling
async def clear_monitoring_history(current_user: User = Depends(get_current_admin_user)):
    """
    Clear all monitoring history data.
    Requires authentication.
    """
    try:
        # Clear all historical data
        historical_data["system"].clear()
        historical_data["backend"].clear()
        historical_data["frontend"].clear()
        historical_data["logs"].clear()
        route_health_data["routes"].clear()
        route_health_data["last_check"] = None
        
        return {"message": "Monitoring history cleared successfully"}
    except Exception as e:
        error_context = create_monitoring_error_context(
            operation="clear_monitoring_history",
            error=e,
            additional_data={"user_id": current_user.id}
        )
        logger.error(
            f"Failed to clear monitoring history: {str(e)}",
            extra={"error_context": error_context.dict()}
        )
        raise MonitoringError(
            message="Failed to clear monitoring history",
            error_code="MON-CLEAR-001",
            context=error_context
        ) from e 