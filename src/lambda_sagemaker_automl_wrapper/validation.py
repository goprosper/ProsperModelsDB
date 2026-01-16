"""
Parameter validation and sanitization utilities.

This module provides comprehensive validation and sanitization for
AutoML job parameters to ensure security and correctness.
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when parameter validation fails."""
    pass


class S3ValidationError(ValidationError):
    """Raised when S3 URI validation fails."""
    pass


def validate_s3_uri(uri: str, parameter_name: str = "S3Uri") -> None:
    """
    Validate S3 URI format and structure.
    
    Args:
        uri: S3 URI to validate
        parameter_name: Name of the parameter for error messages
        
    Raises:
        S3ValidationError: If URI format is invalid
    """
    if not uri:
        raise S3ValidationError(f"{parameter_name} cannot be empty")
    
    if not uri.startswith('s3://'):
        raise S3ValidationError(f"{parameter_name} must start with 's3://': {uri}")
    
    # Parse the URI to validate structure
    try:
        parsed = urlparse(uri)
        if not parsed.netloc:  # bucket name
            raise S3ValidationError(f"{parameter_name} missing bucket name: {uri}")
        
        # Validate bucket name format (basic validation)
        bucket_name = parsed.netloc
        if not re.match(r'^[a-z0-9][a-z0-9.-]*[a-z0-9]$', bucket_name):
            if len(bucket_name) < 3 or len(bucket_name) > 63:
                raise S3ValidationError(f"{parameter_name} bucket name must be 3-63 characters: {bucket_name}")
            # Allow some flexibility for existing buckets that might not follow strict naming
            logger.warning(f"S3 bucket name may not follow strict naming conventions: {bucket_name}")
        
    except Exception as e:
        raise S3ValidationError(f"Invalid {parameter_name} format: {uri} - {str(e)}")


def validate_automl_job_name(job_name: str) -> None:
    """
    Validate AutoML job name format according to SageMaker requirements.
    
    Args:
        job_name: Job name to validate
        
    Raises:
        ValidationError: If job name format is invalid
    """
    if not job_name:
        raise ValidationError("AutoMLJobName cannot be empty")
    
    if len(job_name) < 1 or len(job_name) > 32:
        raise ValidationError(f"AutoMLJobName must be 1-32 characters long: {job_name}")
    
    if not re.match(r'^[a-zA-Z0-9](-*[a-zA-Z0-9]){0,31}$', job_name):
        raise ValidationError(
            f"AutoMLJobName must contain only alphanumeric characters and hyphens, "
            f"cannot start or end with hyphen: {job_name}"
        )


def validate_iam_role_arn(role_arn: str) -> None:
    """
    Validate IAM role ARN format.
    
    Args:
        role_arn: IAM role ARN to validate
        
    Raises:
        ValidationError: If role ARN format is invalid
    """
    if not role_arn:
        raise ValidationError("RoleArn cannot be empty")
    
    # Basic ARN format validation
    arn_pattern = r'^arn:aws:iam::\d{12}:role/[a-zA-Z0-9+=,.@_-]+$'
    if not re.match(arn_pattern, role_arn):
        raise ValidationError(f"Invalid RoleArn format: {role_arn}")


def validate_problem_type(problem_type: Optional[str]) -> None:
    """
    Validate problem type if provided.
    
    Args:
        problem_type: Problem type to validate
        
    Raises:
        ValidationError: If problem type is invalid
    """
    if problem_type is None:
        return
    
    valid_types = ["BinaryClassification", "MulticlassClassification", "Regression"]
    if problem_type not in valid_types:
        raise ValidationError(f"Invalid ProblemType: {problem_type}. Must be one of: {valid_types}")


