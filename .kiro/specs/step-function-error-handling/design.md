# Step Function Comprehensive Error Handling - Design

## Overview
This design adds comprehensive error handling to all Step Function states that currently lack proper error handling, following the established pattern from `UpdateDataValidationFailedStatus`.

## Error Handling Architecture

### Pattern Consistency
All error handling states will follow this consistent pattern:
1. **Naming**: `Update{OperationType}FailedStatus`
2. **DynamoDB Update**: Set Status, ErrorMessage, and ErrorDetails
3. **Retry Logic**: Handle DynamoDB throttling
4. **Termination**: End execution with `End: true`

### Error State Mapping

| Original State | Error Handler State | Error Status | Catch Conditions |
|---|---|---|---|
| GetFeatureList | UpdateFeatureListFailedStatus | Feature_List_Retrieval_Failed | States.TaskFailed, States.Runtime |
| RunRawData | UpdateRawDataFailedStatus | Raw_Data_Processing_Failed | States.TaskFailed, States.Runtime |
| CreateModelingData | UpdateModelingDataFailedStatus | Modeling_Data_Creation_Failed | States.TaskFailed, States.Runtime |
| PutRecord | UpdateInitialRecordFailedStatus | Initial_Record_Creation_Failed | States.TaskFailed, DynamoDB.* |
| UpdateCreateModelingDataStatus | UpdateStatusUpdateFailedStatus | Status_Update_Failed | States.TaskFailed, DynamoDB.* |
| UpdateJobStartedStatus | UpdateJobStatusFailedStatus | Job_Status_Update_Failed | States.TaskFailed, DynamoDB.* |

## Implementation Details

### 1. Lambda Invocation Error Handling
For Lambda states (`GetFeatureList`, `RunRawData`, `CreateModelingData`):
```yaml
Catch:
  - ErrorEquals:
      - States.TaskFailed
      - States.Runtime
      - States.ExecutionLimitExceeded
    Next: Update{Operation}FailedStatus
```

### 2. DynamoDB Operation Error Handling
For DynamoDB states (`PutRecord`, `UpdateCreateModelingDataStatus`, `UpdateJobStartedStatus`):
```yaml
Catch:
  - ErrorEquals:
      - States.TaskFailed
      - DynamoDB.ValidationException
      - DynamoDB.ResourceNotFoundException
      - DynamoDB.ItemCollectionSizeLimitExceededException
    Next: Update{Operation}FailedStatus
```

### 3. Error Message Extraction Strategy
Each error handler will extract error information using JSONata:
- **Primary**: `$states.input.Error` (Step Functions error message)
- **Secondary**: `$states.input.Cause` (Detailed error cause)
- **Fallback**: Descriptive default message

### 4. Error Details Strategy
Store complete error context as stringified JSON:
```yaml
":errorDetails":
  S: "{% $string($states.input) %}"
```

## Error Handler State Definitions

### UpdateFeatureListFailedStatus
```yaml
UpdateFeatureListFailedStatus:
  Type: Task
  Resource: arn:aws:states:::dynamodb:updateItem
  Arguments:
    TableName: ProsperModels
    Key:
      Id:
        S: "{% $id %}"
    UpdateExpression: "SET #status = :status, #errorMessage = :errorMessage, #errorDetails = :errorDetails"
    ExpressionAttributeNames:
      "#status": Status
      "#errorMessage": ErrorMessage
      "#errorDetails": ErrorDetails
    ExpressionAttributeValues:
      ":status":
        S: Feature_List_Retrieval_Failed
      ":errorMessage":
        S: "{% $states.input.Error ? $states.input.Error : 'Failed to retrieve feature list from DynamoDB' %}"
      ":errorDetails":
        S: "{% $string($states.input) %}"
  Retry:
    - ErrorEquals:
        - DynamoDB.ProvisionedThroughputExceededException
        - DynamoDB.ThrottlingException
      IntervalSeconds: 2
      MaxAttempts: 3
      BackoffRate: 2.0
  End: true
```

### UpdateRawDataFailedStatus
```yaml
UpdateRawDataFailedStatus:
  Type: Task
  Resource: arn:aws:states:::dynamodb:updateItem
  Arguments:
    TableName: ProsperModels
    Key:
      Id:
        S: "{% $id %}"
    UpdateExpression: "SET #status = :status, #errorMessage = :errorMessage, #errorDetails = :errorDetails"
    ExpressionAttributeNames:
      "#status": Status
      "#errorMessage": ErrorMessage
      "#errorDetails": ErrorDetails
    ExpressionAttributeValues:
      ":status":
        S: Raw_Data_Processing_Failed
      ":errorMessage":
        S: "{% $states.input.Error ? $states.input.Error : 'Failed to process raw data from external Lambda function' %}"
      ":errorDetails":
        S: "{% $string($states.input) %}"
  Retry:
    - ErrorEquals:
        - DynamoDB.ProvisionedThroughputExceededException
        - DynamoDB.ThrottlingException
      IntervalSeconds: 2
      MaxAttempts: 3
      BackoffRate: 2.0
  End: true
```

