# Requirements Document

## Introduction

The AutoML Job Cost Calculation Lambda function is currently returning $0.00 for all job costs because the AWS Pricing API integration is not working correctly. The pricing API requires specific instance type formats that include the SageMaker service type suffix (e.g., "ml.m5.12xlarge-Training" instead of "ml.m5.12xlarge").

## Glossary

- **Cost_Calculator**: The CalculateJobCostLambda function that calculates AutoML job costs
- **Pricing_API**: AWS Pricing API service for retrieving SageMaker instance pricing
- **Instance_Type**: SageMaker instance type identifier (e.g., ml.m5.12xlarge)
- **Service_Suffix**: SageMaker service type suffix (-Training, -Processing, -Transform)
- **Hourly_Rate**: Cost per hour for a specific instance type in USD

## Requirements

### Requirement 1: Accurate Pricing Retrieval

**User Story:** As a system administrator, I want AutoML job costs to be calculated accurately, so that I can track actual infrastructure expenses.

#### Acceptance Criteria

1. WHEN the Cost_Calculator queries the Pricing_API for a training job instance, THE system SHALL append "-Training" to the Instance_Type
2. WHEN the Cost_Calculator queries the Pricing_API for a processing job instance, THE system SHALL append "-Processing" to the Instance_Type  
3. WHEN the Cost_Calculator queries the Pricing_API for a transform job instance, THE system SHALL append "-Transform" to the Instance_Type
4. WHEN the Pricing_API returns valid pricing data, THE system SHALL extract the hourly rate correctly
5. WHEN the Pricing_API fails to return pricing data, THE system SHALL use a reasonable default rate and log the failure

### Requirement 2: Robust Error Handling

**User Story:** As a developer, I want the cost calculation to be resilient to pricing API failures, so that the system continues to function even when pricing data is unavailable.

#### Acceptance Criteria

1. WHEN the Pricing_API is unavailable, THE Cost_Calculator SHALL use default pricing rates
2. WHEN an unknown instance type is encountered, THE Cost_Calculator SHALL use a default rate and log the instance type
3. WHEN pricing lookup fails for any reason, THE Cost_Calculator SHALL continue processing other jobs
4. THE Cost_Calculator SHALL log all pricing lookup failures for debugging purposes

### Requirement 3: Cost Calculation Accuracy

**User Story:** As a business analyst, I want job costs to reflect actual AWS charges, so that I can make informed decisions about resource usage.

#### Acceptance Criteria

1. WHEN runtime hours are calculated correctly AND pricing is retrieved successfully, THE total cost SHALL equal runtime hours multiplied by hourly rate
2. WHEN multiple jobs of the same type use the same instance type, THE system SHALL cache pricing data to reduce API calls
3. THE Cost_Calculator SHALL round monetary values to 4 decimal places for accuracy
4. THE system SHALL validate that calculated costs are non-negative numbers

### Requirement 4: Pricing Data Validation

**User Story:** As a system administrator, I want to ensure pricing data is valid before using it for calculations, so that cost reports are reliable.

#### Acceptance Criteria

1. WHEN the Pricing_API returns pricing data, THE system SHALL validate that the price is a positive number
2. WHEN the pricing data format is unexpected, THE system SHALL log the error and use default pricing
3. THE system SHALL cache only validated pricing data
4. WHEN cached pricing data is older than 24 hours, THE system SHALL refresh it from the API