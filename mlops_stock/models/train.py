"""Train stock forecasting model with optional S3 support"""

import os
import pandas as pd
import pickle
import xgboost as xgb
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np
from mlops_stock.utils.logger import setup_logger

logger = setup_logger()

# S3 configuration from environment variables
USE_S3 = os.getenv("USE_S3", "false").lower() == "true"
S3_BUCKET_FEATURES = os.getenv("S3_BUCKET_FEATURES", "mlops-stock-features")
S3_BUCKET_MODELS = os.getenv("S3_BUCKET_MODELS", "mlops-stock-models")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Initialize S3 client if using S3
s3_client = None
if USE_S3:
    try:
        import boto3
        s3_client = boto3.client("s3", region_name=AWS_REGION)
        logger.info(f"S3 enabled. Buckets: {S3_BUCKET_FEATURES}, {S3_BUCKET_MODELS}")
    except ImportError:
        logger.warning("boto3 not installed. S3 functionality disabled.")
        USE_S3 = False


def train_model(
    features_path: str = "data/processed/features.csv",
    model_path: str = "models/baseline_model.pkl",
    test_size: float = 0.2,
    features_list: list = None,
    n_estimators: int = 250,
    early_stopping_rounds: int = 50,
    learning_rate: float = 0.01,
) -> dict:
    logger.info(f"Loading features from {features_path}")

    # Load features (from local or S3)
    if USE_S3 and s3_client:
        try:
            # Try to download from S3 first
            s3_key = "features/features.csv"
            local_features = "/tmp/features.csv"
            s3_client.download_file(S3_BUCKET_FEATURES, s3_key, local_features)
            df = pd.read_csv(local_features, index_col=0, parse_dates=True)
            logger.info(f"Loaded features from s3://{S3_BUCKET_FEATURES}/{s3_key}")
        except Exception as e:
            logger.warning(f"Failed to load from S3: {str(e)}. Trying local file...")
            df = pd.read_csv(features_path, index_col=0, parse_dates=True)
    else:
        df = pd.read_csv(features_path, index_col=0, parse_dates=True)

    # Default features if not specified
    if features_list is None:
        features_list = ["Close", "Return", "MA5", "MA10", "MA30", "RSI", "STOCH_D"]

    # Create target variable (next day's close price)
    df["Target"] = df["Close"].shift(-1)
    df = df.dropna()

    # Split features and target
    X = df[features_list]
    y = df["Target"]

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
    model = xgb.XGBRegressor(
        n_estimators=n_estimators,
        early_stopping_rounds=early_stopping_rounds,
        learning_rate=learning_rate,
    )
    model.fit(
        X_train, y_train, eval_set=[(X_train, y_train), (X_test, y_test)], verbose=False
    )
    logger.info("Model training completed")

    # Make predictions
    y_pred = model.predict(X_test)

    # Calculate metrics
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)

    logger.info(
        f"Test Metrics - MSE: {mse:.4f}, MAE: {mae:.4f}, RMSE: {rmse:.4f}, R2: {r2:.4f}"
    )

    # Feature importance
    feature_importance = pd.DataFrame(
        {"feature": model.feature_names_in_, "importance": model.feature_importances_}
    ).sort_values("importance", ascending=False)

    logger.info("Feature importance:")
    for _, row in feature_importance.iterrows():
        logger.info(f"  {row['feature']}: {row['importance']:.4f}")

    # Create model directory if it doesn't exist
    model_file = Path(model_path)
    model_file.parent.mkdir(parents=True, exist_ok=True)

    # Save model locally
    with open(model_path, "wb") as f:
        pickle.dump(model, f)

    logger.info(f"Model saved locally to {model_path}")

    # Upload model to S3 if enabled
    if USE_S3 and s3_client:
        try:
            s3_key = "models/baseline_model.pkl"
            s3_client.upload_file(model_path, S3_BUCKET_MODELS, s3_key)
            logger.info(f"Model uploaded to s3://{S3_BUCKET_MODELS}/{s3_key}")
        except Exception as e:
            logger.error(f"Failed to upload model to S3: {str(e)}")
            # Continue even if S3 upload fails

    return {
        "model": model,
        "metrics": {"mse": mse, "mae": mae, "rmse": rmse, "r2": r2},
        "feature_importance": feature_importance,
        "X_test": X_test,
        "y_test": y_test,
        "y_pred": y_pred,
    }


if __name__ == "__main__":
    # Example usage
    results = train_model()
    print(f"Model trained with R2 score: {results['metrics']['r2']:.4f}")
