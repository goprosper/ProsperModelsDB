# Step Functions Integration Guide

This guide explains how to update your existing Step Functions workflow to use the Lambda SageMaker AutoML wrapper instead of the direct SageMaker integration.

## Current LaunchAutoMLJob State

Your current `LaunchAutoMLJob` state in `statemachine/prosper-models-workflow.json` looks like this:

```json
"LaunchAutoMLJob": {
    "Type": "Task",
    "Resource": "arn:aws:states:::aws-sdk:sagemaker:createAutoMLJob",
    "Arguments": {
        "AutoMLJobName": "{% $jobName %}",
        "InputDataConfig": [
            {
                "DataSource": {
                    "S3DataSource": {
                        "S3DataType": "S3Prefix",
                        "S3Uri": "{% 's3://prosper-raw-data/' & $requestName & '/modeling_data.csv' %}"
                    }
                },
                "TargetAttributeName": "{% $labelList[0].FeatureName %}"
            }
        ],
        "OutputDataConfig": {
            "S3OutputPath": "{% 's3://prosper-raw-data/' & $requestName & '/automl-output/' %}"
        },
        "AutoMLJobObjective": {
            "MetricName": "F1"
        },
        "ProblemType": "BinaryClassification",
        "RoleArn": "${SageMakerExecutionRoleArn}",
        "AutoMLJobConfig": {
            "CompletionCriteria": "{% $modelTrainingPlan = 'Bronze' ? { 'MaxCandidates': 3, 'MaxRuntimePerTrainingJobInSeconds': 300, 'MaxAutoMLJobRuntimeInSeconds': 1800 } : $modelTrainingPlan = 'Silver' ? { 'MaxCandidates': 20, 'MaxRuntimePerTrainingJobInSeconds': 1200, 'MaxAutoMLJobRuntimeInSeconds': 4800 } : null %}"
        }
    },
    "Catch": [
        {
            "ErrorEquals": [
                "States.TaskFailed",
                "States.ExecutionLimitExceeded",
                "States.Runtime"
            ],
            "Next": "UpdateLaunchFailureStatus"
        }
    ],
    "Next": "UpdateJobStartedStatus"
}
```

## Updated LaunchAutoMLJob State

Replace the above state with this updated version that uses the Lambda wrapper:

```json
"LaunchAutoMLJob": {
    "Type": "Task",
    "Resource": "arn:aws:states:::lambda:invoke",
    "Arguments": {
        "FunctionName": "${SageMakerAutoMLWrapperFunctionArn}",
        "Payload": {
            "AutoMLJobName": "{% $jobName %}",
            "InputDataConfig": [
                {
                    "DataSource": {
                        "S3DataSource": {
                            "S3DataType": "S3Prefix",
                            "S3Uri": "{% 's3://prosper-raw-data/' & $requestName & '/modeling_data.csv' %}"
                        }
                    },
                    "TargetAttributeName": "{% $labelList[0].FeatureName %}"
                }
            ],
            "OutputDataConfig": {
                "S3OutputPath": "{% 's3://prosper-raw-data/' & $requestName & '/automl-output/' %}"
            },
            "AutoMLJobObjective": {
                "MetricName": "F1"
            },
            "ProblemType": "BinaryClassification",
            "RoleArn": "${SageMakerExecutionRoleArn}",
            "AutoMLJobConfig": {
                "CompletionCriteria": "{% $modelTrainingPlan = 'Bronze' ? { 'MaxCandidates': 3, 'MaxRuntimePerTrainingJobInSeconds': 300, 'MaxAutoMLJobRuntimeInSeconds': 1800 } : $modelTrainingPlan = 'Silver' ? { 'MaxCandidates': 20, 'MaxRuntimePerTrainingJobInSeconds': 1200, 'MaxAutoMLJobRuntimeInSeconds': 4800 } : null %}",
                "CandidateGenerationConfig": {
                    "FeatureSpecificationS3Uri": "{% 's3://prosper-raw-data/' & $requestName & '/feature_types.json' %}"
                }
            }
        }
    },
    "Retry": [
        {
            "ErrorEquals": [
                "Lambda.ServiceException",
                "Lambda.AWSLambdaException",
                "Lambda.SdkClientException"
            ],
            "IntervalSeconds": 2,
            "MaxAttempts": 3,
            "BackoffRate": 2.0
        }
    ],
    "Catch": [
        {
            "ErrorEquals": [
                "States.TaskFailed",
                "States.ExecutionLimitExceeded",
                "States.Runtime",
                "SageMaker.ValidationException",
                "SageMaker.AccessDeniedException",
                "SageMaker.ThrottlingException",
                "S3.NoSuchKey",
                "S3.AccessDenied"
            ],
            "Next": "UpdateLaunchFailureStatus"
        }
    ],
    "Next": "UpdateJobStartedStatus"
}
```

## Key Changes

1. **Resource**: Changed from `arn:aws:states:::aws-sdk:sagemaker:createAutoMLJob` to `arn:aws:states:::lambda:invoke`

2. **Arguments Structure**: Wrapped the original arguments in a `Payload` object and added `FunctionName`

3. **FeatureSpecificationS3Uri**: Added the new parameter that was causing the original error:
   ```json
   "CandidateGenerationConfig": {
       "FeatureSpecificationS3Uri": "{% 's3://prosper-raw-data/' & $requestName & '/feature_types.json' %}"
   }
   ```

4. **Error Handling**: Added Lambda-specific retry logic and additional error types for better error handling

5. **Response Format**: The Lambda function returns the same format as the original SageMaker integration, so no changes needed to subsequent states

## CloudFormation Template Updates

Add this parameter to your main CloudFormation template:

```yaml
Parameters:
  # ... existing parameters ...
  
  SageMakerAutoMLWrapperFunctionArn:
    Type: String
    Description: ARN of the SageMaker AutoML Wrapper Lambda function
```

Then reference it in your Step Functions state machine definition:

```yaml
Resources:
  # ... existing resources ...
  
  ProsperModelsStateMachine:
    Type: AWS::StepFunctions::StateMachine
    Properties:
      # ... existing properties ...
      DefinitionSubstitutions:
        # ... existing substitutions ...
        SageMakerAutoMLWrapperFunctionArn: !Ref SageMakerAutoMLWrapperFunctionArn
```

## Deployment Steps

1. **Deploy the Lambda function** using the SAM template:
   ```bash
   cd src/lambda_sagemaker_automl_wrapper
   sam build
   sam deploy --guided
   ```

2. **Update your main CloudFormation template** with the parameter and reference

3. **Update the Step Functions definition** with the new state configuration

4. **Deploy the updated CloudFormation stack**

## Testing

After deployment, test the integration by:

1. Running your Step Functions workflow with the same input as before
2. Verifying that the AutoML job is created successfully
3. Checking that the `FeatureSpecificationS3Uri` parameter is now accepted
4. Confirming that the workflow continues to the next state as expected

## Rollback Plan

If issues occur, you can quickly rollback by:

1. Reverting the Step Functions state definition to use the original SageMaker integration
2. Removing the `FeatureSpecificationS3Uri` parameter temporarily
3. Redeploying the CloudFormation stack

The Lambda function can remain deployed as it doesn't affect the original workflow when not used.