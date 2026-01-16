# Deployment Strategy Recommendations

## Problem Analysis

The recent issue where production API was calling the wrong Lambda function (`ModelRequestsAPI-ModelRequestsFunction-hZWTRpJpUXti` instead of `ProsperModelsDB-ModelRequestsFunction-8XYQcdpjcjLM`) highlights critical infrastructure management gaps:

1. **Duplicate Resources**: Multiple Lambda functions with similar names
2. **Inconsistent Naming**: No clear environment or service identification
3. **Manual Deployments**: Resources created outside of Infrastructure as Code
4. **Lack of Validation**: No automated checks to ensure correct resource targeting

## Immediate Action Items

### 1. Resource Inventory and Cleanup
- [ ] Audit all Lambda functions with pattern `*ModelRequests*` or `*ProsperModels*`
- [ ] Identify which API Gateways are actively used in production
- [ ] Document current resource dependencies and data flows
- [ ] Create migration plan to consolidate duplicate resources
- [ ] Remove unused/obsolete Lambda functions and API Gateways

### 2. Environment Separation Strategy
- **Dev**: `prosper-models-dev-*` 
- **Staging**: `prosper-models-staging-*`
- **Production**: `prosper-models-prod-*`

### 3. Standardized Naming Conventions

#### Lambda Functions
- Pattern: `{service}-{environment}-{function-purpose}`
- Examples:
  - `prosper-models-prod-api-handler`
  - `prosper-models-dev-data-processor`
  - `prosper-models-staging-feature-extractor`

#### API Gateways
- Pattern: `{service}-{environment}-api`
- Examples:
  - `prosper-models-prod-api`
  - `prosper-models-dev-api`

#### DynamoDB Tables
- Pattern: `{service}-{environment}-{table-purpose}`
- Examples:
  - `prosper-models-prod-main`
  - `prosper-models-dev-main`

### 4. Infrastructure as Code Enforcement

#### SAM Template Structure
```yaml
# template.yaml
Parameters:
  Environment:
    Type: String
    AllowedValues: [dev, staging, prod]
    Description: Deployment environment

Globals:
  Function:
    Environment:
      Variables:
        ENVIRONMENT: !Ref Environment
        SERVICE_NAME: prosper-models

Resources:
  ModelRequestsFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub "${AWS::StackName}-api-handler"
      # ... other properties
```

#### Environment-Specific Parameter Files
- `samconfig-dev.toml`
- `samconfig-staging.toml` 
- `samconfig-prod.toml`

### 5. Deployment Pipeline Implementation

```yaml
# .github/workflows/deploy.yml or similar
stages:
  - name: validate
    steps:
      - sam validate
      - cfn-lint template.yaml
      - run unit tests
      
  - name: deploy-dev
    steps:
      - sam deploy --config-env dev
      - run integration tests
      
  - name: deploy-staging
    condition: branch == main
    steps:
      - sam deploy --config-env staging
      - run e2e tests
      
  - name: deploy-production
    condition: manual approval
    steps:
      - sam deploy --config-env prod
      - run smoke tests
      - validate production endpoints
```

### 6. Monitoring and Validation

#### Resource Tagging Strategy
```yaml
Tags:
  Environment: !Ref Environment
  Service: prosper-models
  ManagedBy: sam
  Owner: data-team
```

#### Automated Validation Checks
- [ ] CloudWatch alarms for Lambda function invocations
- [ ] API Gateway endpoint health checks
- [ ] DynamoDB table access pattern monitoring
- [ ] Cross-reference API Gateway → Lambda function mappings

#### Production Validation Script
```python
# validate-production.py
def validate_api_endpoints():
    """Ensure API Gateway points to correct Lambda functions"""
    # Check API Gateway integration targets
    # Validate Lambda function names match expected pattern
    # Verify environment variables are correct
    pass

def validate_dynamodb_access():
    """Ensure Lambda functions can access correct DynamoDB tables"""
    # Test table permissions
    # Validate GSI configurations
    pass
```

### 7. Emergency Response Procedures

#### Rollback Strategy
1. Keep previous SAM deployment artifacts
2. Implement blue-green deployment for zero-downtime updates
3. Automated rollback triggers on error rate thresholds

#### Incident Response
1. **Detection**: CloudWatch alarms for API errors
2. **Diagnosis**: Automated checks to identify misconfigured resources
3. **Resolution**: Standardized runbooks for common issues
4. **Prevention**: Post-incident reviews and infrastructure updates

### 8. Team Processes

#### Code Review Requirements
- [ ] All infrastructure changes require peer review
- [ ] SAM template changes must include environment validation
- [ ] No manual resource creation in AWS console

#### Documentation Standards
- [ ] Maintain architecture decision records (ADRs)
- [ ] Document all API Gateway → Lambda mappings
- [ ] Keep deployment runbooks updated

#### Training and Knowledge Sharing
- [ ] Team training on SAM best practices
- [ ] Regular infrastructure review sessions
- [ ] Incident post-mortems with lessons learned

## Implementation Timeline

### Phase 1 (Week 1): Immediate Stabilization
- Complete resource inventory
- Implement production validation checks
- Document current state

### Phase 2 (Week 2-3): Standardization
- Implement naming conventions
- Consolidate duplicate resources
- Update SAM templates

### Phase 3 (Week 4-6): Automation
- Implement CI/CD pipeline
- Add monitoring and alerting
- Create rollback procedures

### Phase 4 (Ongoing): Maintenance
- Regular infrastructure reviews
- Continuous improvement of processes
- Team training and documentation updates