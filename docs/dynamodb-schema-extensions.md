# DynamoDB Schema Extensions for AutoML Integration

## Overview

This document describes the schema extensions made to the ProsperModels DynamoDB table to support SageMaker AutoML integration. These extensions enable tracking of AutoML job status, error information, and job references.

## New Attributes

### 1. Status (String)

The `Status` attribute tracks the current state of the AutoML workflow for a given record.

**Valid Values:**
- `AutoML_Job_Started` - AutoML job has been successfully launched
- `AutoML_Job_Running` - AutoML job is currently in progress
- `AutoML_Job_Completed` - AutoML job completed successfully
- `AutoML_Job_Failed` - AutoML job failed during execution
- `AutoML_Job_Launch_Failed` - Failed to launch the AutoML job

**Requirements Addressed:** 1.3, 2.5, 3.1, 3.2

**Usage:**
```python
from automl_constants import AutoMLStatus

# Set status when job starts
status = AutoMLStatus.JOB_STARTED

# Validate status
from automl_constants import validate_automl_status
is_valid = validate_automl_status(status)
```

### 2. ErrorMessage (String, Optional)

The `ErrorMessage` attribute stores detailed error information when an AutoML job fails or encounters issues.

**When Populated:**
- Job launch failures (e.g., invalid S3 paths, permission issues)
- Job execution failures (e.g., insufficient data, training errors)
- Workflow errors (e.g., timeout conditions, service limits)

**Requirements Addressed:** 1.5, 3.3

**Usage:**
```python
from automl_dynamodb_utils import update_job_launch_failed_status

# Update status with error message
update_job_launch_failed_status(
    table_name='ProsperModels',
    record_id='record-123',
    error_message='SageMaker service limit exceeded'
)
```

### 3. AutoMLJobName (String, Optional)

The `AutoMLJobName` attribute stores the SageMaker AutoML job name for traceability and monitoring.

**Format:** `prosper-automl-{requestName}-{timestamp}`

**Characteristics:**
- Unique identifier for each AutoML job
- Contains the original request name for traceability
- Complies with SageMaker naming requirements (1-63 characters, alphanumeric and hyphens only)

**Requirements Addressed:** 1.4

**Usage:**
```python
from automl_job_utils import generate_automl_job_name

# Generate a valid job name
job_name = generate_automl_job_name(
    request_name='customer-analysis',
    timestamp='2023-12-21T10:30:00Z'
)
# Result: 'prosper-automl-customer-analysis-2023-12-21T10-30-00Z'
```

## Implementation Details

### DynamoDB Table Configuration

The ProsperModels table uses DynamoDB's schemaless design for non-key attributes. The new attributes are added dynamically when records are created or updated:

```yaml
ProsperModelsTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: ProsperModels
    BillingMode: PAY_PER_REQUEST
    AttributeDefinitions:
      - AttributeName: Id
        AttributeType: S
    KeySchema:
      - AttributeName: Id
        KeyType: HASH
```

### Update Operations

Status updates preserve all existing record attributes using DynamoDB's `UpdateExpression`:

```python
UpdateExpression: "SET #status = :status, #autoMLJobName = :jobName, #errorMessage = :error"
ExpressionAttributeNames: {
    "#status": "Status",
    "#autoMLJobName": "AutoMLJobName",
    "#errorMessage": "ErrorMessage"
}
```

### Query Operations

The ProsperModelsLambda.py function includes all new attributes in its projection expression:

```python
expression_attr_names = {
    "#Status": "Status",
    "#ErrorMessage": "ErrorMessage",
    "#AutoMLJobName": "AutoMLJobName",
    # ... other attributes
}
```

## Utility Modules

### automl_constants.py

Defines constants for AutoML status values and attribute names:
- `AutoMLStatus` class - Status value constants
- `DynamoDBAttributes` class - Attribute name constants
- `SageMakerJobStatus` class - SageMaker API status values
- Helper functions for validation and mapping

### automl_dynamodb_utils.py

Provides functions for DynamoDB operations:
- `update_automl_status()` - Generic status update function
- `update_job_started_status()` - Update when job starts
- `update_job_running_status()` - Update when job is running
- `update_job_completed_status()` - Update when job completes
- `update_job_failed_status()` - Update when job fails
- `update_job_launch_failed_status()` - Update when launch fails
- `get_record_status()` - Retrieve current status

### automl_job_utils.py

Provides functions for AutoML job management:
- `generate_automl_job_name()` - Generate valid job names
- `validate_job_name()` - Validate job name format
- `construct_input_s3_path()` - Build S3 input paths
- `construct_output_s3_path()` - Build S3 output paths
- `create_automl_job_config()` - Create job configuration

## Testing

Test files are provided to verify the schema extensions:

- `test_error_message_support.py` - Tests ErrorMessage attribute
- `test_automl_job_name_support.py` - Tests AutoMLJobName attribute

Run tests with:
```bash
python src/test_error_message_support.py
python src/test_automl_job_name_support.py
```

## Migration Notes

### Backward Compatibility

The schema extensions are fully backward compatible:
- Existing records without the new attributes will continue to work
- New attributes are optional and only populated when AutoML jobs are involved
- Existing queries and operations are unaffected

### No Migration Required

Since DynamoDB is schemaless for non-key attributes, no data migration is required. The new attributes will be added to records as they are updated through the AutoML workflow.

## Status Transition Diagram

```
[Initial State]
       |
       v
AutoML_Job_Started -----> AutoML_Job_Launch_Failed (if launch fails)
       |
       v
AutoML_Job_Running
       |
       +-----> AutoML_Job_Completed (if successful)
       |
       +-----> AutoML_Job_Failed (if execution fails)
```

## Example Record

```json
{
  "Id": "abc-123-def-456",
  "UserId": "user-789",
  "UserName": "John Doe",
  "SubmissionDateTime": "2023-12-21T10:30:00Z",
  "ShortDescription": "Customer Analysis Model",
  "StudyName": "customer-study",
  "FeatureListName": "customer-features",
  "Label": 42,
  "Status": "AutoML_Job_Completed",
  "AutoMLJobName": "prosper-automl-Customer-Analysis-Model-2023-12-21T10-30-00Z-abc-123-def-456",
  "ErrorMessage": null
}
```

## References

- Requirements: `.kiro/specs/sagemaker-automl-integration/requirements.md`
- Design: `.kiro/specs/sagemaker-automl-integration/design.md`
- Tasks: `.kiro/specs/sagemaker-automl-integration/tasks.md`