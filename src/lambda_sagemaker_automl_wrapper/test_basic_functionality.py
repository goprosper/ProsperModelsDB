#!/usr/bin/env python3
"""
Basic functionality test for the Lambda SageMaker AutoML wrapper.

This script performs basic validation of the implementation without
requiring AWS services to be available.
"""

import sys
import json
from typing import Dict, Any

# Test imports
try:
    from models import AutoMLJobRequest, validate_required_parameters, sanitize_input
    from validation import validate_automl_job_request, sanitize_parameters
    from sagemaker_client import SageMakerAutoMLClient
    from s3_handler import S3FeatureSpecificationHandler
    from response_handler import format_success_response, validate_step_functions_compatibility
    from error_handler import StepFunctionsErrorFormatter, ParameterValidationError
    from logger import setup_logging, get_logger
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)


def test_parameter_validation():
    """Test parameter validation functionality."""
    print("\n🧪 Testing parameter validation...")
    
    # Valid parameters
    valid_params = {
        "AutoMLJobName": "test-job-123",
        "InputDataConfig": [
            {
                "DataSource": {
                    "S3DataSource": {
                        "S3DataType": "S3Prefix",
                        "S3Uri": "s3://test-bucket/data.csv"
                    }
                },
                "TargetAttributeName": "target"
            }
        ],
        "OutputDataConfig": {
            "S3OutputPath": "s3://test-bucket/output/"
        },
        "RoleArn": "arn:aws:iam::123456789012:role/TestRole"
    }
    
    try:
        validate_automl_job_request(valid_params)
        print("✅ Valid parameters accepted")
    except Exception as e:
        print(f"❌ Valid parameters rejected: {e}")
        return False
    
    # Invalid parameters (missing required field)
    invalid_params = valid_params.copy()
    del invalid_params["AutoMLJobName"]
    
    try:
        validate_automl_job_request(invalid_params)
        print("❌ Invalid parameters accepted (should have failed)")
        return False
    except Exception:
        print("✅ Invalid parameters correctly rejected")
    
    return True


def test_parameter_sanitization():
    """Test parameter sanitization functionality."""
    print("\n🧪 Testing parameter sanitization...")
    
    # Parameters with potential issues
    params_with_issues = {
        "AutoMLJobName": "test-job\x00\x01",  # null bytes
        "InputDataConfig": [
            {
                "DataSource": {
                    "S3DataSource": {
                        "S3Uri": "s3://test-bucket/data.csv\n\r"  # control characters
                    }
                },
                "TargetAttributeName": "target\t"  # tab character
            }
        ]
    }
    
    try:
        sanitized = sanitize_parameters(params_with_issues)
        
        # Check that control characters were removed
        if "\x00" not in sanitized["AutoMLJobName"]:
            print("✅ Null bytes removed from job name")
        else:
            print("❌ Null bytes not removed")
            return False
        
        if sanitized["InputDataConfig"][0]["TargetAttributeName"].strip() == "target":
            print("✅ Control characters handled in target attribute")
        else:
            print("❌ Control characters not handled properly")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Sanitization failed: {e}")
        return False


def test_s3_uri_validation():
    """Test S3 URI validation."""
    print("\n🧪 Testing S3 URI validation...")
    
    try:
        from validation import validate_s3_uri
        
        # Valid S3 URI
        validate_s3_uri("s3://test-bucket/path/to/file.json")
        print("✅ Valid S3 URI accepted")
        
        # Invalid S3 URI
        try:
            validate_s3_uri("http://example.com/file.json")
            print("❌ Invalid S3 URI accepted (should have failed)")
            return False
        except Exception:
            print("✅ Invalid S3 URI correctly rejected")
        
        return True
        
    except Exception as e:
        print(f"❌ S3 URI validation failed: {e}")
        return False


def test_response_formatting():
    """Test response formatting for Step Functions compatibility."""
    print("\n🧪 Testing response formatting...")
    
    # Mock SageMaker response
    sagemaker_response = {
        "AutoMLJobArn": "arn:aws:sagemaker:us-east-1:123456789012:automl-job/test-job-123"
    }
    
    try:
        formatted_response = format_success_response(sagemaker_response)
        
        if "AutoMLJobArn" in formatted_response:
            print("✅ Response contains required AutoMLJobArn")
        else:
            print("❌ Response missing AutoMLJobArn")
            return False
        
        if validate_step_functions_compatibility(formatted_response):
            print("✅ Response is Step Functions compatible")
        else:
            print("❌ Response not Step Functions compatible")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Response formatting failed: {e}")
        return False


def test_error_handling():
    """Test error handling and formatting."""
    print("\n🧪 Testing error handling...")
    
    try:
        # Test parameter validation error
        test_error = ParameterValidationError("Test validation error", parameter_name="TestParam")
        
        try:
            StepFunctionsErrorFormatter.format_error_for_step_functions(test_error)
            print("❌ Error formatting should have raised an exception")
            return False
        except Exception as formatted_error:
            # Check that the error message is properly formatted
            error_message = str(formatted_error)
            if "Test validation error" in error_message:
                print("✅ Error properly formatted for Step Functions")
            else:
                print("❌ Error not properly formatted")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


def test_logging_setup():
    """Test logging configuration."""
    print("\n🧪 Testing logging setup...")
    
    try:
        logger = setup_logging("INFO")
        
        if logger:
            print("✅ Logger setup successful")
            
            # Test logging without errors
            logger.info("Test log message")
            print("✅ Logging functionality works")
            
            return True
        else:
            print("❌ Logger setup failed")
            return False
            
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        return False


def main():
    """Run all basic functionality tests."""
    print("🚀 Starting basic functionality tests for Lambda SageMaker AutoML Wrapper")
    
    tests = [
        test_parameter_validation,
        test_parameter_sanitization,
        test_s3_uri_validation,
        test_response_formatting,
        test_error_handling,
        test_logging_setup
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ Test {test.__name__} failed")
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All basic functionality tests passed!")
        return True
    else:
        print("💥 Some tests failed. Please review the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)