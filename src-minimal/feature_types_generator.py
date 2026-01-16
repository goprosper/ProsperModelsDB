"""
Feature types mapping generator for ML model configuration.

This module provides functionality to generate feature data type mappings
from feature definitions and save them as JSON files in S3.
"""

import json
import boto3
import logging
from io import StringIO

logger = logging.getLogger(__name__)


class FeatureTypesGenerator:
    """Generate feature data type mappings for ML models."""
    
    def __init__(self):
        self.s3_client = boto3.client('s3')
    
    def generate_feature_types_mapping(self, feature_list, exclude_labels=None):
        """
        Generate feature data type mapping from feature definitions.
        
        Args:
            feature_list (list): List of Feature objects
            exclude_labels (list, optional): List of label names to exclude
            
        Returns:
            dict: Dictionary mapping feature names to data types
        """
        if not feature_list:
            return {}
        
        exclude_labels = exclude_labels or []
        feature_types = {}
        
        for feature in feature_list:
            # Skip if this is a label column
            if feature.name in exclude_labels:
                continue
                
            # Map FeatureType to data type
            data_type = self._map_feature_type_to_data_type(feature.feature_type)
            feature_types[feature.name] = data_type
            
            logger.debug(f"Mapped feature '{feature.name}' "
                        f"({feature.feature_type}) -> {data_type}")
        
        logger.info(f"Generated feature types mapping for "
                   f"{len(feature_types)} features")
        
        return {"FeatureDataTypes": feature_types}
    
    def _map_feature_type_to_data_type(self, feature_type):
        """
        Map FeatureType to ML data type.
        
        Args:
            feature_type (str): The FeatureType from feature definition
            
        Returns:
            str: Either "categorical" or "numeric"
        """
        # Categorical types
        if feature_type in ["Categorical", "Category", "Zip", "Binary"]:
            return "categorical"
        
        # Numeric types
        elif feature_type in ["Ordinal"]:
            return "numeric"
        
        else:
            # Default to numeric for unknown types
            logger.warning(f"Unknown FeatureType '{feature_type}', "
                          f"defaulting to 'numeric'")
            return "numeric"
    
    def save_feature_types_to_s3(self, mapping, bucket, key):
        """
        Save feature types mapping to S3 as JSON file.
        
        Args:
            mapping (dict): Feature types mapping dictionary
            bucket (str): S3 bucket name
            key (str): S3 key for the JSON file
            
        Returns:
            str: S3 URI of the saved file, or None if failed
        """
        try:
            # Convert to JSON string
            json_content = json.dumps(mapping, indent=2, sort_keys=True)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=json_content,
                ContentType='application/json'
            )
            
            s3_uri = f"s3://{bucket}/{key}"
            logger.info(f"Feature types mapping saved to {s3_uri}")
            return s3_uri
            
        except Exception as e:
            logger.error(f"Failed to save feature types to S3: {e}")
            return None
    
    def generate_and_save_feature_types(self, feature_list, bucket, 
                                       request_name, exclude_labels=None):
        """
        Generate feature types mapping and save to S3.
        
        Args:
            feature_list (list): List of Feature objects
            bucket (str): S3 bucket name
            request_name (str): Request name for S3 path
            exclude_labels (list, optional): List of label names to exclude
            
        Returns:
            tuple: (mapping_dict, s3_uri) or (None, None) if failed
        """
        try:
            # Generate the mapping
            mapping = self.generate_feature_types_mapping(
                feature_list, exclude_labels
            )
            
            if not mapping.get("FeatureDataTypes"):
                logger.warning("No feature types to save")
                return None, None
            
            # Save to S3
            key = f"{request_name}/feature_types.json"
            s3_uri = self.save_feature_types_to_s3(mapping, bucket, key)
            
            return mapping, s3_uri
            
        except Exception as e:
            logger.error(f"Failed to generate and save feature types: {e}")
            return None, None