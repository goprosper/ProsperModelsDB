# Implementation Plan: Modeling Data Metadata Enhancement

## Overview

Enhance the CreateModelingData Lambda function to provide dataset metadata in the response and generate a feature types JSON file for ML model configuration.

## Tasks

- [x] 1. Create metadata calculation utilities
  - Add MetadataCalculator class with row count and positive class ratio calculation
  - Implement error handling for edge cases (empty datasets, missing labels)
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ]* 1.1 Write unit tests for metadata calculation
  - Test row count calculation with various dataset sizes
  - Test positive class ratio calculation with different label distributions
  - Test edge cases (empty dataset, no positive labels, invalid labels)
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Create feature types mapping functionality
  - Add FeatureTypesGenerator class to map FeatureType to data types
  - Implement JSON file generation and S3 upload
  - Handle FeatureType mapping: Categorical/Zip → "categorical", Binary/Ordinal → "numeric"
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_

- [ ]* 2.1 Write unit tests for feature types generation
  - Test FeatureType to data type mapping for all combinations
  - Test JSON structure and S3 upload functionality
  - Test feature name extraction and label exclusion
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_

- [x] 3. Integrate metadata calculation into main lambda handler
  - Calculate dataset metadata after data processing is complete
  - Add "Modeling Data" object to successful responses
  - Ensure backward compatibility with existing response structure
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 3.1, 3.2_

- [x] 4. Integrate feature types generation into main lambda handler
  - Generate feature types mapping from processed feature list
  - Save feature_types.json to S3 in same location as modeling_data.csv
  - Add featureTypesPath to response details
  - Handle errors gracefully without failing the main process
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 3.3, 3.4_

- [ ]* 4.1 Write property tests for enhanced lambda handler
  - **Property 1: Row count accuracy** - For any valid dataset, returned RowCount equals actual CSV rows
  - **Property 2: Positive class ratio bounds** - PositiveClassRatio is always between 0 and 1
  - **Property 3: Feature type consistency** - JSON contains exactly the features in CSV (excluding labels)
  - **Property 4: JSON validity** - Generated feature_types.json is always valid JSON
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_

- [x] 5. Update error handling to maintain backward compatibility
  - Ensure new metadata is only added to successful responses
  - Preserve existing error response formats
  - Add appropriate logging for new functionality
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ]* 5.1 Write integration tests for error scenarios
  - Test that errors don't include new metadata fields
  - Test that S3 JSON upload failures don't break CSV generation
  - Test backward compatibility with existing error handling
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 6. Checkpoint - Ensure all tests pass and deploy
  - Run all unit tests, property tests, and integration tests
  - Verify backward compatibility with existing integrations
  - Deploy to AWS and test with real data
  - Ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Integration tests ensure end-to-end functionality works correctly