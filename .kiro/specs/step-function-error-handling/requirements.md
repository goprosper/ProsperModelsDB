# Step Function Comprehensive Error Handling - Requirements

## User Story
As a system administrator, I want comprehensive error handling for all Step Function states so that when any step fails, the system updates DynamoDB with appropriate error status and messages, ensuring users can understand what went wrong and the system maintains data consistency.

## Current State Analysis
The Step Function currently has some error handling:
- ✅ `UpdateDataValidationFailedStatus` - Complete error handling pattern
- ✅ `LaunchAutoMLJob` - Has Catch block pointing to `UpdateLaunchFailureStatus`
- ✅ `PollAutoMLJob` - Has Catch block pointing to `UpdateMonitoringFailedStatus`
- ✅ Most DynamoDB update states have Retry blocks for throttling
- ❌ Many states lack comprehensive error handling

## States Needing Error Handling

### Lambda Invocation States
1. **GetFeatureList** - No error handling
   - Can fail due to: DynamoDB read errors, Lambda timeout, invalid study/feature names
   - Should catch and update status to "Feature_List_Retrieval_Failed"

2. **RunRawData** - No error handling  
   - Can fail due to: External Lambda errors, S3 access issues, invalid parameters
   - Should catch and update status to "Raw_Data_Processing_Failed"

3. **CreateModelingData** - No error handling
   - Can fail due to: S3 access issues, data processing errors, Lambda timeout
   - Should catch and update status to "Modeling_Data_Creation_Failed"

### DynamoDB States
4. **PutRecord** - No error handling
   - Can fail due to: DynamoDB write errors, validation errors, throttling
   - Should catch and update status to "Initial_Record_Creation_Failed"

5. **UpdateCreateModelingDataStatus** - Has Retry but no Catch
   - Can fail due to: DynamoDB errors, item not found
   - Should catch and update status to "Status_Update_Failed"

6. **UpdateJobStartedStatus** - Has Retry but no Catch
   - Can fail due to: DynamoDB errors, item not found  
   - Should catch and update status to "Job_Status_Update_Failed"

## Error Handling Pattern
Follow the `UpdateDataValidationFailedStatus` pattern:
```yaml
UpdateXxxFailedStatus:
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
        S: "{% 'Specific_Error_Status' %}"
      ":errorMessage":
        S: "{% $states.input.Error ? $states.input.Error : 'Default error message' %}"
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

## Acceptance Criteria
1. All Lambda invocation states have Catch blocks pointing to appropriate error handling states
2. All DynamoDB states without Catch blocks get Catch blocks pointing to appropriate error handling states
3. Each error handling state follows the established pattern with:
   - Appropriate error status name
   - Error message extraction from input
   - Error details as stringified input
   - Retry logic for DynamoDB throttling
   - End: true to terminate execution
4. Error status names are consistent and descriptive
5. All error handling states update the same DynamoDB record using the `$id` variable

## Error Status Names
- `Feature_List_Retrieval_Failed`
- `Raw_Data_Processing_Failed` 
- `Modeling_Data_Creation_Failed`
- `Initial_Record_Creation_Failed`
- `Status_Update_Failed`
- `Job_Status_Update_Failed`

## Success Criteria
- Step Function execution stops gracefully on any error
- DynamoDB always contains accurate error status and messages
- Users can understand what went wrong from the error messages
- No unhandled exceptions cause Step Function to fail without status updates