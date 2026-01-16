# Design Document

## Overview

This design addresses the pricing integration issue in the AutoML Job Cost Calculation Lambda function. The current implementation fails to retrieve pricing data because it doesn't use the correct instance type format required by the AWS Pricing API for SageMaker services.

## Architecture

The solution involves modifying the `get_instance_pricing` function to:
1. Map job types to appropriate SageMaker service suffixes
2. Implement robust error handling and fallback pricing
3. Add proper validation and caching mechanisms
4. Improve logging for debugging pricing issues

## Components and Interfaces

### Modified Components

#### `get_instance_pricing(instance_type, job_type)`
- **Input**: Base instance type (e.g., "ml.m5.12xlarge") and job type ("Training", "Processing", "Transform")
- **Output**: Hourly rate in USD as float
- **Behavior**: Appends appropriate suffix and queries AWS Pricing API

#### `pricing_cache`
- **Enhancement**: Include timestamp for cache expiration
- **Structure**: `{instance_type_with_suffix: {'rate': float, 'timestamp': datetime}}`

### New Components

#### `get_service_suffix(job_type)`
- **Input**: Job type string
- **Output**: Service suffix string
- **Mapping**: 
  - "Training" → "-Training"
  - "Processing" → "-Processing" 
  - "Transform" → "-Transform"

#### `validate_pricing_data(price_data)`
- **Input**: Raw pricing API response
- **Output**: Boolean indicating validity
- **Validation**: Checks for positive numeric values and expected structure

## Data Models

### Enhanced Pricing Cache Entry
```python
{
    "instance_type_with_suffix": {
        "rate": 1.234,  # USD per hour
        "timestamp": datetime.utcnow(),
        "source": "api|default"  # Track data source
    }
}
```

### Default Pricing Rates
```python
DEFAULT_RATES = {
    "ml.m5.large": 0.115,
    "ml.m5.xlarge": 0.230,
    "ml.m5.2xlarge": 0.461,
    "ml.m5.4xlarge": 0.922,
    "ml.m5.12xlarge": 2.765,
    "ml.c5.large": 0.096,
    "ml.c5.xlarge": 0.192,
    "ml.c5.2xlarge": 0.384,
    "ml.c5.4xlarge": 0.768,
    "default": 0.50  # Fallback rate
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Service Suffix Mapping
*For any* valid job type ("Training", "Processing", "Transform"), the service suffix should be correctly appended to the instance type when querying the pricing API
**Validates: Requirements 1.1, 1.2, 1.3**

### Property 2: Pricing Data Validation
*For any* pricing API response, if the response contains valid pricing data, the extracted hourly rate should be a positive number
**Validates: Requirements 4.1, 4.2**

### Property 3: Fallback Pricing
*For any* pricing API failure or invalid response, the system should return a positive default rate and continue processing
**Validates: Requirements 2.1, 2.2**

### Property 4: Cache Consistency
*For any* instance type and job type combination, repeated calls within the cache timeout period should return the same pricing rate
**Validates: Requirements 3.2**

### Property 5: Cost Calculation Accuracy
*For any* valid runtime hours and hourly rate, the calculated cost should equal runtime multiplied by rate, rounded to 4 decimal places
**Validates: Requirements 3.1, 3.3**

## Error Handling

### Pricing API Failures
- **Network errors**: Use cached data if available, otherwise use defaults
- **Invalid responses**: Log error details and use default pricing
- **Rate limiting**: Implement exponential backoff with maximum retry limit

### Data Validation Failures
- **Invalid pricing format**: Log warning and use default rate
- **Negative or zero rates**: Log error and use default rate
- **Missing pricing data**: Use instance-type-specific defaults

### Cache Management
- **Cache expiration**: Refresh stale entries (>24 hours old)
- **Cache size limits**: Implement LRU eviction if cache grows too large
- **Cache corruption**: Clear cache and rebuild from API calls

## Testing Strategy

### Unit Tests
- Test service suffix mapping for all job types
- Test pricing data validation with various input formats
- Test default rate fallback scenarios
- Test cache expiration and refresh logic

### Property-Based Tests
- **Minimum 100 iterations per property test**
- Generate random instance types and job types to test suffix mapping
- Generate various pricing API response formats to test validation
- Test cost calculation accuracy with random runtime and rate values

### Integration Tests
- Test actual AWS Pricing API calls with real instance types
- Verify end-to-end cost calculation with live AutoML job data
- Test error scenarios with mocked API failures

## Implementation Notes

### AWS Pricing API Specifics
- Service Code: "AmazonSageMaker"
- Instance Type Format: "{base_instance_type}-{service_suffix}"
- Required Filters: location, instanceType, tenancy
- Response Structure: OnDemand terms with nested price dimensions

### Performance Considerations
- Cache pricing data to minimize API calls
- Use async/concurrent pricing lookups when possible
- Implement circuit breaker pattern for API failures

### Monitoring and Logging
- Log all pricing API failures with instance type details
- Track cache hit/miss ratios
- Monitor default rate usage frequency
- Alert on excessive pricing API failures