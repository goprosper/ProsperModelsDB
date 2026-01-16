"""
Data models for SageMaker AutoML job parameters.

These models define the structure and validation for input parameters
that will be passed to the SageMaker CreateAutoMLJob API.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
import re


@dataclass
class S3DataSource:
    """S3 data source configuration."""
    S3DataType: str  # "S3Prefix", "ManifestFile", "AugmentedManifestFile"
    S3Uri: str
    
    def __post_init__(self):
        """Validate S3 URI format."""
        if not self.S3Uri.startswith('s3://'):
            raise ValueError(f"Invalid S3 URI format: {self.S3Uri}")


@dataclass
class DataSource:
    """Data source configuration."""
    S3DataSource: S3DataSource


@dataclass
class InputDataConfig:
    """Input data configuration for AutoML job."""
    DataSource: DataSource
    TargetAttributeName: str
    ChannelType: Optional[str] = None  # "training", "validation"
    CompressionType: Optional[str] = None  # "None", "Gzip"
    ContentType: Optional[str] = None  # "text/csv", "application/x-parquet"
    SampleWeightAttributeName: Optional[str] = None


@dataclass
class OutputDataConfig:
    """Output data configuration for AutoML job."""
    S3OutputPath: str
    KmsKeyId: Optional[str] = None
    
    def __post_init__(self):
        """Validate S3 output path format."""
        if not self.S3OutputPath.startswith('s3://'):
            raise ValueError(f"Invalid S3 output path format: {self.S3OutputPath}")


@dataclass
class AutoMLJobObjective:
    """AutoML job optimization objective."""
    MetricName: str  # "Accuracy", "AUC", "F1", "F1macro", "MSE", etc.


@dataclass
class CompletionCriteria:
    """Completion criteria for AutoML job."""
    MaxCandidates: Optional[int] = None
    MaxRuntimePerTrainingJobInSeconds: Optional[int] = None
    MaxAutoMLJobRuntimeInSeconds: Optional[int] = None


@dataclass
class AlgorithmConfig:
    """Algorithm configuration for candidate generation."""
    AutoMLAlgorithms: List[str] = field(default_factory=list)


@dataclass
class CandidateGenerationConfig:
    """Configuration for candidate generation."""
    FeatureSpecificationS3Uri: Optional[str] = None
    AlgorithmsConfig: Optional[List[AlgorithmConfig]] = None
    
    def __post_init__(self):
        """Validate feature specification S3 URI if provided."""
        if self.FeatureSpecificationS3Uri and not self.FeatureSpecificationS3Uri.startswith('s3://'):
            raise ValueError(f"Invalid FeatureSpecificationS3Uri format: {self.FeatureSpecificationS3Uri}")


@dataclass
class DataSplitConfig:
    """Data split configuration."""
    ValidationFraction: Optional[float] = None


@dataclass
class VpcConfig:
    """VPC configuration for security."""
    SecurityGroupIds: List[str] = field(default_factory=list)
    Subnets: List[str] = field(default_factory=list)


@dataclass
class SecurityConfig:
    """Security configuration for AutoML job."""
    EnableInterContainerTrafficEncryption: Optional[bool] = None
    VolumeKmsKeyId: Optional[str] = None
    VpcConfig: Optional[VpcConfig] = None


@dataclass
class AutoMLJobConfig:
    """AutoML job configuration."""
    CompletionCriteria: Optional[CompletionCriteria] = None
    CandidateGenerationConfig: Optional[CandidateGenerationConfig] = None
    DataSplitConfig: Optional[DataSplitConfig] = None
    Mode: Optional[str] = None  # "AUTO", "ENSEMBLING", "HYPERPARAMETER_TUNING"
    SecurityConfig: Optional[SecurityConfig] = None


@dataclass
class ModelDeployConfig:
    """Model deployment configuration."""
    AutoGenerateEndpointName: Optional[bool] = None
    EndpointName: Optional[str] = None


@dataclass
class Tag:
    """Resource tag."""
    Key: str
    Value: str


@dataclass
class AutoMLJobRequest:
    """Complete AutoML job request structure."""
    AutoMLJobName: str
    InputDataConfig: List[InputDataConfig]
    OutputDataConfig: OutputDataConfig
    RoleArn: str
    AutoMLJobObjective: Optional[AutoMLJobObjective] = None
    ProblemType: Optional[str] = None  # "BinaryClassification", "MulticlassClassification", "Regression"
    AutoMLJobConfig: Optional[AutoMLJobConfig] = None
    GenerateCandidateDefinitionsOnly: Optional[bool] = None
    ModelDeployConfig: Optional[ModelDeployConfig] = None
    Tags: Optional[List[Tag]] = None
    
    def __post_init__(self):
        """Validate required parameters and formats."""
        # Validate job name format (SageMaker requirements)
        if not re.match(r'^[a-zA-Z0-9](-*[a-zA-Z0-9]){0,31}$', self.AutoMLJobName):
            raise ValueError(f"Invalid AutoMLJobName format: {self.AutoMLJobName}")
        
        # Validate role ARN format
        if not self.RoleArn.startswith('arn:aws:iam::'):
            raise ValueError(f"Invalid RoleArn format: {self.RoleArn}")
        
        # Validate input data config is not empty
        if not self.InputDataConfig:
            raise ValueError("InputDataConfig cannot be empty")


@dataclass
class AutoMLJobResponse:
    """Response from AutoML job creation."""
    AutoMLJobArn: str


def validate_required_parameters(data: Dict[str, Any]) -> None:
    """
    Validate that all required parameters are present.
    
    Args:
        data: Input data dictionary
        
    Raises:
        ValueError: If required parameters are missing
    """
    required_fields = ['AutoMLJobName', 'InputDataConfig', 'OutputDataConfig', 'RoleArn']
    
    for field in required_fields:
        if field not in data or data[field] is None:
            raise ValueError(f"Missing required parameter: {field}")
    
    # Validate InputDataConfig structure
    if not isinstance(data['InputDataConfig'], list) or len(data['InputDataConfig']) == 0:
        raise ValueError("InputDataConfig must be a non-empty list")
    
    for i, input_config in enumerate(data['InputDataConfig']):
        if 'TargetAttributeName' not in input_config:
            raise ValueError(f"Missing TargetAttributeName in InputDataConfig[{i}]")
        if 'DataSource' not in input_config:
            raise ValueError(f"Missing DataSource in InputDataConfig[{i}]")


def sanitize_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize input data to prevent injection attacks.
    
    Args:
        data: Input data dictionary
        
    Returns:
        Sanitized data dictionary
    """
    # Create a deep copy to avoid modifying original
    import copy
    sanitized = copy.deepcopy(data)
    
    # Remove any potentially dangerous characters from string fields
    def sanitize_string(value: str) -> str:
        if not isinstance(value, str):
            return value
        # Remove null bytes and control characters
        return ''.join(char for char in value if ord(char) >= 32 or char in '\t\n\r')
    
    def sanitize_recursive(obj):
        if isinstance(obj, dict):
            return {key: sanitize_recursive(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [sanitize_recursive(item) for item in obj]
        elif isinstance(obj, str):
            return sanitize_string(obj)
        else:
            return obj
    
    return sanitize_recursive(sanitized)