# Implementation Plan

- [x] 1. Set up IAM roles and permissions for SageMaker integration





  - Create SageMaker execution role with S3 and CloudWatch permissions
  - Update Step Functions execution role with SageMaker permissions
  - Configure S3 bucket policies for AutoML job access
  - _Requirements: 1.1, 1.5_

- [x] 2. Extend DynamoDB table schema for AutoML tracking





  - [x] 2.1 Add Status attribute support for AutoML states


    - Update table to support new status values: "AutoML_Job_Started", "AutoML_Job_Running", "AutoML_Job_Completed", "AutoML_Job_Failed", "AutoML_Job_Launch_Failed"
    - _Requirements: 1.3, 2.5, 3.1, 3.2_
  
  - [x] 2.2 Add ErrorMessage attribute for failure tracking


    - Implement ErrorMessage attribute to store failure reasons
    - _Requirements: 1.5, 3.3_
  
  - [x] 2.3 Add AutoMLJobName attribute for job reference


    - Store SageMaker job name for traceability and monitoring
    - _Requirements: 1.4_

- [ ]* 2.4 Write property test for database schema extensions
  - **Property 11: Database Attribute Preservation**
  - **Validates: Requirements 3.4**

- [x] 3. Implement AutoML job launch state in Step Functions




  - [x] 3.1 Create LaunchAutoMLJob state definition


    - Configure SageMaker CreateAutoMLJob integration
    - Set up input data configuration with S3 path construction
    - Configure output data location
    - Set target attribute name from label data
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 3.2 Implement job name generation logic


    - Create unique job names using requestName and timestamp
    - Ensure job name compliance with SageMaker naming requirements
    - _Requirements: 1.4_

  - [x] 3.3 Add error handling for job launch failures


    - Configure catch blocks for SageMaker API errors
    - Update database status on launch failures
    - _Requirements: 1.5_

- [ ]* 3.4 Write property test for AutoML job configuration
  - **Property 1: AutoML Job Launch with Correct S3 Path**
  - **Property 2: AutoML Job Output Configuration**
  - **Property 4: Job Name Contains Request Name**
  - **Validates: Requirements 1.1, 1.2, 1.4**

- [ ]* 3.5 Write property test for job launch status updates
  - **Property 3: Database Status Update on Job Launch**
  - **Property 5: Launch Failure Status Update**
  - **Validates: Requirements 1.3, 1.5**

- [x] 4. Implement AutoML job polling mechanism





  - [ ] 4.1 Create PollAutoMLJob state with Wait and Choice logic
    - Configure 1-minute wait intervals between status checks
    - Implement Choice state for job status evaluation
    - Set up loop for continued polling


    - _Requirements: 2.1, 2.2_

  - [ ] 4.2 Add polling timeout and retry logic
    - Implement maximum polling duration limits


    - Configure retry mechanisms for API failures
    - Handle timeout conditions gracefully
    - _Requirements: 2.3, 2.4_

  - [ ] 4.3 Implement job completion detection
    - Configure transitions for completed, failed, and running states
    - Ensure proper workflow progression on completion
    - _Requirements: 2.5_

- [ ]* 4.4 Write property test for job status detection
  - **Property 6: Job Status Detection**
  - **Property 7: Workflow Progression on Completion**
  - **Validates: Requirements 2.2, 2.5**

- [ ] 5. Implement final status update mechanism
  - [ ] 5.1 Create UpdateFinalStatus state for successful completion
    - Configure DynamoDB update for completed jobs
    - Preserve existing record attributes during updates
    - _Requirements: 3.1, 3.4_

  - [ ] 5.2 Create UpdateFailureStatus state for failed jobs
    - Configure DynamoDB update for failed jobs
    - Capture and store error messages from SageMaker
    - _Requirements: 3.2, 3.3_

  - [ ] 5.3 Add retry logic for database update failures
    - Implement exponential backoff for DynamoDB throttling
    - Configure maximum retry attempts
    - _Requirements: 3.5_

- [ ]* 5.4 Write property test for status updates
  - **Property 8: Successful Completion Status Update**
  - **Property 9: Failure Status Update**
  - **Property 10: Error Message Capture**
  - **Validates: Requirements 3.1, 3.2, 3.3**

- [ ] 6. Integrate AutoML states into existing Step Functions workflow
  - [ ] 6.1 Update workflow definition to include AutoML states
    - Add LaunchAutoMLJob state after CreateModelingData
    - Connect polling and status update states
    - Maintain existing workflow functionality
    - _Requirements: 5.1, 5.3_

  - [ ] 6.2 Ensure backward compatibility with existing inputs
    - Validate that existing input parameters continue to work
    - Preserve all original workflow outputs and behavior
    - _Requirements: 5.4_

  - [ ] 6.3 Implement error isolation for AutoML failures
    - Ensure AutoML errors don't affect previous workflow steps
    - Maintain data integrity of completed operations
    - _Requirements: 5.5_

- [ ]* 6.4 Write property test for workflow integration
  - **Property 14: Workflow Sequencing**
  - **Property 15: Input Parameter Backward Compatibility**
  - **Property 16: Error Isolation**
  - **Validates: Requirements 5.1, 5.4, 5.5**

- [ ] 7. Implement comprehensive error handling
  - [ ] 7.1 Add global error handling for Step Functions workflow
    - Configure catch blocks for all AutoML-related states
    - Ensure database reflects failure states for any workflow errors
    - _Requirements: 4.3_

  - [ ] 7.2 Implement service limit and throttling handling
    - Add retry logic with exponential backoff for SageMaker API calls
    - Handle DynamoDB throttling scenarios
    - _Requirements: 4.5_

  - [ ] 7.3 Add comprehensive logging and monitoring
    - Configure CloudWatch logging for all AutoML operations
    - Add detailed error information capture
    - _Requirements: 4.1_

- [ ]* 7.4 Write property test for error handling
  - **Property 12: Error Status Database Update**
  - **Property 13: Workflow Failure Database Reflection**
  - **Validates: Requirements 4.2, 4.3**

- [ ] 8. Update CloudFormation template with new resources
  - [ ] 8.1 Add SageMaker execution role to template
    - Define IAM role with necessary SageMaker permissions
    - Configure S3 access for input and output data
    - Add CloudWatch logging permissions
    - _Requirements: 1.1_

  - [ ] 8.2 Update Step Functions role permissions
    - Add SageMaker service permissions
    - Update DynamoDB permissions for new attributes
    - _Requirements: 1.1, 2.1_

  - [ ] 8.3 Update Step Functions state machine definition
    - Replace existing workflow definition with enhanced version
    - Configure all new states and transitions
    - _Requirements: 5.1_

- [ ] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 10. Write integration tests for end-to-end workflow
  - Create integration tests with real SageMaker jobs
  - Test S3 integration with actual file operations
  - Validate DynamoDB integration with real table operations
  - Test error scenarios with service limit simulation

- [ ] 11. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.