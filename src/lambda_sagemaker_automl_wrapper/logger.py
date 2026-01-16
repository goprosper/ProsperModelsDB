"""
Structured logging utilities for the AutoML wrapper.

This module provides comprehensive logging functionality with security-conscious
filtering and structured output for CloudWatch integration.
"""

import json
import logging
import os
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime


class SensitiveDataFilter(logging.Filter):
    """
    Filter to remove sensitive data from log records.
    
    This filter ensures that sensitive information like AWS credentials,
    account IDs, and other PII is not logged.
    """
    
    SENSITIVE_PATTERNS = [
        # AWS Account IDs
        r'\b\d{12}\b',
        # AWS Access Keys
        r'AKIA[0-9A-Z]{16}',
        # AWS Secret Keys (basic pattern)
        r'[A-Za-z0-9/+=]{40}',
        # Potential passwords or tokens
        r'password["\']?\s*[:=]\s*["\']?[^"\'\s]+',
        r'token["\']?\s*[:=]\s*["\']?[^"\'\s]+',
        r'secret["\']?\s*[:=]\s*["\']?[^"\'\s]+',
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log record to remove sensitive data.
        
        Args:
            record: Log record to filter
            
        Returns:
            True to keep the record, False to discard
        """
        # Sanitize the message
        if hasattr(record, 'msg') and record.msg:
            record.msg = self._sanitize_message(str(record.msg))
        
        # Sanitize args if present
        if hasattr(record, 'args') and record.args:
            record.args = tuple(self._sanitize_message(str(arg)) for arg in record.args)
        
        return True
    
    def _sanitize_message(self, message: str) -> str:
        """
        Sanitize message content to remove sensitive data.
        
        Args:
            message: Original message
            
        Returns:
            Sanitized message
        """
        import re
        
        sanitized = message
        
        # Apply sensitive data patterns
        for pattern in self.SENSITIVE_PATTERNS:
            sanitized = re.sub(pattern, '***', sanitized, flags=re.IGNORECASE)
        
        # Sanitize ARNs to show only resource names
        sanitized = re.sub(
            r'arn:aws:[^:]*:[^:]*:\d{12}:([^/]+/)?([^/\s]+)',
            r'\2',
            sanitized
        )
        
        return sanitized


class StructuredFormatter(logging.Formatter):
    """
    Formatter for structured JSON logging.
    
    This formatter creates structured log entries that are easily parsed
    by CloudWatch and other log analysis tools.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as structured JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON formatted log entry
        """
        # Base log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'message': record.getMessage(),
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add request ID if available
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        # Add job name if available
        if hasattr(record, 'job_name'):
            log_entry['job_name'] = record.job_name
        
        # Add operation if available
        if hasattr(record, 'operation'):
            log_entry['operation'] = record.operation
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add stack info if present
        if record.stack_info:
            log_entry['stack_info'] = record.stack_info
        
        return json.dumps(log_entry, default=str)


class AutoMLLogger:
    """
    Centralized logger for AutoML wrapper operations.
    
    This class provides structured logging with appropriate filtering
    and formatting for CloudWatch integration.
    """
    
    def __init__(self, name: str = 'automl_wrapper', level: str = None):
        """
        Initialize logger with structured formatting.
        
        Args:
            name: Logger name
            level: Log level (defaults to INFO)
        """
        self.logger = logging.getLogger(name)
        
        # Set log level from environment or parameter
        log_level = level or os.getenv('LOG_LEVEL', 'INFO')
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create console handler with structured formatting
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        handler.addFilter(SensitiveDataFilter())
        
        self.logger.addHandler(handler)
        
        # Prevent duplicate logs
        self.logger.propagate = False
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message with optional context."""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message with optional context."""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message with optional context."""
        self.logger.error(message, extra=kwargs)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message with optional context."""
        self.logger.debug(message, extra=kwargs)
    
    def log_lambda_start(self, event: Dict[str, Any], request_id: str) -> None:
        """
        Log Lambda function start with sanitized event data.
        
        Args:
            event: Lambda event (will be sanitized)
            request_id: Lambda request ID
        """
        sanitized_event = self._sanitize_event_for_logging(event)
        
        self.info(
            "Lambda function started",
            request_id=request_id,
            operation="lambda_start",
            event_keys=list(sanitized_event.keys())
        )
        
        # Log key parameters at debug level
        if 'AutoMLJobName' in sanitized_event:
            self.debug(
                f"Processing AutoML job: {sanitized_event['AutoMLJobName']}",
                request_id=request_id,
                job_name=sanitized_event['AutoMLJobName']
            )
    
    def log_parameter_validation_start(self, request_id: str) -> None:
        """Log start of parameter validation."""
        self.info(
            "Starting parameter validation",
            request_id=request_id,
            operation="parameter_validation"
        )
    
    def log_parameter_validation_success(self, request_id: str) -> None:
        """Log successful parameter validation."""
        self.info(
            "Parameter validation completed successfully",
            request_id=request_id,
            operation="parameter_validation"
        )
    
    def log_parameter_validation_error(self, error_message: str, parameter_name: str, 
                                     request_id: str) -> None:
        """Log parameter validation error."""
        self.error(
            f"Parameter validation failed: {error_message}",
            request_id=request_id,
            operation="parameter_validation",
            parameter=parameter_name
        )
    
    def log_s3_operation_start(self, operation: str, s3_uri: str, request_id: str) -> None:
        """Log start of S3 operation."""
        sanitized_uri = self._sanitize_s3_uri(s3_uri)
        self.info(
            f"Starting S3 operation: {operation}",
            request_id=request_id,
            operation=f"s3_{operation}",
            s3_uri=sanitized_uri
        )
    
    def log_s3_operation_success(self, operation: str, s3_uri: str, request_id: str) -> None:
        """Log successful S3 operation."""
        sanitized_uri = self._sanitize_s3_uri(s3_uri)
        self.info(
            f"S3 operation completed successfully: {operation}",
            request_id=request_id,
            operation=f"s3_{operation}",
            s3_uri=sanitized_uri
        )
    
    def log_s3_operation_error(self, operation: str, s3_uri: str, error_message: str, 
                              request_id: str) -> None:
        """Log S3 operation error."""
        sanitized_uri = self._sanitize_s3_uri(s3_uri)
        self.error(
            f"S3 operation failed: {operation} - {error_message}",
            request_id=request_id,
            operation=f"s3_{operation}",
            s3_uri=sanitized_uri
        )
    
    def log_sagemaker_api_start(self, job_name: str, request_id: str) -> None:
        """Log start of SageMaker API call."""
        self.info(
            "Starting SageMaker CreateAutoMLJob API call",
            request_id=request_id,
            operation="sagemaker_create_job",
            job_name=job_name
        )
    
    def log_training_plan_applied(self, training_plan: str, completion_criteria: Dict[str, Any], request_id: str) -> None:
        """Log when a training plan is applied."""
        self.info(
            f"Applied {training_plan} training plan completion criteria",
            request_id=request_id,
            operation="training_plan_processing",
            training_plan=training_plan,
            completion_criteria=completion_criteria
        )
    
    def log_sagemaker_api_success(self, job_name: str, job_arn: str, request_id: str) -> None:
        """Log successful SageMaker API call."""
        # Sanitize ARN for logging
        sanitized_arn = self._sanitize_arn(job_arn)
        
        self.info(
            "SageMaker AutoML job created successfully",
            request_id=request_id,
            operation="sagemaker_create_job",
            job_name=job_name,
            job_arn=sanitized_arn
        )
    
    def log_sagemaker_api_error(self, job_name: str, error_code: str, error_message: str, 
                               request_id: str) -> None:
        """Log SageMaker API error."""
        self.error(
            f"SageMaker API call failed: [{error_code}] {error_message}",
            request_id=request_id,
            operation="sagemaker_create_job",
            job_name=job_name,
            error_code=error_code
        )
    
    def log_lambda_success(self, job_name: str, job_arn: str, request_id: str) -> None:
        """Log successful Lambda completion."""
        sanitized_arn = self._sanitize_arn(job_arn)
        
        self.info(
            "Lambda function completed successfully",
            request_id=request_id,
            operation="lambda_complete",
            job_name=job_name,
            job_arn=sanitized_arn
        )
    
    def log_lambda_error(self, error_type: str, error_message: str, request_id: str) -> None:
        """Log Lambda function error."""
        self.error(
            f"Lambda function failed: [{error_type}] {error_message}",
            request_id=request_id,
            operation="lambda_error",
            error_type=error_type
        )
    
    def _sanitize_event_for_logging(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize Lambda event for safe logging.
        
        Args:
            event: Original Lambda event
            
        Returns:
            Sanitized event data
        """
        import copy
        
        sanitized = copy.deepcopy(event)
        
        # Remove or sanitize sensitive fields
        if 'RoleArn' in sanitized:
            sanitized['RoleArn'] = self._sanitize_arn(sanitized['RoleArn'])
        
        # Sanitize nested structures
        def sanitize_recursive(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key.lower() in ['rolearn', 'arn']:
                        obj[key] = self._sanitize_arn(str(value))
                    elif key.lower() in ['s3uri', 'featurespecifications3uri']:
                        obj[key] = self._sanitize_s3_uri(str(value))
                    elif isinstance(value, (dict, list)):
                        sanitize_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    sanitize_recursive(item)
        
        sanitize_recursive(sanitized)
        return sanitized
    
    def _sanitize_s3_uri(self, s3_uri: str) -> str:
        """Sanitize S3 URI for logging."""
        if len(s3_uri) > 100:
            return s3_uri[:50] + "..." + s3_uri[-47:]
        return s3_uri
    
    def _sanitize_arn(self, arn: str) -> str:
        """Sanitize ARN for logging."""
        import re
        # Replace account ID with ***
        return re.sub(r':\d{12}:', ':***:', arn)


# Global logger instance
_global_logger = None


def get_logger() -> AutoMLLogger:
    """
    Get global logger instance.
    
    Returns:
        Configured AutoML logger
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = AutoMLLogger()
    return _global_logger


def setup_logging(level: str = None) -> AutoMLLogger:
    """
    Setup logging configuration for Lambda function.
    
    Args:
        level: Log level to set
        
    Returns:
        Configured logger
    """
    global _global_logger
    _global_logger = AutoMLLogger(level=level)
    return _global_logger