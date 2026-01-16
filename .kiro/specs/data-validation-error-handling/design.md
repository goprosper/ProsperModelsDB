# Design Document: Data Validation and Error Handling

## Overview

This design implements comprehensive data validation and error handling for the CreateModelingData Lambda function to address the EmptyDataError issue and improve overall system robustness. The solution focuses on early detection of data availability issues, clear error messaging, and graceful failure handling.

## Architecture

### Current Flow (Problematic)
```
RawData Function → Empty data_file (0 bytes) → CreateModelingData → pandas.read_csv() → EmptyDataError
```

### Improved Flow (With Validation)
```
RawData Function → Empty data_file → CreateModelingData → File Validation → Clear Error Message → Step Function Error Handling
```

## Components and Interfaces

### 1. Data Validation Layer

**Purpose**: Validate data files before processing to prevent pandas errors

**Interface**:
```python
class DataValidator:
    def validate_data_file(self, s3_path: str) -> ValidationResult
    def validate_map_file(self, s3_path: str) -> ValidationResult
    def check_file_size(self, s3_path: str) -> int
    def suggest_alternatives(self, study_name: str, dates: List[str]) -> List[str]
```

**Validation Checks**:
- File existence and accessibility
- File size (must be > 0 bytes)
- Basic CSV structure (headers, minimum rows)
- Required columns presence
- Data type consistency

### 2. Error Response Handler

**Purpose**: Generate structured, user-friendly error messages

**Interface**:
```python
class ErrorResponseHandler:
    def create_data_unavailable_error(self, requested_dates: List[str], study_name: str) -> Dict
    def create_file_validation_error(self, file_path: str, issue: str) -> Dict
    def suggest_alternative_dates(self, study_name: str) -> List[str]
```

**Error Response Format**:
```json
{
    "errorType": "DataValidationError",
    "errorMessage": "No data available for study 'MBI' on dates 2024-12-01, 2023-12-01",
    "details": {
        "requestedDates": ["2024-12-01", "2023-12-01"],
        "studyName": "MBI",
        "suggestedDates": ["2025-01-01"],
        "dataFilePath": "s3://prosper-raw-data/.../data_file",
        "fileSize": 0
    },
    "userMessage": "The requested dates do not have available data. Try using 2025-01-01 instead."
}
```

### 3. Enhanced CreateModelingData Function

**Modified Processing Flow**:
1. **Pre-validation Phase**
   - Check data_file and map_file existence and size
   - Validate basic file structure
   - Early exit with clear errors if validation fails

2. **Data Loading Phase** (only if validation passes)
   - Load files with enhanced error handling
   - Validate data consistency
   - Process features and labels

3. **Error Handling Phase**
   - Catch and transform pandas errors
   - Generate structured error responses
   - Log detailed information for debugging

## Data Models

### ValidationResult
```python
@dataclass
class ValidationResult:
    is_valid: bool
    error_type: Optional[str]
    error_message: Optional[str]
    file_size: int
    suggestions: List[str]
```

### DataAvailabilityInfo
```python
@dataclass
class DataAvailabilityInfo:
    study_name: str
    available_dates: List[str]
    requested_dates: List[str]
    missing_dates: List[str]
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

<function_calls>
<invoke name="prework">
<parameter name="featureName">data-validation-error-handling

### Property Reflection

After reviewing all testable properties from the prework analysis, I identified several areas where properties can be consolidated:

**Consolidation Opportunities:**
- Properties 1.1, 1.5, and 4.1 all relate to file validation before processing - can be combined into a comprehensive file validation property
- Properties 1.2, 1.3, 2.1, and 3.1 all relate to error message content and structure - can be combined into an error message completeness property  
- Properties 3.2, 3.3, and 2.2 all relate to suggestion generation - can be combined into a suggestion accuracy property
- Properties 2.4 and 4.4 both relate to error specificity - can be combined into error specificity property

**Final Property Set:**

Property 1: File validation prevents processing errors
*For any* data file or map file, validation must detect empty files, missing files, and structural issues before attempting pandas processing
**Validates: Requirements 1.1, 1.5, 4.1**

Property 2: Error messages contain complete context
*For any* validation failure, the error message must include the requested study dates, parameters, error type, and specific details about what failed
**Validates: Requirements 1.2, 1.3, 2.1, 3.1**

Property 3: Error classification distinguishes failure types
*For any* error condition, the system must correctly classify whether it's a data availability issue, file format issue, or processing error
**Validates: Requirements 1.4, 2.4, 4.4**

Property 4: Suggestions are accurate and helpful
*For any* data availability issue, if alternative dates or parameters exist, the system must suggest valid alternatives that have available data
**Validates: Requirements 2.2, 3.2, 3.3**

Property 5: Data privacy is preserved in responses
*For any* error response or data availability information, sensitive data contents must never be exposed in error messages or suggestions
**Validates: Requirements 3.4**

Property 6: Partial processing handles mixed validity
*For any* request with both valid and invalid components, the system must process valid portions and report what could not be fulfilled
**Validates: Requirements 2.5, 3.5**

Property 7: Question ID validation prevents processing errors
*For any* feature list with question IDs, all required question IDs must be validated against available data before processing begins
**Validates: Requirements 3.6**

Property 8: File format handling is robust
*For any* CSV file with encoding or format issues, the system must handle the issues gracefully and provide specific format error messages
**Validates: Requirements 4.2, 4.3**

Property 9: S3 operations are resilient
*For any* transient S3 access failure, the system must implement appropriate retry logic before failing permanently
**Validates: Requirements 4.5**

Property 10: Logging preserves debugging information
*For any* error condition, detailed debugging information must be logged while user-facing messages remain friendly and actionable
**Validates: Requirements 2.3**

## Error Handling

### Error Categories

1. **DataValidationError**: File validation failures
   - Empty files (0 bytes)
   - Missing required columns
   - Malformed CSV structure

2. **DataUnavailableError**: No data for requested parameters
   - Requested dates have no data
   - Study name not found
   - Feature list not available

3. **FileFormatError**: File parsing issues
   - Encoding problems
   - Unexpected file format
   - Corrupted files

4. **S3AccessError**: Infrastructure issues
   - File not found
   - Permission denied
   - Transient network issues

### Error Response Strategy

- **User-facing messages**: Clear, actionable guidance
- **Debug logs**: Detailed technical information
- **Structured responses**: Consistent JSON format for API consumption
- **Suggestions**: Alternative parameters when available

### Retry Logic

- **S3 operations**: 3 retries with exponential backoff
- **File validation**: No retries (fail fast)
- **Data processing**: No retries (deterministic failures)

## Testing Strategy

### Unit Testing
- Test each validation function with known good/bad inputs
- Verify error message formatting and content
- Test suggestion generation logic
- Validate retry mechanisms

### Property-Based Testing
- Generate random file contents and validate error handling
- Test error message completeness across all failure scenarios
- Verify suggestion accuracy with various data availability patterns
- Test partial processing with mixed valid/invalid data

**Property Test Configuration:**
- Minimum 100 iterations per property test
- Use Hypothesis for Python property-based testing
- Each test references its corresponding design property
- Tag format: **Feature: data-validation-error-handling, Property {number}: {property_text}**

### Integration Testing
- Test end-to-end workflow with various data scenarios
- Verify Step Function error handling integration
- Test API error response formatting
- Validate DynamoDB error status updates

The dual testing approach ensures both specific edge cases (unit tests) and comprehensive input coverage (property tests) for robust data validation and error handling.