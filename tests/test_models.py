"""Tests for model training and prediction"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import pickle
from mlops_stock.models.train import train_model
from mlops_stock.models.predict import load_model, predict_next_day


@pytest.fixture
def sample_features_data():
    """Create sample features data for testing"""
    dates = pd.date_range('2023-01-01', periods=200, freq='D')
    np.random.seed(42)
    
    # Generate realistic features
    base_price = 150
    prices = []
    for i in range(200):
        change = np.random.normal(0, 2)
        base_price = max(50, base_price + change)
        prices.append(base_price)
    
    df = pd.DataFrame({
        'Open': prices,
        'High': [p * 1.02 for p in prices],
        'Low': [p * 0.98 for p in prices],
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, 200),
        'Return': np.random.normal(0, 0.01, 200),
        'MA5': prices,
        'MA10': prices,
        'MA30': prices,
        'RSI': np.random.uniform(30, 70, 200),
        'STOCH_K': np.random.uniform(0, 100, 200),
        'STOCH_D': np.random.uniform(0, 100, 200)
    }, index=dates)
    
    # Save to file for testing
    test_path = "data/processed/test_train_features.csv"
    Path(test_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(test_path)
    
    yield test_path
    
    # Cleanup
    Path(test_path).unlink(missing_ok=True)


def test_model_trains_without_errors(sample_features_data):
    """Test that model trains without errors"""
    model_path = "models/test_model.pkl"
    
    try:
        results = train_model(
            features_path=sample_features_data,
            model_path=model_path,
            test_size=0.2,
            n_estimators=10,  # Small number for faster testing
            early_stopping_rounds=5
        )
        
        # Check that model was created
        assert results['model'] is not None, "Model should be created"
        
        # Check that metrics exist
        assert 'metrics' in results, "Results should contain metrics"
        assert 'mse' in results['metrics'], "Metrics should contain MSE"
        assert 'mae' in results['metrics'], "Metrics should contain MAE"
        assert 'rmse' in results['metrics'], "Metrics should contain RMSE"
        assert 'r2' in results['metrics'], "Metrics should contain R2"
        
        # Check that model file was saved
        assert Path(model_path).exists(), "Model file should be saved"
        
    finally:
        # Cleanup
        Path(model_path).unlink(missing_ok=True)


def test_model_saves_correctly(sample_features_data):
    """Test that model saves and loads correctly"""
    model_path = "models/test_model2.pkl"
    
    try:
        # Train and save model
        results = train_model(
            features_path=sample_features_data,
            model_path=model_path,
            test_size=0.2,
            n_estimators=10,
            early_stopping_rounds=5
        )
        
        # Load model
        loaded_model = load_model(model_path)
        
        # Check that loaded model has same feature names
        assert list(loaded_model.feature_names_in_) == list(results['model'].feature_names_in_), \
            "Loaded model should have same feature names"
        
    finally:
        # Cleanup
        Path(model_path).unlink(missing_ok=True)


def test_predict_next_day(sample_features_data):
    """Test that prediction works"""
    model_path = "models/test_model3.pkl"
    
    try:
        # Train model first
        train_model(
            features_path=sample_features_data,
            model_path=model_path,
            test_size=0.2,
            n_estimators=10,
            early_stopping_rounds=5
        )
        
        # Make prediction
        prediction = predict_next_day(
            features_path=sample_features_data,
            model_path=model_path
        )
        
        # Check that prediction is a number (including numpy numeric types)
        assert isinstance(prediction, (int, float, np.integer, np.floating)), "Prediction should be a number"
        assert float(prediction) > 0, "Stock price prediction should be positive"
        
    finally:
        # Cleanup
        Path(model_path).unlink(missing_ok=True)


def test_model_metrics_are_reasonable(sample_features_data):
    """Test that model metrics are reasonable values"""
    model_path = "models/test_model4.pkl"
    
    try:
        results = train_model(
            features_path=sample_features_data,
            model_path=model_path,
            test_size=0.2,
            n_estimators=10,
            early_stopping_rounds=5
        )
        
        metrics = results['metrics']
        
        # MSE and RMSE should be positive
        assert metrics['mse'] > 0, "MSE should be positive"
        assert metrics['rmse'] > 0, "RMSE should be positive"
        assert metrics['mae'] > 0, "MAE should be positive"
        
        # R2 should be between -inf and 1 (can be negative for bad models)
        assert metrics['r2'] <= 1, "R2 should be <= 1"
        
    finally:
        # Cleanup
        Path(model_path).unlink(missing_ok=True)

