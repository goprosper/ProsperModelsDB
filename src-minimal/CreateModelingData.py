"""
Enhanced CreateModelingData Lambda function with comprehensive data validation.

This function now includes robust error handling and validation to prevent
pandas errors and provide clear, actionable error messages to users.
"""

import os
# Patch for pandas compatibility in Lambda
if not hasattr(os, 'add_dll_directory'):
    os.add_dll_directory = lambda x: None

import boto3
import pandas as pd
import numpy as np
import logging
from io import StringIO
from data_validation import DataValidator
from error_response import ErrorResponseHandler
from metadata_calculator import MetadataCalculator
from feature_types_generator import FeatureTypesGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Question:
    def __init__(self, qid, type, offset, answer_values):
        self.qid = qid
        self.type = type
        self.offset = offset
        self.answer_values = answer_values

    def __str__(self):
        return f"qid {self.qid}, type {self.type}, offset {self.offset}, answer_values {self.answer_values}"
    
    def __repr__(self):
        return self.__str__()


class QuestionDef:
    def __init__(self, questionId, answerIds=None):
        self.qid = questionId
        self.aids = answerIds

    def __str__(self):
        return f"qid {self.qid}, answerIDS {self.aids}"
    
    def __repr__(self):
        return self.__str__()

class Feature:
    def __init__(self, feature):
        self.name = feature['FeatureName']
        self.feature_type = feature.get('FeatureType', 'Binary')  # Default to Binary if not specified
        self.literal = False
        self.disjuncts = []
        
        # Validate and normalize FeatureType
        valid_feature_types = ['Binary', 'Categorical', 'Ordinal', 'Zip']
        # Handle legacy 'Category' type for backward compatibility
        if self.feature_type == 'Category':
            self.feature_type = 'Categorical'
        
        if self.feature_type not in valid_feature_types:
            raise ValueError(f"Invalid FeatureType '{self.feature_type}'. Valid types are: {valid_feature_types}")
     
        if 'QuestionId' in feature:
            print('Feature type', self.feature_type, ' -- Feature QuestionId', feature['QuestionId'])
        else:
            print('Feature type', self.feature_type, ' -- No QuestionId')

        # Handle different feature types (note: 'Category' maps to 'Categorical')
        if self.feature_type in ['Category', 'Categorical']:
            print("In category")
            self.literal = True
            self.disjuncts.append([QuestionDef(feature['QuestionId'])])
            print('self', self)
        elif self.feature_type == 'Zip':
            self.literal = True
            self.disjuncts.append([QuestionDef(feature['QuestionId'])])
        elif self.feature_type == 'Ordinal':
            # Ordinal features are treated similarly to categorical for now
            self.literal = True
            self.disjuncts.append([QuestionDef(feature['QuestionId'])])
        elif self.feature_type == 'Binary':
            self.literal = False
            conjuncts = []
            for selection in feature['Selections']:
                qdef = QuestionDef(selection['QuestionId'], selection['AnswerIds'])
                conjuncts.append(qdef)
            self.disjuncts.append(conjuncts)

    def __str__(self):
        return f"Feature(name='{self.name}', type='{self.feature_type}', literal={self.literal}, disjuncts={self.disjuncts})"
    
    def __repr__(self):
        return self.__str__()


    def get_value(self, qmap, zip_dict, data_row):
        """Get feature value based on FeatureType."""
        feature_value = 0

        if self.feature_type == 'Zip':
            # Type Zip: Process as zip code and return 'Z' + cluster value
            q = qmap[self.disjuncts[0][0].qid]
            try:
                raw_value = data_row[q.offset]
                if raw_value == '' or raw_value == '#NA':
                    feature_value = np.nan
                else:
                    feature_value = int(raw_value)
                    if q.type == 'Z':  # for zip code, map to cluster
                        zip_code = feature_value
                        cluster = zip_dict[zip_code]  # get zip cluster
                        feature_value = cluster  
            except (ValueError, KeyError, IndexError) as e:
                logger.debug(f"Error processing Zip feature {self.name}: {e}")
                feature_value = np.nan
                
        elif self.feature_type == 'Ordinal':
            # Type Ordinal: Process as self-literal. Return the integer value.
            q = qmap[self.disjuncts[0][0].qid]
            try:
                raw_value = data_row[q.offset]
                if raw_value == '' or raw_value == '#NA':
                    feature_value = np.nan
                else:
                    feature_value = int(raw_value)
            except (ValueError, KeyError, IndexError) as e:
                logger.debug(f"Error processing Ordinal feature {self.name}: {e}")
                feature_value = np.nan
                
        elif self.feature_type == 'Categorical':
            # Type Categorical: Similar to self-literal. Append 'C' to the front of the string integer. Return the string.
            q = qmap[self.disjuncts[0][0].qid]
            try:
                data_value = data_row[q.offset]
                if data_value == '' or data_value == '#NA':
                    feature_value = np.nan
                else:
                    # Try to convert directly to int first
                    try:
                        int_value = int(data_value)
                    except ValueError:
                        # If it's a string, find its index in answer_values
                        if data_value in q.answer_values:
                            int_value = q.answer_values.index(data_value)
                        else:
                            logger.debug(f"Categorical feature {self.name}: value '{data_value}' not found in answer_values {q.answer_values}")
                            feature_value = np.nan
                            int_value = None
                    
                    if int_value is not None:
                        feature_value = int_value  
            except (KeyError, IndexError) as e:
                logger.debug(f"Error processing Categorical feature {self.name}: {e}")
                feature_value = np.nan
                
        elif self.feature_type == 'Binary':
            # Type Binary: Process as not self-literal. Returns 1 or 0.
            feature_value = 0
            try:
                for con in self.disjuncts:
                    con_value = 1
                    for qdef in con:
                        q = qmap[qdef.qid]
                        if q.type == 'S':
                            raw_value = data_row[q.offset]
                            if raw_value == '' or raw_value == '#NA':
                                con_value = np.nan
                                break
                            else:
                                values = [q.answer_values[i] for i in qdef.aids]
                                if not (raw_value in values):
                                    con_value = 0
                                    break
                        else:
                            if data_row[q.offset] == '#NA':
                                con_value = np.nan
                                break
                            else:
                                multi_value = 0
                                for a in qdef.aids:
                                    if data_row[q.offset + a] == '1':
                                        multi_value = 1
                                        break
                                if multi_value == 0:
                                    con_value = 0
                                    break

                    if np.isnan(con_value):
                        feature_value = np.nan
                        break
                    elif con_value == 1:
                        feature_value = 1
                        break
            except (KeyError, IndexError) as e:
                logger.debug(f"Error processing Binary feature {self.name}: {e}")
                feature_value = np.nan

        # Format return value based on type
        if isinstance(feature_value, str) and (feature_value.startswith('C') or feature_value.startswith('Z')):
            return feature_value  # Categorical and Zip values are already formatted as strings
        elif feature_value is np.nan or (isinstance(feature_value, float) and np.isnan(feature_value)):
            return ''  # Convert NaN to empty string (this is correct)
        elif self.feature_type in ['Categorical', 'Zip']:
            return feature_value  # Already formatted as strings with prefixes
        elif self.feature_type in ['Ordinal', 'Binary']:
            return int(feature_value) if isinstance(feature_value, (int, float)) else feature_value  # Return as integers
        else:
            return str(int(feature_value)) if isinstance(feature_value, (int, float)) else str(feature_value)

        
