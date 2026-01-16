# Design Document

## Overview

This design addresses the Lambda deployment failure caused by package size exceeding AWS Lambda's 262MB limit. The solution involves optimizing the build process, excluding unnecessary files, and potentially using Lambda Layers for heavy dependencies.

## Architecture

### Current Problem
- Lambda functions are packaged with entire `src/` directory including `venv/`
- Virtual environment contains ~274MB of Python packages
- Test files and cache files are unnecessarily included
- All functions share the same large dependency set

### Proposed Solution
1. **Build Exclusions**: Configure SAM to exclude unnecessary files and directories
2. **Dependency Separation**: Split heavy dependencies into Lambda Layers
3. **Function-Specific Dependencies**: Use targeted requirements for each function
4. **Clean Build Process**: Ensure only runtime-necessary files are packaged

## Components and Interfaces

### 1. SAM Build Configuration
- **Purpose**: Configure build exclusions and optimizations
- **Location**: `template.yaml` and `.samignore` file
- **Exclusions**: 
  - `venv/` directories
  - `__pycache__/` directories  
  - `test_*.py` files
  - `.pyc` files
  - `.git*` files

### 2. Function-Specific Requirements
- **ModelRequestsFunction**: Minimal dependencies (boto3 only)
- **GetFeatureListFunction**: Minimal dependencies (boto3 only)
- **CreateModelingDataFunction**: Heavy dependencies (pandas, numpy) via Layer

### 3. Lambda Layer (Optional)
- **Purpose**: Share heavy dependencies across functions that need them
- **Contents**: pandas, numpy, s3fs, and other data processing libraries
- **Usage**: Referenced by CreateModelingDataFunction only

## Data Models

### Build Exclusion Patterns
```
venv/
__pycache__/
test_*.py
*.pyc
.git*
.pytest_cache/
*.egg-info/
```

### Dependency Matrix
| Function | boto3 | pandas | numpy | s3fs | pymysql |
|----------|-------|--------|-------|------|---------|
| ModelRequestsFunction | ✓ | ✗ | ✗ | ✗ | ✗ |
| GetFeatureListFunction | ✓ | ✗ | ✗ | ✗ | ✗ |
| CreateModelingDataFunction | ✓ | ✓ | ✓ | ✓ | ✓ |

## Implementation Strategy

### Phase 1: Immediate Fix (Build Exclusions)
1. Create `.samignore` file to exclude unnecessary directories
2. Remove `venv/` directory from `src/`
3. Clean up `__pycache__` directories
4. Test deployment with current dependencies

### Phase 2: Dependency Optimization (If Phase 1 Insufficient)
1. Create separate requirements files for each function
2. Move heavy dependencies to Lambda Layer
3. Update template.yaml to reference layers
4. Test all functions work correctly

### Phase 3: Validation
1. Deploy all functions successfully
2. Test ModelRequests API endpoint
3. Verify all existing functionality works
4. Monitor function performance

## Error Handling

### Build Failures
- If exclusions don't reduce size enough, proceed to Phase 2
- If Layer creation fails, fall back to function-specific builds
- Validate each function can import required dependencies

### Runtime Errors
- Ensure all required dependencies are available at runtime
- Test import statements in each function
- Verify Layer compatibility with function runtime

## Testing Strategy

### Unit Tests
- Test each function can import required modules
- Test DynamoDB operations work correctly
- Test data processing functions work with layers

### Integration Tests  
- Test ModelRequests API returns correct data
- Test Step Functions workflow still works
- Test all Lambda functions deploy successfully

### Property Tests
- **Property 1: Package Size Constraint**
  *For any* Lambda function deployment package, the size should be less than 262MB
  **Validates: Requirements 1.4**

- **Property 2: Dependency Availability**
  *For any* Lambda function, all imported modules should be available at runtime
  **Validates: Requirements 2.1, 4.4**

- **Property 3: Function Isolation**
  *For any* Lambda function, it should only include dependencies it actually uses
  **Validates: Requirements 2.4, 2.5**