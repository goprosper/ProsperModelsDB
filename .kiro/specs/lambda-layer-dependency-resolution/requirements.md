# Lambda Layer Dependency Resolution

## Overview
This spec addresses the recurring fsspec dependency issue in the CreateModelingData Lambda function that was preventing pandas from reading S3 files directly.

## Problem Statement
The CreateModelingData Lambda function was failing with "Missing optional dependency 'fsspec'" error when trying to use pandas to read CSV files directly from S3 URLs (e.g., `pd.read_csv('s3://bucket/key')`).

### Root Cause Analysis
1. **AWS Managed Layer Limitation**: The AWS managed pandas layer (`arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python313:5`) includes pandas and numpy but excludes `fsspec` and `s3fs` dependencies
2. **Direct S3 Access Pattern**: The code uses `pd.read_csv('s3://bucket/key')` which requires these additional dependencies
3. **Recurring Issue**: This was happening repeatedly because the underlying dependency gap wasn't addressed

## User Stories

### US-1: S3 File Access
**As a** data processing function  
**I want to** read CSV files directly from S3 using pandas  
**So that** I can process data without manual file downloads  

#### Acceptance Criteria
1. WHEN CreateModelingData function calls `pd.read_csv('s3://bucket/key')`, THEN it SHALL successfully read the file
2. WHEN the function imports pandas, THEN it SHALL have access to fsspec and s3fs dependencies
3. WHEN the function processes data, THEN it SHALL not fail with "Missing optional dependency 'fsspec'" error

### US-2: Layer Architecture
**As a** deployment engineer  
**I want to** use a hybrid layer approach  
**So that** I can leverage AWS managed layers while adding missing dependencies  

#### Acceptance Criteria
1. WHEN deploying the function, THEN it SHALL use the AWS managed pandas layer for core dependencies
2. WHEN deploying the function, THEN it SHALL use a supplementary layer for S3-specific dependencies
3. WHEN the function starts, THEN both layers SHALL be available in the Python path

### US-3: Dependency Isolation
**As a** system architect  
**I want to** minimize custom layer size  
**So that** I can reduce deployment time and complexity  

#### Acceptance Criteria
1. WHEN creating the supplementary layer, THEN it SHALL contain only fsspec and s3fs
2. WHEN building the layer, THEN it SHALL be compatible with Python 3.13
3. WHEN deploying, THEN the total layer size SHALL be minimized

## Technical Requirements

### TR-1: Layer Configuration
- The CreateModelingData function SHALL use two layers:
  - AWS managed pandas layer: `arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python313:5`
  - Custom S3 dependencies layer: Contains fsspec==2024.12.0 and s3fs==2024.12.0

### TR-2: Python Path
- The function environment SHALL set `PYTHONPATH: /opt/python` to ensure layer dependencies are available

### TR-3: Compatibility
- All dependencies SHALL be compatible with Python 3.13
- The solution SHALL work with the existing codebase without modifications

## Success Criteria

### SC-1: Functional Testing
- The CreateModelingData function SHALL successfully import pandas with S3 support
- The function SHALL read CSV files from S3 without fsspec errors
- All existing FeatureType processing SHALL continue to work correctly

### SC-2: Deployment Testing
- SAM build SHALL complete successfully with both layers
- SAM deploy SHALL update the function with new layer configuration
- CloudFormation stack SHALL show the new S3DependenciesLayer resource

### SC-3: Error Resolution
- The recurring "Missing optional dependency 'fsspec'" error SHALL be eliminated
- Function invocations SHALL progress past import stage to data processing
- Error messages SHALL be related to data validation, not dependency imports

## Implementation Notes

### Layer Structure
```
layers/s3-dependencies/
└── requirements.txt
    ├── fsspec==2024.12.0
    └── s3fs==2024.12.0
```

### Template Configuration
```yaml
S3DependenciesLayer:
  Type: AWS::Serverless::LayerVersion
  Properties:
    LayerName: !Sub "S3DependenciesLayer-v${DeploymentVersion}"
    Description: S3 file access dependencies (fsspec, s3fs) to supplement AWS pandas layer
    ContentUri: layers/s3-dependencies/
    CompatibleRuntimes:
      - python3.13
    RetentionPolicy: Retain
  Metadata:
    BuildMethod: python3.13

CreateModelingDataFunction:
  Properties:
    Layers:
      - arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python313:5
      - !Ref S3DependenciesLayer
```

## Validation Approach

### Test Cases
1. **Import Test**: Verify pandas can import with S3 support
2. **Functional Test**: Verify FeatureType processing works correctly  
3. **Integration Test**: Verify function progresses past import stage
4. **Regression Test**: Verify existing functionality remains intact

### Success Indicators
- Function invocation reaches data validation stage (not import errors)
- Error messages are about missing data files, not missing dependencies
- All FeatureType tests pass with correct return values and types