def get_data(bucket, data_key):
    """Load data file with enhanced error handling using boto3."""
    s3_client = boto3.client('s3')
    
    try:
        # Download file content from S3
        response = s3_client.get_object(Bucket=bucket, Key=data_key)
        content = response['Body'].read()
        
        # Try to decode with iso-8859-1 first
        try:
            content_str = content.decode('iso-8859-1')
        except UnicodeDecodeError:
            logger.warning("ISO-8859-1 encoding failed, trying UTF-8")
            content_str = content.decode('utf-8')
        
        # Read CSV from string
        df = pd.read_csv(
            StringIO(content_str), 
            header=None, 
            dtype=str, 
            na_values=[], 
            keep_default_na=False
        )
        return df
    except Exception as e:
        logger.error(f"Error loading data from s3://{bucket}/{data_key}: {e}")
        raise

def get_question_map(bucket, parms_key):
    """Load question map with enhanced error handling using boto3."""
    question_map = {}
    s3_client = boto3.client('s3')
    
    try:
        # Download file content from S3
        response = s3_client.get_object(Bucket=bucket, Key=parms_key)
        content = response['Body'].read()
        
        # Try to decode with iso-8859-1 first
        try:
            content_str = content.decode('iso-8859-1')
        except UnicodeDecodeError:
            logger.warning("ISO-8859-1 encoding failed for map file, trying UTF-8")
            content_str = content.decode('utf-8')
        
        # Read CSV from string
        parms = pd.read_csv(StringIO(content_str), header=0)
    except Exception as e:
        logger.error(f"Error loading question map from s3://{bucket}/{parms_key}: {e}")
        raise
    
    qid_save = '0'
    for row in parms.itertuples(index=False):
        if (row[1] != 'Auto'):
            if row[1] != qid_save:
                question_map[int(row[1])] = Question(
                    int(row[1]), 
                    'M' if row[2] in ['M', 'P'] else 'Z' if row[2] == 'Z' else 'S', 
                    int(row[0]) - 1, 
                    row[5].split('^')
                )
                qid_save = row[1]
                
    logger.info(f'Question map loaded: {len(question_map)} questions')
    return question_map
