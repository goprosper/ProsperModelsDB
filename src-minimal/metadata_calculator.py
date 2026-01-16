"""
Metadata calculation utilities for modeling data analysis.

This module provides functionality to calculate dataset statistics
including sample sizes and positive class ratios for ML datasets.
"""

import pandas as pd
import logging

logger = logging.getLogger(__name__)


class MetadataCalculator:
    """Calculate metadata statistics for modeling datasets."""

    def calculate_sample_size(self, dataframe):
        """
        Calculate the number of rows in the dataset (sample size).

        Args:
            dataframe (pd.DataFrame): The dataset to analyze

        Returns:
            int: Number of rows in the dataset (sample size)
        """
        if dataframe is None or dataframe.empty:
            return 0
        return len(dataframe)

    def calculate_positive_class_ratio(self, dataframe, label_column):
        """
        Calculate the decimal ratio of rows with positive target labels.

        Args:
            dataframe (pd.DataFrame): The dataset to analyze
            label_column (str): Name of the label column

        Returns:
            float: Decimal ratio of positive labels (0-1), or 0 if no data
        """
        if dataframe is None or dataframe.empty:
            return 0.0

        if label_column not in dataframe.columns:
            logger.warning(f"Label column '{label_column}' not found in "
                           f"dataset")
            return 0.0

        try:
            # Get the label column values
            label_values = dataframe[label_column]

            # Count total non-null values
            total_count = label_values.notna().sum()

            if total_count == 0:
                logger.warning("No valid label values found")
                return 0.0

            # Count positive labels (value = 1)
            # Handle both numeric and string representations
            positive_count = 0
            for value in label_values:
                if pd.notna(value):
                    try:
                        # Try to convert to int and check if it equals 1
                        if int(float(str(value))) == 1:
                            positive_count += 1
                    except (ValueError, TypeError):
                        # Skip invalid values
                        continue

            # Calculate decimal ratio (0-1)
            ratio = positive_count / total_count
            return round(ratio, 4)  # Round to 4 decimal places for precision

        except Exception as e:
            logger.error(f"Error calculating positive class ratio: {e}")
            return 0.0

    def get_dataset_metadata(self, dataframe, label_column=None):
        """
        Get comprehensive dataset metadata.

        Args:
            dataframe (pd.DataFrame): The dataset to analyze
            label_column (str, optional): Name of the label column

        Returns:
            dict: Dictionary containing dataset metadata
        """
        metadata = {
            "SampleSize": self.calculate_sample_size(dataframe)
        }

        # Only calculate positive class ratio if label column is provided
        if label_column:
            metadata["PositiveClassRatio"] = (
                self.calculate_positive_class_ratio(dataframe, label_column)
            )

        return metadata