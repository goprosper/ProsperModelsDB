"""
Constants for AutoML integration with ProsperModels workflow.

This module defines the status values and other constants used throughout
the AutoML integration process.
"""

# AutoML Job Status Values
class AutoMLStatus:
    """Status values for tracking AutoML job progress in DynamoDB."""
    
    # Job lifecycle statuses
    JOB_STARTED = "AutoML_Job_Started"
    JOB_RUNNING = "AutoML_Job_Running" 
    JOB_COMPLETED = "AutoML_Job_Completed"
    JOB_FAILED = "AutoML_Job_Failed"
    JOB_LAUNCH_FAILED = "AutoML_Job_Launch_Failed"
    JOB_TIMEOUT = "AutoML_Job_Timeout"
    JOB_MONITORING_FAILED = "AutoML_Job_Monitoring_Failed"
    
    # All valid status values
    ALL_STATUSES = [
        JOB_STARTED,
        JOB_RUNNING,
        JOB_COMPLETED,
        JOB_FAILED,
        JOB_LAUNCH_FAILED,
        JOB_TIMEOUT,
        JOB_MONITORING_FAILED
    ]

# DynamoDB Attribute Names
class DynamoDBAttributes:
    """Attribute names used in the ProsperModels DynamoDB table."""
    
    # Existing attributes
    ID = "Id"
    USER_ID = "UserId"
    USER_NAME = "UserName"
    SUBMISSION_DATE_TIME = "SubmissionDateTime"
    SHORT_DESCRIPTION = "ShortDescription"
    STUDY_NAME = "StudyName"
    FEATURE_LIST_NAME = "FeatureListName"
    LABEL = "Label"
    
    # New AutoML attributes
    STATUS = "Status"
    ERROR_MESSAGE = "ErrorMessage"
    AUTOML_JOB_NAME = "AutoMLJobName"

# SageMaker Job Status Values (from SageMaker API)
class SageMakerJobStatus:
    """Status values returned by SageMaker DescribeAutoMLJob API."""
    
    IN_PROGRESS = "InProgress"
    COMPLETED = "Completed"
    FAILED = "Failed"
    STOPPED = "Stopped"
    STOPPING = "Stopping"

def validate_automl_status(status):
    """
    Validate that a status value is a valid AutoML status.
    
    Args:
        status (str): The status value to validate
        
    Returns:
        bool: True if the status is valid, False otherwise
    """
    return status in AutoMLStatus.ALL_STATUSES

def map_sagemaker_to_automl_status(sagemaker_status):
    """
    Map SageMaker job status to AutoML status for DynamoDB storage.
    
    Args:
        sagemaker_status (str): Status from SageMaker DescribeAutoMLJob
        
    Returns:
        str: Corresponding AutoML status for DynamoDB
    """
    mapping = {
        SageMakerJobStatus.IN_PROGRESS: AutoMLStatus.JOB_RUNNING,
        SageMakerJobStatus.COMPLETED: AutoMLStatus.JOB_COMPLETED,
        SageMakerJobStatus.FAILED: AutoMLStatus.JOB_FAILED,
        SageMakerJobStatus.STOPPED: AutoMLStatus.JOB_FAILED,
        SageMakerJobStatus.STOPPING: AutoMLStatus.JOB_RUNNING
    }
    
    return mapping.get(sagemaker_status, AutoMLStatus.JOB_FAILED)

# Polling Configuration
class PollingConfig:
    """Configuration constants for AutoML job polling."""
    
    # Polling intervals and limits
    POLL_INTERVAL_SECONDS = 60  # 1 minute
    MAX_POLL_COUNT = 1440  # 24 hours (1440 minutes)
    MAX_RETRIES = 3
    RETRY_BACKOFF_RATE = 2.0
    INITIAL_RETRY_INTERVAL = 2