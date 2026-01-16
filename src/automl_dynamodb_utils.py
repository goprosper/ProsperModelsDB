"""
Utility functions for DynamoDB operations related to AutoML integration.

This module provides functions to update the ProsperModels table with
AutoML job status and related information.
"""

import boto3
from botocore.exceptions import ClientError
from automl_constants import AutoMLStatus, DynamoDBAttributes, validate_automl_status

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')

def update_automl_status(table_name, record_id, status, job_name=None, error_message=None):
    """
    Update the AutoML status and related attributes for a record in DynamoDB.
    
    Args:
        table_name (str): Name of the DynamoDB table
        record_id (str): The Id of the record to update
        status (str): The AutoML status to set (must be valid AutoMLStatus)
        job_name (str, optional): The SageMaker AutoML job name
        error_message (str, optional): Error message for failed jobs
        
    Returns:
        dict: DynamoDB update response
        
    Raises:
        ValueError: If status is not a valid AutoML status
        ClientError: If DynamoDB operation fails
    """
    if not validate_automl_status(status):
        raise ValueError(f"Invalid AutoML status: {status}")
    
    table = dynamodb.Table(table_name)
    
    # Build update expression and attribute values
    update_expression = f"SET #{DynamoDBAttributes.STATUS} = :{DynamoDBAttributes.STATUS}"
    expression_attribute_names = {
        f"#{DynamoDBAttributes.STATUS}": DynamoDBAttributes.STATUS
    }
    expression_attribute_values = {
        f":{DynamoDBAttributes.STATUS}": status
    }
    
    # Add job name if provided
    if job_name:
        update_expression += f", #{DynamoDBAttributes.AUTOML_JOB_NAME} = :{DynamoDBAttributes.AUTOML_JOB_NAME}"
        expression_attribute_names[f"#{DynamoDBAttributes.AUTOML_JOB_NAME}"] = DynamoDBAttributes.AUTOML_JOB_NAME
        expression_attribute_values[f":{DynamoDBAttributes.AUTOML_JOB_NAME}"] = job_name
    
    # Add error message if provided
    if error_message:
        update_expression += f", #{DynamoDBAttributes.ERROR_MESSAGE} = :{DynamoDBAttributes.ERROR_MESSAGE}"
        expression_attribute_names[f"#{DynamoDBAttributes.ERROR_MESSAGE}"] = DynamoDBAttributes.ERROR_MESSAGE
        expression_attribute_values[f":{DynamoDBAttributes.ERROR_MESSAGE}"] = error_message
    
    try:
        response = table.update_item(
            Key={DynamoDBAttributes.ID: record_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="ALL_NEW"
        )
        return response
    except ClientError as e:
        print(f"Error updating DynamoDB record {record_id}: {e}")
        raise

def update_job_started_status(table_name, record_id, job_name):
    """
    Update status to indicate AutoML job has started.
    
    Args:
        table_name (str): Name of the DynamoDB table
        record_id (str): The Id of the record to update
        job_name (str): The SageMaker AutoML job name
        
    Returns:
        dict: DynamoDB update response
    """
    return update_automl_status(
        table_name=table_name,
        record_id=record_id,
        status=AutoMLStatus.JOB_STARTED,
        job_name=job_name
    )

def update_job_running_status(table_name, record_id, job_name):
    """
    Update status to indicate AutoML job is running.
    
    Args:
        table_name (str): Name of the DynamoDB table
        record_id (str): The Id of the record to update
        job_name (str): The SageMaker AutoML job name
        
    Returns:
        dict: DynamoDB update response
    """
    return update_automl_status(
        table_name=table_name,
        record_id=record_id,
        status=AutoMLStatus.JOB_RUNNING,
        job_name=job_name
    )

def update_job_completed_status(table_name, record_id, job_name):
    """
    Update status to indicate AutoML job completed successfully.
    
    Args:
        table_name (str): Name of the DynamoDB table
        record_id (str): The Id of the record to update
        job_name (str): The SageMaker AutoML job name
        
    Returns:
        dict: DynamoDB update response
    """
    return update_automl_status(
        table_name=table_name,
        record_id=record_id,
        status=AutoMLStatus.JOB_COMPLETED,
        job_name=job_name
    )

def update_job_failed_status(table_name, record_id, job_name, error_message):
    """
    Update status to indicate AutoML job failed.
    
    Args:
        table_name (str): Name of the DynamoDB table
        record_id (str): The Id of the record to update
        job_name (str): The SageMaker AutoML job name
        error_message (str): Error message describing the failure
        
    Returns:
        dict: DynamoDB update response
    """
    return update_automl_status(
        table_name=table_name,
        record_id=record_id,
        status=AutoMLStatus.JOB_FAILED,
        job_name=job_name,
        error_message=error_message
    )

def update_job_launch_failed_status(table_name, record_id, error_message):
    """
    Update status to indicate AutoML job launch failed.
    
    Args:
        table_name (str): Name of the DynamoDB table
        record_id (str): The Id of the record to update
        error_message (str): Error message describing the launch failure
        
    Returns:
        dict: DynamoDB update response
    """
    return update_automl_status(
        table_name=table_name,
        record_id=record_id,
        status=AutoMLStatus.JOB_LAUNCH_FAILED,
        error_message=error_message
    )

def update_job_timeout_status(table_name, record_id, job_name, error_message):
    """
    Update status to indicate AutoML job timed out.
    
    Args:
        table_name (str): Name of the DynamoDB table
        record_id (str): The Id of the record to update
        job_name (str): The SageMaker AutoML job name
        error_message (str): Error message describing the timeout
        
    Returns:
        dict: DynamoDB update response
    """
    return update_automl_status(
        table_name=table_name,
        record_id=record_id,
        status=AutoMLStatus.JOB_TIMEOUT,
        job_name=job_name,
        error_message=error_message
    )

def update_job_monitoring_failed_status(table_name, record_id, job_name, error_message):
    """
    Update status to indicate AutoML job monitoring failed.
    
    Args:
        table_name (str): Name of the DynamoDB table
        record_id (str): The Id of the record to update
        job_name (str): The SageMaker AutoML job name
        error_message (str): Error message describing the monitoring failure
        
    Returns:
        dict: DynamoDB update response
    """
    return update_automl_status(
        table_name=table_name,
        record_id=record_id,
        status=AutoMLStatus.JOB_MONITORING_FAILED,
        job_name=job_name,
        error_message=error_message
    )

def get_record_status(table_name, record_id):
    """
    Get the current status of a record from DynamoDB.
    
    Args:
        table_name (str): Name of the DynamoDB table
        record_id (str): The Id of the record to retrieve
        
    Returns:
        dict: Record data including status information
        
    Raises:
        ClientError: If DynamoDB operation fails
    """
    table = dynamodb.Table(table_name)
    
    try:
        response = table.get_item(
            Key={DynamoDBAttributes.ID: record_id},
            ProjectionExpression=f"#{DynamoDBAttributes.STATUS}, #{DynamoDBAttributes.AUTOML_JOB_NAME}, #{DynamoDBAttributes.ERROR_MESSAGE}",
            ExpressionAttributeNames={
                f"#{DynamoDBAttributes.STATUS}": DynamoDBAttributes.STATUS,
                f"#{DynamoDBAttributes.AUTOML_JOB_NAME}": DynamoDBAttributes.AUTOML_JOB_NAME,
                f"#{DynamoDBAttributes.ERROR_MESSAGE}": DynamoDBAttributes.ERROR_MESSAGE
            }
        )
        return response.get('Item', {})
    except ClientError as e:
        print(f"Error retrieving DynamoDB record {record_id}: {e}")
        raise