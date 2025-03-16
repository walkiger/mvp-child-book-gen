import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Container, 
  Typography, 
  Grid, 
  Paper, 
  Card, 
  CardContent, 
  CircularProgress,
  Tabs,
  Tab,
  Alert,
  Chip,
  Button,
  Divider,
  Table,
  TableBody, 
  TableCell, 
  TableHead,
  TableRow
} from '@mui/material';
import { styled } from '@mui/material/styles';
import RefreshIcon from '@mui/icons-material/Refresh';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import WarningIcon from '@mui/icons-material/Warning';
import MemoryIcon from '@mui/icons-material/Memory';
import StorageIcon from '@mui/icons-material/Storage';
import SystemUpdateAltIcon from '@mui/icons-material/SystemUpdateAlt';
import useAuth from '../hooks/useAuth';
import LoadingState from '../components/LoadingState';
import ErrorDisplay from '../components/ErrorDisplay';
import { ApiError, formatApiError, retryOperation } from '../lib/errorHandling';

// Define styled components
const StyledPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  marginBottom: theme.spacing(3),
  borderRadius: theme.shape.borderRadius,
  boxShadow: theme.shadows[2],
}));

const StatusChip = styled(Chip)(({ theme }) => ({
  fontWeight: 'bold',
  marginLeft: theme.spacing(1),
}));

const MetricCard = styled(Card)(({ theme }) => ({
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  boxShadow: theme.shadows[2],
}));

