"""
Test script to verify AutoMLJobName attribute support in DynamoDB operations.

This script demonstrates that the AutoMLJobName attribute can be properly
stored and retrieved from the ProsperModels table.
"""

import boto3
from moto import mock_dynamodb
import pytest
from automl_dynamodb_utils import update_job_started_status, get_record_status
from automl_job_utils import generate_automl_job_name, validate_job_name, extract_request_name_from_job_name
from automl_constants import AutoMLStatus, DynamoDBAttributes

@mock_dynamodb
def test_automl_job_name_storage_and_retrieval():
    """Test that AutoMLJobName can be stored and retrieved from DynamoDB."""
    
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
    request_name = 'test-request'
    timestamp = '2023-12-21T10:30:00Z'
    job_name = generate_automl_job_name(request_name, timestamp)
    
    # First, put a basic record
    table.put_item(
        Item={
            'Id': record_id,
            'UserId': 'test-user',
            'UserName': 'Test User'
        }
    )
    
    # Update with job name
    response = update_job_started_status(
        table_name=table_name,
        record_id=record_id,
        job_name=job_name
    )
    
    # Verify the update response contains the job name
    assert response['Attributes'][DynamoDBAttributes.STATUS] == AutoMLStatus.JOB_STARTED
    assert response['Attributes'][DynamoDBAttributes.AUTOML_JOB_NAME] == job_name
    
    # Retrieve the record and verify job name is stored
    record_status = get_record_status(table_name, record_id)
    assert record_status[DynamoDBAttributes.STATUS] == AutoMLStatus.JOB_STARTED
    assert record_status[DynamoDBAttributes.AUTOML_JOB_NAME] == job_name
    
    print("✓ AutoMLJobName attribute can be stored and retrieved successfully")

def test_job_name_generation():
    """Test AutoML job name generation with various inputs."""
    
    test_cases = [
        {
            'request_name': 'simple-request',
            'timestamp': '2023-12-21T10:30:00Z',
            'expected_pattern': 'prosper-automl-simple-request-'
        },
        {
            'request_name': 'Request With Spaces',
            'timestamp': '2023-12-21T10:30:00Z',
            'expected_pattern': 'prosper-automl-Request-With-Spaces-'
        },
        {
            'request_name': 'request@with#special$chars',
            'timestamp': '2023-12-21T10:30:00Z',
            'expected_pattern': 'prosper-automl-request-with-special-chars-'
        }
    ]
    
    for case in test_cases:
        job_name = generate_automl_job_name(case['request_name'], case['timestamp'])
        
        # Verify job name is valid
        assert validate_job_name(job_name), f"Generated job name is invalid: {job_name}"
        
        # Verify it starts with expected pattern
        assert job_name.startswith(case['expected_pattern']), f"Job name doesn't match pattern: {job_name}"
        
        # Verify length is within limits
        assert len(job_name) <= 63, f"Job name too long: {len(job_name)} characters"
        
        # Verify we can extract the original request name
        extracted_name = extract_request_name_from_job_name(job_name)
        assert extracted_name is not None, f"Could not extract request name from: {job_name}"
    
    print("✓ AutoML job name generation works correctly")

def test_job_name_validation():
    """Test job name validation function."""
    
    valid_names = [
        'prosper-automl-test-2023-12-21',
        'a',
        'a' * 63,
        'test-123',
        'AutoML-Job-Name'
    ]
    
    invalid_names = [
        '',  # Empty
        'a' * 64,  # Too long
        '-starts-with-hyphen',  # Starts with hyphen
        'ends-with-hyphen-',  # Ends with hyphen
        'has@invalid$chars',  # Invalid characters
        'has spaces',  # Spaces not allowed
        None  # None value
    ]
    
    for name in valid_names:
        assert validate_job_name(name), f"Valid name rejected: {name}"
    
    for name in invalid_names:
        assert not validate_job_name(name), f"Invalid name accepted: {name}"
    
    print("✓ Job name validation works correctly")

@mock_dynamodb
def test_job_name_traceability():
    """Test that job names provide proper traceability to original requests."""
    
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
    
    # Test multiple records with different request names
    test_records = [
        {'id': 'record-1', 'request_name': 'customer-analysis'},
        {'id': 'record-2', 'request_name': 'product-recommendation'},
        {'id': 'record-3', 'request_name': 'fraud-detection'}
    ]
    
    for record in test_records:
        # Put basic record
        table.put_item(
            Item={
                'Id': record['id'],
                'UserId': 'test-user',
                'UserName': 'Test User'
            }
        )
        
        # Generate job name and update status
        job_name = generate_automl_job_name(record['request_name'])
        update_job_started_status(
            table_name=table_name,
            record_id=record['id'],
            job_name=job_name
        )
        
        # Verify traceability
        record_status = get_record_status(table_name, record['id'])
        stored_job_name = record_status[DynamoDBAttributes.AUTOML_JOB_NAME]
        
        # Verify job name contains request name
        assert record['request_name'].replace('-', '-') in stored_job_name or \
               record['request_name'].replace('_', '-') in stored_job_name, \
               f"Job name {stored_job_name} doesn't contain request name {record['request_name']}"
        
        # Verify we can extract the request name back
        extracted_name = extract_request_name_from_job_name(stored_job_name)
        assert extracted_name is not None, f"Could not extract request name from {stored_job_name}"
    
    print("✓ Job name traceability works correctly")

if __name__ == '__main__':
    test_automl_job_name_storage_and_retrieval()
    test_job_name_generation()
    test_job_name_validation()
    test_job_name_traceability()
    print("All AutoMLJobName attribute tests passed!")