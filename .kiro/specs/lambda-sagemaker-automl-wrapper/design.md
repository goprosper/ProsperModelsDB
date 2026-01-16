# Design Document

## Overview

This design creates a Lambda function that acts as a wrapper for the SageMaker CreateAutoMLJob API, enabling the use of parameters not supported by AWS Step Functions' direct SageMaker integration. The primary motivation is to support the `FeatureSpecificationS3Uri` parameter, which allows specifying feature types and selected features for AutoML jobs but is not available through Step Functions' `arn:aws:states:::aws-sdk:sagemaker:createAutoMLJob` integration.

The Lambda wrapper will accept the same input format as the current Step Functions SageMaker integration, call the full SageMaker CreateAutoMLJob API with all parameters including `FeatureSpecificationS3Uri`, and return a response compatible with the existing workflow.

## Architecture

### High-Level Flow
```
Step Functions → Lambda Wrapper → SageMaker CreateAutoMLJob API → Response → Step Functions
```

### Integration Points
1. **Step Functions Integration**: Replace `arn:aws:states:::aws-sdk:sagemaker:createAutoMLJob` with `arn:aws:states:::lambda:invoke`
2. **SageMaker API**: Direct boto3 call to `create_auto_ml_job()` with full parameter support
3. **S3 Integration**: Validation of `FeatureSpecificationS3Uri` parameter and file existence
4. **Error Handling**: Compatible error responses for Step Functions catch blocks

### Deployment Architecture
- **Lambda Function**: Single-purpose function deployed via SAM/CloudFormation
- **IAM Role**: Least-privilege permissions for SageMaker, S3, and CloudWatch
- **VPC**: Optional VPC configuration for enhanced security
- **Monitoring**: CloudWatch logs and metrics integration

## Components and Interfaces

### Lambda Function Interface

#### Input Format
The Lambda function accepts the same input structure as Step Functions SageMaker integration:

```json
{
  "AutoMLJobName": "string",
  "InputDataConfig": [
    {
      "DataSource": {
        "S3DataSource": {
          "S3DataType": "S3Prefix",
          "S3Uri": "string"
        }
      },
      "TargetAttributeName": "string"
    }
  ],
  "OutputDataConfig": {
    "S3OutputPath": "string"
  },
  "AutoMLJobObjective": {
    "MetricName": "string"
  },
  "ProblemType": "string",
  "RoleArn": "string",
  "modelTrainingPlan": "string",
  "AutoMLJobConfig": {
    "CompletionCriteria": {
      "MaxCandidates": "number",
      "MaxRuntimePerTrainingJobInSeconds": "number",
      "MaxAutoMLJobRuntimeInSeconds": "number"
    },
    "CandidateGenerationConfig": {
      "FeatureSpecificationS3Uri": "string"
    }
  }
}
```

#### Output Format
The function returns the same structure as SageMaker CreateAutoMLJob API:

```json
{
  "AutoMLJobArn": "string"
}
```

#### Error Format
Errors are thrown as exceptions compatible with Step Functions error handling:

```json
{
  "errorType": "SageMaker.ValidationException",
  "errorMessage": "Detailed error description"
}
```

### SageMaker API Integration

#### Parameter Mapping
The Lambda function maps input parameters to SageMaker CreateAutoMLJob API:

- **Direct Mapping**: `AutoMLJobName`, `InputDataConfig`, `OutputDataConfig`, `AutoMLJobObjective`, `ProblemType`, `RoleArn`
- **Nested Mapping**: `AutoMLJobConfig.CompletionCriteria`, `AutoMLJobConfig.CandidateGenerationConfig.FeatureSpecificationS3Uri`
- **Optional Parameters**: All optional SageMaker parameters are supported if provided
- **Training Plan Processing**: `modelTrainingPlan` parameter is processed to set appropriate `CompletionCriteria`

#### Training Plan Configuration
The `modelTrainingPlan` parameter determines the AutoML job completion criteria:

- **Test Mode**: `modelTrainingPlan = 'Test'`
  - `MaxCandidates`: 1
  - `MaxRuntimePerTrainingJobInSeconds`: 120
  - `MaxAutoMLJobRuntimeInSeconds`: 120
  - Purpose: Rapid validation and testing with minimal resource usage

- **Bronze Mode**: `modelTrainingPlan = 'Bronze'` 
  - `MaxCandidates`: 10
  - `MaxRuntimePerTrainingJobInSeconds`: 900
  - `MaxAutoMLJobRuntimeInSeconds`: 3600
  - Purpose: Basic training with moderate resource usage

- **Silver Mode**: `modelTrainingPlan = 'Silver'`
  - `MaxCandidates`: 20
  - `MaxRuntimePerTrainingJobInSeconds`: 1200
  - `MaxAutoMLJobRuntimeInSeconds`: 4800
  - Purpose: Enhanced training with higher resource allocation

- **Gold Mode**: `modelTrainingPlan = 'Gold'`
  - No completion criteria specified (uses SageMaker defaults)
  - Purpose: Maximum training flexibility with SageMaker's default limits

