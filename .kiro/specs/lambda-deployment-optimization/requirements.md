# Requirements Document

## Introduction

The ProsperModels Lambda functions are failing to deploy due to package size exceeding AWS Lambda's 262MB limit. The actual size is approximately 274MB, primarily caused by including a Python virtual environment and unnecessary files in the deployment package.

## Glossary

- **Lambda_Function**: AWS Lambda function resource
- **Deployment_Package**: The ZIP file containing Lambda function code and dependencies
- **Virtual_Environment**: Python venv directory containing installed packages
- **SAM_Build**: AWS SAM build process that packages Lambda functions

## Requirements

### Requirement 1: Reduce Lambda Package Size

**User Story:** As a developer, I want Lambda functions to deploy successfully, so that the ModelRequests API can be made available.

#### Acceptance Criteria

1. WHEN SAM builds Lambda functions, THE Lambda_Function SHALL exclude virtual environment directories from the deployment package
2. WHEN SAM builds Lambda functions, THE Lambda_Function SHALL exclude test files from the deployment package  
3. WHEN SAM builds Lambda functions, THE Lambda_Function SHALL exclude __pycache__ directories from the deployment package
4. WHEN Lambda functions are deployed, THE Deployment_Package SHALL be under 262MB in size
5. WHEN Lambda functions are deployed, THE Lambda_Function SHALL contain only necessary runtime dependencies

### Requirement 2: Optimize Dependencies

**User Story:** As a developer, I want Lambda functions to use only required dependencies, so that deployment packages are minimal and efficient.

#### Acceptance Criteria

1. WHEN Lambda functions are built, THE Lambda_Function SHALL include only dependencies specified in requirements.txt
2. WHEN Lambda functions use heavy dependencies, THE Lambda_Function SHALL use AWS Lambda Layers where appropriate
3. WHEN multiple Lambda functions share dependencies, THE Lambda_Function SHALL reuse common layers
4. THE ModelRequestsFunction SHALL use minimal dependencies for DynamoDB operations
5. THE GetFeatureListFunction SHALL use minimal dependencies for DynamoDB operations

### Requirement 3: Implement Build Exclusions

**User Story:** As a developer, I want the build process to automatically exclude unnecessary files, so that deployment packages are optimized without manual intervention.

#### Acceptance Criteria

1. THE SAM_Build SHALL exclude files matching pattern "venv/*"
2. THE SAM_Build SHALL exclude files matching pattern "__pycache__/*"  
3. THE SAM_Build SHALL exclude files matching pattern "test_*.py"
4. THE SAM_Build SHALL exclude files matching pattern "*.pyc"
5. THE SAM_Build SHALL exclude files matching pattern ".git*"

### Requirement 4: Separate Heavy Dependencies

**User Story:** As a developer, I want functions with heavy dependencies to be optimized separately, so that lightweight functions remain fast and efficient.

#### Acceptance Criteria

1. WHEN CreateModelingDataFunction requires pandas/numpy, THE Lambda_Function SHALL use a separate Lambda Layer
2. WHEN functions have different dependency requirements, THE Lambda_Function SHALL use function-specific requirements files
3. THE ModelRequestsFunction SHALL use only boto3 and standard library dependencies
4. THE GetFeatureListFunction SHALL use only boto3 and standard library dependencies
5. WHEN Lambda Layers are used, THE Lambda_Function SHALL reference the layer ARN correctly

### Requirement 5: Validate Deployment Success

**User Story:** As a developer, I want to verify that optimized Lambda functions deploy and work correctly, so that the ModelRequests API is functional.

#### Acceptance Criteria

1. WHEN Lambda functions are deployed, THE Lambda_Function SHALL deploy without size limit errors
2. WHEN ModelRequestsFunction is invoked, THE Lambda_Function SHALL successfully query DynamoDB
3. WHEN GetFeatureListFunction is invoked, THE Lambda_Function SHALL successfully retrieve feature lists
4. WHEN CreateModelingDataFunction is invoked, THE Lambda_Function SHALL successfully process data
5. THE ModelRequests API endpoint SHALL return paginated results correctly