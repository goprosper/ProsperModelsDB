# Design Document

## Overview

This design extends the existing ProsperModels Step Functions workflow to integrate SageMaker AutoML capabilities. The solution adds three new states to the workflow: AutoML job creation, job status polling, and final status updates. The design leverages AWS Step Functions' native SageMaker integration and built-in polling mechanisms to provide a robust, serverless AutoML pipeline.

## Architecture

The enhanced workflow follows this sequence:
1. Existing workflow creates modeling data CSV
2. New AutoML job launch state creates SageMaker AutoML job
3. New polling state monitors job progress with 1-minute intervals
4. New status update state writes final results to DynamoDB

The architecture maintains the existing serverless approach using Step Functions native integrations, avoiding the need for additional Lambda functions for basic AutoML operations.

## Components and Interfaces

### Enhanced Step Functions Workflow
- **LaunchAutoMLJob**: Creates SageMaker AutoML job using Step Functions SageMaker integration
- **PollAutoMLJob**: Monitors job status using Step Functions Wait and Choice states
- **UpdateFinalStatus**: Updates DynamoDB with completion/failure status

### SageMaker AutoML Job Configuration
- **Input Data**: S3 path to modeling_data.csv in prosper-raw-data/$requestName/
- **Output Location**: S3 path to prosper-raw-data/$requestName/automl-output/
- **Job Name**: Constructed from requestName and timestamp for uniqueness
- **Target Column**: Uses the label column from LabelList as the target for prediction
- **Problem Type**: Auto-detected based on target column characteristics

### DynamoDB Schema Extensions
- **Status**: String attribute tracking workflow progress
  - Values: "AutoML_Job_Started", "AutoML_Job_Running", "AutoML_Job_Completed", "AutoML_Job_Failed", "AutoML_Job_Launch_Failed"
- **ErrorMessage**: String attribute containing failure details (optional)
- **AutoMLJobName**: String attribute storing the SageMaker job name for reference (optional)

## Data Models

### AutoML Job Input Structure
```json
{
  "JobName": "prosper-automl-{requestName}-{timestamp}",
  "InputDataConfig": [{
    "DataSource": {
      "S3DataSource": {
        "S3DataType": "S3Prefix",
        "S3Uri": "s3://prosper-raw-data/{requestName}/modeling_data.csv"
      }
    },
    "TargetAttributeName": "{labelColumnName}"
  }],
  "OutputDataConfig": {
    "S3OutputPath": "s3://prosper-raw-data/{requestName}/automl-output/"
  },
  "RoleArn": "arn:aws:iam::{account}:role/SageMakerExecutionRole"
}
```

### Polling State Data Structure
```json
{
  "AutoMLJobName": "prosper-automl-{requestName}-{timestamp}",
  "JobStatus": "InProgress|Completed|Failed|Stopped",
  "FailureReason": "string (if failed)",
  "PollCount": 0,
  "MaxPolls": 1440
}
```

