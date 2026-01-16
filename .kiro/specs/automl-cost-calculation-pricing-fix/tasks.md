# Implementation Plan: AutoML Cost Calculation Pricing Fix

## Overview

Fix the pricing integration in the CalculateJobCostLambda function to correctly retrieve SageMaker instance pricing from the AWS Pricing API by using the proper instance type format with service suffixes.

## Tasks

- [x] 1. Implement service suffix mapping functionality
  - Create `get_service_suffix()` function to map job types to SageMaker service suffixes
  - Add mapping for Training, Processing, and Transform job types
  - _Requirements: 1.1, 1.2, 1.3_

- [ ]* 1.1 Write property test for service suffix mapping
  - **Property 1: Service Suffix Mapping**
  - **Validates: Requirements 1.1, 1.2, 1.3**

- [x] 2. Update pricing API integration
  - Modify `get_instance_pricing()` function to accept job_type parameter
  - Update function to append service suffix to instance type before API call
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ]* 2.1 Write property test for pricing API integration
  - **Property 2: Pricing Data Validation**
  - **Validates: Requirements 4.1, 4.2**

- [x] 3. Implement default pricing rates
  - Add comprehensive default pricing table for common SageMaker instance types
  - Implement fallback logic when pricing API fails
  - _Requirements: 2.1, 2.2_

- [ ]* 3.1 Write property test for fallback pricing
  - **Property 3: Fallback Pricing**
  - **Validates: Requirements 2.1, 2.2**

- [x] 4. Enhance pricing data validation
  - Add `validate_pricing_data()` function to check API response format
  - Implement validation for positive numeric pricing values
  - _Requirements: 4.1, 4.2_

- [ ]* 4.1 Write unit tests for pricing validation
  - Test validation with various API response formats
  - Test handling of invalid pricing data
  - _Requirements: 4.1, 4.2_

- [x] 5. Improve caching mechanism
  - Enhance pricing cache to include timestamps
  - Implement cache expiration logic (24-hour timeout)
  - _Requirements: 3.2, 4.4_

- [ ]* 5.1 Write property test for cache consistency
  - **Property 4: Cache Consistency**
  - **Validates: Requirements 3.2**

- [x] 6. Update cost calculation logic
  - Modify job cost calculation functions to pass job type to pricing function
  - Ensure proper rounding of monetary values to 4 decimal places
  - _Requirements: 3.1, 3.3_

- [ ]* 6.1 Write property test for cost calculation accuracy
  - **Property 5: Cost Calculation Accuracy**
  - **Validates: Requirements 3.1, 3.3**

- [x] 7. Enhance error handling and logging
  - Add comprehensive error logging for pricing API failures
  - Implement graceful degradation when pricing data is unavailable
  - _Requirements: 2.3, 2.4_

- [ ]* 7.1 Write unit tests for error handling
  - Test various API failure scenarios
  - Test logging functionality
  - _Requirements: 2.3, 2.4_

- [x] 8. Checkpoint - Test pricing integration
  - Test pricing API calls with real SageMaker instance types
  - Verify cost calculations with actual AutoML job data
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Deploy and validate fix
  - Deploy updated Lambda function to AWS
  - Test with existing AutoML jobs to verify cost calculation
  - _Requirements: All_

- [ ]* 9.1 Write integration tests
  - Test end-to-end cost calculation with live data
  - Verify DynamoDB updates with correct cost values
  - _Requirements: All_

- [x] 10. Final checkpoint - Verify cost calculation accuracy
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties
- Unit tests validate specific examples and error conditions
- Integration tests verify end-to-end functionality with real AWS services