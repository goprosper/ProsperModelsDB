# Infrastructure Validation Tools

This directory contains tools to validate and monitor AWS infrastructure to prevent configuration issues like API Gateways pointing to wrong Lambda functions.

## Quick Start

```bash
# Validate production environment
./scripts/validate.sh prod

# Validate all environments
./scripts/validate.sh all

# Validate specific environment with Python directly
python scripts/validate-infrastructure.py --environment staging
```

## Tools Overview

### 1. `validate-infrastructure.py`
Comprehensive Python script that validates:
- **Lambda Functions**: Naming conventions, environment variables, duplicates
- **API Gateways**: Naming conventions, Lambda integrations
- **DynamoDB Tables**: Naming conventions, environment alignment

**Features:**
- Detects duplicate resources that could cause confusion
- Validates naming conventions across all resource types
- Checks API Gateway → Lambda function mappings
- Identifies cross-environment resource references
- Provides actionable error messages with severity levels

### 2. `validate.sh`
Simple shell wrapper that:
- Checks prerequisites (Python 3, boto3)
- Provides user-friendly interface
- Handles error reporting

### 3. GitHub Actions Workflow
Automated validation that runs:
- On template changes (push/PR)
- Daily scheduled checks for configuration drift
- Manual triggers with environment selection
- Security scans with cfn-lint and cfn_nag

## Validation Categories

### Critical Issues ❌
Issues that could cause production outages:
- API Gateway pointing to wrong Lambda function
- Lambda function accessing wrong DynamoDB table
- Cross-environment resource references

### Warnings ⚠️
Issues that violate conventions but don't break functionality:
- Inconsistent naming conventions
- Missing environment tags
- Suboptimal configurations

### Info ℹ️
Successful validations and helpful information:
- Resources following naming conventions
- Correct integrations
- Environment alignment

## Prerequisites

### Local Development
```bash
# Install Python dependencies
pip install boto3 botocore

# Configure AWS credentials
aws configure
# OR use environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

### CI/CD Pipeline
The GitHub Actions workflow requires:
- AWS OIDC role configured in repository secrets as `AWS_ROLE_ARN`
- Role must have permissions to list and describe:
  - Lambda functions
  - API Gateways (REST and HTTP)
  - DynamoDB tables

## Usage Examples

### Development Workflow
```bash
# Before deploying changes
./scripts/validate.sh dev

# After deployment
./scripts/validate.sh dev

# Before promoting to production
./scripts/validate.sh all
```

### Troubleshooting Production Issues
```bash
# Check if API Gateway points to correct Lambda
python scripts/validate-infrastructure.py --environment prod

# Look for duplicate resources
python scripts/validate-infrastructure.py --all-environments | grep "Duplicate"
```

### Monitoring Configuration Drift
The GitHub Actions workflow runs daily to catch:
- Manual changes made outside of Infrastructure as Code
- Resource naming inconsistencies
- Cross-environment contamination

## Common Issues and Solutions

### Issue: API Gateway points to wrong Lambda function
**Detection:** Critical error in validation output
**Solution:** 
1. Check API Gateway integrations in AWS Console
2. Update SAM template to use correct function reference
3. Redeploy with `sam deploy`

### Issue: Duplicate Lambda functions
**Detection:** Critical error about duplicate functions
**Solution:**
1. Identify which function is actively used
2. Update API Gateway to point to correct function
3. Delete unused function after verification

### Issue: Inconsistent naming conventions
**Detection:** Warning about naming convention violations
**Solution:**
1. Update SAM template with standardized names
2. Deploy with new names
3. Update any hardcoded references

## Integration with Deployment Pipeline

### Pre-deployment Validation
```yaml
# In your deployment workflow
- name: Validate infrastructure
  run: python scripts/validate-infrastructure.py --environment ${{ env.ENVIRONMENT }}
```

### Post-deployment Verification
```yaml
# After SAM deploy
- name: Verify deployment
  run: |
    sleep 30  # Allow resources to stabilize
    python scripts/validate-infrastructure.py --environment ${{ env.ENVIRONMENT }}
```

## Extending the Validation

### Adding New Resource Types
1. Add validation method to `InfrastructureValidator` class
2. Call from `validate_environment()` method
3. Follow existing pattern for issue categorization

### Custom Validation Rules
```python
def _validate_custom_resource(self, environment: str) -> Dict[str, List[str]]:
    """Add custom validation logic here."""
    issues = {'critical': [], 'warnings': [], 'info': []}
    
    # Your validation logic
    
    return issues
```

### Environment-Specific Rules
```python
# In validation methods
if environment == 'prod':
    # Stricter validation for production
    pass
elif environment == 'dev':
    # More lenient validation for development
    pass
```

## Best Practices

1. **Run validation before every deployment**
2. **Address critical issues immediately**
3. **Fix warnings during regular maintenance**
4. **Review validation results in PR reviews**
5. **Monitor daily validation reports**
6. **Update validation rules as infrastructure evolves**

## Troubleshooting

### Permission Issues
```bash
# Check AWS credentials
aws sts get-caller-identity

# Test specific permissions
aws lambda list-functions --max-items 1
aws apigateway get-rest-apis --limit 1
aws dynamodb list-tables --limit 1
```

### Script Errors
```bash
# Run with debug output
python -v scripts/validate-infrastructure.py --environment dev

# Check dependencies
python -c "import boto3; print(boto3.__version__)"
```

### GitHub Actions Failures
1. Check AWS OIDC role permissions
2. Verify role ARN in repository secrets
3. Check workflow logs for specific error messages
4. Ensure SAM CLI installation succeeds

## Support

For issues with the validation tools:
1. Check this README for common solutions
2. Review validation output for specific error messages
3. Check AWS CloudTrail for permission issues
4. Consult team documentation for environment-specific configurations