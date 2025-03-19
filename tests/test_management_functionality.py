import pytest
import asyncio
import psutil
import os
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi import FastAPI
from httpx import AsyncClient

from management.pid_utils import get_process_info, check_process_running
from management.monitoring import SystemMonitor, MetricsCollector
from management.server_utils import check_server_health, get_server_metrics
from management.db_utils import check_database_health, get_database_metrics
from management.error_utils import format_error_message, parse_error_code
from management.content_inspection import ContentInspector
from management.db_inspection import DatabaseInspector
from management.dashboard import DashboardMetrics

# Test PID Utils
class TestPIDUtils:
    def test_get_process_info(self):
        """Test getting process information"""
        # Test with current process
        current_pid = os.getpid()
        process_info = get_process_info(current_pid)
        
        assert process_info is not None
        assert "cpu_percent" in process_info
        assert "memory_percent" in process_info
        assert "status" in process_info
        
        # Test with non-existent process
        assert get_process_info(999999) is None
    
    def test_check_process_running(self):
        """Test checking if process is running"""
        # Test with current process
        current_pid = os.getpid()
        assert check_process_running(current_pid) is True
        
        # Test with non-existent process
        assert check_process_running(999999) is False

# Test Monitoring
class TestMonitoring:
    @pytest.fixture
    def system_monitor(self):
        """Create a system monitor instance"""
        return SystemMonitor()
    
    @pytest.fixture
    def metrics_collector(self):
        """Create a metrics collector instance"""
        return MetricsCollector()
    
    def test_system_monitor_metrics(self, system_monitor):
        """Test system monitor metrics collection"""
        metrics = system_monitor.collect_metrics()
        
        assert "cpu_usage" in metrics
        assert "memory_usage" in metrics
        assert "disk_usage" in metrics
        assert isinstance(metrics["cpu_usage"], float)
        assert isinstance(metrics["memory_usage"], float)
        assert isinstance(metrics["disk_usage"], dict)
    
    def test_metrics_collector_storage(self, metrics_collector):
        """Test metrics storage and retrieval"""
        test_metrics = {
            "test_metric": 42.0,
            "timestamp": datetime.now()
        }
        
        metrics_collector.store_metrics(test_metrics)
        stored_metrics = metrics_collector.get_recent_metrics(minutes=5)
        
        assert len(stored_metrics) > 0
        assert any(m["test_metric"] == 42.0 for m in stored_metrics)

# Test Server Utils
class TestServerUtils:
    @pytest.mark.asyncio
    async def test_server_health_check(self):
        """Test server health check functionality"""
        app = FastAPI()
        
        @app.get("/health")
        async def health():
            return {"status": "healthy"}
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            health_status = await check_server_health(client)
            assert health_status["status"] == "healthy"
    
    def test_server_metrics(self):
        """Test server metrics collection"""
        metrics = get_server_metrics()
        
        assert "uptime" in metrics
        assert "request_count" in metrics
        assert "error_count" in metrics
        assert isinstance(metrics["uptime"], float)
        assert isinstance(metrics["request_count"], int)
        assert isinstance(metrics["error_count"], int)

# Test DB Utils
class TestDBUtils:
    @pytest.fixture
    def test_db(self):
        """Create a test database connection"""
        conn = sqlite3.connect(":memory:")
        yield conn
        conn.close()
    
    def test_database_health_check(self, test_db):
        """Test database health check functionality"""
        health_status = check_database_health(test_db)
        
        assert health_status["status"] in ["healthy", "unhealthy"]
        assert "connection_pool" in health_status
        assert "active_connections" in health_status
    
    def test_database_metrics(self, test_db):
        """Test database metrics collection"""
        metrics = get_database_metrics(test_db)
        
        assert "query_count" in metrics
        assert "slow_queries" in metrics
        assert "error_count" in metrics
        assert isinstance(metrics["query_count"], int)
        assert isinstance(metrics["slow_queries"], list)
        assert isinstance(metrics["error_count"], int)

# Test Error Utils
class TestErrorUtils:
    def test_format_error_message(self):
        """Test error message formatting"""
        error_data = {
            "code": "TEST-001",
            "message": "Test error",
            "details": {"key": "value"}
        }
        
        formatted_message = format_error_message(error_data)
        assert "TEST-001" in formatted_message
        assert "Test error" in formatted_message
        assert "key: value" in formatted_message
    
    def test_parse_error_code(self):
        """Test error code parsing"""
        error_code = "TEST-ERR-001"
        parsed = parse_error_code(error_code)
        
        assert parsed["domain"] == "TEST"
        assert parsed["category"] == "ERR"
        assert parsed["number"] == "001"

# Test Content Inspection
class TestContentInspection:
    @pytest.fixture
    def content_inspector(self):
        """Create a content inspector instance"""
        return ContentInspector()
    
    def test_content_validation(self, content_inspector):
        """Test content validation functionality"""
        valid_content = {
            "title": "Test Story",
            "content": "Once upon a time...",
            "age_range": "6-8"
        }
        
        validation_result = content_inspector.validate_content(valid_content)
        assert validation_result["is_valid"] is True
        assert len(validation_result["errors"]) == 0
        
        invalid_content = {
            "title": "",  # Empty title
            "content": "Too short",
            "age_range": "invalid"
        }
        
        validation_result = content_inspector.validate_content(invalid_content)
        assert validation_result["is_valid"] is False
        assert len(validation_result["errors"]) > 0

# Test DB Inspection
class TestDBInspection:
    @pytest.fixture
    def db_inspector(self):
        """Create a database inspector instance"""
        return DatabaseInspector(":memory:")
    
    def test_table_inspection(self, db_inspector):
        """Test database table inspection"""
        tables_info = db_inspector.get_tables_info()
        assert isinstance(tables_info, dict)
        
        for table in tables_info.values():
            assert "columns" in table
            assert "row_count" in table
            assert "size" in table
    
    def test_query_analysis(self, db_inspector):
        """Test query analysis functionality"""
        test_query = "SELECT * FROM test_table WHERE id = ?"
        analysis = db_inspector.analyze_query(test_query)
        
        assert "complexity" in analysis
        assert "tables_accessed" in analysis
        assert "estimated_cost" in analysis

# Test Dashboard
class TestDashboard:
    @pytest.fixture
    def dashboard_metrics(self):
        """Create dashboard metrics instance"""
        return DashboardMetrics()
    
    def test_metrics_collection(self, dashboard_metrics):
        """Test dashboard metrics collection"""
        metrics = dashboard_metrics.collect_all_metrics()
        
        assert "system" in metrics
        assert "application" in metrics
        assert "database" in metrics
        assert isinstance(metrics["system"], dict)
        assert isinstance(metrics["application"], dict)
        assert isinstance(metrics["database"], dict)
    
    def test_metrics_aggregation(self, dashboard_metrics):
        """Test metrics aggregation functionality"""
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()
        
        aggregated_metrics = dashboard_metrics.aggregate_metrics(
            start_time=start_time,
            end_time=end_time,
            interval="5m"
        )
        
        assert len(aggregated_metrics) > 0
        for metric in aggregated_metrics:
            assert "timestamp" in metric
            assert "values" in metric
            assert isinstance(metric["values"], dict)

if __name__ == "__main__":
    pytest.main(["-v", "test_management_functionality.py"]) 