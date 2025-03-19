"""
Validation Error Handling

This module defines validation-specific errors extending the base error system.
"""

from typing import Optional, Dict, Any, List, Union

from .base import BaseError, ErrorContext, ErrorSeverity


class ValidationError(BaseError):
    """Base class for all validation-related errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        http_status_code: int = 422,
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None
    ):
        if not error_code.startswith('VAL-'):
            error_code = f"VAL-{error_code}"
        super().__init__(
            message,
            error_code,
            http_status_code,
            context,
            details,
            suggestions
        )


class DataValidationError(ValidationError):
    """Data content validation failures."""
    
    def __init__(
        self,
        message: str,
        field_name: str,
        received_value: Any,
        expected_type: Union[str, List[str]],
        error_code: str = "VAL-DATA-TYPE-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'field_name': field_name,
            'received_value': str(received_value),
            'expected_type': expected_type
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=422,
            context=context,
            details=details,
            suggestions=[
                f"Check {field_name} data type",
                f"Ensure value matches {expected_type}",
                "Verify input format"
            ]
        )
        self.set_severity(ErrorSeverity.WARNING)


class FormatValidationError(ValidationError):
    """Data format validation failures."""
    
    def __init__(
        self,
        message: str,
        field_name: str,
        received_format: str,
        expected_format: str,
        error_code: str = "VAL-DATA-FMT-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'field_name': field_name,
            'received_format': received_format,
            'expected_format': expected_format
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=422,
            context=context,
            details=details,
            suggestions=[
                f"Check {field_name} format",
                f"Format should be: {expected_format}",
                "Verify input structure"
            ]
        )
        self.set_severity(ErrorSeverity.WARNING)


class RequiredFieldError(ValidationError):
    """Required field missing errors."""
    
    def __init__(
        self,
        message: str,
        field_name: str,
        error_code: str = "VAL-FIELD-REQ-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'field_name': field_name
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=422,
            context=context,
            details=details,
            suggestions=[
                f"Provide value for {field_name}",
                "Check required fields list",
                "Ensure all mandatory fields are included"
            ]
        )
        self.set_severity(ErrorSeverity.WARNING)


class LengthValidationError(ValidationError):
    """Field length validation failures."""
    
    def __init__(
        self,
        message: str,
        field_name: str,
        current_length: int,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        error_code: str = "VAL-FIELD-LEN-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'field_name': field_name,
            'current_length': current_length,
            'min_length': min_length,
            'max_length': max_length
        })
        
        constraints = []
        if min_length is not None:
            constraints.append(f"minimum length: {min_length}")
        if max_length is not None:
            constraints.append(f"maximum length: {max_length}")
        
        super().__init__(
            message,
            error_code,
            http_status_code=422,
            context=context,
            details=details,
            suggestions=[
                f"Check {field_name} length",
                f"Length constraints: {', '.join(constraints)}",
                "Adjust content length"
            ]
        )
        self.set_severity(ErrorSeverity.WARNING)


class RangeValidationError(ValidationError):
    """Value range validation failures."""
    
    def __init__(
        self,
        message: str,
        field_name: str,
        current_value: Union[int, float],
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        error_code: str = "VAL-FIELD-RNG-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'field_name': field_name,
            'current_value': current_value,
            'min_value': min_value,
            'max_value': max_value
        })
        
        constraints = []
        if min_value is not None:
            constraints.append(f"minimum: {min_value}")
        if max_value is not None:
            constraints.append(f"maximum: {max_value}")
        
        super().__init__(
            message,
            error_code,
            http_status_code=422,
            context=context,
            details=details,
            suggestions=[
                f"Check {field_name} value",
                f"Value constraints: {', '.join(constraints)}",
                "Adjust value to be within range"
            ]
        )
        self.set_severity(ErrorSeverity.WARNING) 