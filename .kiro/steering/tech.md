---
inclusion: always
---

# Technology Stack

## Build System

**AWS SAM (Serverless Application Model)** - Infrastructure as Code and deployment framework

## Core Technologies

- **Runtime**: Python 3.13
- **Cloud Platform**: AWS
- **Infrastructure**: CloudFormation via SAM templates

## AWS Services

- **Lambda**: Serverless compute (Python 3.13 runtime)
- **Step Functions**: Workflow orchestration with JSONata query language
- **API Gateway V2**: HTTP APIs with JWT authorization
- **DynamoDB**: NoSQL database for feature lists and model requests
- **SageMaker**: AutoML job execution
- **S3**: Object storage for data files
- **Cognito**: User authentication and JWT token management
- **CloudWatch**: Logging and monitoring

## Python Libraries

### Data Processing
- `pandas==2.3.3` - Data manipulation and analysis
- `numpy==2.3.5` - Numerical computing
- `s3fs==2025.10.0` - S3 filesystem interface
- `fsspec==2025.10.0` - Filesystem abstraction

### AWS SDK
- `boto3==1.41.5` - AWS SDK for Python
- `botocore==1.41.5` - Low-level AWS service access
- `aiobotocore==2.26.0` - Async AWS SDK

### Async/HTTP
- `aiohttp==3.13.2` - Async HTTP client/server
- `aioitertools==0.13.0` - Async itertools

## Lambda Layers

- **AWS SDK Pandas Layer**: `arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python313:5`
  - Used by CreateModelingDataFunction for pandas operations
  - Reduces deployment package size

## Common Commands

### Build
```bash
sam build --use-container
```

### Deploy
```bash
# Guided deployment (first time)
sam deploy --guided

# Subsequent deployments
sam deploy
```

### Local Testing
```bash
# Invoke function locally
sam local invoke <FunctionName> --event events/event.json

# Start local API
sam local start-api
```

### Testing
```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Run unit tests
python -m pytest tests/unit -v

# Run integration tests (requires deployed stack)
AWS_SAM_STACK_NAME="ProsperModelsDB" python -m pytest tests/integration -v
```

### Logs
```bash
sam logs -n <FunctionName> --stack-name "ProsperModelsDB" --tail
```

### Cleanup
```bash
sam delete --stack-name "ProsperModelsDB"
```

## Configuration Files

- `template.yaml` - Main SAM template defining all AWS resources
- `samconfig.toml` - SAM CLI configuration with deployment parameters
- `statemachine/prosper-models-workflow.json` - Step Functions state machine definition

## Environment Variables

Lambda functions use environment variables for configuration:
- `LOG_LEVEL` - Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `TABLE_NAME` - DynamoDB table name
- `ENVIRONMENT` - Deployment environment identifier
- `PYTHONPATH` - Python module search path (for layers)

## IAM Permissions

Functions follow least-privilege principle with specific policies:
- DynamoDB read/write policies
- S3 read/write policies for specific buckets
- SageMaker job creation and monitoring
- Lambda invocation permissions
- CloudWatch logging permissions