def validate_metric_name(metric_name: Optional[str]) -> None:
    """
    Validate metric name if provided.
    
    Args:
        metric_name: Metric name to validate
        
    Raises:
        ValidationError: If metric name is invalid
    """
    if metric_name is None:
        return
    
    # Common SageMaker AutoML metrics
    valid_metrics = [
        "Accuracy", "AUC", "F1", "F1macro", "MSE", "MAE", "R2", "RMSE",
        "Precision", "PrecisionMacro", "Recall", "RecallMacro"
    ]
    
    if metric_name not in valid_metrics:
        logger.warning(f"Metric name '{metric_name}' not in common list, but allowing it")


def validate_model_training_plan(training_plan: Optional[str]) -> None:
    """
    Validate model training plan parameter.
    
    Args:
        training_plan: Training plan to validate
        
    Raises:
        ValidationError: If training plan is invalid
    """
    if training_plan is None:
        return
    
    valid_plans = ["Test", "Bronze", "Silver", "Gold"]
    if training_plan not in valid_plans:
        raise ValidationError(f"Invalid modelTrainingPlan: {training_plan}. Must be one of: {valid_plans}")


def validate_completion_criteria(criteria: Optional[Dict[str, Any]]) -> None:
    """
    Validate completion criteria parameters.
    
    Args:
        criteria: Completion criteria to validate
        
    Raises:
        ValidationError: If criteria values are invalid
    """
    if criteria is None:
        return
    
    max_candidates = criteria.get('MaxCandidates')
    if max_candidates is not None:
        if not isinstance(max_candidates, int) or max_candidates < 1 or max_candidates > 250:
            raise ValidationError(f"MaxCandidates must be between 1 and 250: {max_candidates}")
    
    max_runtime_per_job = criteria.get('MaxRuntimePerTrainingJobInSeconds')
    if max_runtime_per_job is not None:
        if not isinstance(max_runtime_per_job, int) or max_runtime_per_job < 1:
            raise ValidationError(f"MaxRuntimePerTrainingJobInSeconds must be positive: {max_runtime_per_job}")
    
    max_automl_runtime = criteria.get('MaxAutoMLJobRuntimeInSeconds')
    if max_automl_runtime is not None:
        if not isinstance(max_automl_runtime, int) or max_automl_runtime < 1:
            raise ValidationError(f"MaxAutoMLJobRuntimeInSeconds must be positive: {max_automl_runtime}")


