"""
Test script to verify ErrorMessage attribute support in DynamoDB operations.

This script demonstrates that the ErrorMessage attribute can be properly
stored and retrieved from the ProsperModels table.
"""

import boto3
from moto import mock_dynamodb
import pytest
from automl_dynamodb_utils import update_job_launch_failed_status, get_record_status
from automl_constants import AutoMLStatus, DynamoDBAttributes

@mock_dynamodb
def test_error_message_storage_and_retrieval():
    """Test that ErrorMessage can be stored and retrieved from DynamoDB."""
    
    # Create mock DynamoDB table
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table_name = 'test-prosper-models'
    
    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {
                'AttributeName': 'Id',
                'KeyType': 'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'Id',
                'AttributeType': 'S'
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    # Test data
    record_id = 'test-record-123'
    error_message = 'SageMaker service limit exceeded: Maximum number of AutoML jobs reached'
    
    # First, put a basic record
    table.put_item(
        Item={
            'Id': record_id,
            'UserId': 'test-user',
            'UserName': 'Test User'
        }
    )
    
    # Update with error message
    response = update_job_launch_failed_status(
        table_name=table_name,
        record_id=record_id,
        error_message=error_message
    )
    
    # Verify the update response contains the error message
    assert response['Attributes'][DynamoDBAttributes.STATUS] == AutoMLStatus.JOB_LAUNCH_FAILED
    assert response['Attributes'][DynamoDBAttributes.ERROR_MESSAGE] == error_message
    
    # Retrieve the record and verify error message is stored
    record_status = get_record_status(table_name, record_id)
    assert record_status[DynamoDBAttributes.STATUS] == AutoMLStatus.JOB_LAUNCH_FAILED
    assert record_status[DynamoDBAttributes.ERROR_MESSAGE] == error_message
    
    print("✓ ErrorMessage attribute can be stored and retrieved successfully")

@mock_dynamodb 
def test_error_message_with_different_failure_types():
    """Test ErrorMessage storage with different types of failures."""
    
    # Create mock DynamoDB table
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table_name = 'test-prosper-models'
    
    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {
                'AttributeName': 'Id',
                'KeyType': 'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'Id',
                'AttributeType': 'S'
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    # Test different error scenarios
    test_cases = [
        {
            'record_id': 'test-launch-failure',
            'error_message': 'Invalid S3 path: s3://invalid-bucket/path',
            'expected_status': AutoMLStatus.JOB_LAUNCH_FAILED
        },
        {
            'record_id': 'test-job-failure', 
            'error_message': 'AutoML job failed: Insufficient data for training',
            'expected_status': AutoMLStatus.JOB_FAILED
        }
    ]
    
    for case in test_cases:
        # Put basic record
        table.put_item(
            Item={
                'Id': case['record_id'],
                'UserId': 'test-user',
                'UserName': 'Test User'
            }
        )
        
        # Update with appropriate failure status
        if case['expected_status'] == AutoMLStatus.JOB_LAUNCH_FAILED:
            update_job_launch_failed_status(
                table_name=table_name,
                record_id=case['record_id'],
                error_message=case['error_message']
            )
        else:
            from automl_dynamodb_utils import update_job_failed_status
            update_job_failed_status(
                table_name=table_name,
                record_id=case['record_id'],
                job_name='test-job-name',
                error_message=case['error_message']
            )
        
        # Verify error message is stored correctly
        record_status = get_record_status(table_name, case['record_id'])
        assert record_status[DynamoDBAttributes.STATUS] == case['expected_status']
        assert record_status[DynamoDBAttributes.ERROR_MESSAGE] == case['error_message']
    
    print("✓ ErrorMessage attribute works correctly with different failure types")

if __name__ == '__main__':
    test_error_message_storage_and_retrieval()
    test_error_message_with_different_failure_types()
    print("All ErrorMessage attribute tests passed!")