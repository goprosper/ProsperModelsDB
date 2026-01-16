"""
Response handling utilities for Step Functions compatibility.

This module ensures that Lambda responses are formatted correctly
for Step Functions workflow integration.
"""

import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ResponseFormattingError(Exception):
    """Raised when response formatting fails."""
    pass


def format_success_response(sagemaker_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format successful SageMaker response for Step Functions compatibility.
    
    Args:
        sagemaker_response: Response from SageMaker CreateAutoMLJob API
        
    Returns:
        Formatted response compatible with Step Functions
        
    Raises:
        ResponseFormattingError: If response formatting fails
    """
    try:
        logger.info("Formatting successful SageMaker response for Step Functions")
        
        # Validate that we have the required AutoMLJobArn
        if 'AutoMLJobArn' not in sagemaker_response:
            raise ResponseFormattingError("Missing AutoMLJobArn in SageMaker response")
        
        automl_job_arn = sagemaker_response['AutoMLJobArn']
        if not automl_job_arn:
            raise ResponseFormattingError("AutoMLJobArn is empty in SageMaker response")
        
        # Format response to match Step Functions SageMaker integration format
        formatted_response = {
            'AutoMLJobArn': automl_job_arn
        }
        
        # Log the successful response (without sensitive data)
        logger.info(f"Successfully formatted response with AutoMLJobArn: {automl_job_arn}")
        
        return formatted_response
        
    except Exception as e:
        logger.error(f"Failed to format success response: {str(e)}")
        raise ResponseFormattingError(f"Response formatting failed: {str(e)}")


def format_error_response(error: Exception, error_context: Optional[Dict[str, Any]] = None) -> None:
    """
    Format error response for Step Functions compatibility.
    
    This function raises an exception in the format expected by Step Functions
    error handling mechanisms.
    
    Args:
        error: The original error that occurred
        error_context: Additional context about the error
        
    Raises:
        Exception: Formatted exception for Step Functions
    """
    try:
        logger.info("Formatting error response for Step Functions")
        
        # Determine error type and message
        error_type = type(error).__name__
        error_message = str(error)
        
        # Map common error types to Step Functions compatible formats
        if hasattr(error, 'error_code') and error.error_code:
            # Use SageMaker error code if available
            error_type = f"SageMaker.{error.error_code}"
        elif 'ValidationException' in error_message:
            error_type = "SageMaker.ValidationException"
        elif 'AccessDenied' in error_message:
            error_type = "SageMaker.AccessDeniedException"
        elif 'ThrottlingException' in error_message:
            error_type = "SageMaker.ThrottlingException"
        elif 'ResourceLimitExceeded' in error_message:
            error_type = "SageMaker.ResourceLimitExceeded"
        elif 'S3' in error_message and ('not found' in error_message.lower() or '404' in error_message):
            error_type = "S3.NoSuchKey"
        elif 'S3' in error_message and ('access denied' in error_message.lower() or '403' in error_message):
            error_type = "S3.AccessDenied"
        
        # Ensure error message is clean and doesn't expose sensitive information
        clean_message = sanitize_error_message(error_message)
        
        # Log the error details
        logger.error(f"Formatted error for Step Functions - Type: {error_type}, Message: {clean_message}")
        
        # Create Step Functions compatible error
        step_functions_error = Exception(clean_message)
        # Note: Don't set .name attribute as it doesn't exist on standard Exception
        
        # Raise the formatted error
        raise step_functions_error
        
    except Exception as formatting_error:
        # If error formatting itself fails, raise a generic error
        logger.error(f"Failed to format error response: {str(formatting_error)}")
        raise Exception("Internal error occurred during AutoML job creation")


def sanitize_error_message(message: str) -> str:
    """
    Sanitize error message to remove sensitive information.
    
    Args:
        message: Original error message
        
    Returns:
        Sanitized error message
    """
    # Remove potential sensitive information patterns
    import re
    
    # Remove AWS account IDs
    message = re.sub(r'\b\d{12}\b', '***', message)
    
    # Remove potential access keys (basic pattern)
    message = re.sub(r'AKIA[0-9A-Z]{16}', '***', message)
    
    # Remove potential secret keys (basic pattern)
    message = re.sub(r'[A-Za-z0-9/+=]{40}', '***', message)
    
    # Remove full ARNs, keep only resource names
    message = re.sub(r'arn:aws:[^:]*:[^:]*:\d{12}:([^/]+/)?([^/\s]+)', r'\2', message)
    
    # Limit message length
    if len(message) > 500:
        message = message[:497] + "..."
    
    return message


def validate_step_functions_compatibility(response: Dict[str, Any]) -> bool:
    """
    Validate that response is compatible with Step Functions.
    
    Args:
        response: Response to validate
        
    Returns:
        True if compatible, False otherwise
    """
    try:
        # Check that response can be JSON serialized
        json.dumps(response)
        
        # Check for required fields
        if 'AutoMLJobArn' not in response:
            logger.warning("Response missing AutoMLJobArn field")
            return False
        
        # Check that AutoMLJobArn is a valid string
        if not isinstance(response['AutoMLJobArn'], str) or not response['AutoMLJobArn']:
            logger.warning("AutoMLJobArn is not a valid string")
            return False
        
        # Check response size (Step Functions has limits)
        response_size = len(json.dumps(response))
        if response_size > 256000:  # 256KB limit
            logger.warning(f"Response size ({response_size} bytes) exceeds Step Functions limit")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Response compatibility validation failed: {str(e)}")
        return False


def create_lambda_response(data: Dict[str, Any], status_code: int = 200) -> Dict[str, Any]:
    """
    Create properly formatted Lambda response.
    
    Args:
        data: Response data
        status_code: HTTP status code
        
    Returns:
        Formatted Lambda response
    """
    try:
        # For Step Functions integration, we typically return the data directly
        # rather than wrapping it in statusCode/body structure
        
        # Validate compatibility
        if not validate_step_functions_compatibility(data):
            raise ResponseFormattingError("Response not compatible with Step Functions")
        
        logger.info("Created Lambda response for Step Functions")
        return data
        
    except Exception as e:
        logger.error(f"Failed to create Lambda response: {str(e)}")
        # Return a minimal error response
        return {
            "errorType": "ResponseFormattingError",
            "errorMessage": f"Failed to format response: {str(e)}"
        }