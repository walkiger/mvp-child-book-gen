# Monitoring API Documentation

## Overview
The Monitoring API (`app/api/monitoring.py`) provides endpoints for system monitoring, metrics collection, and health checks. It includes real-time monitoring, historical data tracking, and comprehensive logging capabilities.

## Endpoints

### Current Metrics
1. **Get Current Metrics** (`GET /current`)
   - System-wide metrics
   - Server status
   - Log summaries
   - Real-time data

2. **Get System Metrics** (`GET /system`)
   - CPU usage
   - Memory usage
   - Disk metrics
   - Resource tracking

3. **Get Server Status** (`GET /servers`)
   - Backend status
   - Frontend status
   - Service health
   - Performance data

### Historical Data
1. **Get System History** (`GET /history/system`)
   - Historical metrics
   - Trend analysis
   - Performance tracking
   - Resource usage

2. **Get Server History** (`GET /history/server/{server_type}`)
   - Server-specific history
   - Performance trends
   - Health tracking
   - Usage patterns

### Logs and Analysis
1. **Get Logs Summary** (`GET /logs`)
   - Error counts
   - Recent errors
   - Log analysis
   - Pattern detection

2. **Refresh Metrics** (`POST /refresh`)
   - Background updates
   - Data collection
   - Metric refresh
   - Async processing

### Route Health
1. **Get Route Health** (`GET /routes`)
   - API route status
   - Health checks
   - Response times
   - Error rates

2. **Check All Routes** (`POST /check-routes`)
   - Route validation
   - Health verification
   - Status updates
   - Background checks

## Implementation Examples

### System Metrics Collection
```python
@router.get("/system", response_model=Dict[str, Any])
async def get_system_metrics(current_user: User = Depends(get_current_admin_user)):
    """Get current system resource metrics."""
    system_resources = check_system_resources()
    system_resources["timestamp"] = datetime.datetime.now().isoformat()
    
    historical_data["system"].append(system_resources)
    if len(historical_data["system"]) > MAX_HISTORY_LENGTH:
        historical_data["system"].pop(0)
    
    return system_resources
```

### Log Analysis
```python
@router.get("/logs", response_model=Dict[str, Any])
async def get_logs_summary(
    log_file: Optional[str] = None,
    lines: int = 100,
    current_user: User = Depends(get_current_admin_user)
):
    """Get summary of log files with error counts."""
    logs_data = {}
    timestamp = datetime.datetime.now().isoformat()
    
    if log_file:
        logs_data[log_file] = analyze_logs(f"logs/{log_file}.log", lines)
    else:
        logs_data = {
            "app": analyze_logs("logs/app.log", lines),
            "management": analyze_logs("logs/management.log", lines),
            "backend": analyze_logs("logs/backend.log", lines),
            "frontend": analyze_logs("logs/frontend.log", lines)
        }
    
    return {"timestamp": timestamp, "logs": logs_data}
```

## Error Classes

### MonitoringError
- **Error Code Pattern**: `MON-*`
- **Purpose**: Handle monitoring failures
- **Example**: `MON-SYS-001`
- **Suggestions**:
  - Check permissions
  - Verify metrics
  - Review access
  - Check resources

### MetricCollectionError
- **Error Code Pattern**: `MON-MET-*`
- **Purpose**: Handle metric collection issues
- **Example**: `MON-MET-001`
- **Suggestions**:
  - Check collectors
  - Verify sources
  - Review timing
  - Check storage

### LogAnalysisError
- **Error Code Pattern**: `MON-LOG-*`
- **Purpose**: Handle log analysis failures
- **Example**: `MON-LOG-001`
- **Suggestions**:
  - Check log files
  - Verify format
  - Review access
  - Check parsing

## Best Practices

1. **Data Collection**
   - Regular intervals
   - Efficient storage
   - Data cleanup
   - Resource limits

2. **Error Handling**
   - Specific errors
   - Context inclusion
   - Log failures
   - Recovery steps

3. **Performance**
   - Background tasks
   - Data aggregation
   - Efficient storage
   - Resource usage

4. **Security**
   - Admin access
   - Data protection
   - Access control
   - Audit logging

## Integration Points

1. **System Monitoring**
   - Resource metrics
   - Performance data
   - Health checks
   - Alert triggers

2. **Log Management**
   - Log collection
   - Analysis tools
   - Pattern detection
   - Alert generation

3. **Metrics Storage**
   - Data persistence
   - Historical tracking
   - Trend analysis
   - Data cleanup

## Testing Requirements

1. **Endpoint Testing**
   - Metric collection
   - Log analysis
   - Health checks
   - Error handling

2. **Performance Testing**
   - Response times
   - Resource usage
   - Data storage
   - Background tasks

3. **Integration Testing**
   - System metrics
   - Log analysis
   - Health checks
   - Alert triggers

## Future Improvements

1. **Short-term**
   - Enhanced metrics
   - Better visualization
   - Alert integration
   - Performance optimization

2. **Long-term**
   - ML-based analysis
   - Predictive alerts
   - Custom dashboards
   - Distributed monitoring 