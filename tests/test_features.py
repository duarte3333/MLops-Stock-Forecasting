"""Tests for feature engineering module"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from mlops_stock.features.build_features import create_features, build_features


@pytest.fixture
def sample_stock_data():
    """Create sample stock data for testing"""
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    # Generate realistic stock price data
    base_price = 150
    prices = []
    for i in range(100):
        change = np.random.normal(0, 2)
        base_price = max(50, base_price + change)  # Ensure price stays positive
        prices.append(base_price)
    
    df = pd.DataFrame({
        'Open': prices,
        'High': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'Low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, 100)
    }, index=dates)
    
    return df


def test_create_features(sample_stock_data):
    """Test that features are created correctly"""
    df_features = create_features(sample_stock_data)
    
    # Check that new feature columns are added
    expected_features = ['Return', 'MA5', 'MA10', 'MA30', 'RSI', 'STOCH_K', 'STOCH_D']
    for feature in expected_features:
        assert feature in df_features.columns, f"Feature {feature} should be created"
    
    # Check that original columns are preserved
    original_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    for col in original_cols:
        assert col in df_features.columns, f"Original column {col} should be preserved"


def test_features_shape(sample_stock_data):
    """Test that features shape is correct"""
    df_features = create_features(sample_stock_data)
    
    # After creating features, some rows will have NaN due to rolling windows
    # But the shape should match the original (before dropna)
    assert df_features.shape[0] == sample_stock_data.shape[0], \
        "Number of rows should match original data"
    
    # Should have more columns than original
    assert df_features.shape[1] > sample_stock_data.shape[1], \
        "Should have more columns after feature engineering"


def test_build_features_saves_file(sample_stock_data):
    """Test that build_features saves features to file"""
    # Save sample data first
    test_input_path = "data/raw/test_features_input.csv"
    test_output_path = "data/processed/test_features_output.csv"
    
    Path(test_input_path).parent.mkdir(parents=True, exist_ok=True)
    sample_stock_data.to_csv(test_input_path)
    
    # Build features
    df_features = build_features(input_path=test_input_path, output_path=test_output_path, dropna=True)
    
    # Check that output file exists
    assert Path(test_output_path).exists(), "Features file should be saved"
    
    # Check that loaded file matches returned DataFrame
    df_loaded = pd.read_csv(test_output_path, index_col=0, parse_dates=True)
    pd.testing.assert_frame_equal(df_features, df_loaded)
    
    # Clean up
    Path(test_input_path).unlink(missing_ok=True)
    Path(test_output_path).unlink(missing_ok=True)


def test_features_dropna(sample_stock_data):
    """Test that dropna works correctly"""
    df_features = create_features(sample_stock_data)
    df_with_na = df_features.copy()
    df_no_na = df_features.dropna()
    
    # After dropna, should have fewer or equal rows
    assert len(df_no_na) <= len(df_with_na), \
        "After dropna, should have fewer or equal rows"
    
    # No NaN values in numeric columns
    numeric_cols = df_no_na.select_dtypes(include=[np.number]).columns
    assert df_no_na[numeric_cols].isna().sum().sum() == 0, \
        "No NaN values should remain after dropna"

