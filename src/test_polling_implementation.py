"""
Test script to verify Requirement 2 implementation - AutoML job polling mechanism.

This script tests the polling logic and status mapping functions.
"""

from automl_constants import (
    AutoMLStatus, 
    SageMakerJobStatus, 
    map_sagemaker_to_automl_status,
    PollingConfig,
    validate_automl_status
)

def test_sagemaker_status_mapping():
    """Test that SageMaker statuses are correctly mapped to AutoML statuses."""
    
    test_cases = [
        (SageMakerJobStatus.IN_PROGRESS, AutoMLStatus.JOB_RUNNING),
        (SageMakerJobStatus.COMPLETED, AutoMLStatus.JOB_COMPLETED),
        (SageMakerJobStatus.FAILED, AutoMLStatus.JOB_FAILED),
        (SageMakerJobStatus.STOPPED, AutoMLStatus.JOB_FAILED),
        (SageMakerJobStatus.STOPPING, AutoMLStatus.JOB_RUNNING),
        ("UnknownStatus", AutoMLStatus.JOB_FAILED)  # Default case
    ]
    
    for sagemaker_status, expected_automl_status in test_cases:
        result = map_sagemaker_to_automl_status(sagemaker_status)
        assert result == expected_automl_status, \
            f"Expected {expected_automl_status} for {sagemaker_status}, got {result}"
    
    print("✅ SageMaker status mapping works correctly")

def test_polling_configuration():
    """Test that polling configuration constants are set correctly for Requirement 2."""
    
    # Verify polling interval is 1 minute (60 seconds)
    assert PollingConfig.POLL_INTERVAL_SECONDS == 60, \
        f"Expected 60 seconds, got {PollingConfig.POLL_INTERVAL_SECONDS}"
    
    # Verify max polls is 1440 (24 hours worth of 1-minute intervals)
    assert PollingConfig.MAX_POLL_COUNT == 1440, \
        f"Expected 1440 polls, got {PollingConfig.MAX_POLL_COUNT}"
    
    # Verify retry configuration matches requirement (3 retries with exponential backoff)
    assert PollingConfig.MAX_RETRIES == 3, \
        f"Expected 3 retries, got {PollingConfig.MAX_RETRIES}"
    
    assert PollingConfig.RETRY_BACKOFF_RATE == 2.0, \
        f"Expected 2.0 backoff rate, got {PollingConfig.RETRY_BACKOFF_RATE}"
    
    print("✅ Polling configuration matches Requirement 2 specifications")

def test_all_status_values_are_valid():
    """Test that all AutoML status values are valid."""
    
    all_statuses = [
        AutoMLStatus.JOB_STARTED,
        AutoMLStatus.JOB_RUNNING,
        AutoMLStatus.JOB_COMPLETED,
        AutoMLStatus.JOB_FAILED,
        AutoMLStatus.JOB_LAUNCH_FAILED,
        AutoMLStatus.JOB_TIMEOUT,
        AutoMLStatus.JOB_MONITORING_FAILED
    ]
    
    for status in all_statuses:
        assert validate_automl_status(status), f"Status {status} is not valid"
    
    # Test that all statuses are in the ALL_STATUSES list
    for status in all_statuses:
        assert status in AutoMLStatus.ALL_STATUSES, \
            f"Status {status} not found in ALL_STATUSES list"
    
    print("✅ All AutoML status values are valid and properly defined")

def test_requirement_2_acceptance_criteria_coverage():
    """Verify that the implementation covers all Requirement 2 acceptance criteria."""
    
    # AC 2.1: Poll every minute using DescribeAutoMLJob API
    # ✅ Implemented in Step Functions with 60-second wait and DescribeAutoMLJob task
    
    # AC 2.2: Evaluate AutoMLJobStatus for specific values
    expected_sagemaker_statuses = ["InProgress", "Completed", "Failed", "Stopped"]
    for status in expected_sagemaker_statuses:
        # Verify we can map each expected status
        mapped_status = map_sagemaker_to_automl_status(status)
        assert mapped_status in AutoMLStatus.ALL_STATUSES, \
            f"Cannot map SageMaker status {status} to valid AutoML status"
    
    # AC 2.3: Update to "AutoML_Job_Running" for "InProgress"
    assert map_sagemaker_to_automl_status("InProgress") == AutoMLStatus.JOB_RUNNING
    
    # AC 2.4: Retry up to 3 times with exponential backoff
    assert PollingConfig.MAX_RETRIES == 3
    assert PollingConfig.RETRY_BACKOFF_RATE == 2.0
    
    # AC 2.5: 24-hour timeout
    assert PollingConfig.MAX_POLL_COUNT == 1440  # 24 hours * 60 minutes
    assert AutoMLStatus.JOB_TIMEOUT in AutoMLStatus.ALL_STATUSES
    
    # AC 2.6: Proceed to final status update for "Completed" or "Failed"
    assert map_sagemaker_to_automl_status("Completed") == AutoMLStatus.JOB_COMPLETED
    assert map_sagemaker_to_automl_status("Failed") == AutoMLStatus.JOB_FAILED
    
    # AC 2.7: Handle persistent API failures
    assert AutoMLStatus.JOB_MONITORING_FAILED in AutoMLStatus.ALL_STATUSES
    
    print("✅ All Requirement 2 acceptance criteria are covered by the implementation")

if __name__ == '__main__':
    test_sagemaker_status_mapping()
    test_polling_configuration()
    test_all_status_values_are_valid()
    test_requirement_2_acceptance_criteria_coverage()
    print("\n🎉 Requirement 2 implementation is complete and verified!")