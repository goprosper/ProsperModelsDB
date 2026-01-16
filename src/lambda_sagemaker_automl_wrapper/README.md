# Lambda SageMaker AutoML Wrapper

This Lambda function provides a wrapper around the SageMaker CreateAutoMLJob API to support parameters not available through AWS Step Functions' direct SageMaker integration, specifically the `FeatureSpecificationS3Uri` parameter.

## Problem Solved

AWS Step Functions' direct SageMaker integration (`arn:aws:states:::aws-sdk:sagemaker:createAutoMLJob`) doesn't support all parameters available in the SageMaker CreateAutoMLJob API. Specifically, the `FeatureSpecificationS3Uri` parameter, which allows you to specify feature types and selected features for AutoML jobs, is not supported and causes this error:

```
The field "FeatureSpecificationS3Uri" is not supported by Step Functions
```

This Lambda wrapper solves this by providing full SageMaker API access while maintaining compatibility with your existing Step Functions workflow.

## Features

- ✅ **Full SageMaker API Support**: Access to all CreateAutoMLJob parameters including `FeatureSpecificationS3Uri`
- ✅ **Step Functions Compatible**: Same input/output format as the original SageMaker integration
- ✅ **Comprehensive Validation**: Parameter validation and sanitization for security
- ✅ **S3 Integration**: Validates and accesses feature specification files from S3
- ✅ **Error Handling**: Step Functions compatible error formatting
- ✅ **Structured Logging**: CloudWatch integration with sensitive data filtering
- ✅ **Security Focused**: Least-privilege IAM permissions and input sanitization

## Quick Start

### 1. Deploy the Lambda Function

```bash
cd src/lambda_sagemaker_automl_wrapper
./deploy.sh
```

Or manually:

```bash
sam build
sam deploy --guided
```

### 2. Update Your Step Functions Workflow

Replace your current `LaunchAutoMLJob` state:

```json
"LaunchAutoMLJob": {
    "Type": "Task",
    "Resource": "arn:aws:states:::lambda:invoke",
    "Arguments": {
        "FunctionName": "${SageMakerAutoMLWrapperFunctionArn}",
        "Payload": {
            "AutoMLJobName": "{% $jobName %}",
            "InputDataConfig": [...],
            "OutputDataConfig": {...},
            "RoleArn": "${SageMakerExecutionRoleArn}",
            "AutoMLJobConfig": {
                "CompletionCriteria": {...},
                "CandidateGenerationConfig": {
                    "FeatureSpecificationS3Uri": "s3://your-bucket/feature_types.json"
                }
            }
        }
    },
    "Next": "UpdateJobStartedStatus"
}
```

See `step-functions-integration-guide.md` for detailed instructions.

### 3. Create Feature Specification File

Create a JSON file in S3 with your feature specifications:

```json
{
    "FeatureAttributeNames": ["feature1", "feature2", "feature3"],
    "FeatureDataTypes": {
        "feature1": "numeric",
        "feature2": "categorical",
        "feature3": "text"
    }
}
```

## Architecture

```
Step Functions → Lambda Wrapper → SageMaker CreateAutoMLJob API
                      ↓
                 S3 Feature Specs
```

The Lambda function:
1. Validates and sanitizes input parameters
2. Validates S3 feature specification files (if provided)
3. Calls the full SageMaker CreateAutoMLJob API
4. Returns Step Functions compatible response

## File Structure

```
src/lambda_sagemaker_automl_wrapper/
├── lambda_function.py          # Main Lambda handler
├── models.py                   # Data models and validation
├── validation.py               # Parameter validation utilities
├── sagemaker_client.py         # SageMaker API client wrapper
├── s3_handler.py              # S3 feature specification handler
├── response_handler.py         # Step Functions response formatting
├── error_handler.py           # Comprehensive error handling
├── logger.py                  # Structured logging with security filtering
├── template.yaml              # SAM deployment template
├── requirements.txt           # Python dependencies
├── test_basic_functionality.py # Basic functionality tests
├── deploy.sh                  # Deployment script
└── step-functions-integration-guide.md # Integration guide
```

## Configuration

### Environment Variables

- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR) - default: INFO
- `ENVIRONMENT`: Environment name (dev, staging, prod) - default: dev

### IAM Permissions

The Lambda function requires these permissions:
- `sagemaker:CreateAutoMLJob` - Create AutoML jobs
- `sagemaker:DescribeAutoMLJob` - Describe AutoML jobs (for validation)
- `s3:GetObject` - Read feature specification files
- `s3:HeadObject` - Check feature specification file existence
- `logs:*` - CloudWatch logging

## Testing

Run basic functionality tests:

```bash
python test_basic_functionality.py
```

This validates:
- Parameter validation and sanitization
- S3 URI validation
- Response formatting
- Error handling
- Logging setup

## Monitoring

The Lambda function provides structured JSON logging to CloudWatch with:
- Request tracing with correlation IDs
- Parameter validation results
- S3 operation status
- SageMaker API call results
- Error details with sanitized sensitive data

## Security

- **Input Sanitization**: All input parameters are sanitized to prevent injection attacks
- **Sensitive Data Filtering**: Logs automatically filter AWS credentials, account IDs, and other sensitive data
- **Least Privilege IAM**: Function uses minimal required permissions
- **Error Message Security**: Error messages don't expose sensitive information

## Troubleshooting

### Common Issues

1. **"Missing required parameter" errors**: Ensure all required parameters (AutoMLJobName, InputDataConfig, OutputDataConfig, RoleArn) are provided

2. **S3 access errors**: Check that the Lambda function has read permissions to your S3 bucket and the feature specification file exists

3. **SageMaker permission errors**: Ensure the SageMaker execution role has proper permissions for AutoML jobs

4. **Step Functions integration issues**: Verify the Lambda function ARN is correctly referenced in your state machine

### Debugging

Enable debug logging by setting `LOG_LEVEL=DEBUG` environment variable. This provides detailed information about:
- Parameter processing
- S3 operations
- SageMaker API calls
- Error handling

## Support

For issues related to:
- **Lambda function**: Check CloudWatch logs for detailed error information
- **Step Functions integration**: Verify the state machine definition matches the integration guide
- **SageMaker API**: Refer to AWS SageMaker documentation for parameter requirements
- **S3 access**: Check IAM permissions and file existence

## License

This implementation is provided as-is for solving the Step Functions SageMaker integration limitation.