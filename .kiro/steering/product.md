---
inclusion: always
---

# Product Overview

ProsperModelsDB is a serverless machine learning workflow orchestration system that automates the end-to-end process of creating, training, and managing SageMaker AutoML jobs.

## Core Functionality

The system orchestrates ML model creation through a Step Functions workflow that:
- Retrieves feature lists from DynamoDB based on study configurations
- Processes raw survey/questionnaire data into modeling datasets
- Launches and monitors SageMaker AutoML jobs with custom feature specifications
- Tracks job status, costs, and results in DynamoDB
- Provides authenticated API access for users to submit requests and view results

## Key Components

- **API Gateway**: HTTP API with JWT authentication (Cognito) for workflow submission and data retrieval
- **Step Functions**: Orchestrates the multi-stage ML pipeline with comprehensive error handling
- **Lambda Functions**: Modular functions for data processing, feature engineering, and SageMaker integration
- **DynamoDB**: Stores feature lists, model requests, and job metadata
- **SageMaker AutoML**: Automated model training and selection
- **S3**: Storage for raw data, modeling data, and feature specifications

## User Workflow

1. User submits model request via API with study name, feature list, labels, and training plan
2. System retrieves feature definitions and processes raw data
3. Modeling data files are created and uploaded to S3
4. AutoML job is launched with feature specifications
5. System monitors job progress and calculates costs
6. Results and metadata are stored for user retrieval
