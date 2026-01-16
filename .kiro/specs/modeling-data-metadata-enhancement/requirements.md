# Requirements Document

## Introduction

Enhance the CreateModelingData Lambda function to provide additional metadata about the generated modeling data and create a feature types mapping file for downstream ML processes.

## Glossary

- **CreateModelingData**: Lambda function that processes raw survey data into modeling-ready CSV files
- **PositiveClassRatio**: The decimal ratio of rows in the dataset that have a positive target label (value = 1)
- **FeatureDataTypes**: Mapping of feature names to their data types for ML model training
- **S3_Bucket**: AWS S3 storage bucket containing the modeling data files

## Requirements

### Requirement 1: Enhanced Response Metadata

**User Story:** As a data scientist, I want to receive metadata about the generated modeling data, so that I can understand the dataset characteristics before training models.

#### Acceptance Criteria

1. WHEN the CreateModelingData function completes successfully, THE System SHALL return a "Modeling Data" object in the response
2. THE "Modeling Data" object SHALL contain a "RowCount" field with the integer count of rows in the final dataset
3. THE "Modeling Data" object SHALL contain a "PositiveClassRatio" field with the decimal ratio of rows having a positive target label
4. THE "PositiveClassRatio" SHALL be calculated as (count of rows where label = 1) / (total row count)
5. THE "PositiveClassRatio" SHALL be returned as a numeric value between 0 and 1 (float)

### Requirement 2: Feature Types JSON File Creation

**User Story:** As an ML engineer, I want a feature types mapping file, so that I can configure ML models with appropriate data type handling.

#### Acceptance Criteria

1. WHEN the CreateModelingData function processes features, THE System SHALL create a feature_types.json file
2. THE feature_types.json file SHALL be stored in the same S3 location as the modeling_data.csv file
3. THE feature_types.json file SHALL contain a "FeatureDataTypes" object mapping feature names to data types
4. WHEN a feature has FeatureType "Categorical", "Zip", or "Binary", THE data type SHALL be mapped to "categorical"
5. WHEN a feature has FeatureType "Ordinal", THE data type SHALL be mapped to "numeric"
6. THE feature names in the mapping SHALL match exactly the column headers in the modeling_data.csv file
7. THE target label column SHALL NOT be included in the feature_types.json file
8. THE JSON file SHALL be valid JSON format with proper structure and encoding

### Requirement 3: Backward Compatibility

**User Story:** As a system administrator, I want the enhanced function to maintain backward compatibility, so that existing integrations continue to work.

#### Acceptance Criteria

1. THE existing response structure SHALL be preserved with additional fields added
2. THE existing CSV file generation SHALL continue to work unchanged
3. THE existing error handling and validation SHALL remain functional
4. WHEN the function encounters errors, THE enhanced metadata SHALL NOT be included in error responses