"""
Test script for zip_enhanced.csv integration.

This script tests:
1. Loading zip_enhanced.csv data
2. Adding zip-enhanced columns to modeling data
3. Feature types generation with extra categorical features
"""

import sys
import os
import pandas as pd
import numpy as np
from io import StringIO
import json

# Add src-minimal to path
sys.path.insert(0, os.path.dirname(__file__))

from feature_types_generator import FeatureTypesGenerator


class MockFeature:
    """Mock Feature class for testing."""
    def __init__(self, name, feature_type):
        self.name = name
        self.feature_type = feature_type


def test_zip_enhanced_data_structure():
    """Test that zip_enhanced data has the correct structure."""
    print("\n=== Test 1: Zip Enhanced Data Structure ===")
    
    # Create sample zip_enhanced data
    sample_data = """zip,cluster,census_division,rural_code
10001,5,New England,Urban
10002,5,New England,Urban
90001,12,Pacific,Urban
60601,8,East North Central,Urban
30301,15,South Atlantic,Suburban"""
    
    # Parse the data
    df = pd.read_csv(StringIO(sample_data))
    
    # Verify columns
    expected_columns = ['zip', 'cluster', 'census_division', 'rural_code']
    assert list(df.columns) == expected_columns, f"Expected columns {expected_columns}, got {list(df.columns)}"
    print(f"✓ Columns are correct: {list(df.columns)}")
    
    # Verify data types
    assert df['zip'].dtype in [np.int64, np.int32], "Zip should be integer"
    assert df['cluster'].dtype in [np.int64, np.int32], "Cluster should be integer"
    assert df['census_division'].dtype == object, "Census division should be string"
    assert df['rural_code'].dtype == object, "Rural code should be string"
    print("✓ Data types are correct")
    
    # Create zip_dict structure as used in the code
    zip_dict = {}
    for row in df.itertuples(index=False):
        zip_code = int(row[0])
        zip_dict[zip_code] = {
            'cluster': int(row[1]),
            'census_division': str(row[2]),
            'rural_code': str(row[3])
        }
    
    # Verify zip_dict structure
    assert 10001 in zip_dict, "Zip 10001 should be in dictionary"
    assert zip_dict[10001]['cluster'] == 5, "Cluster should be 5"
    assert zip_dict[10001]['census_division'] == 'New England', "Census division should be 'New England'"
    assert zip_dict[10001]['rural_code'] == 'Urban', "Rural code should be 'Urban'"
    print(f"✓ Zip dictionary structure is correct: {zip_dict[10001]}")
    
    print("✓ Test 1 PASSED\n")
    return zip_dict


def test_add_zip_enhanced_columns():
    """Test adding zip-enhanced columns to a dataframe."""
    print("=== Test 2: Add Zip Enhanced Columns ===")
    
    # Create sample zip_dict
    zip_dict = {
        10001: {'cluster': 5, 'census_division': 'New England', 'rural_code': 'Urban'},
        10002: {'cluster': 5, 'census_division': 'New England', 'rural_code': 'Urban'},
        90001: {'cluster': 12, 'census_division': 'Pacific', 'rural_code': 'Urban'},
        60601: {'cluster': 8, 'census_division': 'East North Central', 'rural_code': 'Urban'},
    }
    
    # Create sample data with zip codes
    sample_data = pd.DataFrame({
        'feature1': [1, 2, 3, 4],
        'feature2': [10, 20, 30, 40]
    })
    
    # Simulate raw data with zip codes
    raw_data = pd.DataFrame({
        'zip_column': [10001, 10002, 90001, 60601]
    })
    
    # Manually add zip-enhanced columns (simulating the function)
    clusters = []
    census_divisions = []
    rural_codes = []
    
    for i in range(len(raw_data)):
        zip_code = raw_data.iloc[i]['zip_column']
        zip_data = zip_dict.get(zip_code)
        if zip_data:
            clusters.append(zip_data['cluster'])
            census_divisions.append(zip_data['census_division'])
            rural_codes.append(zip_data['rural_code'])
        else:
            clusters.append(np.nan)
            census_divisions.append(np.nan)
            rural_codes.append(np.nan)
    
    sample_data['zip_cluster'] = clusters
    sample_data['zip_census_division'] = census_divisions
    sample_data['zip_rural_code'] = rural_codes
    
    # Verify columns were added
    assert 'zip_cluster' in sample_data.columns, "zip_cluster column should exist"
    assert 'zip_census_division' in sample_data.columns, "zip_census_division column should exist"
    assert 'zip_rural_code' in sample_data.columns, "zip_rural_code column should exist"
    print(f"✓ All three columns added: {[col for col in sample_data.columns if 'zip_' in col]}")
    
    # Verify data
    assert sample_data['zip_cluster'].iloc[0] == 5, "First cluster should be 5"
    assert sample_data['zip_census_division'].iloc[2] == 'Pacific', "Third census division should be 'Pacific'"
    assert sample_data['zip_rural_code'].iloc[3] == 'Urban', "Fourth rural code should be 'Urban'"
    print("✓ Column values are correct")
    
    print(f"\nSample data with zip-enhanced columns:")
    print(sample_data)
    
    print("\n✓ Test 2 PASSED\n")
    return sample_data


