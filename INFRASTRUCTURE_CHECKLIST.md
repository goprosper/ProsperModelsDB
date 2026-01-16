# Infrastructure Change Checklist

Use this checklist for all infrastructure changes to prevent issues like API Gateways pointing to wrong Lambda functions.

## Pre-Deployment Checklist

### 📋 Planning Phase
- [ ] **Environment identified**: Clearly specify target environment (dev/staging/prod)
- [ ] **Naming convention verified**: All resources follow `{service}-{environment}-{purpose}` pattern
- [ ] **Dependencies mapped**: Identify all resources that will be created/modified
- [ ] **Rollback plan prepared**: Document how to revert changes if needed

### 🔍 Code Review Phase
- [ ] **SAM template validated**: Run `sam validate` on all templates
- [ ] **Resource names consistent**: Check naming follows established conventions
- [ ] **Environment variables correct**: Verify TABLE_NAME, GSI_NAME, etc. match environment
- [ ] **No hardcoded values**: Ensure no environment-specific values are hardcoded
- [ ] **Parameter files updated**: Verify samconfig-{env}.toml files are correct

### 🧪 Pre-Deployment Testing
- [ ] **Local validation passed**: Run `./scripts/validate.sh {environment}`
- [ ] **Template linting passed**: Run `cfn-lint template.yaml`
- [ ] **Security scan passed**: Run security validation tools
- [ ] **Unit tests passed**: Ensure all Lambda function tests pass

## Deployment Checklist

### 🚀 Deployment Phase
- [ ] **Correct environment targeted**: Double-check samconfig file and parameters
- [ ] **Backup created**: Document current state for rollback
- [ ] **Deployment command verified**: Confirm `sam deploy --config-env {environment}`
- [ ] **Deployment logs monitored**: Watch for errors during deployment

### ✅ Post-Deployment Verification
- [ ] **Infrastructure validation passed**: Run `./scripts/validate.sh {environment}`
- [ ] **API endpoints responding**: Test all API Gateway endpoints
- [ ] **Lambda functions working**: Verify functions can be invoked
- [ ] **Database connections working**: Test DynamoDB access
- [ ] **Integration tests passed**: Run end-to-end tests

## Critical Validation Points

### 🎯 API Gateway → Lambda Integration
- [ ] **Correct function targeted**: API Gateway points to intended Lambda function
- [ ] **Function name matches environment**: Lambda function name includes correct environment
- [ ] **Permissions configured**: API Gateway has invoke permissions for Lambda
- [ ] **Response format correct**: API returns expected data structure

### 🗄️ Lambda → DynamoDB Integration  
- [ ] **Correct table targeted**: Lambda uses TABLE_NAME for intended environment
- [ ] **GSI configuration correct**: GSI_NAME matches table configuration
- [ ] **Permissions configured**: Lambda has read/write permissions for table
- [ ] **Attribute projection correct**: Lambda queries return all required attributes

### 🏷️ Resource Naming and Tagging
- [ ] **Naming convention followed**: All resources use standardized naming
- [ ] **Environment tags applied**: Resources tagged with correct environment
- [ ] **Service tags applied**: Resources tagged with service name
- [ ] **Owner tags applied**: Resources tagged with team/owner information

## Environment-Specific Checks

### 🧪 Development Environment
- [ ] **Isolated from other environments**: No cross-environment dependencies
- [ ] **Test data available**: Sample data loaded for testing
- [ ] **Debug logging enabled**: Enhanced logging for troubleshooting
- [ ] **Cost optimization**: Use minimal instance sizes and configurations

### 🎭 Staging Environment
- [ ] **Production-like configuration**: Mirrors production setup
- [ ] **Performance testing ready**: Configured for load testing
- [ ] **Data migration tested**: Verify data migration scripts work
- [ ] **Monitoring configured**: CloudWatch alarms and dashboards set up

### 🏭 Production Environment
- [ ] **High availability configured**: Multi-AZ deployment where applicable
- [ ] **Monitoring and alerting active**: All critical alarms configured
- [ ] **Backup and recovery tested**: Verify backup procedures work
- [ ] **Security hardened**: All security best practices applied
- [ ] **Change window scheduled**: Deployment during approved maintenance window

## Rollback Procedures

### 🔄 If Issues Detected
1. **Stop deployment immediately**
2. **Run validation script**: `./scripts/validate.sh {environment}`
3. **Check CloudWatch logs**: Look for error patterns
4. **Verify API responses**: Test critical endpoints
5. **Execute rollback plan**: Revert to previous known-good state

### 📞 Escalation Criteria
Escalate immediately if:
- [ ] **Critical APIs not responding**: 5xx errors or timeouts
- [ ] **Data corruption detected**: Incorrect data returned from APIs
- [ ] **Cross-environment contamination**: Resources pointing to wrong environment
- [ ] **Security issues identified**: Unauthorized access or data exposure

## Post-Deployment Tasks

### 📊 Monitoring Setup
- [ ] **CloudWatch dashboards updated**: Include new resources
- [ ] **Alarms configured**: Set up error rate and latency alarms
- [ ] **Log aggregation working**: Logs flowing to centralized system
- [ ] **Performance baselines established**: Document normal operating metrics

### 📚 Documentation Updates
- [ ] **Architecture diagrams updated**: Reflect new resource relationships
- [ ] **Runbooks updated**: Include new operational procedures
- [ ] **Team knowledge shared**: Brief team on changes made
- [ ] **Lessons learned documented**: Record any issues and solutions

## Automation Integration

### 🤖 CI/CD Pipeline
- [ ] **Validation integrated**: Pipeline runs infrastructure validation
- [ ] **Automated testing**: Integration tests run after deployment
- [ ] **Approval gates configured**: Manual approval required for production
- [ ] **Rollback automation**: Automated rollback on failure detection

### 📈 Continuous Monitoring
- [ ] **Daily validation scheduled**: Automated infrastructure checks
- [ ] **Drift detection enabled**: Monitor for manual changes
- [ ] **Cost monitoring active**: Track resource costs and usage
- [ ] **Security scanning scheduled**: Regular security assessments

## Team Responsibilities

### 👥 Developer Responsibilities
- [ ] Follow naming conventions
- [ ] Run local validation before committing
- [ ] Write comprehensive tests
- [ ] Document changes clearly

### 🔧 DevOps Responsibilities  
- [ ] Review infrastructure changes
- [ ] Maintain deployment pipelines
- [ ] Monitor system health
- [ ] Manage environment configurations

### 🛡️ Security Team Responsibilities
- [ ] Review security configurations
- [ ] Validate access controls
- [ ] Monitor for security issues
- [ ] Maintain compliance standards

---

## Quick Reference Commands

```bash
# Validate before deployment
./scripts/validate.sh {environment}

# Deploy with validation
sam validate && sam deploy --config-env {environment}

# Verify after deployment  
./scripts/validate.sh {environment}

# Check specific resource
aws lambda get-function --function-name {function-name}
aws apigateway get-rest-apis
aws dynamodb describe-table --table-name {table-name}
```

## Emergency Contacts

- **On-call Engineer**: [Contact information]
- **Team Lead**: [Contact information]  
- **AWS Support**: [Support case process]
- **Security Team**: [Security incident process]

---

**Remember**: When in doubt, validate twice and deploy once! 🚀