def get_zip_clusters(bucket, zip_key):
    """Load zip clusters with enhanced error handling using boto3."""
    zip_dict = {}
    s3_client = boto3.client('s3')
    
    try:
        # Download file content from S3
        response = s3_client.get_object(Bucket=bucket, Key=zip_key)
        content = response['Body'].read()
        
        # Try to decode with iso-8859-1 first
        try:
            content_str = content.decode('iso-8859-1')
        except UnicodeDecodeError:
            logger.warning("ISO-8859-1 encoding failed for zip file, trying UTF-8")
            content_str = content.decode('utf-8')
        
        # Read CSV from string
        zips = pd.read_csv(StringIO(content_str), header=0)
    except Exception as e:
        logger.error(f"Error loading zip clusters from s3://{bucket}/{zip_key}: {e}")
        raise
    
    for row in zips.itertuples(index=False):
        zip_dict[int(row[0])] = int(row[1])
                
    logger.info(f'Zip clusters loaded: {len(zip_dict)} zip codes')
    return zip_dict


def get_feature_list(featureList):
    """Process feature list with enhanced logging."""
    feature_list = []
    for feature in featureList:
        feature_list.append(Feature(feature))
        logger.debug(f'Added feature: {feature["FeatureName"]}')

    logger.info(f'Feature list processed: {len(feature_list)} features')
    return feature_list


def append_features_from_data(features, data_df, question_map, zip_dict, feature_list):
    """Extract features from data with partial processing support."""
    successful_features = []
    failed_features = []
    
    for f in feature_list:
        try:
            # Check if required question IDs exist in question map
            missing_questions = []
            for disjunct in f.disjuncts:
                for qdef in disjunct:
                    if qdef.qid not in question_map:
                        missing_questions.append(qdef.qid)
            
            if missing_questions:
                logger.error(f"Feature {f.name} failed: Missing question IDs in map: {missing_questions}")
                failed_features.append(f.name)
                continue
            
            feature_values = []
            for i in range(len(data_df)):
                try:
                    value = f.get_value(question_map, zip_dict, data_df.iloc[i])
                    feature_values.append(value)
                except KeyError as e:
                    logger.warning(f"KeyError processing row {i} for feature {f.name}: {e}")
                    feature_values.append('')  # Use empty string for failed values
                except Exception as e:
                    logger.warning(f"Error processing row {i} for feature {f.name}: {e}")
                    feature_values.append('')  # Use empty string for failed values
            
            features[f.name] = feature_values
            successful_features.append(f.name)
            logger.debug(f'Successfully processed feature: {f.name}')
            
        except Exception as e:
            logger.error(f"Failed to process feature {f.name}: {e}")
            failed_features.append(f.name)
    
    if failed_features:
        logger.warning(f"Failed to process {len(failed_features)} features: {failed_features}")
    
    logger.info(f'Feature processing: {len(successful_features)} successful, {len(failed_features)} failed')
    
    return features


def df_to_s3(df, bucket, key):
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, header=True, index=False)
    
    s3_resource = boto3.resource('s3')
    s3_resource.Object(bucket, key).put(Body=csv_buffer.getvalue())
    return f's3://{bucket}/{key}'


