"""Tests for data download module"""

import pandas as pd
from pathlib import Path
from mlops_stock.data.download_data import download_data


def test_download_data():
    """Test that data downloads successfully"""
    # Download a small amount of data for testing
    df = download_data(ticker="AAPL", period="1mo", output_path="data/raw/test_data.csv")
    
    # Check that DataFrame is not empty
    assert len(df) > 0, "Downloaded data should not be empty"
    
    # Check required columns exist
    required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    for col in required_columns:
        assert col in df.columns, f"Column {col} should exist in downloaded data"
    
    # Check that data is saved to file
    assert Path("data/raw/test_data.csv").exists(), "Data file should be saved"
    
    # Clean up
    Path("data/raw/test_data.csv").unlink(missing_ok=True)


def test_download_data_returns_dataframe():
    """Test that download_data returns a pandas DataFrame"""
    df = download_data(ticker="AAPL", period="1mo", output_path="data/raw/test_data2.csv")
    
    assert isinstance(df, pd.DataFrame), "Function should return a pandas DataFrame"
    assert not df.empty, "DataFrame should not be empty"
    
    # Clean up
    Path("data/raw/test_data2.csv").unlink(missing_ok=True)

