# Design Document

## Overview

This design enhances the CreateModelingData Lambda function to provide richer metadata about generated datasets and create feature type mappings for downstream ML processes. The enhancement adds two key capabilities: dataset statistics in the response and a feature types JSON file stored in S3.

## Architecture

The enhancement follows the existing function architecture with minimal changes:

1. **Data Processing Layer**: Existing feature extraction and data processing logic remains unchanged
2. **Metadata Calculation Layer**: New component to calculate dataset statistics after data processing
3. **File Generation Layer**: Enhanced to create both CSV and JSON files
4. **Response Enhancement Layer**: Augments existing response with new metadata fields

## Components and Interfaces

### Enhanced Response Structure

```json
{
  "statusCode": 200,
  "message": "Data processing completed successfully",
  "Modeling Data": {
    "RowCount": 1250,
    "PositiveClassRatio": 0.236
  },
  "details": {
    "outputPath": "s3://prosper-raw-data/request-name/modeling_data.csv",
    "featureTypesPath": "s3://prosper-raw-data/request-name/feature_types.json",
    "dataRows": 1250,
    "dataColumns": 15,
    "requestName": "request-name"
  }
}
```

### Feature Types JSON Structure

```json
{
  "FeatureDataTypes": {
    "age_group": "categorical",
    "income_level": "numeric",
    "zip_cluster": "categorical",
    "satisfaction_score": "numeric",
    "product_category": "categorical"
  }
}
```

### New Components

#### MetadataCalculator Class
```python
class MetadataCalculator:
    def calculate_row_count(self, dataframe) -> int
    def calculate_positive_class_ratio(self, dataframe, label_column) -> float
    def get_dataset_metadata(self, dataframe, label_column) -> dict
```

#### FeatureTypesGenerator Class
```python
class FeatureTypesGenerator:
    def generate_feature_types_mapping(self, feature_list) -> dict
    def save_feature_types_to_s3(self, mapping, bucket, key) -> str
```

## Data Models

### Enhanced Response Model
- **Modeling Data**: Object containing dataset statistics
  - **RowCount**: Integer count of rows in final dataset
  - **PositiveClassRatio**: Float decimal ratio of positive labels (0-1)

### Feature Types Model
- **FeatureDataTypes**: Dictionary mapping feature names to data types
  - Keys: Feature names (strings matching CSV headers)
  - Values: Data types ("categorical" or "numeric")

## Implementation Details

### Metadata Calculation Logic

1. **Row Count**: Use `len(dataframe)` after all data cleaning and processing
2. **Positive Class Ratio**: 
   - Identify the label column (first column in label_list)
   - Count rows where label value equals 1
   - Calculate decimal ratio: (positive_count / total_count)
   - Handle edge cases (empty dataset, no positive labels)

### Feature Type Mapping Logic

1. **Type Determination**:
   - Categorical: FeatureType in ["Categorical", "Zip", "Binary"] → "categorical"
   - Numeric: FeatureType in ["Ordinal"] → "numeric"
   - Legacy support: "Category" → "categorical"

2. **Feature Name Extraction**:
   - Use feature.name from Feature objects
   - Ensure names match CSV column headers exactly
   - Exclude label columns from the mapping

### File Storage Strategy

1. **CSV File**: Existing logic unchanged
2. **JSON File**: Store in same S3 location with fixed name "feature_types.json"
3. **Error Handling**: If JSON creation fails, log warning but don't fail the entire process

## Error Handling

### Enhanced Error Scenarios

1. **Metadata Calculation Errors**:
   - Empty dataset: Return RowCount=0, PositiveClassRatio=0
   - No label column: Return RowCount only, omit PositiveClassRatio
   - Invalid label values: Log warning, calculate based on available data

2. **Feature Types Generation Errors**:
   - Invalid FeatureType: Log warning, default to "numeric"
   - S3 upload failure: Log error, continue with CSV generation
   - JSON serialization error: Log error, continue with CSV generation

### Backward Compatibility

- All existing error responses remain unchanged
- New metadata only added to successful responses
- Existing integrations continue to work without modification

## Testing Strategy

### Unit Tests
- Test metadata calculation with various dataset sizes and label distributions
- Test feature type mapping for all FeatureType combinations
- Test JSON file generation and S3 upload
- Test error handling scenarios

### Property Tests
- **Property 1: Row count accuracy**: For any valid dataset, the returned RowCount should equal the actual number of rows in the generated CSV
- **Property 2: Positive class ratio bounds**: For any dataset, PositiveClassRatio should be between 0 and 1 inclusive
- **Property 3: Feature type consistency**: For any feature list, the feature types JSON should contain exactly the features present in the CSV (excluding labels)
- **Property 4: JSON validity**: For any generated feature_types.json file, it should be valid JSON and parseable

### Integration Tests
- Test end-to-end processing with real feature lists
- Verify S3 file creation and accessibility
- Test with various label distributions (0%, 50%, 100% positive)
- Test with different FeatureType combinations