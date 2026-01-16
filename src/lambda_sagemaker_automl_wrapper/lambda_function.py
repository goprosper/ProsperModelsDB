"""
Lambda SageMaker AutoML Wrapper

This Lambda function wraps the SageMaker CreateAutoMLJob API to support parameters
not available through AWS Step Functions' direct SageMaker integration, specifically
the FeatureSpecificationS3Uri parameter.
"""

import os
from typing import Dict, Any

# Import our modules
from logger import setup_logging, get_logger
from validation import validate_automl_job_request, sanitize_parameters
from sagemaker_client import create_sagemaker_client, SageMakerClientError
from s3_handler import create_s3_handler, S3Error
from response_handler import format_success_response, format_error_response
from error_handler import handle_error, ParameterValidationError, S3AccessError, SageMakerAPIError


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda handler for SageMaker AutoML job creation.
    
    This function accepts the same input format as Step Functions SageMaker integration
    but provides full SageMaker CreateAutoMLJob API support including FeatureSpecificationS3Uri.
    
    Args:
        event: Lambda event containing AutoML job parameters in Step Functions format
        context: Lambda context object
        
    Returns:
        Dict containing AutoMLJobArn in Step Functions compatible format
        
    Raises:
        Exception: Formatted exception for Step Functions error handling
    """
    # Setup logging
    logger = setup_logging(os.getenv('LOG_LEVEL', 'INFO'))
    request_id = context.aws_request_id
    
    try:
        # Log Lambda start
        logger.log_lambda_start(event, request_id)
        
        # Step 1: Sanitize input parameters
        logger.info("Sanitizing input parameters", request_id=request_id)
        sanitized_event = sanitize_parameters(event)
        
        # Log modelTrainingPlan if present
        if 'modelTrainingPlan' in sanitized_event and sanitized_event['modelTrainingPlan']:
            logger.info(f"Processing with modelTrainingPlan: {sanitized_event['modelTrainingPlan']}", request_id=request_id)
        
        # Step 2: Validate parameters
        logger.log_parameter_validation_start(request_id)
        try:
            validate_automl_job_request(sanitized_event)
            logger.log_parameter_validation_success(request_id)
        except Exception as e:
            logger.log_parameter_validation_error(str(e), "unknown", request_id)
            raise ParameterValidationError(str(e), original_error=e)
        
        # Step 3: Handle feature specification if present
        feature_spec_uri = None
        if ('AutoMLJobConfig' in sanitized_event and 
            sanitized_event['AutoMLJobConfig'] and
            'CandidateGenerationConfig' in sanitized_event['AutoMLJobConfig'] and
            sanitized_event['AutoMLJobConfig']['CandidateGenerationConfig'] and
            'FeatureSpecificationS3Uri' in sanitized_event['AutoMLJobConfig']['CandidateGenerationConfig']):
            
            feature_spec_uri = sanitized_event['AutoMLJobConfig']['CandidateGenerationConfig']['FeatureSpecificationS3Uri']
            
            if feature_spec_uri:
                logger.log_s3_operation_start("validate_feature_spec", feature_spec_uri, request_id)
                try:
                    s3_handler = create_s3_handler()
                    # Validate and access the feature specification file
                    feature_spec_content = s3_handler.validate_and_access_feature_specification(feature_spec_uri)
                    logger.log_s3_operation_success("validate_feature_spec", feature_spec_uri, request_id)
                    logger.debug(f"Feature specification validated: {len(feature_spec_content)} keys", 
                               request_id=request_id)
                except S3Error as e:
                    logger.log_s3_operation_error("validate_feature_spec", feature_spec_uri, str(e), request_id)
                    raise S3AccessError(str(e), s3_uri=feature_spec_uri, original_error=e)
        
        # Step 4: Create SageMaker client and make API call
        job_name = sanitized_event.get('AutoMLJobName', 'unknown')
        logger.log_sagemaker_api_start(job_name, request_id)
        
        try:
            sagemaker_client = create_sagemaker_client()
            sagemaker_response = sagemaker_client.create_automl_job(sanitized_event)
            
            job_arn = sagemaker_response.get('AutoMLJobArn', '')
            logger.log_sagemaker_api_success(job_name, job_arn, request_id)
            
        except SageMakerClientError as e:
            logger.log_sagemaker_api_error(job_name, e.error_code or 'Unknown', str(e), request_id)
            raise SageMakerAPIError(str(e), error_code=e.error_code, original_error=e)
        
        # Step 5: Format response for Step Functions compatibility
        try:
            formatted_response = format_success_response(sagemaker_response)
            logger.log_lambda_success(job_name, formatted_response.get('AutoMLJobArn', ''), request_id)
            return formatted_response
            
        except Exception as e:
            logger.error(f"Failed to format response: {str(e)}", request_id=request_id)
            raise SageMakerAPIError(f"Response formatting failed: {str(e)}", original_error=e)
        
    except Exception as e:
        # Centralized error handling
        error_context = {
            'operation': 'automl_job_creation',
            'job_name': event.get('AutoMLJobName', 'unknown')
        }
        
        if feature_spec_uri:
            error_context['s3_uri'] = feature_spec_uri
        
        logger.log_lambda_error(type(e).__name__, str(e), request_id)
        
        # This will format and raise the error for Step Functions
        handle_error(e, error_context, request_id)