If `modelTrainingPlan` is not provided or has an unrecognized value, the existing `CompletionCriteria` from the input will be used unchanged.

#### Feature Specification Handling
The `FeatureSpecificationS3Uri` parameter points to a JSON file with format:
```json
{
  "FeatureAttributeNames": ["col1", "col2", "col3"],
  "FeatureDataTypes": {
    "col1": "numeric",
    "col2": "categorical", 
    "col3": "text"
  }
}
```

### Error Handling Strategy

#### Parameter Validation
1. **Required Parameters**: Validate presence of `AutoMLJobName`, `InputDataConfig`, `OutputDataConfig`, `RoleArn`
2. **Format Validation**: Validate S3 URI formats, job name patterns, and data types
3. **S3 Validation**: Check existence and accessibility of `FeatureSpecificationS3Uri` file

#### SageMaker API Errors
1. **Service Exceptions**: Map SageMaker exceptions to Step Functions compatible format
2. **Throttling**: Handle rate limiting with exponential backoff
3. **Resource Limits**: Provide actionable error messages for quota exceeded scenarios

#### S3 Access Errors
1. **File Not Found**: Clear error message when feature specification file is missing
2. **Access Denied**: Specific guidance for IAM permission issues
3. **Invalid Format**: JSON parsing errors with line number information

## Data Models

### Lambda Event Model
```python
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class S3DataSource:
    S3DataType: str
    S3Uri: str

@dataclass
class DataSource:
    S3DataSource: S3DataSource

@dataclass
class InputDataConfig:
    DataSource: DataSource
    TargetAttributeName: str
    ChannelType: Optional[str] = None
    CompressionType: Optional[str] = None
    ContentType: Optional[str] = None

@dataclass
class OutputDataConfig:
    S3OutputPath: str
    KmsKeyId: Optional[str] = None

@dataclass
class AutoMLJobObjective:
    MetricName: str

@dataclass
class CompletionCriteria:
    MaxCandidates: Optional[int] = None
    MaxRuntimePerTrainingJobInSeconds: Optional[int] = None
    MaxAutoMLJobRuntimeInSeconds: Optional[int] = None

@dataclass
class CandidateGenerationConfig:
    FeatureSpecificationS3Uri: Optional[str] = None
    AlgorithmsConfig: Optional[List[Dict[str, Any]]] = None

@dataclass
class AutoMLJobConfig:
    CompletionCriteria: Optional[CompletionCriteria] = None
    CandidateGenerationConfig: Optional[CandidateGenerationConfig] = None
    Mode: Optional[str] = None

@dataclass
class AutoMLJobRequest:
    AutoMLJobName: str
    InputDataConfig: List[InputDataConfig]
    OutputDataConfig: OutputDataConfig
    RoleArn: str
    AutoMLJobObjective: Optional[AutoMLJobObjective] = None
    ProblemType: Optional[str] = None
    AutoMLJobConfig: Optional[AutoMLJobConfig] = None
    modelTrainingPlan: Optional[str] = None
```

### Response Model
```python
@dataclass
class AutoMLJobResponse:
    AutoMLJobArn: str
```

