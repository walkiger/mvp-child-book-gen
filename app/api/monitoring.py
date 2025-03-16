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

from app.core.auth import get_current_admin_user
from app.database.models import User
from management.monitoring import (
    generate_monitoring_report, monitor_backend, monitor_frontend,
    check_system_resources, analyze_logs
)

# Create router with "/api/monitoring" prefix
router = APIRouter(
    prefix="/api/monitoring",
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


@router.get("/current", response_model=Dict[str, Any])
async def get_current_metrics(current_user: User = Depends(get_current_admin_user)):
    """
    Get current system metrics, server status, and logs.
    Requires authentication.
    """
    # Generate monitoring report
    report = generate_monitoring_report()
    
    # Return the report data
    return report


@router.get("/system", response_model=Dict[str, Any])
async def get_system_metrics(current_user: User = Depends(get_current_admin_user)):
    """
    Get current system resource metrics (CPU, memory, disk).
    Requires authentication.
    """
    # Get system resources
    system_resources = check_system_resources()
    
    # Add timestamp
    system_resources["timestamp"] = datetime.datetime.now().isoformat()
    
    # Store in historical data
    historical_data["system"].append(system_resources)
    
    # Trim historical data if needed
    if len(historical_data["system"]) > MAX_HISTORY_LENGTH:
        historical_data["system"].pop(0)
    
    return system_resources


@router.get("/servers", response_model=Dict[str, Any])
async def get_server_status(current_user: User = Depends(get_current_admin_user)):
    """
    Get current server status for backend and frontend.
    Requires authentication.
    """
    # Monitor backend and frontend
    backend_metrics = monitor_backend()
    frontend_metrics = monitor_frontend()
    
    # Create response with timestamp
    timestamp = datetime.datetime.now().isoformat()
    response = {
        "timestamp": timestamp,
        "backend": backend_metrics.to_dict(),
        "frontend": frontend_metrics.to_dict()
    }
    
    # Store in historical data
    historical_data["backend"].append({
        "timestamp": timestamp,
        **backend_metrics.to_dict()
    })
    historical_data["frontend"].append({
        "timestamp": timestamp,
        **frontend_metrics.to_dict()
    })
    
    # Trim historical data if needed
    if len(historical_data["backend"]) > MAX_HISTORY_LENGTH:
        historical_data["backend"].pop(0)
    if len(historical_data["frontend"]) > MAX_HISTORY_LENGTH:
        historical_data["frontend"].pop(0)
    
    return response


@router.get("/logs", response_model=Dict[str, Any])
async def get_logs_summary(
    log_file: Optional[str] = None,
    lines: int = 100,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get summary of log files with error counts and recent errors.
    Optionally specify a specific log file to analyze.
    Requires authentication.
    """
    logs_data = {}
    timestamp = datetime.datetime.now().isoformat()
    
    if log_file:
        # Analyze specific log file
        logs_data[log_file] = analyze_logs(f"logs/{log_file}.log", lines)
    else:
        # Analyze all standard logs
        logs_data = {
            "app": analyze_logs("logs/app.log", lines),
            "management": analyze_logs("logs/management.log", lines),
            "backend": analyze_logs("logs/backend.log", lines),
            "frontend": analyze_logs("logs/frontend.log", lines)
        }
    
    # Create response with timestamp
    response = {
        "timestamp": timestamp,
        "logs": logs_data
    }
    
    # Store in historical data
    historical_data["logs"].append(response)
    
    # Trim historical data if needed
    if len(historical_data["logs"]) > MAX_HISTORY_LENGTH:
        historical_data["logs"].pop(0)
    
    return response


@router.get("/history/system", response_model=List[Dict[str, Any]])
async def get_system_history(
    limit: int = 20,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get historical system metrics.
    Limit parameter controls how many data points to return.
    Requires authentication.
    """
    return historical_data["system"][-limit:]


@router.get("/history/server/{server_type}", response_model=List[Dict[str, Any]])
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
    if server_type not in ["backend", "frontend"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid server type. Must be 'backend' or 'frontend'."
        )
    
    return historical_data[server_type][-limit:]


@router.post("/refresh", response_model=Dict[str, str])
async def refresh_metrics(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Refresh all metrics in the background.
    Returns immediately but triggers data collection.
    Requires authentication.
    """
    # Add tasks to refresh metrics in the background
    background_tasks.add_task(get_system_metrics, current_user)
    background_tasks.add_task(get_server_status, current_user)
    background_tasks.add_task(get_logs_summary, None, 100, current_user)
    
    return {"status": "Refresh started in background"}


@router.get("/routes", response_model=Dict[str, Any])
async def get_route_health(current_user: User = Depends(get_current_admin_user)):
    """
    Get health status of all registered API routes.
    Requires authentication.
    """
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "last_check": route_health_data["last_check"],
        "routes": route_health_data["routes"]
    }


@router.post("/check-routes", response_model=Dict[str, str])
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
    # Start route health check in the background
    background_tasks.add_task(
        _check_all_routes,
        base_url=str(request.base_url)
    )
    
    return {"status": "Route health check started in background"}


async def _check_all_routes(base_url: str):
    """
    Check health of all registered API routes by making requests to them.
    Updates route_health_data with the results.
    """
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
                        "last_checked": datetime.datetime.now().isoformat()
                    }
                except Exception as e:
                    # Handle request errors
                    route_key = f"{method} {path}"
                    results[route_key] = {
                        "status_code": None,
                        "response_time_ms": None,
                        "healthy": False,
                        "error": str(e),
                        "last_checked": datetime.datetime.now().isoformat()
                    }
    
    # Update the global route health data
    route_health_data["routes"] = results
    route_health_data["last_check"] = datetime.datetime.now().isoformat() 