# Requirements Document

## Introduction

This feature creates a Lambda function wrapper for SageMaker CreateAutoMLJob API to support parameters that are not available through AWS Step Functions' direct SageMaker integration, specifically the FeatureSpecificationS3Uri parameter. The wrapper will allow the Step Functions workflow to use the complete SageMaker AutoML API while maintaining the existing workflow structure.

## Glossary

- **Lambda_Wrapper**: A Lambda function that acts as a proxy between Step Functions and SageMaker CreateAutoMLJob API
- **FeatureSpecificationS3Uri**: SageMaker parameter that specifies the S3 location of a JSON file containing feature type specifications
- **AutoML_Job_Parameters**: Complete set of parameters for SageMaker CreateAutoMLJob API call
- **Step_Functions_Workflow**: The existing ProsperModels workflow that needs to call SageMaker with full parameter support
- **SageMaker_Response**: The response from SageMaker CreateAutoMLJob API that needs to be passed back to Step Functions
- **ModelTrainingPlan**: A parameter that determines the training configuration and completion criteria for AutoML jobs (Bronze, Silver, Test, Gold)

## Requirements

### Requirement 1

**User Story:** As a data scientist, I want to specify feature types for my AutoML job using FeatureSpecificationS3Uri, so that SageMaker can properly handle different data types in my modeling data.

#### Acceptance Criteria

1. WHEN the Step Functions workflow needs to launch an AutoML job with feature specifications THEN THE Lambda_Wrapper SHALL accept FeatureSpecificationS3Uri as a parameter
2. WHEN the Lambda_Wrapper receives AutoML job parameters THEN THE Lambda_Wrapper SHALL pass FeatureSpecificationS3Uri to the SageMaker CreateAutoMLJob API
3. WHEN the feature specification file exists at the S3 URI THEN THE Lambda_Wrapper SHALL successfully create the AutoML job with feature type information
4. WHEN the feature specification file is missing or invalid THEN THE Lambda_Wrapper SHALL return a descriptive error message
5. WHEN the AutoML job is created successfully THEN THE Lambda_Wrapper SHALL return the SageMaker response including the AutoMLJobArn

### Requirement 2

**User Story:** As a system administrator, I want the Lambda wrapper to support all existing AutoML job parameters, so that the current workflow functionality is preserved.

#### Acceptance Criteria

1. WHEN the Lambda_Wrapper is called THEN THE Lambda_Wrapper SHALL accept all standard SageMaker CreateAutoMLJob parameters
2. WHEN processing AutoML job parameters THEN THE Lambda_Wrapper SHALL validate required parameters (AutoMLJobName, InputDataConfig, OutputDataConfig, RoleArn)
3. WHEN optional parameters are provided THEN THE Lambda_Wrapper SHALL pass them to SageMaker without modification
4. WHEN the SageMaker API call succeeds THEN THE Lambda_Wrapper SHALL return the complete SageMaker response
5. WHEN the SageMaker API call fails THEN THE Lambda_Wrapper SHALL return the error details in a format compatible with Step Functions error handling

### Requirement 3

**User Story:** As a developer, I want the Lambda wrapper to integrate seamlessly with the existing Step Functions workflow, so that minimal changes are required to the current implementation.

#### Acceptance Criteria

1. WHEN the Step Functions workflow calls the Lambda_Wrapper THEN THE Lambda_Wrapper SHALL accept the same input format as the current LaunchAutoMLJob state
2. WHEN the Lambda_Wrapper completes successfully THEN THE Lambda_Wrapper SHALL return output in the same format as the SageMaker Step Functions integration
3. WHEN the Lambda_Wrapper encounters errors THEN THE Lambda_Wrapper SHALL throw exceptions that can be caught by existing Step Functions error handling
4. WHEN the workflow transitions from Lambda_Wrapper to the next state THEN THE Step_Functions_Workflow SHALL continue with the same data structure as before
5. WHEN the Lambda_Wrapper is deployed THEN THE Step_Functions_Workflow SHALL only need to change the Resource ARN from aws-sdk:sagemaker to lambda:invoke

### Requirement 4

**User Story:** As a system administrator, I want comprehensive error handling and logging in the Lambda wrapper, so that I can troubleshoot AutoML job creation issues effectively.

#### Acceptance Criteria

1. WHEN the Lambda_Wrapper starts execution THEN THE Lambda_Wrapper SHALL log the input parameters (excluding sensitive data)
2. WHEN parameter validation fails THEN THE Lambda_Wrapper SHALL log the validation error and return a structured error response
3. WHEN the SageMaker API call fails THEN THE Lambda_Wrapper SHALL log the SageMaker error details and return a formatted error
4. WHEN S3 access issues occur with FeatureSpecificationS3Uri THEN THE Lambda_Wrapper SHALL log the S3 error and provide actionable error messages
5. WHEN the Lambda_Wrapper completes successfully THEN THE Lambda_Wrapper SHALL log the AutoML job creation success with job name and ARN

### Requirement 5

**User Story:** As a developer, I want the Lambda wrapper to be secure and follow AWS best practices, so that the system maintains proper access controls and resource management.

#### Acceptance Criteria

1. WHEN the Lambda_Wrapper accesses SageMaker THEN THE Lambda_Wrapper SHALL use IAM roles with least-privilege permissions
2. WHEN the Lambda_Wrapper accesses S3 for feature specifications THEN THE Lambda_Wrapper SHALL validate S3 URI format and permissions
3. WHEN processing input parameters THEN THE Lambda_Wrapper SHALL sanitize and validate all inputs to prevent injection attacks
4. WHEN the Lambda_Wrapper handles errors THEN THE Lambda_Wrapper SHALL not expose sensitive information in error messages
### Requirement 6

**User Story:** As a developer, I want to use a 'Test' mode for modelTrainingPlan, so that I can quickly validate AutoML job functionality with minimal resource usage and fast completion times.

#### Acceptance Criteria

1. WHEN modelTrainingPlan is set to 'Test' THEN THE Lambda_Wrapper SHALL set AutoMLJobConfig.CompletionCriteria to MaxCandidates: 1, MaxRuntimePerTrainingJobInSeconds: 120, MaxAutoMLJobRuntimeInSeconds: 120
2. WHEN the Step Functions workflow passes modelTrainingPlan as 'Test' THEN THE Lambda_Wrapper SHALL apply the test completion criteria before calling SageMaker CreateAutoMLJob API
3. WHEN using Test mode THEN THE AutoML job SHALL complete within the specified time limits to enable rapid development and testing cycles
4. WHEN Test mode is used THEN THE Lambda_Wrapper SHALL log that Test mode completion criteria are being applied
5. WHEN Test mode AutoML job is created successfully THEN THE Lambda_Wrapper SHALL return the same response format as other training plans