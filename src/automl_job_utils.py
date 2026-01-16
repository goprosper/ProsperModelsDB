"""
Utility functions for AutoML job management.

This module provides functions for generating job names, constructing S3 paths,
and other AutoML job-related operations.
"""

import re
from datetime import datetime
from automl_constants import DynamoDBAttributes

def generate_automl_job_name(request_name, timestamp=None):
    """
    Generate a unique AutoML job name based on request name and timestamp.
    
    SageMaker AutoML job names must:
    - Be 1-63 characters long
    - Contain only alphanumeric characters and hyphens
    - Not start or end with a hyphen
    
    Args:
        request_name (str): The request name from the workflow
        timestamp (str, optional): ISO timestamp. If None, uses current time.
        
    Returns:
        str: A valid SageMaker AutoML job name
    """
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()
    
    # Clean the request name to be SageMaker-compliant
    clean_request_name = re.sub(r'[^a-zA-Z0-9-]', '-', request_name)
    clean_request_name = re.sub(r'-+', '-', clean_request_name)  # Remove multiple consecutive hyphens
    clean_request_name = clean_request_name.strip('-')  # Remove leading/trailing hyphens
    
    # Clean the timestamp to be SageMaker-compliant
    clean_timestamp = re.sub(r'[^a-zA-Z0-9-]', '-', timestamp)
    clean_timestamp = re.sub(r'-+', '-', clean_timestamp)
    clean_timestamp = clean_timestamp.strip('-')
    
    # Construct job name with prefix
    job_name = f"prosper-automl-{clean_request_name}-{clean_timestamp}"
    
    # Ensure it's within the 63 character limit
    if len(job_name) > 63:
        # Truncate the request name part if needed
        max_request_length = 63 - len("prosper-automl-") - len(clean_timestamp) - 1
        if max_request_length > 0:
            clean_request_name = clean_request_name[:max_request_length]
            job_name = f"prosper-automl-{clean_request_name}-{clean_timestamp}"
        else:
            # If timestamp is too long, truncate it too
            max_timestamp_length = 63 - len("prosper-automl-") - len(clean_request_name) - 1
            clean_timestamp = clean_timestamp[:max_timestamp_length]
            job_name = f"prosper-automl-{clean_request_name}-{clean_timestamp}"
    
    return job_name

def construct_input_s3_path(bucket_name, request_name):
    """
    Construct the S3 path for AutoML job input data.
    
    Args:
        bucket_name (str): Name of the S3 bucket
        request_name (str): The request name from the workflow
        
    Returns:
        str: S3 URI for the modeling data CSV file
    """
    return f"s3://{bucket_name}/{request_name}/modeling_data.csv"

def construct_output_s3_path(bucket_name, request_name):
    """
    Construct the S3 path for AutoML job output data.
    
    Args:
        bucket_name (str): Name of the S3 bucket
        request_name (str): The request name from the workflow
        
    Returns:
        str: S3 URI for the AutoML job output directory
    """
    return f"s3://{bucket_name}/{request_name}/automl-output/"

def validate_job_name(job_name):
    """
    Validate that a job name meets SageMaker AutoML requirements.
    
    Args:
        job_name (str): The job name to validate
        
    Returns:
        bool: True if the job name is valid, False otherwise
    """
    if not job_name:
        return False
    
    # Check length
    if len(job_name) < 1 or len(job_name) > 63:
        return False
    
    # Check character requirements
    if not re.match(r'^[a-zA-Z0-9-]+$', job_name):
        return False
    
    # Check that it doesn't start or end with hyphen
    if job_name.startswith('-') or job_name.endswith('-'):
        return False
    
    return True

def extract_request_name_from_job_name(job_name):
    """
    Extract the original request name from an AutoML job name.
    
    Args:
        job_name (str): The AutoML job name
        
    Returns:
        str: The extracted request name, or None if not extractable
    """
    if not job_name.startswith('prosper-automl-'):
        return None
    
    # Remove the prefix
    remainder = job_name[len('prosper-automl-'):]
    
    # Find the last hyphen (separates request name from timestamp)
    last_hyphen = remainder.rfind('-')
    if last_hyphen == -1:
        return remainder
    
    return remainder[:last_hyphen]

def create_automl_job_config(job_name, input_s3_path, output_s3_path, target_column, role_arn):
    """
    Create the configuration dictionary for a SageMaker AutoML job.
    
    Args:
        job_name (str): The AutoML job name
        input_s3_path (str): S3 path to the input CSV file
        output_s3_path (str): S3 path for output data
        target_column (str): Name of the target column for prediction
        role_arn (str): ARN of the SageMaker execution role
        
    Returns:
        dict: AutoML job configuration for SageMaker API
    """
    return {
        "AutoMLJobName": job_name,
        "InputDataConfig": [
            {
                "DataSource": {
                    "S3DataSource": {
                        "S3DataType": "S3Prefix",
                        "S3Uri": input_s3_path
                    }
                },
                "TargetAttributeName": target_column
            }
        ],
        "OutputDataConfig": {
            "S3OutputPath": output_s3_path
        },
        "RoleArn": role_arn,
        "AutoMLJobConfig": {
            "CompletionCriteria": {
                "MaxCandidates": 250,
                "MaxRuntimePerTrainingJobInSeconds": 3600,
                "MaxAutoMLJobRuntimeInSeconds": 86400  # 24 hours
            }
        }
    }