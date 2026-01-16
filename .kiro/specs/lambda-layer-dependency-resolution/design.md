# Lambda Layer Dependency Resolution - Design

## Architecture Overview

### Current State (Before Fix)
```
CreateModelingDataFunction
├── Runtime: Python 3.13
├── Code: src-minimal/CreateModelingData.py
├── Layer: AWS Managed Pandas Layer
│   ├── ✅ pandas==2.3.3
│   ├── ✅ numpy==2.3.5
│   ├── ❌ fsspec (missing)
│   └── ❌ s3fs (missing)
└── Result: ImportError when accessing S3 URLs
```

### Target State (After Fix)
```
CreateModelingDataFunction
├── Runtime: Python 3.13
├── Code: src-minimal/CreateModelingData.py
├── Layer 1: AWS Managed Pandas Layer
│   ├── ✅ pandas==2.3.3
│   ├── ✅ numpy==2.3.5
│   └── ✅ boto3, botocore, etc.
├── Layer 2: Custom S3 Dependencies Layer
│   ├── ✅ fsspec==2024.12.0
│   └── ✅ s3fs==2024.12.0
└── Result: ✅ Full S3 support for pandas
```

## Design Decisions

### Decision 1: Hybrid Layer Approach
**Chosen**: Use AWS managed layer + custom supplementary layer  
**Alternatives Considered**:
- Single custom layer with all dependencies
- Modify code to use boto3 instead of direct S3 URLs
- Find different AWS managed layer with fsspec

**Rationale**: 
- Minimizes custom layer size (only 2 packages vs 20+)
- Leverages AWS managed layer for core dependencies
- Maintains existing code patterns
- Reduces build time and deployment size

### Decision 2: Minimal Supplementary Layer
**Chosen**: Include only fsspec and s3fs in custom layer  
**Alternatives Considered**:
- Include all data processing dependencies
- Include additional S3-related packages

**Rationale**:
- Addresses the specific missing dependencies
- Keeps layer size minimal for faster deployments
- Reduces maintenance burden
- Clear separation of concerns

### Decision 3: Version Pinning
**Chosen**: Pin fsspec==2024.12.0 and s3fs==2024.12.0  
**Alternatives Considered**:
- Use latest versions without pinning
- Use version ranges

**Rationale**:
- Ensures reproducible builds
- Matches versions that work with pandas 2.3.3
- Prevents unexpected breaking changes
- Consistent with existing requirements.txt pattern

## Implementation Strategy

### Phase 1: Layer Creation
1. Create `layers/s3-dependencies/requirements.txt` with minimal dependencies
2. Update CloudFormation template to define S3DependenciesLayer
3. Configure layer with Python 3.13 compatibility

### Phase 2: Function Update
1. Update CreateModelingDataFunction to reference both layers
2. Maintain existing environment variables (PYTHONPATH)
3. Preserve all existing function configuration

### Phase 3: Deployment
1. SAM build to create both layers
2. SAM deploy to update CloudFormation stack
3. Verify layer creation and function update

### Phase 4: Validation
1. Test import capabilities
2. Test functional behavior
3. Verify error resolution

## Technical Specifications

### Layer Configuration
```yaml
S3DependenciesLayer:
  Type: AWS::Serverless::LayerVersion
  Properties:
    LayerName: !Sub "S3DependenciesLayer-v${DeploymentVersion}"
    Description: S3 file access dependencies (fsspec, s3fs) to supplement AWS pandas layer
    ContentUri: layers/s3-dependencies/
    CompatibleRuntimes:
      - python3.13
    RetentionPolicy: Retain
  Metadata:
    BuildMethod: python3.13
```

### Function Configuration
```yaml
CreateModelingDataFunction:
  Type: AWS::Serverless::Function
  Properties:
    Runtime: python3.13
    Handler: CreateModelingData.lambda_handler
    CodeUri: src-minimal/
    Layers:
      - arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python313:5  # AWS managed
      - !Ref S3DependenciesLayer  # Custom supplementary
    Environment:
      Variables:
        PYTHONPATH: /opt/python
```

### Dependency Specifications
```txt
# layers/s3-dependencies/requirements.txt
fsspec==2024.12.0
s3fs==2024.12.0
```

## Error Handling

### Before Fix
```python
# Error pattern that was occurring
ImportError: Missing optional dependency 'fsspec'. 
Use pip or conda to install fsspec.
```

### After Fix
```python
# Expected behavior - function progresses to data validation
DataValidationError: File validation failed for data_file: Required data_file not found
```

## Performance Considerations

### Layer Size Impact
- AWS Managed Layer: ~50MB (pandas, numpy, etc.)
- Custom S3 Layer: ~5MB (fsspec, s3fs only)
- Total: ~55MB (vs ~70MB for single custom layer)

### Cold Start Impact
- Minimal additional overhead from second layer
- Faster than single large custom layer
- Leverages AWS managed layer caching

### Build Time Impact
- Custom layer builds only 2 packages
- Significantly faster than building pandas/numpy
- Parallel layer building in SAM

## Monitoring and Validation

### Success Metrics
1. **Import Success**: Function can import pandas with S3 support
2. **Functional Success**: FeatureType processing works correctly
3. **Error Elimination**: No more fsspec dependency errors
4. **Performance**: No significant cold start degradation

### Validation Tests
1. **test-import-only.py**: Verifies import capabilities
2. **test-feature-get-value.py**: Verifies functional behavior
3. **Integration tests**: End-to-end workflow validation

### Monitoring Points
- CloudWatch logs for import errors
- Function execution duration
- Error rates and types
- Layer usage metrics

## Rollback Strategy

### If Issues Occur
1. **Immediate**: Revert to single AWS managed layer (will restore fsspec error but function won't crash)
2. **Alternative**: Switch to boto3-based file access pattern
3. **Fallback**: Use single custom layer with all dependencies

### Rollback Commands
```bash
# Remove custom layer from function
sam deploy --parameter-overrides UseCustomLayer=false

# Or revert entire stack
aws cloudformation update-stack --stack-name ProsperModelsDB --use-previous-template
```

## Future Considerations

### Maintenance
- Monitor for AWS managed layer updates
- Update fsspec/s3fs versions as needed
- Consider consolidation if AWS adds fsspec to managed layer

### Optimization Opportunities
- Evaluate other AWS managed layers
- Consider layer sharing across functions
- Monitor for pandas S3 API changes