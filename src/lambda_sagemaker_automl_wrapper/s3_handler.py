"""
S3 handling utilities for feature specification files.

This module provides validation and access functionality for S3-stored
feature specification files used in AutoML jobs.
"""

import boto3
import json
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)


class S3Error(Exception):
    """Base class for S3-related errors."""
    pass


class S3AccessError(S3Error):
    """Raised when S3 access fails."""
    pass


class S3ValidationError(S3Error):
    """Raised when S3 URI or content validation fails."""
    pass


class FeatureSpecificationError(S3Error):
    """Raised when feature specification content is invalid."""
    pass


class S3FeatureSpecificationHandler:
    """
    Handler for S3-stored feature specification files.
    
    This class provides validation and access functionality for feature
    specification files that define feature types and selections for AutoML jobs.
    """
    
    def __init__(self, region_name: Optional[str] = None):
        """
        Initialize S3 client.
        
        Args:
            region_name: AWS region name (defaults to Lambda's region)
        """
        try:
            self.s3_client = boto3.client('s3', region_name=region_name)
            logger.info(f"S3 client initialized for region: {region_name or 'default'}")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")
            raise S3Error(f"Failed to initialize S3 client: {str(e)}")
    
    def validate_and_access_feature_specification(self, s3_uri: str) -> Dict[str, Any]:
        """
        Validate S3 URI and access feature specification file.
        
        Args:
            s3_uri: S3 URI to the feature specification file
            
        Returns:
            Parsed feature specification content
            
        Raises:
            S3ValidationError: If URI format is invalid
            S3AccessError: If file access fails
            FeatureSpecificationError: If content is invalid
        """
        logger.info(f"Validating and accessing feature specification: {s3_uri}")
        
        # Validate URI format
        bucket, key = self._parse_s3_uri(s3_uri)
        
        # Check file existence and accessibility
        self._validate_file_access(bucket, key)
        
        # Download and parse content
        content = self._download_and_parse_content(bucket, key)
        
        # Validate content structure
        self._validate_feature_specification_content(content)
        
        logger.info(f"Successfully validated feature specification: {s3_uri}")
        return content
    
    def validate_s3_uri_format(self, s3_uri: str) -> tuple[str, str]:
        """
        Validate S3 URI format and extract bucket and key.
        
        Args:
            s3_uri: S3 URI to validate
            
        Returns:
            Tuple of (bucket, key)
            
        Raises:
            S3ValidationError: If URI format is invalid
        """
        return self._parse_s3_uri(s3_uri)
    
    def check_file_exists(self, s3_uri: str) -> bool:
        """
        Check if file exists at the given S3 URI.
        
        Args:
            s3_uri: S3 URI to check
            
        Returns:
            True if file exists, False otherwise
            
        Raises:
            S3ValidationError: If URI format is invalid
            S3AccessError: If access check fails due to permissions
        """
        try:
            bucket, key = self._parse_s3_uri(s3_uri)
            self.s3_client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == '404':
                return False
            elif error_code == '403':
                raise S3AccessError(f"Access denied to S3 file: {s3_uri}")
            else:
                raise S3AccessError(f"Failed to check S3 file existence: {str(e)}")
        except Exception as e:
            raise S3AccessError(f"Unexpected error checking S3 file: {str(e)}")
    
    def _parse_s3_uri(self, s3_uri: str) -> tuple[str, str]:
        """
        Parse S3 URI to extract bucket and key.
        
        Args:
            s3_uri: S3 URI to parse
            
        Returns:
            Tuple of (bucket, key)
            
        Raises:
            S3ValidationError: If URI format is invalid
        """
        if not s3_uri:
            raise S3ValidationError("S3 URI cannot be empty")
        
        if not s3_uri.startswith('s3://'):
            raise S3ValidationError(f"S3 URI must start with 's3://': {s3_uri}")
        
        try:
            parsed = urlparse(s3_uri)
            bucket = parsed.netloc
            key = parsed.path.lstrip('/')
            
            if not bucket:
                raise S3ValidationError(f"S3 URI missing bucket name: {s3_uri}")
            
            if not key:
                raise S3ValidationError(f"S3 URI missing object key: {s3_uri}")
            
            # Basic bucket name validation
            if len(bucket) < 3 or len(bucket) > 63:
                raise S3ValidationError(f"Invalid S3 bucket name length: {bucket}")
            
            return bucket, key
            
        except Exception as e:
            if isinstance(e, S3ValidationError):
                raise
            raise S3ValidationError(f"Failed to parse S3 URI: {s3_uri} - {str(e)}")
    
    def _validate_file_access(self, bucket: str, key: str) -> None:
        """
        Validate that file exists and is accessible.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            
        Raises:
            S3AccessError: If file access fails
        """
        try:
            response = self.s3_client.head_object(Bucket=bucket, Key=key)
            
            # Check file size (reasonable limit for feature specification)
            content_length = response.get('ContentLength', 0)
            if content_length > 10 * 1024 * 1024:  # 10MB limit
                raise S3AccessError(f"Feature specification file too large: {content_length} bytes")
            
            if content_length == 0:
                raise S3AccessError("Feature specification file is empty")
            
            logger.info(f"File validation successful - Size: {content_length} bytes")
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            
            if error_code == '404':
                raise S3AccessError(f"Feature specification file not found: s3://{bucket}/{key}")
            elif error_code == '403':
                raise S3AccessError(f"Access denied to feature specification file: s3://{bucket}/{key}")
            else:
                raise S3AccessError(f"Failed to access feature specification file: {error_message}")
        
        except BotoCoreError as e:
            raise S3AccessError(f"AWS service error accessing file: {str(e)}")
        
        except Exception as e:
            raise S3AccessError(f"Unexpected error accessing file: {str(e)}")
    
    def _download_and_parse_content(self, bucket: str, key: str) -> Dict[str, Any]:
        """
        Download and parse feature specification content.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            
        Returns:
            Parsed JSON content
            
        Raises:
            S3AccessError: If download fails
            FeatureSpecificationError: If content parsing fails
        """
        try:
            logger.info(f"Downloading feature specification: s3://{bucket}/{key}")
            
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            content_bytes = response['Body'].read()
            
            # Decode content
            try:
                content_str = content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                raise FeatureSpecificationError("Feature specification file must be UTF-8 encoded")
            
            # Parse JSON
            try:
                content = json.loads(content_str)
            except json.JSONDecodeError as e:
                raise FeatureSpecificationError(f"Invalid JSON in feature specification: {str(e)}")
            
            logger.info("Successfully downloaded and parsed feature specification")
            return content
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            
            if error_code == '404':
                raise S3AccessError(f"Feature specification file not found during download: s3://{bucket}/{key}")
            elif error_code == '403':
                raise S3AccessError(f"Access denied during download: s3://{bucket}/{key}")
            else:
                raise S3AccessError(f"Failed to download feature specification: {error_message}")
        
        except (BotoCoreError, FeatureSpecificationError):
            raise
        
        except Exception as e:
            raise S3AccessError(f"Unexpected error downloading file: {str(e)}")
    
    def _validate_feature_specification_content(self, content: Dict[str, Any]) -> None:
        """
        Validate feature specification content structure.
        
        Args:
            content: Parsed feature specification content
            
        Raises:
            FeatureSpecificationError: If content structure is invalid
        """
        if not isinstance(content, dict):
            raise FeatureSpecificationError("Feature specification must be a JSON object")
        
        # Check for valid structure - either FeatureAttributeNames or FeatureDataTypes should be present
        has_feature_names = 'FeatureAttributeNames' in content
        has_feature_types = 'FeatureDataTypes' in content
        
        if not has_feature_names and not has_feature_types:
            raise FeatureSpecificationError(
                "Feature specification must contain either 'FeatureAttributeNames' or 'FeatureDataTypes'"
            )
        
        # Validate FeatureAttributeNames if present
        if has_feature_names:
            feature_names = content['FeatureAttributeNames']
            if not isinstance(feature_names, list):
                raise FeatureSpecificationError("FeatureAttributeNames must be a list")
            
            if not feature_names:
                raise FeatureSpecificationError("FeatureAttributeNames cannot be empty")
            
            for i, name in enumerate(feature_names):
                if not isinstance(name, str) or not name.strip():
                    raise FeatureSpecificationError(f"Invalid feature name at index {i}: {name}")
        
        # Validate FeatureDataTypes if present
        if has_feature_types:
            feature_types = content['FeatureDataTypes']
            if not isinstance(feature_types, dict):
                raise FeatureSpecificationError("FeatureDataTypes must be an object")
            
            if not feature_types:
                raise FeatureSpecificationError("FeatureDataTypes cannot be empty")
            
            valid_types = ['numeric', 'categorical', 'text', 'datetime', 'sequence']
            for feature_name, feature_type in feature_types.items():
                if not isinstance(feature_name, str) or not feature_name.strip():
                    raise FeatureSpecificationError(f"Invalid feature name: {feature_name}")
                
                if feature_type not in valid_types:
                    logger.warning(f"Feature type '{feature_type}' for '{feature_name}' not in standard list: {valid_types}")
        
        # If both are present, validate consistency
        if has_feature_names and has_feature_types:
            feature_names = set(content['FeatureAttributeNames'])
            feature_type_names = set(content['FeatureDataTypes'].keys())
            
            # FeatureDataTypes keys should be a subset of FeatureAttributeNames
            if not feature_type_names.issubset(feature_names):
                extra_types = feature_type_names - feature_names
                raise FeatureSpecificationError(
                    f"FeatureDataTypes contains features not in FeatureAttributeNames: {extra_types}"
                )
        
        logger.info("Feature specification content validation successful")


def create_s3_handler(region_name: Optional[str] = None) -> S3FeatureSpecificationHandler:
    """
    Factory function to create S3 feature specification handler.
    
    Args:
        region_name: AWS region name
        
    Returns:
        Configured S3 handler
    """
    return S3FeatureSpecificationHandler(region_name=region_name)