def sanitize_string_value(value: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize string value to prevent injection attacks.
    
    Args:
        value: String value to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string value
    """
    if not isinstance(value, str):
        return str(value)
    
    # Remove null bytes and control characters except common whitespace
    sanitized = ''.join(char for char in value if ord(char) >= 32 or char in '\t\n\r')
    
    # Trim whitespace
    sanitized = sanitized.strip()
    
    # Apply length limit if specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
        logger.warning(f"String value truncated to {max_length} characters")
    
    return sanitized


def sanitize_parameters(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively sanitize all string parameters in the input data.
    
    Args:
        data: Input data dictionary
        
    Returns:
        Sanitized data dictionary
    """
    import copy
    
    def sanitize_recursive(obj):
        if isinstance(obj, dict):
            return {key: sanitize_recursive(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [sanitize_recursive(item) for item in obj]
        elif isinstance(obj, str):
            return sanitize_string_value(obj)
        else:
            return obj
    
    return sanitize_recursive(copy.deepcopy(data))


def validate_input_data_config(input_configs: List[Dict[str, Any]]) -> None:
    """
    Validate input data configuration list.
    
    Args:
        input_configs: List of input data configurations
        
    Raises:
        ValidationError: If configuration is invalid
    """
    if not input_configs:
        raise ValidationError("InputDataConfig cannot be empty")
    
    if not isinstance(input_configs, list):
        raise ValidationError("InputDataConfig must be a list")
    
    for i, config in enumerate(input_configs):
        if not isinstance(config, dict):
            raise ValidationError(f"InputDataConfig[{i}] must be a dictionary")
        
        # Validate required fields
        if 'TargetAttributeName' not in config:
            raise ValidationError(f"Missing TargetAttributeName in InputDataConfig[{i}]")
        
        if 'DataSource' not in config:
            raise ValidationError(f"Missing DataSource in InputDataConfig[{i}]")
        
        # Validate DataSource structure
        data_source = config['DataSource']
        if not isinstance(data_source, dict):
            raise ValidationError(f"DataSource in InputDataConfig[{i}] must be a dictionary")
        
        if 'S3DataSource' not in data_source:
            raise ValidationError(f"Missing S3DataSource in InputDataConfig[{i}].DataSource")
        
        s3_data_source = data_source['S3DataSource']
        if not isinstance(s3_data_source, dict):
            raise ValidationError(f"S3DataSource in InputDataConfig[{i}] must be a dictionary")
        
        if 'S3Uri' not in s3_data_source:
            raise ValidationError(f"Missing S3Uri in InputDataConfig[{i}].DataSource.S3DataSource")
        
        # Validate S3 URI
        validate_s3_uri(s3_data_source['S3Uri'], f"InputDataConfig[{i}].DataSource.S3DataSource.S3Uri")
        
        # Validate S3DataType if present
        s3_data_type = s3_data_source.get('S3DataType')
        if s3_data_type:
            valid_types = ['S3Prefix', 'ManifestFile', 'AugmentedManifestFile']
            if s3_data_type not in valid_types:
                raise ValidationError(f"Invalid S3DataType in InputDataConfig[{i}]: {s3_data_type}")


def validate_output_data_config(output_config: Dict[str, Any]) -> None:
    """
    Validate output data configuration.
    
    Args:
        output_config: Output data configuration
        
    Raises:
        ValidationError: If configuration is invalid
    """
    if not isinstance(output_config, dict):
        raise ValidationError("OutputDataConfig must be a dictionary")
    
    if 'S3OutputPath' not in output_config:
        raise ValidationError("Missing S3OutputPath in OutputDataConfig")
    
    validate_s3_uri(output_config['S3OutputPath'], "OutputDataConfig.S3OutputPath")


def validate_automl_job_request(data: Dict[str, Any]) -> None:
    """
    Comprehensive validation of AutoML job request parameters.
    
    Args:
        data: Complete AutoML job request data
        
    Raises:
        ValidationError: If any validation fails
    """
    logger.info("Starting comprehensive parameter validation")
    
    # Validate required parameters
    required_fields = ['AutoMLJobName', 'InputDataConfig', 'OutputDataConfig', 'RoleArn']
    for field in required_fields:
        if field not in data or data[field] is None:
            raise ValidationError(f"Missing required parameter: {field}")
    
    # Validate individual components
    validate_automl_job_name(data['AutoMLJobName'])
    validate_iam_role_arn(data['RoleArn'])
    validate_input_data_config(data['InputDataConfig'])
    validate_output_data_config(data['OutputDataConfig'])
    
    # Validate optional parameters
    if 'ProblemType' in data:
        validate_problem_type(data['ProblemType'])
    
    if 'modelTrainingPlan' in data:
        validate_model_training_plan(data['modelTrainingPlan'])
    
    if 'AutoMLJobObjective' in data and data['AutoMLJobObjective']:
        objective = data['AutoMLJobObjective']
        if isinstance(objective, dict) and 'MetricName' in objective:
            validate_metric_name(objective['MetricName'])
    
    if 'AutoMLJobConfig' in data and data['AutoMLJobConfig']:
        config = data['AutoMLJobConfig']
        if isinstance(config, dict):
            if 'CompletionCriteria' in config:
                validate_completion_criteria(config['CompletionCriteria'])
            
            if 'CandidateGenerationConfig' in config and config['CandidateGenerationConfig']:
                candidate_config = config['CandidateGenerationConfig']
                if isinstance(candidate_config, dict) and 'FeatureSpecificationS3Uri' in candidate_config:
                    feature_uri = candidate_config['FeatureSpecificationS3Uri']
                    if feature_uri:
                        validate_s3_uri(feature_uri, "FeatureSpecificationS3Uri")
    
    logger.info("Parameter validation completed successfully")