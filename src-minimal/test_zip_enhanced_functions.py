"""
Test script for actual functions in CreateModelingData.py.

This script tests the actual implementation of:
1. get_zip_enhanced_data() function
2. add_zip_enhanced_columns() function
3. Integration with Feature class
"""

import sys
import os
import pandas as pd
import numpy as np
from io import StringIO
import boto3
from moto import mock_aws

# Add src-minimal to path
sys.path.insert(0, os.path.dirname(__file__))

# Import after path is set
import CreateModelingData


class MockQuestion:
    """Mock Question class for testing."""
    def __init__(self, qid, offset, qtype='Z'):
        self.qid = qid
        self.offset = offset
        self.type = qtype


class MockQuestionDef:
    """Mock QuestionDef class for testing."""
    def __init__(self, qid):
        self.qid = qid


class MockZipFeature:
    """Mock Zip Feature for testing."""
    def __init__(self):
        self.name = 'zip_code'
        self.feature_type = 'Zip'
        self.disjuncts = [[MockQuestionDef('Q1')]]


@mock_aws
def test_get_zip_enhanced_data():
    """Test the get_zip_enhanced_data function."""
    print("\n=== Test 1: get_zip_enhanced_data() Function ===")
    
    # Create mock S3 bucket and upload test data
    s3_client = boto3.client('s3', region_name='us-east-1')
    bucket_name = 'test-bucket'
    s3_client.create_bucket(Bucket=bucket_name)
    
    # Create sample zip_enhanced.csv data
    csv_data = """zip,cluster,census_division,rural_code
10001,5,New England,Urban
10002,5,New England,Urban
90001,12,Pacific,Urban
60601,8,East North Central,Urban
30301,15,South Atlantic,Suburban
78701,14,West South Central,Urban"""
    
    # Upload to S3
    s3_client.put_object(
        Bucket=bucket_name,
        Key='Metadata/zip_enhanced.csv',
        Body=csv_data.encode('utf-8')
    )
    
    # Test the function
    zip_dict = CreateModelingData.get_zip_enhanced_data(bucket_name, 'Metadata/zip_enhanced.csv')
    
    # Verify structure
    assert isinstance(zip_dict, dict), "Should return a dictionary"
    assert len(zip_dict) == 6, f"Should have 6 zip codes, got {len(zip_dict)}"
    print(f"✓ Loaded {len(zip_dict)} zip codes")
    
    # Verify specific entries
    assert 10001 in zip_dict, "Zip 10001 should be in dictionary"
    assert zip_dict[10001]['cluster'] == 5, "Cluster should be 5"
    assert zip_dict[10001]['census_division'] == 'New England', "Census division should be 'New England'"
    assert zip_dict[10001]['rural_code'] == 'Urban', "Rural code should be 'Urban'"
    print(f"✓ Zip 10001 data: {zip_dict[10001]}")
    
    # Verify another entry
    assert 78701 in zip_dict, "Zip 78701 should be in dictionary"
    assert zip_dict[78701]['cluster'] == 14, "Cluster should be 14"
    assert zip_dict[78701]['census_division'] == 'West South Central', "Census division should be 'West South Central'"
    assert zip_dict[78701]['rural_code'] == 'Urban', "Rural code should be 'Urban'"
    print(f"✓ Zip 78701 data: {zip_dict[78701]}")
    
    print("✓ Test 1 PASSED\n")
    return zip_dict