### Error Model
```python
@dataclass
class AutoMLJobError:
    errorType: str
    errorMessage: str
    errorDetails: Optional[Dict[str, Any]] = None
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Let me analyze the acceptance criteria to determine which ones are testable as properties:

<function_calls>
<invoke name="prework">
<parameter name="featureName">lambda-sagemaker-automl-wrapper

After reviewing the testable acceptance criteria, I need to perform property reflection to eliminate redundancy:

**Property Reflection:**
- Properties 1.1 and 2.1 both test parameter acceptance - can be combined into one comprehensive property
- Properties 1.2 and 2.3 both test parameter pass-through - can be combined  
- Properties 2.4 and 1.5 both test successful response handling - can be combined
- Properties 4.2 and 4.3 both test error logging - can be combined into comprehensive error logging property
- Properties 1.4 and 4.4 both test S3 error handling - can be combined

**Property 1: Parameter Acceptance and Pass-through**
*For any* valid SageMaker CreateAutoMLJob parameters including FeatureSpecificationS3Uri, the Lambda wrapper should accept them and pass them unchanged to the SageMaker API
**Validates: Requirements 1.1, 1.2, 2.1, 2.3**

**Property 2: Required Parameter Validation**
*For any* input missing required parameters (AutoMLJobName, InputDataConfig, OutputDataConfig, RoleArn), the Lambda wrapper should return a validation error
**Validates: Requirements 2.2**

**Property 3: Successful Response Handling**
*For any* successful SageMaker API response, the Lambda wrapper should return the complete response including AutoMLJobArn in Step Functions compatible format
**Validates: Requirements 1.5, 2.4**

**Property 4: S3 Error Handling**
*For any* invalid or inaccessible FeatureSpecificationS3Uri, the Lambda wrapper should return descriptive error messages and log the S3 error details
**Validates: Requirements 1.4, 4.4**

**Property 5: SageMaker Error Compatibility**
*For any* SageMaker API error, the Lambda wrapper should format the error in a way that's compatible with Step Functions error handling
**Validates: Requirements 2.5**

**Property 6: Input Format Compatibility**
*For any* input in the current Step Functions LaunchAutoMLJob format, the Lambda wrapper should accept and process it correctly
**Validates: Requirements 3.1**

**Property 7: Output Format Compatibility**
*For any* successful execution, the Lambda wrapper should return output in the same format as SageMaker Step Functions integration
**Validates: Requirements 3.2**

**Property 8: Error Format Compatibility**
*For any* error condition, the Lambda wrapper should throw exceptions that can be caught by existing Step Functions error handling
**Validates: Requirements 3.3**

**Property 9: Comprehensive Logging**
*For any* execution (successful or failed), the Lambda wrapper should log appropriate information including input parameters (excluding sensitive data), validation errors, SageMaker errors, and success details
**Validates: Requirements 4.1, 4.2, 4.3, 4.5**

**Property 10: S3 URI Validation**
*For any* S3 URI provided as FeatureSpecificationS3Uri, the Lambda wrapper should validate the URI format and accessibility
**Validates: Requirements 5.2**

**Property 11: Input Sanitization**
*For any* input parameters, the Lambda wrapper should sanitize and validate them to prevent injection attacks
**Validates: Requirements 5.3**

**Property 12: Error Message Security**
*For any* error condition, the Lambda wrapper should not expose sensitive information in error messages
**Validates: Requirements 5.4**

**Property 13: Feature Specification File Processing**
*For any* valid feature specification file at the S3 URI, the Lambda wrapper should successfully create the AutoML job with the feature type information
**Validates: Requirements 1.3**

**Property 14: Test Mode Completion Criteria**
*For any* AutoML job request with modelTrainingPlan set to 'Test', the Lambda wrapper should set CompletionCriteria to MaxCandidates: 1, MaxRuntimePerTrainingJobInSeconds: 120, MaxAutoMLJobRuntimeInSeconds: 120
**Validates: Requirements 6.1**

**Property 15: Test Mode Logging**
*For any* AutoML job request using Test mode, the Lambda wrapper should log that Test mode completion criteria are being applied
**Validates: Requirements 6.4**

**Property 16: Training Plan Response Consistency**
*For any* successful AutoML job creation regardless of training plan (Test, Bronze, Silver), the Lambda wrapper should return the same response format
**Validates: Requirements 6.5**

## Error Handling

### Exception Hierarchy
```python
class AutoMLWrapperError(Exception):
    """Base exception for AutoML wrapper errors"""
    pass

class ParameterValidationError(AutoMLWrapperError):
    """Raised when input parameters are invalid"""
    pass

class S3AccessError(AutoMLWrapperError):
    """Raised when S3 access fails for feature specification"""
    pass

class SageMakerAPIError(AutoMLWrapperError):
    """Raised when SageMaker API call fails"""
    pass
```

### Error Response Format
All errors are formatted for Step Functions compatibility:
```json
{
  "errorType": "ParameterValidationError",
  "errorMessage": "Missing required parameter: AutoMLJobName",
  "errorDetails": {
    "parameter": "AutoMLJobName",
    "provided": null,
    "expected": "string"
  }
}
```

### Retry Strategy
- **SageMaker Throttling**: Exponential backoff with jitter (max 3 retries)
- **S3 Access**: Single retry for transient network issues
- **Parameter Validation**: No retry (fail fast)

## Testing Strategy

### Dual Testing Approach
The implementation will use both unit tests and property-based tests for comprehensive coverage:

**Unit Tests** will focus on:
- Specific examples of valid and invalid inputs
- Edge cases like empty parameters or malformed JSON
- Integration points with AWS services
- Error message formatting and content

**Property-Based Tests** will focus on:
- Universal properties that hold across all valid inputs
- Comprehensive input coverage through randomization
- Parameter validation across the full SageMaker API parameter space
- Error handling consistency across different failure scenarios

### Property-Based Testing Configuration
- **Testing Library**: Hypothesis (Python)
- **Test Iterations**: Minimum 100 iterations per property test
- **Test Tags**: Each property test will reference its design document property
- **Tag Format**: **Feature: lambda-sagemaker-automl-wrapper, Property {number}: {property_text}**

### Test Data Generation
**Valid Input Generation**:
- Random AutoML job names following SageMaker naming conventions
- Random S3 URIs with valid bucket/key patterns
- Random feature specification JSON files with valid schemas
- Random completion criteria within SageMaker limits

**Invalid Input Generation**:
- Missing required parameters
- Invalid S3 URI formats
- Malformed JSON in feature specifications
- Parameters exceeding SageMaker limits

**Error Scenario Generation**:
- SageMaker API errors (throttling, validation, resource limits)
- S3 access errors (not found, access denied, network issues)
- JSON parsing errors in feature specifications

### Integration Testing
- **Mock SageMaker API**: Use moto library for SageMaker service mocking
- **Mock S3**: Use moto library for S3 service mocking
- **Step Functions Integration**: Test with actual Step Functions state machine
- **End-to-End Testing**: Deploy to test environment with real AWS services