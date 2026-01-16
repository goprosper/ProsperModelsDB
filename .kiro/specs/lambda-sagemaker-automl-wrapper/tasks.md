# Implementation Plan: Lambda SageMaker AutoML Wrapper

## Overview

This implementation creates a Lambda function that wraps the SageMaker CreateAutoMLJob API to support parameters not available through AWS Step Functions' direct SageMaker integration, specifically the FeatureSpecificationS3Uri parameter. The Lambda will maintain compatibility with the existing Step Functions workflow while providing full SageMaker API access.

## Tasks

- [x] 1. Set up Lambda function structure and dependencies
  - Create Lambda function directory structure
  - Set up Python requirements.txt with boto3, logging, and testing dependencies
  - Configure basic Lambda handler function signature
  - _Requirements: 3.1, 5.1_

- [x] 2. Implement core parameter handling and validation
  - [x] 2.1 Create input parameter data models
    - Define dataclasses for AutoML job request structure
    - Implement parameter validation for required fields
    - Add type hints and documentation
    - _Requirements: 2.2, 3.1_

  - [x] 2.2 Implement parameter sanitization and validation
    - Add input sanitization to prevent injection attacks
    - Validate S3 URI formats and patterns
    - Implement required parameter checking
    - _Requirements: 2.2, 5.2, 5.3_

  - [ ]* 2.3 Write property test for parameter validation
    - **Property 2: Required Parameter Validation**
    - **Property 11: Input Sanitization**
    - **Validates: Requirements 2.2, 5.3**

- [x] 3. Implement SageMaker API integration
  - [x] 3.1 Create SageMaker client wrapper
    - Initialize boto3 SageMaker client with proper configuration
    - Implement parameter mapping from Lambda input to SageMaker API
    - Handle all SageMaker CreateAutoMLJob parameters including FeatureSpecificationS3Uri
    - _Requirements: 1.1, 1.2, 2.1, 2.3_

  - [x] 3.2 Implement response handling
    - Process SageMaker API responses and format for Step Functions
    - Ensure AutoMLJobArn is returned in compatible format
    - Maintain response structure compatibility
    - _Requirements: 1.5, 2.4, 3.2_

  - [ ]* 3.3 Write property test for SageMaker integration
    - **Property 1: Parameter Acceptance and Pass-through**
    - **Property 3: Successful Response Handling**
    - **Validates: Requirements 1.1, 1.2, 1.5, 2.1, 2.3, 2.4**

- [x] 4. Implement S3 feature specification handling
  - [x] 4.1 Add S3 validation and access
    - Validate FeatureSpecificationS3Uri format and accessibility
    - Check S3 file existence and permissions
    - Parse and validate feature specification JSON format
    - _Requirements: 1.3, 1.4, 5.2_

  - [x] 4.2 Implement S3 error handling
    - Handle S3 access denied, file not found, and network errors
    - Provide descriptive error messages for S3 issues
    - Log S3 errors with appropriate detail level
    - _Requirements: 1.4, 4.4_

  - [ ]* 4.3 Write property test for S3 handling
    - **Property 4: S3 Error Handling**
    - **Property 10: S3 URI Validation**
    - **Property 13: Feature Specification File Processing**
    - **Validates: Requirements 1.3, 1.4, 4.4, 5.2**

- [x] 5. Implement comprehensive error handling
  - [x] 5.1 Create error handling framework
    - Define custom exception classes for different error types
    - Implement Step Functions compatible error formatting
    - Add error response structure with errorType and errorMessage
    - _Requirements: 2.5, 3.3, 5.4_

  - [x] 5.2 Handle SageMaker API errors
    - Map SageMaker exceptions to Step Functions compatible format
    - Implement retry logic for throttling scenarios
    - Format SageMaker error details appropriately
    - _Requirements: 2.5, 4.3_

  - [ ]* 5.3 Write property test for error handling
    - **Property 5: SageMaker Error Compatibility**
    - **Property 8: Error Format Compatibility**
    - **Property 12: Error Message Security**
    - **Validates: Requirements 2.5, 3.3, 5.4**

- [x] 6. Implement comprehensive logging
  - [x] 6.1 Add structured logging
    - Log input parameters (excluding sensitive data)
    - Log validation errors with appropriate detail
    - Log SageMaker API calls and responses
    - Log S3 access attempts and results
    - _Requirements: 4.1, 4.2, 4.5_

  - [x] 6.2 Implement security-conscious logging
    - Filter sensitive information from logs
    - Ensure error messages don't expose sensitive data
    - Add appropriate log levels for different scenarios
    - _Requirements: 4.1, 5.4_

  - [ ]* 6.3 Write property test for logging
    - **Property 9: Comprehensive Logging**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.5**