def test_add_zip_enhanced_columns_function():
    """Test the add_zip_enhanced_columns function."""
    print("=== Test 2: add_zip_enhanced_columns() Function ===")
    
    # Create mock data
    zip_dict = {
        10001: {'cluster': 5, 'census_division': 'New England', 'rural_code': 'Urban'},
        10002: {'cluster': 5, 'census_division': 'New England', 'rural_code': 'Urban'},
        90001: {'cluster': 12, 'census_division': 'Pacific', 'rural_code': 'Urban'},
        60601: {'cluster': 8, 'census_division': 'East North Central', 'rural_code': 'Urban'},
    }
    
    # Create mock question map
    question_map = {
        'Q1': MockQuestion('Q1', 0, 'Z')
    }
    
    # Create mock features dataframe
    features_df = pd.DataFrame({
        'feature1': [1, 2, 3, 4],
        'feature2': [10, 20, 30, 40]
    })
    
    # Create mock raw data with zip codes
    data_df = pd.DataFrame({
        'zip_column': [10001, 10002, 90001, 60601]
    })
    
    # Create mock feature list with a Zip feature
    feature_list = [MockZipFeature()]
    
    # Call the function
    result_df = CreateModelingData.add_zip_enhanced_columns(
        features_df, data_df, question_map, zip_dict, feature_list
    )
    
    # Verify columns were added
    assert 'zip_cluster' in result_df.columns, "zip_cluster column should exist"
    assert 'zip_census_division' in result_df.columns, "zip_census_division column should exist"
    assert 'zip_rural_code' in result_df.columns, "zip_rural_code column should exist"
    print(f"✓ All three columns added: {[col for col in result_df.columns if 'zip_' in col]}")
    
    # Verify data
    assert result_df['zip_cluster'].iloc[0] == 5, "First cluster should be 5"
    assert result_df['zip_census_division'].iloc[2] == 'Pacific', "Third census division should be 'Pacific'"
    assert result_df['zip_rural_code'].iloc[3] == 'Urban', "Fourth rural code should be 'Urban'"
    print("✓ Column values are correct")
    
    # Verify original columns are preserved
    assert 'feature1' in result_df.columns, "Original feature1 should be preserved"
    assert 'feature2' in result_df.columns, "Original feature2 should be preserved"
    print("✓ Original columns preserved")
    
    print(f"\nResult dataframe:")
    print(result_df)
    
    print("\n✓ Test 2 PASSED\n")
    return result_df


def test_feature_get_value_with_zip_dict():
    """Test that Feature.get_value() works with new zip_dict structure."""
    print("=== Test 3: Feature.get_value() with New Zip Dict ===")
    
    # Create a real Feature object with Zip type
    feature_def = {
        'FeatureName': 'zip_code',
        'FeatureType': 'Zip',
        'QuestionId': 'Q1'
    }
    
    feature = CreateModelingData.Feature(feature_def)
    
    # Create mock question map
    question_map = {
        'Q1': MockQuestion('Q1', 0, 'Z')
    }
    
    # Create new zip_dict structure
    zip_dict = {
        10001: {'cluster': 5, 'census_division': 'New England', 'rural_code': 'Urban'},
        90001: {'cluster': 12, 'census_division': 'Pacific', 'rural_code': 'Urban'},
    }
    
    # Create mock data row
    data_row = pd.Series([10001])  # Zip code at offset 0
    
    # Get value
    value = feature.get_value(question_map, zip_dict, data_row)
    
    # Verify it returns the cluster value
    assert value == 5, f"Expected cluster value 5, got {value}"
    print(f"✓ Feature.get_value() returns cluster: {value}")
    
    # Test with different zip
    data_row = pd.Series([90001])
    value = feature.get_value(question_map, zip_dict, data_row)
    assert value == 12, f"Expected cluster value 12, got {value}"
    print(f"✓ Feature.get_value() returns cluster: {value}")
    
    # Test with missing zip
    data_row = pd.Series([99999])
    value = feature.get_value(question_map, zip_dict, data_row)
    print(f"DEBUG: value = {repr(value)}, type = {type(value)}")
    assert pd.isna(value) or value == '', f"Expected NaN or empty string for missing zip, got {repr(value)}"
    print(f"✓ Feature.get_value() returns NaN/empty for missing zip")
    
    print("\n✓ Test 3 PASSED\n")


@mock_aws
def test_integration():
    """Integration test of all components."""
    print("=== Test 4: Integration Test ===")
    
    print("Step 1: Test get_zip_enhanced_data()")
    zip_dict = test_get_zip_enhanced_data()
    
    print("Step 2: Test add_zip_enhanced_columns()")
    result_df = test_add_zip_enhanced_columns_function()
    
    print("Step 3: Test Feature.get_value() with new zip_dict")
    test_feature_get_value_with_zip_dict()
    
    print("✓ Integration test PASSED\n")
    print("=" * 60)
    print("ALL FUNCTION TESTS PASSED!")
    print("=" * 60)
    print("\nSummary:")
    print("✓ get_zip_enhanced_data() loads data correctly from S3")
    print("✓ add_zip_enhanced_columns() adds three new columns")
    print("✓ Feature.get_value() works with new zip_dict structure")
    print("✓ All components integrate correctly")


if __name__ == '__main__':
    try:
        test_integration()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