### DynamoDB Update Structure
```json
{
  "TableName": "ProsperModels",
  "Key": {
    "Id": {"S": "{id}"}
  },
  "UpdateExpression": "SET #status = :status, #autoMLJobName = :jobName",
  "ExpressionAttributeNames": {
    "#status": "Status",
    "#autoMLJobName": "AutoMLJobName"
  },
  "ExpressionAttributeValues": {
    ":status": {"S": "AutoML_Job_Completed"},
    ":jobName": {"S": "prosper-automl-{requestName}-{timestamp}"}
  }
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: AutoML Job Launch with Correct S3 Path
*For any* valid request name and modeling data creation, launching an AutoML job should configure the input data source to use the S3 path "s3://prosper-raw-data/{requestName}/modeling_data.csv"
**Validates: Requirements 1.1**

### Property 2: AutoML Job Output Configuration
*For any* AutoML job launch with a valid request name, the output configuration should point to "s3://prosper-raw-data/{requestName}/automl-output/"
**Validates: Requirements 1.2**

### Property 3: Database Status Update on Job Launch
*For any* successful AutoML job launch, the ProsperModels table Status attribute should be updated to "AutoML_Job_Started"
**Validates: Requirements 1.3**

### Property 4: Job Name Contains Request Name
*For any* AutoML job launch with a request name, the generated job name should contain that request name as a substring
**Validates: Requirements 1.4**

### Property 5: Launch Failure Status Update
*For any* AutoML job launch failure, the system should update the Status attribute to "AutoML_Job_Launch_Failed" and populate ErrorMessage with the failure reason
**Validates: Requirements 1.5**

### Property 6: Job Status Detection
*For any* job status polling response, the system should correctly identify whether the job is in completion, failure, or running state
**Validates: Requirements 2.2**

### Property 7: Workflow Progression on Completion
*For any* polling operation that detects job completion, the system should proceed to the final status update step
**Validates: Requirements 2.5**

### Property 8: Successful Completion Status Update
*For any* AutoML job that completes successfully, the ProsperModels table Status attribute should be updated to "AutoML_Job_Completed"
**Validates: Requirements 3.1**

### Property 9: Failure Status Update
*For any* AutoML job that fails, the Status attribute should be updated to "AutoML_Job_Failed"
**Validates: Requirements 3.2**

### Property 10: Error Message Capture
*For any* AutoML job failure with an error reason, the ErrorMessage attribute should be populated with that specific failure reason
**Validates: Requirements 3.3**

### Property 11: Database Attribute Preservation
*For any* database update operation, all existing record attributes not being updated should remain unchanged
**Validates: Requirements 3.4**

### Property 12: Error Status Database Update
*For any* error that occurs in the AutoML process, the database should be updated with an appropriate error status and message
**Validates: Requirements 4.2**

### Property 13: Workflow Failure Database Reflection
*For any* Step Functions workflow failure, the database should reflect the failure state with appropriate status
**Validates: Requirements 4.3**

### Property 14: Workflow Sequencing
*For any* successful CreateModelingData step completion, the workflow should automatically proceed to AutoML job launch
**Validates: Requirements 5.1**

### Property 15: Input Parameter Backward Compatibility
*For any* valid existing input parameters, the enhanced workflow should execute successfully while maintaining all original functionality
**Validates: Requirements 5.4**

### Property 16: Error Isolation
*For any* error occurring in AutoML steps, the integrity and data of previously completed workflow steps should remain unaffected
**Validates: Requirements 5.5**

## Error Handling

### AutoML Job Launch Failures
- Invalid S3 paths or permissions issues
- SageMaker service limits or quotas exceeded
- Malformed job configuration parameters
- IAM role permission issues

### Job Monitoring Failures
- SageMaker API throttling during status checks
- Network connectivity issues during polling
- Job status API response parsing errors
- Timeout conditions after maximum polling duration

### Database Update Failures
- DynamoDB throttling or capacity issues
- Network connectivity problems
- Invalid update expressions or attribute conflicts
- Concurrent modification conflicts

### Recovery Strategies
- Exponential backoff for API throttling
- Retry mechanisms with maximum attempt limits
- Graceful degradation with appropriate error status updates
- Dead letter queue integration for failed executions

## Testing Strategy

### Unit Testing Approach
Unit tests will focus on:
- Step Functions state definition validation
- DynamoDB update expression correctness
- S3 path construction logic
- Error handling and status mapping
- Input parameter validation and transformation

### Property-Based Testing Approach
Property-based tests will use **Hypothesis** for Python to verify:
- Universal properties across all valid inputs
- Invariant preservation during state transitions
- Error handling consistency across failure scenarios
- Database integrity maintenance during updates

Each property-based test will run a minimum of 100 iterations to ensure comprehensive coverage of the input space. Tests will be tagged with comments explicitly referencing the correctness properties they implement using the format: **Feature: sagemaker-automl-integration, Property {number}: {property_text}**

### Integration Testing
- End-to-end workflow execution with real SageMaker jobs
- S3 integration testing with actual file operations
- DynamoDB integration with real table operations
- Error scenario testing with service limit simulation

### Testing Framework Configuration
- **Unit Tests**: pytest with moto for AWS service mocking
- **Property-Based Tests**: Hypothesis with custom generators for AWS resource names and configurations
- **Integration Tests**: pytest with real AWS resources in test environment
- **Test Coverage**: Minimum 90% code coverage for all new components