- [x] 7. Ensure Step Functions compatibility
  - [x] 7.1 Implement input format compatibility
    - Accept exact input format from current LaunchAutoMLJob state
    - Handle JSONata expressions and Step Functions variable references
    - Maintain backward compatibility with existing workflow
    - _Requirements: 3.1, 3.4_

  - [x] 7.2 Implement output format compatibility
    - Return response in same format as SageMaker Step Functions integration
    - Ensure next state in workflow receives expected data structure
    - Test compatibility with existing workflow transitions
    - _Requirements: 3.2, 3.4_

  - [ ]* 7.3 Write property test for Step Functions compatibility
    - **Property 6: Input Format Compatibility**
    - **Property 7: Output Format Compatibility**
    - **Validates: Requirements 3.1, 3.2**

- [x] 8. Create Lambda deployment configuration
  - [x] 8.1 Create SAM template for Lambda function
    - Define Lambda function resource with appropriate runtime
    - Configure IAM role with SageMaker and S3 permissions
    - Set up environment variables and timeout configuration
    - _Requirements: 5.1_

  - [x] 8.2 Configure IAM permissions
    - Create least-privilege IAM role for Lambda execution
    - Add SageMaker CreateAutoMLJob permissions
    - Add S3 read permissions for feature specification files
    - Add CloudWatch logging permissions
    - _Requirements: 5.1, 5.2_

  - [x] 8.3 Update Step Functions workflow
    - Replace LaunchAutoMLJob state Resource from aws-sdk:sagemaker to lambda:invoke
    - Update state configuration to call Lambda function
    - Ensure error handling catch blocks remain compatible
    - _Requirements: 3.5_

- [x] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 10. Write integration tests
  - Create integration tests with mocked AWS services
  - Test end-to-end workflow with Step Functions
  - Validate error scenarios and retry logic
  - Test with real AWS services in development environment

- [x] 11. Performance and security validation
  - [x] 11.1 Validate execution performance
    - Ensure Lambda completes within Step Functions timeout limits
    - Test with various input sizes and complexity
    - Optimize for cold start performance
    - _Requirements: 5.5_

  - [x] 11.2 Security validation
    - Validate IAM permissions are least-privilege
    - Test error message security (no sensitive data exposure)
    - Validate input sanitization effectiveness
    - _Requirements: 5.1, 5.3, 5.4_

- [x] 12. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Implement Test mode training plan support
  - [x] 13.1 Add modelTrainingPlan parameter processing
    - Update parameter validation to accept modelTrainingPlan parameter
    - Implement logic to detect 'Test' mode and apply appropriate CompletionCriteria
    - Add support for Bronze and Silver modes with existing criteria
    - _Requirements: 6.1, 6.2_

  - [x] 13.2 Implement Test mode completion criteria
    - Set MaxCandidates: 1 when modelTrainingPlan = 'Test'
    - Set MaxRuntimePerTrainingJobInSeconds: 120 for Test mode
    - Set MaxAutoMLJobRuntimeInSeconds: 120 for Test mode
    - Ensure existing CompletionCriteria is preserved when modelTrainingPlan is not 'Test'
    - _Requirements: 6.1_

  - [x] 13.3 Add Test mode logging
    - Log when Test mode completion criteria are being applied
    - Include modelTrainingPlan value in parameter logging
    - Ensure Test mode usage is clearly identifiable in logs
    - _Requirements: 6.4_

  - [ ]* 13.4 Write property tests for Test mode functionality
    - **Property 14: Test Mode Completion Criteria**
    - **Property 15: Test Mode Logging**
    - **Property 16: Training Plan Response Consistency**
    - **Validates: Requirements 6.1, 6.4, 6.5**

- [x] 14. Update Step Functions workflow for Test mode
  - [x] 14.1 Update workflow to pass modelTrainingPlan parameter
    - Ensure modelTrainingPlan is passed from Step Functions input to Lambda
    - Update JSONata expressions to handle Test mode alongside Bronze and Silver
    - Maintain backward compatibility with existing workflow executions
    - _Requirements: 6.2_

- [x] 15. Test mode validation checkpoint
  - Ensure Test mode functionality works correctly, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from the design document
- Integration tests ensure compatibility with existing Step Functions workflow
- The Lambda function will be deployed via SAM/CloudFormation alongside existing infrastructure