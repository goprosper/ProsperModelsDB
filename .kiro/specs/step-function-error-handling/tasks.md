# Step Function Comprehensive Error Handling - Implementation Tasks

## Task Overview
Add comprehensive error handling to all Step Function states that currently lack proper error handling, following the established `UpdateDataValidationFailedStatus` pattern.

## Implementation Tasks

### Task 1: Add Error Handler States
**Requirement**: Create 6 new error handler states following the established pattern
**Files**: `template.yaml`

Add the following error handler states to the Step Function definition (place after existing error handlers):

1. **UpdateFeatureListFailedStatus** - Handle GetFeatureList failures
2. **UpdateRawDataFailedStatus** - Handle RunRawData failures  
3. **UpdateModelingDataFailedStatus** - Handle CreateModelingData failures
4. **UpdateInitialRecordFailedStatus** - Handle PutRecord failures
5. **UpdateStatusUpdateFailedStatus** - Handle UpdateCreateModelingDataStatus failures
6. **UpdateJobStatusFailedStatus** - Handle UpdateJobStartedStatus failures

Each state should:
- Update DynamoDB with appropriate error status
- Extract error message from `$states.input.Error` with fallback
- Store error details as stringified input
- Include retry logic for DynamoDB throttling
- End execution with `End: true`

### Task 2: Add Catch Blocks to Lambda States
**Requirement**: Add error handling to Lambda invocation states
**Files**: `template.yaml`

#### 2.1 GetFeatureList State
Add Catch block:
```yaml
Catch:
  - ErrorEquals:
      - States.TaskFailed
      - States.Runtime
      - States.ExecutionLimitExceeded
    Next: UpdateFeatureListFailedStatus
```

#### 2.2 RunRawData State  
Add Catch block:
```yaml
Catch:
  - ErrorEquals:
      - States.TaskFailed
      - States.Runtime
      - States.ExecutionLimitExceeded
    Next: UpdateRawDataFailedStatus
```

#### 2.3 CreateModelingData State
Add Catch block:
```yaml
Catch:
  - ErrorEquals:
      - States.TaskFailed
      - States.Runtime
      - States.ExecutionLimitExceeded
    Next: UpdateModelingDataFailedStatus
```

### Task 3: Add Catch Blocks to DynamoDB States
**Requirement**: Add error handling to DynamoDB operation states
**Files**: `template.yaml`

#### 3.1 PutRecord State
Add Catch block:
```yaml
Catch:
  - ErrorEquals:
      - States.TaskFailed
      - DynamoDB.ValidationException
      - DynamoDB.ResourceNotFoundException
      - DynamoDB.ItemCollectionSizeLimitExceededException
    Next: UpdateInitialRecordFailedStatus
```

#### 3.2 UpdateCreateModelingDataStatus State
Add Catch block (keep existing Retry):
```yaml
Catch:
  - ErrorEquals:
      - States.TaskFailed
      - DynamoDB.ValidationException
      - DynamoDB.ResourceNotFoundException
    Next: UpdateStatusUpdateFailedStatus
```

#### 3.3 UpdateJobStartedStatus State
Add Catch block (keep existing Retry):
```yaml
Catch:
  - ErrorEquals:
      - States.TaskFailed
      - DynamoDB.ValidationException
      - DynamoDB.ResourceNotFoundException
    Next: UpdateJobStatusFailedStatus
```

### Task 4: Validate Template Syntax
**Requirement**: Ensure YAML syntax and Step Function definition are valid
**Files**: `template.yaml`

1. Validate YAML syntax
2. Check JSONata expressions in error handlers
3. Verify state names and transitions
4. Confirm DynamoDB table references

### Task 5: Test Error Handling
**Requirement**: Verify error handling works correctly
**Files**: N/A (testing task)

1. Deploy updated Step Function
2. Test each error scenario:
   - Force GetFeatureList failure (invalid study name)
   - Force RunRawData failure (invalid parameters)
   - Force CreateModelingData failure (missing S3 permissions)
   - Force PutRecord failure (invalid data)
   - Force status update failures (invalid table)
3. Verify DynamoDB records contain proper error status and messages

### Task 6: Update Documentation
**Requirement**: Document new error handling capabilities
**Files**: `README.md` or relevant documentation

1. Document new error status values
2. Explain error handling flow
3. Provide troubleshooting guide for each error type

## Implementation Order
1. **Task 1**: Add all error handler states first
2. **Task 2**: Add Catch blocks to Lambda states
3. **Task 3**: Add Catch blocks to DynamoDB states  
4. **Task 4**: Validate template syntax
5. **Task 5**: Deploy and test
6. **Task 6**: Update documentation

## Error Status Reference
| State | Error Status | Description |
|---|---|---|
| GetFeatureList | Feature_List_Retrieval_Failed | Failed to retrieve feature list from DynamoDB |
| RunRawData | Raw_Data_Processing_Failed | Failed to process raw data from external Lambda |
| CreateModelingData | Modeling_Data_Creation_Failed | Failed to create modeling data files |
| PutRecord | Initial_Record_Creation_Failed | Failed to create initial record in DynamoDB |
| UpdateCreateModelingDataStatus | Status_Update_Failed | Failed to update modeling data status |
| UpdateJobStartedStatus | Job_Status_Update_Failed | Failed to update job started status |

## Success Criteria
- [x] All 6 error handler states added to Step Function
- [x] All 6 original states have appropriate Catch blocks
- [x] All AutoML error handlers properly configured
- [x] Template validates successfully with `sam validate`
- [x] Step Function deploys without errors
- [x] Error scenarios update DynamoDB with correct status and messages
- [x] Step Function execution terminates gracefully on all error types
- [x] Documentation updated with new error handling information

## Notes
- Keep existing Retry blocks on DynamoDB states
- Follow exact pattern from UpdateDataValidationFailedStatus
- Use consistent error status naming convention
- Ensure all error handlers reference correct table name via substitution