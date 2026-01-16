"""
Comprehensive error handling framework for Step Functions compatibility.

This module provides a unified error handling system that formats all errors
in a way that's compatible with AWS Step Functions error handling mechanisms.
"""

import logging
import traceback
from typing import Dict, Any, Optional, Type
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Categories of errors for classification and handling."""
    VALIDATION = "validation"
    S3_ACCESS = "s3_access"
    SAGEMAKER_API = "sagemaker_api"
    INTERNAL = "internal"
    CONFIGURATION = "configuration"


class AutoMLWrapperError(Exception):
    """Base exception for AutoML wrapper errors."""
    
    def __init__(self, message: str, error_category: ErrorCategory = ErrorCategory.INTERNAL, 
                 error_code: Optional[str] = None, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.error_category = error_category
        self.error_code = error_code
        self.original_error = original_error


class ParameterValidationError(AutoMLWrapperError):
    """Raised when input parameters are invalid."""
    
    def __init__(self, message: str, parameter_name: Optional[str] = None, 
                 original_error: Optional[Exception] = None):
        super().__init__(message, ErrorCategory.VALIDATION, "ParameterValidationError", original_error)
        self.parameter_name = parameter_name


class S3AccessError(AutoMLWrapperError):
    """Raised when S3 access fails for feature specification."""
    
    def __init__(self, message: str, s3_uri: Optional[str] = None, 
                 error_code: Optional[str] = None, original_error: Optional[Exception] = None):
        super().__init__(message, ErrorCategory.S3_ACCESS, error_code or "S3AccessError", original_error)
        self.s3_uri = s3_uri


class SageMakerAPIError(AutoMLWrapperError):
    """Raised when SageMaker API call fails."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 original_error: Optional[Exception] = None):
        super().__init__(message, ErrorCategory.SAGEMAKER_API, error_code or "SageMakerAPIError", original_error)


class ConfigurationError(AutoMLWrapperError):
    """Raised when configuration or setup fails."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message, ErrorCategory.CONFIGURATION, "ConfigurationError", original_error)


class StepFunctionsErrorFormatter:
    """
    Formats errors for Step Functions compatibility.
    
    This class ensures that all errors are formatted in a way that Step Functions
    can properly catch and handle using its error handling mechanisms.
    """
    
    @staticmethod
    def format_error_for_step_functions(error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Format and raise error in Step Functions compatible format.
        
        Args:
            error: The original error that occurred
            context: Additional context about the error
            
        Raises:
            Exception: Formatted exception for Step Functions
        """
        try:
            logger.info("Formatting error for Step Functions compatibility")
            
            # Determine error type and message
            error_type, error_message = StepFunctionsErrorFormatter._determine_error_type_and_message(error)
            
            # Sanitize error message
            clean_message = StepFunctionsErrorFormatter._sanitize_error_message(error_message)
            
            # Add context if available
            if context:
                context_str = StepFunctionsErrorFormatter._format_error_context(context)
                if context_str:
                    clean_message = f"{clean_message}. Context: {context_str}"
            
            # Log the error details
            logger.error(f"Step Functions error - Type: {error_type}, Message: {clean_message}")
            
            # Log original error for debugging
            if hasattr(error, 'original_error') and error.original_error:
                logger.error(f"Original error: {str(error.original_error)}")
            
        except Exception as formatting_error:
            # If error formatting itself fails, raise a generic error
            logger.error(f"Failed to format error for Step Functions: {str(formatting_error)}")
            # Create a simple exception without trying to set name attribute
            raise Exception("Internal error occurred during AutoML job creation")
        
        # Create and raise Step Functions compatible error (outside the try block)
        step_functions_error = Exception(clean_message)
        # Note: Don't set .name attribute as it doesn't exist on standard Exception
        raise step_functions_error
    
    @staticmethod
    def _determine_error_type_and_message(error: Exception) -> tuple[str, str]:
        """
        Determine appropriate error type and message for Step Functions.
        
        Args:
            error: The original error
            
        Returns:
            Tuple of (error_type, error_message)
        """
        error_message = str(error)
        
        # Handle AutoML wrapper specific errors
        if isinstance(error, AutoMLWrapperError):
            if error.error_code:
                if error.error_category == ErrorCategory.SAGEMAKER_API:
                    error_type = f"SageMaker.{error.error_code}"
                elif error.error_category == ErrorCategory.S3_ACCESS:
                    error_type = f"S3.{error.error_code}"
                else:
                    error_type = error.error_code
            else:
                error_type = type(error).__name__
        
        # Handle common AWS service errors
        elif 'ValidationException' in error_message:
            error_type = "SageMaker.ValidationException"
        elif 'AccessDenied' in error_message or 'AccessDeniedException' in error_message:
            if 'S3' in error_message:
                error_type = "S3.AccessDenied"
            else:
                error_type = "SageMaker.AccessDeniedException"
        elif 'ThrottlingException' in error_message:
            error_type = "SageMaker.ThrottlingException"
        elif 'ResourceLimitExceeded' in error_message:
            error_type = "SageMaker.ResourceLimitExceeded"
        elif 'NoSuchKey' in error_message or ('not found' in error_message.lower() and 'S3' in error_message):
            error_type = "S3.NoSuchKey"
        elif 'NoSuchBucket' in error_message:
            error_type = "S3.NoSuchBucket"
        elif 'ResourceInUse' in error_message:
            error_type = "SageMaker.ResourceInUse"
        elif 'ResourceNotFound' in error_message:
            error_type = "SageMaker.ResourceNotFound"
        elif 'InternalFailure' in error_message or 'InternalError' in error_message:
            error_type = "SageMaker.InternalFailure"
        elif 'ServiceUnavailable' in error_message:
            error_type = "SageMaker.ServiceUnavailable"
        else:
            # Generic error type based on exception class
            error_type = type(error).__name__
            if error_type == 'Exception':
                error_type = "InternalError"
        
        return error_type, error_message
    
    @staticmethod
    def _sanitize_error_message(message: str) -> str:
        """
        Sanitize error message to remove sensitive information.
        
        Args:
            message: Original error message
            
        Returns:
            Sanitized error message
        """
        import re
        
        # Remove AWS account IDs
        message = re.sub(r'\b\d{12}\b', '***', message)
        
        # Remove potential access keys
        message = re.sub(r'AKIA[0-9A-Z]{16}', '***', message)
        
        # Remove potential secret keys
        message = re.sub(r'[A-Za-z0-9/+=]{40}', '***', message)
        
        # Simplify ARNs to just resource names
        message = re.sub(r'arn:aws:[^:]*:[^:]*:\d{12}:([^/]+/)?([^/\s]+)', r'\2', message)
        
        # Remove stack traces from error messages
        lines = message.split('\n')
        if len(lines) > 1:
            # Keep only the first line if it looks like a stack trace
            if any('Traceback' in line or 'at ' in line or '.py:' in line for line in lines[1:]):
                message = lines[0]
        
        # Limit message length
        if len(message) > 500:
            message = message[:497] + "..."
        
        return message.strip()
    
    @staticmethod
    def _format_error_context(context: Dict[str, Any]) -> str:
        """
        Format error context for inclusion in error message.
        
        Args:
            context: Error context dictionary
            
        Returns:
            Formatted context string
        """
        try:
            context_parts = []
            
            # Include relevant context information
            if 'job_name' in context:
                context_parts.append(f"Job: {context['job_name']}")
            
            if 'parameter' in context:
                context_parts.append(f"Parameter: {context['parameter']}")
            
            if 's3_uri' in context:
                # Sanitize S3 URI
                s3_uri = context['s3_uri']
                if len(s3_uri) > 100:
                    s3_uri = s3_uri[:97] + "..."
                context_parts.append(f"S3 URI: {s3_uri}")
            
            if 'operation' in context:
                context_parts.append(f"Operation: {context['operation']}")
            
            return ", ".join(context_parts)
            
        except Exception:
            return ""


