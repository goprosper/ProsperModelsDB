# AutoML Job Field Extraction Enhancement

## Overview

Enhanced the Step Functions workflow to extract and save additional fields from AutoML job descriptions and best candidate job descriptions to DynamoDB for better visibility and analysis.

## Fields Added

### From AutoML Job Description
When the AutoML job completes, the following fields are extracted and saved:

1. **BestCandidateJobName** (String)
   - Source: `BestCandidate.CandidateName`
   - Description: Name of the best performing training job
   - Example: `"prosper-abc123def-001-training"`

2. **ObjectiveMetric** (String)
   - Source: `ResolvedAttributes.MetricName`
   - Description: Optimization metric used for the AutoML job
   - Example: `"F1"`, `"Accuracy"`, `"AUC"`

3. **CompletionCriteria** (String - JSON)
   - Source: `ResolvedAttributes.CompletionCriteria`
   - Description: Criteria used to determine job completion
   - Example: `{"MaxCandidates": 20, "MaxRuntimePerTrainingJobInSeconds": 1200}`

4. **BestCandidateMetrics** (String - JSON)
   - Source: `BestCandidate.CandidateProperties.CandidateMetrics`
   - Description: Performance metrics of the best candidate
   - Example: `[{"MetricName": "F1", "Value": 0.8542, "Set": "Validation"}]`

### From Best Candidate Job Description
When the best candidate training job description is retrieved, the following fields are extracted:

1. **BestCandidateTrainingImage** (String)
   - Source: `AlgorithmSpecification.TrainingImage`
   - Description: Docker image used for training the best candidate
   - Example: `"382416733822.dkr.ecr.us-east-1.amazonaws.com/xgboost:1.5-1"`

2. **BestCandidateHyperParameters** (String - JSON)
   - Source: `HyperParameters`
   - Description: Hyperparameters used for the best candidate training
   - Example: `{"max_depth": "6", "eta": "0.2", "objective": "binary:logistic"}`

3. **BestCandidateTrainingInstance** (String)
   - Source: `ResourceConfig.InstanceType`
   - Description: Instance type used for training the best candidate
   - Example: `"ml.m5.2xlarge"`

## Implementation Details

### Step Functions Workflow Changes

1. **CaptureAutoMLJobDescription State**
   - Added extraction of 4 fields from the AutoML job description
   - Uses JSONata expressions to safely extract nested fields
   - Handles missing fields gracefully (returns null)

2. **UpdateJobCompletedStatusWithJobDescription State**
   - Added extraction and saving of 3 fields from best candidate job description
   - Updates DynamoDB with extracted fields immediately when available
   - Uses fallback values ("Not available") for missing fields

3. **UpdateJobCompletedStatusWithoutJobDescription State**
   - Updated to save placeholder values when job description is unavailable
   - Maintains consistency in DynamoDB schema

4. **UpdateWorkflowCompletedStatus State**
   - Updated to save all extracted AutoML job fields to DynamoDB
   - Final step that consolidates all extracted information

### Error Handling

- **Missing Fields**: All extractions use safe navigation (e.g., `$states.input.BestCandidate ? $states.input.BestCandidate.CandidateName : null`)
- **Fallback Values**: When fields are missing, appropriate fallback values are used:
  - `null` during extraction (converted to "Not available" in DynamoDB)
  - `"Not available"` for string fields
  - `"{}"` for JSON fields when source object is missing

### DynamoDB Schema Impact

The following new fields will be added to the ProsperModels table:

```
BestCandidateJobName: String
ObjectiveMetric: String  
CompletionCriteria: String (JSON)
BestCandidateMetrics: String (JSON)
BestCandidateTrainingImage: String
BestCandidateHyperParameters: String (JSON)
BestCandidateTrainingInstance: String
```

## Testing

Created comprehensive test script (`test-automl-field-extraction.py`) that validates:

- ✅ Correct extraction of all fields from sample AutoML job descriptions
- ✅ Correct extraction of all fields from sample training job descriptions  
- ✅ Proper handling of missing fields (edge cases)
- ✅ JSON serialization of complex objects

## Benefits

1. **Enhanced Visibility**: Key AutoML job details are now easily accessible in DynamoDB
2. **Better Analysis**: Performance metrics and hyperparameters available for analysis
3. **Debugging Support**: Training image and instance information helps with troubleshooting
4. **Reporting**: Objective metrics and completion criteria support better reporting

## Deployment Status

- ✅ Step Functions workflow updated
- ✅ JSON syntax validated
- ✅ Field extraction logic tested
- ⏳ Ready for deployment (not deployed yet per user request)

## Example Data

After deployment, completed AutoML jobs will have records like:

```json
{
  "Id": "abc-123-def",
  "Status": "Completed",
  "BestCandidateJobName": "prosper-abc123def-001-training",
  "ObjectiveMetric": "F1",
  "CompletionCriteria": "{\"MaxCandidates\": 20, \"MaxRuntimePerTrainingJobInSeconds\": 1200}",
  "BestCandidateMetrics": "[{\"MetricName\": \"F1\", \"Value\": 0.8542}]",
  "BestCandidateTrainingImage": "382416733822.dkr.ecr.us-east-1.amazonaws.com/xgboost:1.5-1",
  "BestCandidateHyperParameters": "{\"max_depth\": \"6\", \"eta\": \"0.2\"}",
  "BestCandidateTrainingInstance": "ml.m5.2xlarge"
}
```