def create_training_sets(label):
    label_df = pd.DataFrame()
    # get label data
    label_df = append_features_from_data(label_df, data_df, qmap, zip_dict, [label])
    # combine label and features
    seed_df = pd.concat([label_df, features_df], axis=1)
    # remove rows with missing data
    seed_df = seed_df.dropna(axis = 0, how ='any')   # may want to remove this
    # split into three sets 70-20-10
    #train_df, validation_df, test_df = np.split(seed_df.sample(frac=1, random_state=1729), [int(0.7 * len(seed_df)), int(0.9*len(seed_df))])  
    
    #return (train_df, validation_df, test_df)
    return (seed_df)


def lambda_handler(event, context):
    """Enhanced lambda handler with comprehensive data validation."""
    # Initialize validation and error handling
    validator = DataValidator()
    error_handler = ErrorResponseHandler()
    
    # Extract request parameters
    request_name = event.get("RequestName")
    feature_list = event.get("FeatureList")
    label_list = event.get("LabelList")
    
    # Extract additional context for error messages
    study_name = "Unknown"
    requested_dates = []
    
    # Try to extract study info from request name for better error messages
    if request_name:
        parts = request_name.split('.')
        if len(parts) >= 3:
            # Extract study name from request name pattern
            study_name = parts[0].replace('-', ' ').title()
            # Extract date from request name if possible
            if len(parts) >= 2:
                date_part = parts[1]
                if 'T' in date_part:
                    requested_dates = [date_part.split('T')[0]]
    
    logger.info(f"Processing request: {request_name}")
    logger.info(f"Study: {study_name}, Dates: {requested_dates}")
    
    try:
        # Phase 1: Pre-validation - Check files before processing
        logger.info("Starting data validation phase")
        
        # Validate data file
        data_validation = validator.validate_data_file(request_name)
        if not data_validation.is_valid:
            logger.warning(f"Data file validation failed: {data_validation.error_message}")
            
            # Get suggestions for better error message
            suggestions = validator.suggest_alternatives(study_name, requested_dates)
            
            if data_validation.error_type == "EmptyDataError":
                # This is the main issue we're solving - empty data files
                return error_handler.create_data_unavailable_error(
                    requested_dates=requested_dates,
                    study_name=study_name,
                    request_name=request_name,
                    suggestions=suggestions
                )
            else:
                return error_handler.create_file_validation_error(
                    file_path=f"s3://prosper-raw-data/{request_name}/data_file",
                    file_type="data_file",
                    issue=data_validation.error_message,
                    file_size=data_validation.file_size,
                    request_name=request_name,
                    requested_dates=requested_dates,
                    study_name=study_name
                )
        
        # Validate map file
        map_validation = validator.validate_map_file(request_name)
        if not map_validation.is_valid:
            logger.warning(f"Map file validation failed: {map_validation.error_message}")
            return error_handler.create_file_validation_error(
                file_path=f"s3://prosper-raw-data/{request_name}/map_file",
                file_type="map_file",
                issue=map_validation.error_message,
                file_size=map_validation.file_size,
                request_name=request_name,
                requested_dates=requested_dates,
                study_name=study_name
            )
        
        logger.info("Data validation passed, proceeding with processing")
        
        # Phase 2: Data Loading (only if validation passes)
        logger.info("Loading data files")
        data_df = get_data('prosper-raw-data', request_name + '/data_file')
        logger.info(f'Data loaded: {len(data_df)} rows, {len(data_df.columns)} columns')
        
        logger.info("Loading question map")
        qmap = get_question_map('prosper-raw-data', request_name + '/map_file')
        
        # Load zip clusters
        zip_dict = get_zip_clusters('prosper-raw-data', 'Metadata/zip_clusters.csv')
        
        # Phase 3: Feature Processing
        logger.info("Processing feature lists")
        feature_list_objects = get_feature_list(feature_list)
        label_list_objects = get_feature_list(label_list)
        
        # Extract features from data with partial processing
        features_df = pd.DataFrame()
        features_df = append_features_from_data(features_df, data_df, qmap, zip_dict, feature_list_objects)
        logger.info(f'Features extracted: {len(features_df.columns)} features')
        
        # Extract labels with partial processing
        label_df = pd.DataFrame()
        label_df = append_features_from_data(label_df, data_df, qmap, zip_dict, label_list_objects)
        logger.info(f'Labels extracted: {len(label_df.columns)} labels')
        
        # Check if we have any valid data to process
        if len(features_df.columns) == 0 and len(label_df.columns) == 0:
            return error_handler.create_processing_error(
                error_type="NoValidDataError",
                error_message="No features or labels could be processed from the data",
                request_name=request_name,
                requested_dates=requested_dates,
                study_name=study_name
            )
        
        # Combine label and features
        if len(label_df.columns) > 0 and len(features_df.columns) > 0:
            seed_df = pd.concat([label_df, features_df], axis=1)
        elif len(label_df.columns) > 0:
            seed_df = label_df
            logger.warning("No features processed, using labels only")
        else:
            seed_df = features_df
            logger.warning("No labels processed, using features only")
        
        # Remove rows where label column is not 0 or 1
        if len(label_df.columns) > 0:
            label_column_name = label_df.columns[0]
            initial_row_count = len(seed_df)
            
            # Filter out rows where the label column is not 0 or 1
            # Convert label column to numeric, coercing errors to NaN
            label_values = pd.to_numeric(seed_df[label_column_name], errors='coerce')
            
            # Keep only rows where label is exactly 0 or 1
            valid_mask = label_values.isin([0, 1])
            seed_df = seed_df[valid_mask]
            
            final_row_count = len(seed_df)
            removed_rows = initial_row_count - final_row_count
            
            if removed_rows > 0:
                logger.info(f'Removed {removed_rows} rows where label column "{label_column_name}" was not 0 or 1')
            else:
                logger.info(f'All rows have valid binary labels (0 or 1) in column "{label_column_name}"')
            
        logger.info(f'Final dataset: {len(seed_df)} rows, {len(seed_df.columns)} columns')
        
        # Save to S3
        output_path = df_to_s3(seed_df, 'prosper-raw-data', request_name + '/modeling_data.csv')
        logger.info(f'Data saved to: {output_path}')
        
        # Calculate dataset metadata
        dataset_metadata = {}
        try:
            metadata_calculator = MetadataCalculator()
            label_column_name = None
            
            # Get the label column name if we have labels
            if len(label_df.columns) > 0:
                label_column_name = label_df.columns[0]
            
            dataset_metadata = metadata_calculator.get_dataset_metadata(
                seed_df, label_column_name
            )
            logger.info(f'Dataset metadata: {dataset_metadata}')
        except Exception as e:
            logger.warning(f'Failed to calculate dataset metadata: {e}')
            # Fallback to basic metadata
            dataset_metadata = {"SampleSize": len(seed_df)}
        
        # Generate and save feature types mapping
        feature_types_path = None
        try:
            feature_types_generator = FeatureTypesGenerator()
            
            # Get label names to exclude from feature types
            exclude_labels = [label.name for label in label_list_objects] if label_list_objects else []
            
            feature_types_mapping, feature_types_path = feature_types_generator.generate_and_save_feature_types(
                feature_list_objects,
                'prosper-raw-data',
                request_name,
                exclude_labels
            )
            
            if feature_types_path:
                logger.info(f'Feature types saved to: {feature_types_path}')
            else:
                logger.warning('Failed to save feature types mapping')
        except Exception as e:
            logger.warning(f'Failed to generate feature types mapping: {e}')
            # Continue without feature types - this is not critical for the main process
        
        # Prepare response with enhanced metadata
        response = {
            "statusCode": 200,
            "message": "Data processing completed successfully",
            "ModelingData": dataset_metadata,
            "details": {
                "outputPath": output_path,
                "dataRows": len(seed_df),
                "dataColumns": len(seed_df.columns),
                "requestName": request_name,
                "requestedFeatures": len(feature_list),
                "processedFeatures": len(features_df.columns),
                "requestedLabels": len(label_list),
                "processedLabels": len(label_df.columns)
            }
        }
        
        # Add feature types path if available
        if feature_types_path:
            response["details"]["featureTypesPath"] = feature_types_path
        
        # Add warnings for partial processing
        if len(features_df.columns) < len(feature_list):
            response["warnings"] = response.get("warnings", [])
            response["warnings"].append(f"Only {len(features_df.columns)} of {len(feature_list)} requested features were processed")
        
        if len(label_df.columns) < len(label_list):
            response["warnings"] = response.get("warnings", [])
            response["warnings"].append(f"Only {len(label_df.columns)} of {len(label_list)} requested labels were processed")
        
        return response
        
    except Exception as e:
        logger.exception(f"Unexpected error processing request {request_name}")
        return error_handler.create_processing_error(
            error_type="ProcessingError",
            error_message=str(e),
            request_name=request_name,
            requested_dates=requested_dates,
            study_name=study_name,
            original_exception=e
        )