### UpdateModelingDataFailedStatus
```yaml
UpdateModelingDataFailedStatus:
  Type: Task
  Resource: arn:aws:states:::dynamodb:updateItem
  Arguments:
    TableName: ProsperModels
    Key:
      Id:
        S: "{% $id %}"
    UpdateExpression: "SET #status = :status, #errorMessage = :errorMessage, #errorDetails = :errorDetails"
    ExpressionAttributeNames:
      "#status": Status
      "#errorMessage": ErrorMessage
      "#errorDetails": ErrorDetails
    ExpressionAttributeValues:
      ":status":
        S: Modeling_Data_Creation_Failed
      ":errorMessage":
        S: "{% $states.input.Error ? $states.input.Error : 'Failed to create modeling data files' %}"
      ":errorDetails":
        S: "{% $string($states.input) %}"
  Retry:
    - ErrorEquals:
        - DynamoDB.ProvisionedThroughputExceededException
        - DynamoDB.ThrottlingException
      IntervalSeconds: 2
      MaxAttempts: 3
      BackoffRate: 2.0
  End: true
```

### UpdateInitialRecordFailedStatus
```yaml
UpdateInitialRecordFailedStatus:
  Type: Task
  Resource: arn:aws:states:::dynamodb:updateItem
  Arguments:
    TableName: ProsperModels
    Key:
      Id:
        S: "{% $id %}"
    UpdateExpression: "SET #status = :status, #errorMessage = :errorMessage, #errorDetails = :errorDetails"
    ExpressionAttributeNames:
      "#status": Status
      "#errorMessage": ErrorMessage
      "#errorDetails": ErrorDetails
    ExpressionAttributeValues:
      ":status":
        S: Initial_Record_Creation_Failed
      ":errorMessage":
        S: "{% $states.input.Error ? $states.input.Error : 'Failed to create initial record in DynamoDB' %}"
      ":errorDetails":
        S: "{% $string($states.input) %}"
  Retry:
    - ErrorEquals:
        - DynamoDB.ProvisionedThroughputExceededException
        - DynamoDB.ThrottlingException
      IntervalSeconds: 2
      MaxAttempts: 3
      BackoffRate: 2.0
  End: true
```

### UpdateStatusUpdateFailedStatus
```yaml
UpdateStatusUpdateFailedStatus:
  Type: Task
  Resource: arn:aws:states:::dynamodb:updateItem
  Arguments:
    TableName: ProsperModels
    Key:
      Id:
        S: "{% $id %}"
    UpdateExpression: "SET #status = :status, #errorMessage = :errorMessage, #errorDetails = :errorDetails"
    ExpressionAttributeNames:
      "#status": Status
      "#errorMessage": ErrorMessage
      "#errorDetails": ErrorDetails
    ExpressionAttributeValues:
      ":status":
        S: Status_Update_Failed
      ":errorMessage":
        S: "{% $states.input.Error ? $states.input.Error : 'Failed to update modeling data status in DynamoDB' %}"
      ":errorDetails":
        S: "{% $string($states.input) %}"
  Retry:
    - ErrorEquals:
        - DynamoDB.ProvisionedThroughputExceededException
        - DynamoDB.ThrottlingException
      IntervalSeconds: 2
      MaxAttempts: 3
      BackoffRate: 2.0
  End: true
```

### UpdateJobStatusFailedStatus
```yaml
UpdateJobStatusFailedStatus:
  Type: Task
  Resource: arn:aws:states:::dynamodb:updateItem
  Arguments:
    TableName: ProsperModels
    Key:
      Id:
        S: "{% $id %}"
    UpdateExpression: "SET #status = :status, #errorMessage = :errorMessage, #errorDetails = :errorDetails"
    ExpressionAttributeNames:
      "#status": Status
      "#errorMessage": ErrorMessage
      "#errorDetails": ErrorDetails
    ExpressionAttributeValues:
      ":status":
        S: Job_Status_Update_Failed
      ":errorMessage":
        S: "{% $states.input.Error ? $states.input.Error : 'Failed to update job started status in DynamoDB' %}"
      ":errorDetails":
        S: "{% $string($states.input) %}"
  Retry:
    - ErrorEquals:
        - DynamoDB.ProvisionedThroughputExceededException
        - DynamoDB.ThrottlingException
      IntervalSeconds: 2
      MaxAttempts: 3
      BackoffRate: 2.0
  End: true
```

## Integration Points

### State Modifications Required
1. **GetFeatureList**: Add Catch block
2. **RunRawData**: Add Catch block  
3. **CreateModelingData**: Add Catch block
4. **PutRecord**: Add Catch block
5. **UpdateCreateModelingDataStatus**: Add Catch block
6. **UpdateJobStartedStatus**: Add Catch block

### Placement in Step Function
All error handler states will be placed at the end of the States section, after the existing error handlers but before the closing brace.

## Testing Strategy
1. **Unit Testing**: Each error handler state can be tested by forcing failures in the corresponding original state
2. **Integration Testing**: Verify error messages and details are properly stored in DynamoDB
3. **End-to-End Testing**: Confirm Step Function execution terminates gracefully on errors

## Monitoring and Observability
- All error states will appear in CloudWatch Step Functions execution history
- DynamoDB records will contain structured error information for debugging
- Error patterns can be monitored through CloudWatch metrics and alarms