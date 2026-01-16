import boto3
import pandas as pd
import numpy as np
from io import StringIO


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
            # Type Zip: Process as zip code as the current code does
            q = qmap[self.disjuncts[0][0].qid]
            try:
                feature_value = int(data_row[q.offset])
                if q.type == 'Z':  # for zip code, map to cluster
                    zip_code = feature_value
                    cluster = zip_dict[zip_code]  # get zip cluster
                    feature_value = cluster  # set feature value to cluster
            except:
                feature_value = np.nan
                
        elif self.feature_type == 'Ordinal':
            # Type Ordinal: Process as self-literal. Return the integer value.
            q = qmap[self.disjuncts[0][0].qid]
            try:
                feature_value = int(data_row[q.offset])
            except:
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
                            feature_value = np.nan
                            int_value = None
                    
                    if int_value is not None:
                        feature_value = f'C{int_value}'  # Append 'C' to the front
            except:
                feature_value = np.nan
                
        elif self.feature_type == 'Binary':
            # Type Binary: Process as not self-literal. Returns 1 or 0.
            feature_value = 0
            for con in self.disjuncts:
                con_value = 1
                for qdef in con:
                    q = qmap[qdef.qid]
                    if q.type == 'S':
                        if data_row[q.offset] == '' or data_row[q.offset] == '#NA':
                            con_value = np.nan
                            break
                        else:
                            values = [q.answer_values[i] for i in qdef.aids]
                            if not (data_row[q.offset] in values):
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

        # Format return value based on type
        if isinstance(feature_value, str) and feature_value.startswith('C'):
            return feature_value  # Categorical values are already formatted
        elif feature_value is np.nan or (isinstance(feature_value, float) and np.isnan(feature_value)):
            return ''
        elif self.feature_type == 'Categorical':
            return feature_value  # Already a string with 'C' prefix
        else:
            return str(int(feature_value)) if isinstance(feature_value, (int, float)) else str(feature_value)

        
def get_data(bucket, data_key):
    data_location = 's3://{}/{}'.format(bucket, data_key)
    df = pd.read_csv(data_location, header=None, dtype=str, na_values=[], keep_default_na=False, encoding='iso-8859-1')

    #df = pd.read_csv(obj['Body'], header=None, dtype=str, na_values=[], keep_default_na=False, encoding='iso-8859-1') # 'Body' is a key word

    return df

def get_question_map(bucket, parms_key):
    question_map = {}
    
    data_location = 's3://{}/{}'.format(bucket, parms_key)
    parms = pd.read_csv(data_location, header=0, encoding='iso-8859-1')
    
    qid_save = '0'
    for row in parms.itertuples(index=False):
        if (row[1] != 'Auto'):
            if row[1] != qid_save:
                question_map[int(row[1])] = Question(int(row[1]), 'M' if row[2] in ['M', 'P'] else 'Z' if row[2] == 'Z' else 'S', int(row[0]) - 1, row[5].split('^'))
                qid_save = row[1]
                
    print('question_map', question_map)            
    return question_map
def get_zip_clusters(bucket, zip_key):
    zip_dict = {}
    
    data_location = 's3://{}/{}'.format(bucket, zip_key)
    zips = pd.read_csv(data_location, header=0, encoding='iso-8859-1')
    
    for row in zips.itertuples(index=False):
        zip_dict[int(row[0])] = int(row[1])
                
    print('zip_dict', zip_dict)
    return zip_dict


def get_feature_list(featureList):
    feature_list = []
    for feature in featureList:
        feature_list.append(Feature(feature))
        print(feature_list)

    return feature_list


def append_features_from_data(features, data_df, question_map, zip_dict, feature_list):
    for f in feature_list:
        features[f.name] = [f.get_value(question_map, zip_dict, data_df.iloc[i]) for i in range(len(data_df)) ]
    
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
    requestName = event.get("RequestName")
    featureList = event.get("FeatureList")
    labelList = event.get("LabelList")

    # Load data file
    data_df = get_data('prosper-raw-data', requestName + '/data_file')
    print('data head', data_df.head())
    print('data tail', data_df.tail())

    print("Loading question map")    # load question metadata
    qmap = get_question_map('prosper-raw-data', requestName + '/map_file')

    # Load zip clusters
    zip_dict = get_zip_clusters('prosper-raw-data', 'Metadata/zip_clusters.csv')
    
    # Load feature list
    feature_list = get_feature_list(featureList)
    print('feature list', feature_list)
     
    # Load labels
    label_list = get_feature_list(labelList)
    print('label list', label_list)

    # Extract features from data
    features_df = pd.DataFrame()
    features_df = append_features_from_data(features_df, data_df, qmap, zip_dict, feature_list)
    print('features head', features_df.head())
    print('features tail', features_df.tail())

    # Create training, validation, and test sets for each label

    # seed_df = create_training_sets(label_list[0])

    label_df = pd.DataFrame()
    label_df = append_features_from_data(label_df, data_df, qmap, zip_dict, label_list)
    print('label head', label_df.head())
    print('label tail', label_df.tail())
    # combine label and features
    seed_df = pd.concat([label_df, features_df], axis=1)

    # Save to S3
    df_to_s3(seed_df, 'prosper-raw-data', requestName + '/modeling_data.csv')
