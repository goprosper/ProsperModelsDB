"""
Error response handling for CreateModelingData function.

This module provides structured error responses with clear, actionable
messages for users while preserving detailed debugging information.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


class ErrorResponseHandler:
    """Handles creation of structured error responses."""

    def create_data_unavailable_error(self, requested_dates: List[str], 
                                    study_name: str, 
                                    request_name: str,
                                    suggestions: List[str] = None) -> Dict[str, Any]:
        """Create error response for data unavailability.
        
        Args:
            requested_dates: The dates that were requested
            study_name: The study name that was requested
            request_name: The full request name for debugging
            suggestions: Alternative dates that have data
            
        Returns:
            Structured error response dictionary
        """
        if suggestions is None:
            suggestions = []
            
        user_message = self._create_user_friendly_message(
            requested_dates, study_name, suggestions
        )
        
        error_response = {
            "errorType": "DataUnavailableError",
            "errorMessage": f"No data available for study '{study_name}' on dates {', '.join(requested_dates)}",
            "details": {
                "requestedDates": requested_dates,
                "studyName": study_name,
                "requestName": request_name,
                "suggestedDates": suggestions,
                "timestamp": datetime.utcnow().isoformat()
            },
            "userMessage": user_message
        }
        
        # Log detailed error for debugging
        logger.error(f"Data unavailable - Request: {request_name}, "
                    f"Study: {study_name}, Dates: {requested_dates}")
        
        return error_response

    def create_file_validation_error(self, file_path: str, 
                                   file_type: str,
                                   issue: str, 
                                   file_size: int,
                                   request_name: str,
                                   requested_dates: List[str] = None,
                                   study_name: str = None) -> Dict[str, Any]:
        """Create error response for file validation failures.
        
        Args:
            file_path: The S3 path that failed validation
            file_type: Type of file (data_file, map_file)
            issue: Description of the validation issue
            file_size: Size of the file in bytes
            request_name: The full request name for debugging
            requested_dates: The dates that were requested (optional)
            study_name: The study name that was requested (optional)
            
        Returns:
            Structured error response dictionary
        """
        if requested_dates is None:
            requested_dates = []
            
        user_message = self._create_file_error_message(
            file_type, issue, file_size, requested_dates, study_name
        )
        
        error_response = {
            "errorType": "DataValidationError",
            "errorMessage": f"File validation failed for {file_type}: {issue}",
            "details": {
                "filePath": file_path,
                "fileType": file_type,
                "fileSize": file_size,
                "validationIssue": issue,
                "requestName": request_name,
                "requestedDates": requested_dates,
                "studyName": study_name,
                "timestamp": datetime.utcnow().isoformat()
            },
            "userMessage": user_message
        }
        
        # Log detailed error for debugging
        logger.error(f"File validation failed - File: {file_path}, "
                    f"Issue: {issue}, Size: {file_size} bytes")
        
        return error_response

    def create_processing_error(self, error_type: str,
                              error_message: str,
                              request_name: str,
                              requested_dates: List[str] = None,
                              study_name: str = None,
                              original_exception: Exception = None) -> Dict[str, Any]:
        """Create error response for processing failures.
        
        Args:
            error_type: Type of processing error
            error_message: Detailed error message
            request_name: The full request name for debugging
            requested_dates: The dates that were requested (optional)
            study_name: The study name that was requested (optional)
            original_exception: The original exception that caused the error
            
        Returns:
            Structured error response dictionary
        """
        if requested_dates is None:
            requested_dates = []
            
        user_message = self._create_processing_error_message(
            error_type, requested_dates, study_name
        )
        
        error_response = {
            "errorType": error_type,
            "errorMessage": error_message,
            "details": {
                "requestName": request_name,
                "requestedDates": requested_dates,
                "studyName": study_name,
                "timestamp": datetime.utcnow().isoformat()
            },
            "userMessage": user_message
        }
        
        if original_exception:
            error_response["details"]["originalError"] = str(original_exception)
        
        # Log detailed error for debugging
        logger.error(f"Processing error - Type: {error_type}, "
                    f"Message: {error_message}, Request: {request_name}")
        if original_exception:
            logger.exception("Original exception:", exc_info=original_exception)
        
        return error_response

    def _create_user_friendly_message(self, requested_dates: List[str],
                                    study_name: str,
                                    suggestions: List[str]) -> str:
        """Create a user-friendly message for data unavailability.
        
        Args:
            requested_dates: The dates that were requested
            study_name: The study name that was requested
            suggestions: Alternative dates that have data
            
        Returns:
            User-friendly error message
        """
        base_message = f"No data is available for study '{study_name}' on the requested dates ({', '.join(requested_dates)})."
        
        if suggestions:
            suggestion_text = ', '.join(suggestions)
            return f"{base_message} Try using these dates instead: {suggestion_text}."
        else:
            return f"{base_message} Please check with your data administrator for available date ranges."

    def _create_file_error_message(self, file_type: str, 
                                 issue: str, 
                                 file_size: int,
                                 requested_dates: List[str],
                                 study_name: str) -> str:
        """Create a user-friendly message for file validation errors.
        
        Args:
            file_type: Type of file that failed
            issue: Description of the issue
            file_size: Size of the file
            requested_dates: The dates that were requested
            study_name: The study name that was requested
            
        Returns:
            User-friendly error message
        """
        if file_size == 0:
            if requested_dates and study_name:
                return (f"The data processing step did not generate any data for "
                       f"study '{study_name}' on dates {', '.join(requested_dates)}. "
                       f"This usually means no survey responses exist for those dates. "
                       f"Please try different dates or contact your data administrator.")
            else:
                return (f"The {file_type} is empty, which means no data was found "
                       f"for your request. Please check your parameters and try again.")
        elif "no columns" in issue.lower() or "no data rows" in issue.lower():
            return (f"The data file was created but contains no usable information. "
                   f"This typically indicates that no survey data exists for your "
                   f"requested parameters. Please try different dates or study parameters.")
        elif "encoding" in issue.lower():
            return (f"There was a problem reading the data file due to character "
                   f"encoding issues. Please contact technical support.")
        elif "missing required columns" in issue.lower():
            return (f"The data file is missing required information columns. "
                   f"This may indicate a problem with data generation. "
                   f"Please contact technical support.")
        else:
            return (f"There was a problem with the {file_type}: {issue}. "
                   f"Please contact technical support if this persists.")

    def _create_processing_error_message(self, error_type: str,
                                       requested_dates: List[str],
                                       study_name: str) -> str:
        """Create a user-friendly message for processing errors.
        
        Args:
            error_type: Type of processing error
            requested_dates: The dates that were requested
            study_name: The study name that was requested
            
        Returns:
            User-friendly error message
        """
        if error_type == "S3AccessError":
            return ("There was a temporary problem accessing the data files. "
                   "Please try your request again in a few minutes.")
        elif error_type == "FileFormatError":
            return ("The data files have an unexpected format. "
                   "Please contact technical support.")
        else:
            return ("An unexpected error occurred while processing your request. "
                   "Please contact technical support if this persists.")

    def suggest_alternative_dates(self, study_name: str) -> List[str]:
        """Suggest alternative dates that might have data.
        
        This is a placeholder implementation. In a real system, this would
        query a metadata store or analyze available data files.
        
        Args:
            study_name: The study name to suggest dates for
            
        Returns:
            List of suggested dates
        """
        # For now, return common dates that are known to have data
        # In production, this would be more sophisticated
        return ['2025-01-01']