class ErrorLogger:
    """
    Centralized error logging with appropriate detail levels.
    """
    
    @staticmethod
    def log_error(error: Exception, context: Optional[Dict[str, Any]] = None, 
                  request_id: Optional[str] = None) -> None:
        """
        Log error with appropriate detail level.
        
        Args:
            error: The error to log
            context: Additional context
            request_id: Lambda request ID for correlation
        """
        extra_fields = {}
        if request_id:
            extra_fields['request_id'] = request_id
        
        # Log error details
        error_type = type(error).__name__
        error_message = str(error)
        
        logger.error(f"Error occurred - Type: {error_type}, Message: {error_message}", extra=extra_fields)
        
        # Log context if available
        if context:
            logger.error(f"Error context: {context}", extra=extra_fields)
        
        # Log original error if available
        if hasattr(error, 'original_error') and error.original_error:
            logger.error(f"Original error: {str(error.original_error)}", extra=extra_fields)
        
        # Log stack trace for debugging (but not in error message)
        logger.debug(f"Stack trace: {traceback.format_exc()}", extra=extra_fields)
    
    @staticmethod
    def log_validation_error(parameter_name: str, error_message: str, 
                           request_id: Optional[str] = None) -> None:
        """
        Log parameter validation error.
        
        Args:
            parameter_name: Name of the invalid parameter
            error_message: Validation error message
            request_id: Lambda request ID
        """
        extra_fields = {}
        if request_id:
            extra_fields['request_id'] = request_id
        
        logger.error(f"Parameter validation failed - Parameter: {parameter_name}, Error: {error_message}", 
                    extra=extra_fields)
    
    @staticmethod
    def log_s3_error(s3_uri: str, operation: str, error_message: str, 
                     request_id: Optional[str] = None) -> None:
        """
        Log S3 operation error.
        
        Args:
            s3_uri: S3 URI that caused the error
            operation: S3 operation that failed
            error_message: Error message
            request_id: Lambda request ID
        """
        extra_fields = {}
        if request_id:
            extra_fields['request_id'] = request_id
        
        # Sanitize S3 URI for logging
        sanitized_uri = s3_uri
        if len(sanitized_uri) > 200:
            sanitized_uri = sanitized_uri[:197] + "..."
        
        logger.error(f"S3 operation failed - URI: {sanitized_uri}, Operation: {operation}, Error: {error_message}", 
                    extra=extra_fields)


def handle_error(error: Exception, context: Optional[Dict[str, Any]] = None, 
                request_id: Optional[str] = None) -> None:
    """
    Centralized error handling function.
    
    Args:
        error: The error that occurred
        context: Additional error context
        request_id: Lambda request ID
        
    Raises:
        Exception: Formatted exception for Step Functions
    """
    # Log the error
    ErrorLogger.log_error(error, context, request_id)
    
    # Format and raise for Step Functions
    StepFunctionsErrorFormatter.format_error_for_step_functions(error, context)