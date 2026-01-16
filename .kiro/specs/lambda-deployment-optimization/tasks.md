# Implementation Plan: Lambda Deployment Optimization

## Overview

This implementation plan addresses the Lambda deployment failure by optimizing package sizes and excluding unnecessary files from deployment packages.

## Tasks

- [x] 1. Clean up source directory and create build exclusions
  - Remove venv directory from src/
  - Remove __pycache__ directories from src/
  - Create .samignore file with exclusion patterns
  - _Requirements: 1.1, 1.2, 1.3, 3.1, 3.2, 3.3_

- [x] 2. Test immediate deployment fix
  - Build Lambda functions with exclusions
  - Attempt deployment to verify size reduction
  - Validate all functions can still import required dependencies
  - _Requirements: 1.4, 1.5_

- [x] 3. Create function-specific requirements (if needed)
  - Create requirements-minimal.txt for lightweight functions
  - Create requirements-heavy.txt for data processing functions
  - Update template.yaml to use specific requirements files
  - _Requirements: 2.1, 2.4, 2.5_

- [ ]* 3.1 Write property test for package size constraint
  - **Property 1: Package Size Constraint**
  - **Validates: Requirements 1.4**

- [x] 4. Implement Lambda Layer for heavy dependencies (if needed)
  - Create Lambda Layer with pandas, numpy, s3fs dependencies
  - Update CreateModelingDataFunction to reference layer
  - Test layer compatibility and import functionality
  - _Requirements: 2.2, 2.3, 4.1, 4.5_

- [ ]* 4.1 Write property test for dependency availability
  - **Property 2: Dependency Availability**  
  - **Validates: Requirements 2.1, 4.4**

- [x] 5. Deploy and validate ModelRequests API
  - Deploy optimized Lambda functions
  - Test ModelRequestsFunction with DynamoDB queries
  - Verify API Gateway integration works correctly
  - _Requirements: 5.1, 5.2, 5.5_

- [ ]* 5.1 Write unit tests for ModelRequests API
  - Test pagination functionality
  - Test JWT token extraction
  - Test DynamoDB query operations
  - _Requirements: 5.2, 5.5_

- [x] 6. Validate all existing functionality
  - Test GetFeatureListFunction works correctly
  - Test CreateModelingDataFunction processes data
  - Test Step Functions workflow executes successfully
  - _Requirements: 5.3, 5.4_

- [ ]* 6.1 Write property test for function isolation
  - **Property 3: Function Isolation**
  - **Validates: Requirements 2.4, 2.5**

- [x] 7. Final checkpoint - Ensure all functions deploy and work
  - Ensure all Lambda functions deploy without errors
  - Ensure ModelRequests API endpoint is accessible
  - Ensure existing AutoML workflow continues to work
  - Ask the user if questions arise
  - **COMPLETED**: ✅ All Lambda functions deployed successfully (5KB packages each). ✅ Lambda Layer deployed (98MB with pandas/numpy). ✅ Step Functions workflow is ACTIVE. ✅ ModelRequests API integrated into main stack. ✅ Main ProsperModelsDB stack deployment successful!

## Notes

- Tasks marked with `*` are optional and can be skipped for faster deployment
- Phase 1 (tasks 1-2) should resolve the immediate deployment issue
- Phase 2 (tasks 3-4) provides additional optimization if needed
- Each task references specific requirements for traceability
- Focus on getting the ModelRequests API working first, then optimize further if needed