const TabPanel = (props: { children?: React.ReactNode; index: number; value: number }) => {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`monitoring-tabpanel-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
};

// Main component
const Monitoring: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [tabValue, setTabValue] = useState<number>(0);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [routeHealth, setRouteHealth] = useState<any>(null);
  const [loadingRoutes, setLoadingRoutes] = useState<boolean>(false);
  const { token } = useAuth();

  // Fetch monitoring data
  const fetchMonitoringData = async () => {
    setRefreshing(true);
    try {
      const response = await retryOperation(async () => {
        const res = await fetch('/api/monitoring/current', {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }

        return res;
      });

      const data = await response.json();
      setMetrics(data);
      setError(null);
    } catch (err) {
      const apiError = formatApiError(err);
      setError(apiError);
      console.error('Error fetching monitoring data:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Trigger a refresh of all metrics
  const triggerRefresh = async () => {
    try {
      await retryOperation(async () => {
        const response = await fetch('/api/monitoring/refresh', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        return response;
      });
      
      // After triggering refresh, fetch the updated data
      fetchMonitoringData();
    } catch (err) {
      const apiError = formatApiError(err);
      setError(apiError);
      console.error('Error triggering refresh:', err);
    }
  };

  // Add a function to fetch route health data
  const fetchRouteHealth = async () => {
    try {
      const response = await retryOperation(async () => {
        const res = await fetch('/api/monitoring/routes', {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }

        return res;
      });

      const data = await response.json();
      setRouteHealth(data);
      setError(null);
    } catch (err) {
      const apiError = formatApiError(err);
      setError(apiError);
      console.error('Error fetching route health data:', err);
    }
  };

  // Add a function to trigger route health check
  const triggerRouteHealthCheck = async () => {
    setLoadingRoutes(true);
    try {
      await retryOperation(async () => {
        const response = await fetch('/api/monitoring/check-routes', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        return response;
      });
      
      // Wait a moment for the background task to run
      setTimeout(() => {
        fetchRouteHealth();
        setLoadingRoutes(false);
      }, 2000);
    } catch (err) {
      const apiError = formatApiError(err);
      setError(apiError);
      console.error('Error triggering route health check:', err);
      setLoadingRoutes(false);
    }
  };

  // Initial data load
  useEffect(() => {
    fetchMonitoringData();
    fetchRouteHealth();
    
    // Set up polling interval (every 30 seconds)
    const interval = setInterval(() => {
      fetchMonitoringData();
    }, 30000);
    
    // Clean up on unmount
    return () => clearInterval(interval);
  }, [token]);

  // Handle tab change
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    event.preventDefault(); // Prevent default behavior
    setTabValue(newValue);
  };

  // Helper function to render server status
  const renderServerStatus = (status: string) => {
    if (status === 'Healthy' || status === 'Running') {
      return <StatusChip label={status} color="success" icon={<CheckCircleIcon />} />;
    } else if (status === 'Unreachable' || status.includes('Unhealthy')) {
      return <StatusChip label={status} color="error" icon={<ErrorIcon />} />;
    } else {
      return <StatusChip label={status} color="warning" icon={<WarningIcon />} />;
    }
  };

  // Add a helper function to render health status
  const renderHealthStatus = (healthy: boolean) => {
    if (healthy) {
      return <Chip label="Healthy" color="success" icon={<CheckCircleIcon />} size="small" />;
    } else {
      return <Chip label="Unhealthy" color="error" icon={<ErrorIcon />} size="small" />;
    }
  };

  if (loading && !metrics) {
    return (
      <Box>
        <LoadingState variant="spinner" text="Loading monitoring data..." />
      </Box>
    );
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            System Monitoring
          </Typography>
          <Button 
            variant="contained" 
            startIcon={<RefreshIcon />} 
            onClick={triggerRefresh}
            disabled={refreshing}
          >
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </Button>
        </Box>

        {error && (
          <Box sx={{ mb: 3 }}>
            <ErrorDisplay 
              error={error} 
              onRetry={error.retry ? fetchMonitoringData : undefined}
            />
          </Box>
        )}

        <Tabs value={tabValue} onChange={handleTabChange} sx={{ mb: 2 }}>
          <Tab label="Overview" />
          <Tab label="System" />
          <Tab label="Servers" />
          <Tab label="Logs" />
          <Tab label="API Routes" />
        </Tabs>

        {metrics && (
          <>
            {/* Overview Tab */}
            <TabPanel value={tabValue} index={0}>
              <StyledPaper>
                <Typography variant="h6" gutterBottom>
                  System Information
                </Typography>
                <Typography variant="body1">
                  Hostname: {metrics.system.hostname}
                </Typography>
                <Typography variant="body1">
                  OS: {metrics.system.os}
                </Typography>
                <Typography variant="body1">
                  Timestamp: {metrics.timestamp}
                </Typography>
              </StyledPaper>

              <StyledPaper>
                <Typography variant="h6" gutterBottom>
                  Server Status
                </Typography>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <MetricCard>
                      <CardContent>
                        <Typography variant="h6" color="text.secondary" gutterBottom>
                          Backend Server
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                          <Typography variant="body1">
                            Status:
                          </Typography>
                          {renderServerStatus(metrics.servers.backend.status)}
                        </Box>
                        <Typography variant="body2">
                          Uptime: {metrics.servers.backend.uptime}
                        </Typography>
                        <Typography variant="body2">
                          PID: {metrics.servers.backend.pid || 'N/A'}
                        </Typography>
                        <Typography variant="body2">
                          Response Time: {metrics.servers.backend.avg_response_ms.toFixed(2)} ms
                        </Typography>
                      </CardContent>
                    </MetricCard>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <MetricCard>
                      <CardContent>
                        <Typography variant="h6" color="text.secondary" gutterBottom>
                          Frontend Server
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                          <Typography variant="body1">
                            Status:
                          </Typography>
                          {renderServerStatus(metrics.servers.frontend.status)}
                        </Box>
                        <Typography variant="body2">
                          Uptime: {metrics.servers.frontend.uptime}
                        </Typography>
                        <Typography variant="body2">
                          PID: {metrics.servers.frontend.pid || 'N/A'}
                        </Typography>
                        <Typography variant="body2">
                          Response Time: {metrics.servers.frontend.avg_response_ms.toFixed(2)} ms
                        </Typography>
                      </CardContent>
                    </MetricCard>
                  </Grid>
                </Grid>
              </StyledPaper>

              <StyledPaper>
                <Typography variant="h6" gutterBottom>
                  Resource Usage
                </Typography>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={4}>
                    <MetricCard>
                      <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                          <MemoryIcon color="primary" sx={{ mr: 1 }} />
                          <Typography variant="h6" color="text.secondary">
                            CPU
                          </Typography>
                        </Box>
                        <Typography variant="h4">
                          {metrics.system.resources.cpu_percent}%
                        </Typography>
                      </CardContent>
                    </MetricCard>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <MetricCard>
                      <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                          <StorageIcon color="primary" sx={{ mr: 1 }} />
                          <Typography variant="h6" color="text.secondary">
                            Memory
                          </Typography>
                        </Box>
                        <Typography variant="h4">
                          {metrics.system.resources.memory_percent}%
                        </Typography>
                        <Typography variant="body2">
                          Available: {metrics.system.resources.memory_available_gb} GB
                        </Typography>
                      </CardContent>
                    </MetricCard>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <MetricCard>
                      <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                          <SystemUpdateAltIcon color="primary" sx={{ mr: 1 }} />
                          <Typography variant="h6" color="text.secondary">
                            Disk
                          </Typography>
                        </Box>
                        <Typography variant="h4">
                          {metrics.system.resources.disk_usage.percent_used}%
                        </Typography>
                        <Typography variant="body2">
                          Used: {metrics.system.resources.disk_usage.used_gb} / {metrics.system.resources.disk_usage.total_gb} GB
                        </Typography>
                      </CardContent>
                    </MetricCard>
                  </Grid>
                </Grid>
              </StyledPaper>
            </TabPanel>

            {/* System Tab */}
            <TabPanel value={tabValue} index={1}>
              <StyledPaper>
                <Typography variant="h6" gutterBottom>
                  Detailed System Metrics
                </Typography>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle1">System Information</Typography>
                    <Divider sx={{ my: 1 }} />
                    <Typography variant="body2">
                      Hostname: {metrics.system.hostname}
                    </Typography>
                    <Typography variant="body2">
                      OS: {metrics.system.os}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle1">Resource Metrics</Typography>
                    <Divider sx={{ my: 1 }} />
                    <Typography variant="body2">
                      CPU Usage: {metrics.system.resources.cpu_percent}%
                    </Typography>
                    <Typography variant="body2">
                      Memory Usage: {metrics.system.resources.memory_percent}%
                    </Typography>
                    <Typography variant="body2">
                      Memory Available: {metrics.system.resources.memory_available_gb} GB
                    </Typography>
                    <Typography variant="body2">
                      Disk Total: {metrics.system.resources.disk_usage.total_gb} GB
                    </Typography>
                    <Typography variant="body2">
                      Disk Used: {metrics.system.resources.disk_usage.used_gb} GB
                    </Typography>
                    <Typography variant="body2">
                      Disk Free: {metrics.system.resources.disk_usage.free_gb} GB
                    </Typography>
                  </Grid>
                </Grid>
              </StyledPaper>
            </TabPanel>

            {/* Servers Tab */}
            <TabPanel value={tabValue} index={2}>
              <StyledPaper>
                <Typography variant="h6" gutterBottom>
                  Backend Server
                </Typography>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle1">Status Information</Typography>
                    <Divider sx={{ my: 1 }} />
                    <Box sx={{ display: 'flex', alignItems: 'center', my: 1 }}>
                      <Typography variant="body2" sx={{ minWidth: 120 }}>
                        Status:
                      </Typography>
                      {renderServerStatus(metrics.servers.backend.status)}
                    </Box>
                    <Typography variant="body2">
                      PID: {metrics.servers.backend.pid || 'N/A'}
                    </Typography>
                    <Typography variant="body2">
                      Uptime: {metrics.servers.backend.uptime}
                    </Typography>
                    <Typography variant="body2">
                      Last Checked: {metrics.servers.backend.last_checked}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle1">Performance Metrics</Typography>
                    <Divider sx={{ my: 1 }} />
                    <Typography variant="body2">
                      Avg. CPU Usage: {metrics.servers.backend.avg_cpu_percent}%
                    </Typography>
                    <Typography variant="body2">
                      Avg. Memory Usage: {metrics.servers.backend.avg_memory_mb} MB
                    </Typography>
                    <Typography variant="body2">
                      Avg. Response Time: {metrics.servers.backend.avg_response_ms.toFixed(2)} ms
                    </Typography>
                    <Typography variant="body2">
                      Error Count: {metrics.servers.backend.error_count}
                    </Typography>
                  </Grid>
                </Grid>
              </StyledPaper>

              <StyledPaper>
                <Typography variant="h6" gutterBottom>
                  Frontend Server
                </Typography>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle1">Status Information</Typography>
                    <Divider sx={{ my: 1 }} />
                    <Box sx={{ display: 'flex', alignItems: 'center', my: 1 }}>
                      <Typography variant="body2" sx={{ minWidth: 120 }}>
                        Status:
                      </Typography>
                      {renderServerStatus(metrics.servers.frontend.status)}
                    </Box>
                    <Typography variant="body2">
                      PID: {metrics.servers.frontend.pid || 'N/A'}
                    </Typography>
                    <Typography variant="body2">
                      Uptime: {metrics.servers.frontend.uptime}
                    </Typography>
                    <Typography variant="body2">
                      Last Checked: {metrics.servers.frontend.last_checked}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle1">Performance Metrics</Typography>
                    <Divider sx={{ my: 1 }} />
                    <Typography variant="body2">
                      Avg. CPU Usage: {metrics.servers.frontend.avg_cpu_percent}%
                    </Typography>
                    <Typography variant="body2">
                      Avg. Memory Usage: {metrics.servers.frontend.avg_memory_mb} MB
                    </Typography>
                    <Typography variant="body2">
                      Avg. Response Time: {metrics.servers.frontend.avg_response_ms.toFixed(2)} ms
                    </Typography>
                    <Typography variant="body2">
                      Error Count: {metrics.servers.frontend.error_count}
                    </Typography>
                  </Grid>
                </Grid>
              </StyledPaper>
            </TabPanel>

            {/* Logs Tab */}
            <TabPanel value={tabValue} index={3}>
              <StyledPaper>
                <Typography variant="h6" gutterBottom>
                  Log Analysis
                </Typography>
                <Grid container spacing={3}>
                  {Object.entries(metrics.logs).map(([logName, logData]: [string, any]) => (
                    <Grid item xs={12} md={6} key={logName}>
                      <MetricCard>
                        <CardContent>
                          <Typography variant="h6" color="text.secondary" gutterBottom>
                            {logName.charAt(0).toUpperCase() + logName.slice(1)} Log
                          </Typography>
                          
                          {"error" in logData ? (
                            <Alert severity="error">{logData.error}</Alert>
                          ) : (
                            <>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                                <Chip 
                                  label={`${logData.error_count} errors`} 
                                  color={logData.error_count > 0 ? "error" : "default"}
                                  size="small"
                                />
                                <Chip 
                                  label={`${logData.warning_count} warnings`} 
                                  color={logData.warning_count > 0 ? "warning" : "default"}
                                  size="small"
                                />
                                <Chip 
                                  label={`${logData.info_count} info`}
                                  color="info"
                                  size="small"
                                />
                              </Box>
                              
                              {logData.recent_errors.length > 0 && (
                                <>
                                  <Typography variant="subtitle2" sx={{ mt: 2 }}>
                                    Recent Errors:
                                  </Typography>
                                  <Box sx={{ 
                                    mt: 1, 
                                    p: 1, 
                                    backgroundColor: '#f5f5f5', 
                                    borderRadius: 1,
                                    maxHeight: 150,
                                    overflow: 'auto'
                                  }}>
                                    {logData.recent_errors.map((error: string, index: number) => (
                                      <Typography key={index} variant="body2" component="div" sx={{ 
                                        fontFamily: 'monospace', 
                                        fontSize: '0.8rem',
                                        mb: 0.5
                                      }}>
                                        {error}
                                      </Typography>
                                    ))}
                                  </Box>
                                </>
                              )}
                            </>
                          )}
                        </CardContent>
                      </MetricCard>
                    </Grid>
                  ))}
                </Grid>
              </StyledPaper>
            </TabPanel>

            {/* Route Health Tab */}
            <TabPanel value={tabValue} index={4}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h6">
                  API Route Health
                </Typography>
                <Button 
                  variant="contained" 
                  startIcon={<RefreshIcon />} 
                  onClick={triggerRouteHealthCheck}
                  disabled={loadingRoutes}
                >
                  {loadingRoutes ? 'Checking...' : 'Check Routes'}
                </Button>
              </Box>
              
              {routeHealth && routeHealth.routes && Object.keys(routeHealth.routes).length > 0 ? (
                <>
                  <Typography variant="body2" sx={{ mb: 2 }}>
                    Last checked: {new Date(routeHealth.last_check).toLocaleString()}
                  </Typography>
                  
                  <StyledPaper>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Method</TableCell>
                          <TableCell>Path</TableCell>
                          <TableCell align="center">Status</TableCell>
                          <TableCell align="right">Response Time</TableCell>
                          <TableCell align="center">Health</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {Object.entries(routeHealth.routes).map(([routeKey, routeData]: [string, any]) => {
                          const [method, path] = routeKey.split(' ');
                          return (
                            <TableRow key={routeKey}>
                              <TableCell>{method}</TableCell>
                              <TableCell>{path}</TableCell>
                              <TableCell align="center">{routeData.status_code || 'N/A'}</TableCell>
                              <TableCell align="right">
                                {routeData.response_time_ms ? `${routeData.response_time_ms} ms` : 'N/A'}
                              </TableCell>
                              <TableCell align="center">
                                {renderHealthStatus(routeData.healthy)}
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </StyledPaper>
                </>
              ) : (
                <Alert severity="info">
                  No route health data available. Click "Check Routes" to start monitoring.
                </Alert>
              )}
            </TabPanel>
          </>
        )}
      </Box>
    </Container>
  );
};

export default Monitoring; 