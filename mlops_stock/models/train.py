"""Train stock forecasting model"""

import pandas as pd
import pickle
import xgboost as xgb
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np
from mlops_stock.utils.logger import setup_logger

logger = setup_logger()


def train_model(features_path: str = "data/processed/features.csv", model_path: str = "models/baseline_model.pkl",
    test_size: float = 0.2, features_list: list = None, n_estimators: int = 1000, early_stopping_rounds: int = 50,
    learning_rate: float = 0.01) -> dict:
    logger.info(f"Loading features from {features_path}")
    
    # Load features
    df = pd.read_csv(features_path, index_col=0, parse_dates=True)
    
    # Default features if not specified
    if features_list is None:
        features_list = ['Close', 'Return', 'MA5', 'MA10', 'MA30', 'RSI', 'STOCH_D']
    
    # Create target variable (next day's close price)
    df['Target'] = df['Close'].shift(-1)
    df = df.dropna()
    
    # Split features and target
    X = df[features_list]
    y = df['Target']
    
    logger.info(f"Data shape: X={X.shape}, y={y.shape}")
    logger.info(f"Using features: {features_list}")
    
    # Train/test split
    split_idx = int(len(df) * (1 - test_size))
    X_train = X.iloc[:split_idx]
    y_train = y.iloc[:split_idx]
    X_test = X.iloc[split_idx:]
    y_test = y.iloc[split_idx:]
    
    logger.info(f"Train set: {len(X_train)} samples")
    logger.info(f"Test set: {len(X_test)} samples")
    
    # Train model
    logger.info("Training XGBoost model...")
    model = xgb.XGBRegressor(n_estimators=n_estimators, early_stopping_rounds=early_stopping_rounds,learning_rate=learning_rate)
    model.fit(X_train, y_train, eval_set=[(X_train, y_train), (X_test, y_test)], verbose=False)
    logger.info("Model training completed")
    
    # Make predictions
    y_pred = model.predict(X_test)
    
    # Calculate metrics
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)
    
    logger.info(f"Test Metrics - MSE: {mse:.4f}, MAE: {mae:.4f}, RMSE: {rmse:.4f}, R2: {r2:.4f}")
    
    # Feature importance
    feature_importance = pd.DataFrame({'feature': model.feature_names_in_,'importance': model.feature_importances_}).sort_values('importance', ascending=False)
    
    logger.info("Feature importance:")
    for _, row in feature_importance.iterrows():
        logger.info(f"  {row['feature']}: {row['importance']:.4f}")
    
    # Create model directory if it doesn't exist
    model_file = Path(model_path)
    model_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save model
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    logger.info(f"Model saved to {model_path}")
    
    return {'model': model,
        'metrics': {'mse': mse,'mae': mae,'rmse': rmse,'r2': r2},
        'feature_importance': feature_importance,
        'X_test': X_test,
        'y_test': y_test,
        'y_pred': y_pred
    }


if __name__ == "__main__":
    # Example usage
    results = train_model()
    print(f"Model trained with R2 score: {results['metrics']['r2']:.4f}")

