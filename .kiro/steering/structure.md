---
inclusion: always
---

# Project Structure

## Root Directory

```
├── template.yaml              # Main SAM template (all AWS resources)
├── samconfig.toml            # SAM deployment configuration
├── README.md                 # Project documentation
└── .gitignore               # Git ignore patterns
```

## Source Code Organization

### `/src/` - Shared utilities and heavy dependencies
- `automl_constants.py` - Constants for AutoML configuration
- `automl_dynamodb_utils.py` - DynamoDB helper functions
- `automl_job_utils.py` - AutoML job utilities
- `CreateModelingData.py` - Data processing logic
- `requirements.txt` - Full dependency list (heavy)
- `test_*.py` - Test files for specific functionality

### `/src-minimal/` - Lightweight Lambda functions
Minimal dependencies (boto3 from Lambda runtime):
- `CreateModelingData.py` - Modeling data generation
- `CalculateJobCostLambda.py` - Cost calculation for AutoML jobs
- `ProsperModelsLambda.py` - Model requests API handler
- `FeatureListsLambda.py` - Feature lists API handler
- `GetFeatureList.py` - Feature list retrieval
- `data_validation.py` - Input validation utilities
- `error_response.py` - Error response formatting
- `metadata_calculator.py` - Metadata computation
- `feature_types_generator.py` - Feature type specification generation
- `requirements.txt` - Minimal dependencies (empty, uses Lambda runtime)

### `/src/lambda_sagemaker_automl_wrapper/` - SageMaker AutoML wrapper
Standalone Lambda function with its own SAM template:
- `lambda_function.py` - Main handler
- `models.py` - Data models and validation schemas
- `validation.py` - Parameter validation
- `sagemaker_client.py` - SageMaker API client
- `s3_handler.py` - S3 operations for feature specs
- `response_handler.py` - Response formatting
- `error_handler.py` - Error handling
- `logger.py` - Structured logging
- `template.yaml` - Standalone SAM template
- `requirements.txt` - Function dependencies
- `deploy.sh` - Deployment script
- `test_basic_functionality.py` - Unit tests
- `*.md` - Documentation files

## Infrastructure

### `/statemachine/` - Step Functions definitions
- `prosper-models-workflow.json` - Main workflow state machine (JSONata syntax)

### `/layers/` - Lambda layers
- `data-processing/` - Data processing dependencies (pandas, numpy, s3fs)
- `s3-dependencies/` - S3-specific dependencies

## Testing

### `/tests/` - Test suite
- `unit/` - Unit tests
- `integration/` - Integration tests (requires deployed stack)
- `requirements.txt` - Test dependencies

## Configuration & Specs

### `/.kiro/` - Kiro IDE configuration
- `specs/` - Feature specifications and implementation plans
- `steering/` - AI assistant guidance documents

### `/specs/` - Sample data and specifications
- JSON sample files for testing
- Text specifications for various components

### `/events/` - Test events
- `event.json` - Sample Lambda event for local testing

## Scripts

### `/scripts/` - Utility scripts
- `validate-infrastructure.py` - Infrastructure validation
- `validate.ps1` / `validate.sh` - Validation scripts

## Documentation

### Root-level documentation
- `AUTOML_FIELD_EXTRACTION_SUMMARY.md` - AutoML field extraction details
- `deployment-diagnosis-tasks.md` - Deployment troubleshooting
- `deployment-strategy.md` - Deployment approach
- `INFRASTRUCTURE_CHECKLIST.md` - Infrastructure verification

### `/docs/` - Additional documentation
- `dynamodb-schema-extensions.md` - DynamoDB schema details

## Naming Conventions

### Lambda Functions
- Suffix: `Function` (e.g., `GetFeatureListFunction`)
- Naming: PascalCase descriptive names

### DynamoDB Tables
- Format: `ProsperModels-<Purpose>` (e.g., `ProsperModels-FeatureLists`)
- Attributes: PascalCase (e.g., `UserId`, `SubmissionDateTime`)

### S3 Buckets
- Format: `prosper-<purpose>` (e.g., `prosper-raw-data`)

### AutoML Jobs
- Format: `prosper-<uuid-prefix>` (24 chars max)
- Generated from request ID

### API Routes
- Format: kebab-case (e.g., `/start-workflow`, `/model-requests`)

### Python Code
- Functions: snake_case
- Classes: PascalCase
- Constants: UPPER_SNAKE_CASE
- Private methods: prefix with underscore

## Module Organization

Each Lambda function is self-contained with:
1. Main handler file (e.g., `lambda_function.py`)
2. Supporting modules for specific concerns (validation, logging, clients)
3. Local requirements.txt
4. Tests co-located or in tests/ directory
5. Documentation in README.md or markdown files

## Error Handling Pattern

All Lambda functions follow consistent error handling:
1. Validate inputs early
2. Use structured logging with request IDs
3. Return Step Functions compatible error responses
4. Store error details in DynamoDB for troubleshooting
5. Use specific error status codes (e.g., `Feature_List_Retrieval_Failed`)