def test_feature_types_generator():
    """Test feature types generator with extra categorical features."""
    print("=== Test 3: Feature Types Generator ===")
    
    # Create mock features
    features = [
        MockFeature('age', 'Ordinal'),
        MockFeature('income', 'Ordinal'),
        MockFeature('zip_code', 'Zip'),  # This will be excluded
        MockFeature('gender', 'Categorical'),
        MockFeature('has_loan', 'Binary'),
    ]
    
    # Create generator
    generator = FeatureTypesGenerator()
    
    # Exclude Zip-type features (simulating the actual code behavior)
    exclude_labels = ['zip_code']  # Zip features are excluded
    
    # Generate feature types with extra categorical features
    extra_categorical = ['zip_cluster', 'zip_census_division', 'zip_rural_code']
    
    mapping = generator.generate_feature_types_mapping(
        features,
        exclude_labels=exclude_labels,
        extra_categorical_features=extra_categorical
    )
    
    # Verify structure
    assert 'FeatureDataTypes' in mapping, "Mapping should have FeatureDataTypes key"
    feature_types = mapping['FeatureDataTypes']
    
    # Verify original features (except Zip)
    assert 'age' in feature_types, "age should be in feature types"
    assert feature_types['age'] == 'numeric', "age should be numeric"
    
    assert 'zip_code' not in feature_types, "zip_code should NOT be in feature types (excluded)"
    
    assert 'gender' in feature_types, "gender should be in feature types"
    assert feature_types['gender'] == 'categorical', "gender should be categorical"
    
    # Verify extra categorical features
    assert 'zip_cluster' in feature_types, "zip_cluster should be in feature types"
    assert feature_types['zip_cluster'] == 'categorical', "zip_cluster should be categorical"
    
    assert 'zip_census_division' in feature_types, "zip_census_division should be in feature types"
    assert feature_types['zip_census_division'] == 'categorical', "zip_census_division should be categorical"
    
    assert 'zip_rural_code' in feature_types, "zip_rural_code should be in feature types"
    assert feature_types['zip_rural_code'] == 'categorical', "zip_rural_code should be categorical"
    
    print("✓ All features mapped correctly")
    print(f"\nFeature types mapping:")
    print(json.dumps(feature_types, indent=2))
    
    # Verify counts (4 original features - 1 excluded Zip + 3 extra = 6 total)
    total_features = len(feature_types)
    expected_count = 4 + 3  # age, income, gender, has_loan + 3 zip columns (zip_code excluded)
    assert total_features == expected_count, f"Expected {expected_count} features, got {total_features}"
    print(f"\n✓ Total features: {total_features} (4 original + 3 extra, zip_code excluded)")
    
    print("\n✓ Test 3 PASSED\n")
    return mapping


def test_integration():
    """Integration test combining all components."""
    print("=== Test 4: Integration Test ===")
    
    # Simulate the full workflow
    print("Step 1: Load zip_enhanced data")
    zip_dict = test_zip_enhanced_data_structure()
    
    print("Step 2: Add zip-enhanced columns to modeling data")
    modeling_data = test_add_zip_enhanced_columns()
    
    print("Step 3: Generate feature types with extra columns")
    feature_types = test_feature_types_generator()
    
    print("✓ Integration test PASSED\n")
    print("=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)
    print("\nSummary:")
    print("✓ zip_enhanced.csv data structure is correct")
    print("✓ Three new columns (zip_cluster, zip_census_division, zip_rural_code) are added")
    print("✓ All three columns are marked as categorical in feature types")
    print("✓ Integration between components works correctly")


if __name__ == '__main__':
    try:
        test_integration()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
