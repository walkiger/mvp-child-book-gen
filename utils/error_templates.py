"""
Standardized error message templates to ensure consistent error messaging.

These templates can be used for error messages across both the management
tools and the API to maintain a consistent user experience.
"""

# Database error templates
DATABASE_NOT_FOUND = "Database '{db_path}' not found or not accessible"
DATABASE_PERMISSION_DENIED = "Permission denied to access database at '{db_path}'"
TABLE_MISSING = "Table '{table_name}' missing from database"
COLUMN_MISSING = "Column '{column_name}' missing from table '{table_name}'"
INVALID_DATA = "Invalid data in '{table_name}': {details}"
QUERY_ERROR = "Error executing database query: {details}"
CONNECTION_ERROR = "Database connection error: {details}"
MIGRATION_ERROR = "Error running database migration: {details}"

# Server error templates
SERVER_START_ERROR = "Failed to start {server_type} server: {details}"
SERVER_STOP_ERROR = "Failed to stop {server_type} server: {details}"
SERVER_NOT_RUNNING = "{server_type} server is not running"
SERVER_ALREADY_RUNNING = "{server_type} server is already running (PID: {pid})"
PORT_IN_USE = "Port {port} is already in use by another process"

# Process error templates
PROCESS_NOT_FOUND = "Process with PID {pid} not found"
PROCESS_PERMISSION_ERROR = "Permission denied when accessing process {pid}"
PROCESS_START_ERROR = "Failed to start process: {details}"
PROCESS_STOP_ERROR = "Failed to stop process: {details}"

# Configuration error templates
CONFIG_NOT_FOUND = "Configuration file '{config_path}' not found"
CONFIG_PARSE_ERROR = "Error parsing configuration file '{config_path}': {details}"
INVALID_CONFIG = "Invalid configuration: {details}"
REQUIRED_CONFIG_MISSING = "Required configuration '{config_item}' is missing"

# Resource error templates
RESOURCE_NOT_FOUND = "Resource '{resource_name}' not found"
RESOURCE_ACCESS_DENIED = "Access denied to resource '{resource_name}'"
RESOURCE_CREATION_ERROR = "Failed to create resource '{resource_name}': {details}"
RESOURCE_DELETION_ERROR = "Failed to delete resource '{resource_name}': {details}"

# Input error templates
MISSING_PARAMETER = "Required parameter '{param_name}' is missing"
INVALID_PARAMETER = "Invalid value for parameter '{param_name}': {details}"
VALIDATION_ERROR = "Input validation failed: {details}"

# Authentication error templates
AUTH_FAILED = "Authentication failed: {details}"
UNAUTHORIZED = "Unauthorized access to '{resource}'"
INVALID_TOKEN = "Invalid or expired authentication token"
ACCESS_DENIED = "Access denied: {details}"

# Image processing error templates
IMAGE_GENERATION_ERROR = "Failed to generate image: {details}"
IMAGE_PROCESSING_ERROR = "Failed to process image '{image_path}': {details}"
INVALID_IMAGE_FORMAT = "Invalid image format: {details}"

# API error templates
API_REQUEST_ERROR = "API request failed: {details}"
RATE_LIMIT_EXCEEDED = "Rate limit exceeded for operation '{operation}'"
MALFORMED_REQUEST = "Malformed request: {details}"

# General error templates
UNEXPECTED_ERROR = "An unexpected error occurred: {details}"
OPERATION_TIMEOUT = "Operation '{operation}' timed out after {timeout} seconds"
SERVICE_UNAVAILABLE = "Service '{service}' is currently unavailable: {details}"
DEPENDENCY_ERROR = "Error with dependency '{dependency}': {details}" 