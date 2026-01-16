"""
SageMaker client wrapper for AutoML job operations.

This module provides a wrapper around the boto3 SageMaker client with
parameter mapping and error handling specific to AutoML job creation.
"""

import boto3
import logging
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)


class SageMakerClientError(Exception):
    """Raised when SageMaker API calls fail."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.error_code = error_code
        self.original_error = original_error


class SageMakerAutoMLClient:
    """
    Wrapper for SageMaker client focused on AutoML operations.
    
    This class handles parameter mapping, error handling, and retry logic
    for SageMaker AutoML job creation.
    """
    
    def __init__(self, region_name: Optional[str] = None):
        """
        Initialize SageMaker client.
        
        Args:
            region_name: AWS region name (defaults to Lambda's region)
        """
        try:
            self.client = boto3.client('sagemaker', region_name=region_name)
            logger.info(f"SageMaker client initialized for region: {region_name or 'default'}")
        except Exception as e:
            logger.error(f"Failed to initialize SageMaker client: {str(e)}")
            raise SageMakerClientError(f"Failed to initialize SageMaker client: {str(e)}", original_error=e)
    
    def create_automl_job(self, job_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an AutoML job using the SageMaker API.
        
        Args:
            job_parameters: Complete AutoML job parameters
            
        Returns:
            Dict containing AutoMLJobArn
            
        Raises:
            SageMakerClientError: If the API call fails
        """
        try:
            logger.info(f"Creating AutoML job: {job_parameters.get('AutoMLJobName', 'unknown')}")
            
            # Map parameters to SageMaker API format
            api_parameters = self._map_parameters_to_api(job_parameters)
            
            # Log the API call (excluding sensitive data)
            self._log_api_call(api_parameters)
            
            # Make the API call
            response = self.client.create_auto_ml_job(**api_parameters)
            
            logger.info(f"AutoML job created successfully: {response.get('AutoMLJobArn')}")
            
            return {
                'AutoMLJobArn': response['AutoMLJobArn']
            }
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            
            logger.error(f"SageMaker API error [{error_code}]: {error_message}")
            
            # Map common SageMaker errors to user-friendly messages
            user_message = self._map_sagemaker_error(error_code, error_message)
            
            raise SageMakerClientError(
                user_message,
                error_code=error_code,
                original_error=e
            )
            
        except BotoCoreError as e:
            logger.error(f"Boto3 error: {str(e)}")
            raise SageMakerClientError(
                f"AWS service error: {str(e)}",
                error_code="BotoCoreError",
                original_error=e
            )
            
        except Exception as e:
            logger.error(f"Unexpected error creating AutoML job: {str(e)}")
            raise SageMakerClientError(
                f"Unexpected error: {str(e)}",
                error_code="UnexpectedError",
                original_error=e
            )
    
    def _map_parameters_to_api(self, job_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map Lambda input parameters to SageMaker API parameters.
        
        Args:
            job_parameters: Input parameters from Lambda event
            
        Returns:
            Parameters formatted for SageMaker API
        """
        api_params = {}
        
        # Direct mapping parameters
        direct_mapping = [
            'AutoMLJobName',
            'InputDataConfig',
            'OutputDataConfig',
            'RoleArn',
            'AutoMLJobObjective',
            'ProblemType',
            'GenerateCandidateDefinitionsOnly',
            'ModelDeployConfig',
            'Tags'
        ]
        
        for param in direct_mapping:
            if param in job_parameters and job_parameters[param] is not None:
                api_params[param] = job_parameters[param]
        
        # Handle AutoMLJobConfig with special processing
        if 'AutoMLJobConfig' in job_parameters and job_parameters['AutoMLJobConfig']:
            api_params['AutoMLJobConfig'] = self._process_automl_job_config(
                job_parameters['AutoMLJobConfig'],
                job_parameters.get('modelTrainingPlan')
            )
        elif 'modelTrainingPlan' in job_parameters and job_parameters['modelTrainingPlan']:
            # If only modelTrainingPlan is provided without AutoMLJobConfig
            api_params['AutoMLJobConfig'] = self._process_automl_job_config(
                {},
                job_parameters.get('modelTrainingPlan')
            )
        
        return api_params
    
    def _process_automl_job_config(self, config: Dict[str, Any], model_training_plan: Optional[str] = None) -> Dict[str, Any]:
        """
        Process AutoMLJobConfig with special handling for nested parameters and training plans.
        
        Args:
            config: AutoMLJobConfig from input parameters
            model_training_plan: Training plan (Test, Bronze, Silver) to apply
            
        Returns:
            Processed config for SageMaker API
        """
        processed_config = {}
        
        # Direct mapping for most config parameters
        direct_config_params = [
            'DataSplitConfig',
            'Mode',
            'SecurityConfig'
        ]
        
        for param in direct_config_params:
            if param in config and config[param] is not None:
                processed_config[param] = config[param]
        
        # Handle CompletionCriteria with training plan processing
        completion_criteria = self._process_completion_criteria(
            config.get('CompletionCriteria'),
            model_training_plan
        )
        if completion_criteria:
            processed_config['CompletionCriteria'] = completion_criteria
        
        # Handle CandidateGenerationConfig with FeatureSpecificationS3Uri
        if 'CandidateGenerationConfig' in config and config['CandidateGenerationConfig']:
            candidate_config = config['CandidateGenerationConfig']
            processed_candidate_config = {}
            
            # Handle FeatureSpecificationS3Uri (the key parameter we're adding support for)
            if 'FeatureSpecificationS3Uri' in candidate_config and candidate_config['FeatureSpecificationS3Uri']:
                processed_candidate_config['FeatureSpecificationS3Uri'] = candidate_config['FeatureSpecificationS3Uri']
                logger.info(f"Including FeatureSpecificationS3Uri: {candidate_config['FeatureSpecificationS3Uri']}")
            
            # Handle AlgorithmsConfig
            if 'AlgorithmsConfig' in candidate_config and candidate_config['AlgorithmsConfig']:
                processed_candidate_config['AlgorithmsConfig'] = candidate_config['AlgorithmsConfig']
            
            if processed_candidate_config:
                processed_config['CandidateGenerationConfig'] = processed_candidate_config
        
        return processed_config
    
    def _process_completion_criteria(self, existing_criteria: Optional[Dict[str, Any]], model_training_plan: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Process completion criteria based on training plan.
        
        Args:
            existing_criteria: Existing completion criteria from input
            model_training_plan: Training plan to apply (Test, Bronze, Silver)
            
        Returns:
            Processed completion criteria
        """
        # If no training plan specified, return existing criteria unchanged
        if not model_training_plan:
            return existing_criteria
        
        # Define training plan configurations
        training_plan_configs = {
            'Test': {
                'MaxCandidates': 1,
                'MaxRuntimePerTrainingJobInSeconds': 120,
                'MaxAutoMLJobRuntimeInSeconds': 120
            },
            'Bronze': {
                'MaxCandidates': 10,
                'MaxRuntimePerTrainingJobInSeconds': 900,
                'MaxAutoMLJobRuntimeInSeconds': 3600
            },
            'Silver': {
                'MaxCandidates': 20,
                'MaxRuntimePerTrainingJobInSeconds': 1200,
                'MaxAutoMLJobRuntimeInSeconds': 4800
            },
            'Gold': None  # Use SageMaker defaults - no completion criteria
        }
        
        if model_training_plan in training_plan_configs:
            plan_config = training_plan_configs[model_training_plan]
            
            # Gold mode uses defaults (no completion criteria)
            if model_training_plan == 'Gold':
                logger.info("Using Gold training plan - applying SageMaker default completion criteria")
                return existing_criteria  # Return existing criteria unchanged, or None for defaults
            
            logger.info(f"Applying {model_training_plan} training plan completion criteria: {plan_config}")
            
            # Start with the plan configuration
            result_criteria = plan_config.copy()
            
            # If existing criteria exist, merge them (existing criteria take precedence for non-plan parameters)
            if existing_criteria:
                # For training plans, we override the key parameters but preserve others
                for key, value in existing_criteria.items():
                    if key not in plan_config:  # Don't override plan-specific parameters
                        result_criteria[key] = value
            
            return result_criteria
        else:
            # Unknown training plan, return existing criteria
            logger.warning(f"Unknown training plan '{model_training_plan}', using existing completion criteria")
            return existing_criteria
    
    def _log_api_call(self, api_parameters: Dict[str, Any]) -> None:
        """
        Log API call parameters (excluding sensitive data).
        
        Args:
            api_parameters: Parameters being sent to SageMaker API
        """
        # Create a copy for logging with sensitive data removed
        log_params = api_parameters.copy()
        
        # Remove or mask sensitive information
        if 'RoleArn' in log_params:
            # Keep only the role name, mask account ID
            role_arn = log_params['RoleArn']
            if '::' in role_arn and ':role/' in role_arn:
                role_name = role_arn.split(':role/')[-1]
                log_params['RoleArn'] = f"arn:aws:iam::***:role/{role_name}"
        
        # Log key parameters
        logger.info(f"SageMaker API call parameters: {log_params.get('AutoMLJobName')}")
        logger.debug(f"Full API parameters: {log_params}")
    
    def _map_sagemaker_error(self, error_code: str, error_message: str) -> str:
        """
        Map SageMaker error codes to user-friendly messages.
        
        Args:
            error_code: SageMaker error code
            error_message: Original error message
            
        Returns:
            User-friendly error message
        """
        error_mappings = {
            'ValidationException': f"Parameter validation failed: {error_message}",
            'ResourceLimitExceeded': f"AWS resource limit exceeded: {error_message}",
            'ResourceInUse': f"Resource is currently in use: {error_message}",
            'ResourceNotFound': f"Required resource not found: {error_message}",
            'AccessDeniedException': f"Access denied - check IAM permissions: {error_message}",
            'ThrottlingException': f"Request rate exceeded - please retry: {error_message}",
            'InternalFailure': f"AWS internal error - please retry: {error_message}",
            'ServiceUnavailable': f"SageMaker service temporarily unavailable: {error_message}",
        }
        
        return error_mappings.get(error_code, f"SageMaker error [{error_code}]: {error_message}")


def create_sagemaker_client(region_name: Optional[str] = None) -> SageMakerAutoMLClient:
    """
    Factory function to create SageMaker client.
    
    Args:
        region_name: AWS region name
        
    Returns:
        Configured SageMaker client
    """
    return SageMakerAutoMLClient(region_name=region_name)