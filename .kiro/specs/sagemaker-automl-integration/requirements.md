# Requirements Document

## Introduction

This feature extends the existing ProsperModels Step Functions workflow to integrate SageMaker AutoML capabilities. The system will automatically launch AutoML jobs using generated modeling data, monitor job progress, and update the DynamoDB table with status information.

## Glossary

- **AutoML_Job**: A SageMaker AutoML training job that automatically builds machine learning models
- **ProsperModels_System**: The complete system including Step Functions workflow, DynamoDB table, and Lambda functions
- **ProsperModels_Table**: DynamoDB table storing model request information with Id as primary key
- **Modeling_Data**: CSV file containing processed feature and label data for ML training
- **Job_Polling**: Periodic checking of AutoML job status to determine completion or failure
- **Status_Update**: Process of updating DynamoDB record with current job status information

## Requirements

### Requirement 1

**User Story:** As a data scientist, I want the system to automatically launch SageMaker AutoML jobs using my modeling data, so that I can build machine learning models without manual intervention.

#### Acceptance Criteria

1. WHEN modeling data is successfully created THEN THE ProsperModels_System SHALL launch a SageMaker AutoML job using the modeling_data.csv file from prosper-raw-data/$requestName/ folder
2. WHEN launching the AutoML job THEN THE ProsperModels_System SHALL configure the job to output results to prosper-raw-data/$requestName/ folder
3. WHEN launching the AutoML job THEN THE ProsperModels_System SHALL use the label from LabelList as the target column for the AutoML job
4. WHEN the AutoML job is launched THEN THE ProsperModels_System SHALL update the ProsperModels_Table Status attribute to "AutoML_Job_Started"
5. WHEN launching the AutoML job THEN THE ProsperModels_System SHALL use the requestName as part of the job identifier for traceability
6. WHEN the AutoML job launch fails THEN THE ProsperModels_System SHALL update the Status attribute to "AutoML_Job_Launch_Failed" and populate ErrorMessage with the failure reason

### Requirement 2

**User Story:** As a data scientist, I want the system to monitor AutoML job progress automatically, so that I know when my models are ready or if issues occur.

#### Acceptance Criteria

1. WHEN an AutoML job is running THEN THE ProsperModels_System SHALL poll the job status every minute using SageMaker DescribeAutoMLJob API
2. WHEN polling the job status THEN THE ProsperModels_System SHALL evaluate the AutoMLJobStatus field for "InProgress", "Completed", "Failed", or "Stopped" values
3. WHEN the job status is "InProgress" THEN THE ProsperModels_System SHALL update the ProsperModels_Table Status to "AutoML_Job_Running" and continue polling
4. WHEN the job status check API call fails THEN THE ProsperModels_System SHALL retry the status check up to 3 times with exponential backoff before marking as failed
5. WHEN maximum polling duration of 24 hours is reached THEN THE ProsperModels_System SHALL timeout and update Status to "AutoML_Job_Timeout"
6. WHEN polling detects job status "Completed" or "Failed" THEN THE ProsperModels_System SHALL proceed to final status update
7. WHEN polling encounters persistent API failures after retries THEN THE ProsperModels_System SHALL update Status to "AutoML_Job_Monitoring_Failed" with error details

### Requirement 3

**User Story:** As a data scientist, I want the system to update the database with final job results, so that I can track the outcome of my AutoML requests.

#### Acceptance Criteria

1. WHEN the AutoML job completes successfully THEN THE ProsperModels_System SHALL update the ProsperModels_Table Status attribute to "AutoML_Job_Completed"
2. WHEN the AutoML job fails THEN THE ProsperModels_System SHALL update the Status attribute to "AutoML_Job_Failed"
3. WHEN the AutoML job fails THEN THE ProsperModels_System SHALL populate the ErrorMessage attribute with the specific failure reason from SageMaker
4. WHEN updating the database THEN THE ProsperModels_System SHALL preserve all existing record attributes
5. WHEN database update fails THEN THE ProsperModels_System SHALL retry the update operation up to 3 times

### Requirement 4

**User Story:** As a system administrator, I want proper error handling and logging throughout the AutoML process, so that I can troubleshoot issues effectively.

#### Acceptance Criteria

1. WHEN any step in the AutoML process encounters an error THEN THE ProsperModels_System SHALL log detailed error information
2. WHEN errors occur THEN THE ProsperModels_System SHALL update the database with appropriate error status and messages
3. WHEN the Step Functions workflow fails THEN THE ProsperModels_System SHALL ensure the database reflects the failure state
4. WHEN timeout conditions are met THEN THE ProsperModels_System SHALL gracefully handle the timeout and update status accordingly
5. WHEN SageMaker service limits are exceeded THEN THE ProsperModels_System SHALL handle the throttling appropriately

### Requirement 5

**User Story:** As a data scientist, I want the AutoML integration to work seamlessly with the existing workflow, so that my current process remains unchanged.

#### Acceptance Criteria

1. WHEN the existing CreateModelingData step completes THEN THE ProsperModels_System SHALL automatically proceed to AutoML job launch
2. WHEN the AutoML process completes THEN THE ProsperModels_System SHALL maintain the same output format as the current workflow
3. WHEN integrating AutoML THEN THE ProsperModels_System SHALL preserve all existing Step Functions functionality
4. WHEN the workflow executes THEN THE ProsperModels_System SHALL maintain backward compatibility with existing input parameters
5. WHEN errors occur in AutoML steps THEN THE ProsperModels_System SHALL ensure the integrity of previously completed steps remains unaffected