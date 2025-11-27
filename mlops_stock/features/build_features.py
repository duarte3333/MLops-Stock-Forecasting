"""Feature engineering for stock forecasting with optional S3 support"""

import os
import pandas as pd
import ta
from pathlib import Path
from mlops_stock.utils.logger import setup_logger

logger = setup_logger()

# S3 configuration from environment variables
USE_S3 = os.getenv("USE_S3", "false").lower() == "true"
S3_BUCKET_RAW = os.getenv("S3_BUCKET_RAW", "mlops-stock-raw")
S3_BUCKET_FEATURES = os.getenv("S3_BUCKET_FEATURES", "mlops-stock-features")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Initialize S3 client if using S3
s3_client = None
if USE_S3:
    try:
        import boto3
        s3_client = boto3.client("s3", region_name=AWS_REGION)
        logger.info(f"S3 enabled. Buckets: {S3_BUCKET_RAW}, {S3_BUCKET_FEATURES}")
    except ImportError:
        logger.warning("boto3 not installed. S3 functionality disabled.")
        USE_S3 = False


def create_features(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Creating features from raw data")
    df = df.copy()

    # Price-based features
    df["Return"] = df["Close"].pct_change()

    # Moving averages
    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA10"] = df["Close"].rolling(10).mean()
    df["MA30"] = df["Close"].rolling(30).mean()

    # RSI (Relative Strength Index)
    df["RSI"] = ta.momentum.RSIIndicator(close=df["Close"], window=14).rsi()

    # Stochastic Oscillator
    stoch = ta.momentum.StochasticOscillator(
        high=df["High"], low=df["Low"], close=df["Close"], window=9, smooth_window=6
    )
    df["STOCH_K"] = stoch.stoch()
    df["STOCH_D"] = stoch.stoch_signal()

    logger.info(f"Created features. Shape: {df.shape}")
    logger.info(f"Feature columns: {list(df.columns)}")

    return df


def build_features(
    input_path: str = "data/raw/stock_data.csv",
    output_path: str = "data/processed/features.csv",
    dropna: bool = True,
    ticker: str = "AAPL",
) -> pd.DataFrame:
    logger.info(f"Loading data from {input_path}")

    # Load data (from local or S3)
    if USE_S3 and s3_client:
        try:
            # Try to download from S3 first
            s3_key = f"{ticker}/stock_data.csv"
            local_input = "/tmp/stock_data.csv"
            s3_client.download_file(S3_BUCKET_RAW, s3_key, local_input)
            df = pd.read_csv(local_input, index_col=0, parse_dates=True)
            logger.info(f"Loaded data from s3://{S3_BUCKET_RAW}/{s3_key}")
        except Exception as e:
            logger.warning(f"Failed to load from S3: {str(e)}. Trying local file...")
            df = pd.read_csv(input_path, index_col=0, parse_dates=True)
    else:
        df = pd.read_csv(input_path, index_col=0, parse_dates=True)

    # Create features
    df_features = create_features(df)

    # Drop NaN values if requested
    if dropna:
        initial_len = len(df_features)
        df_features = df_features.dropna()
        logger.info(f"Dropped {initial_len - len(df_features)} rows with NaN values")

    # Create output directory if it doesn't exist
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Save features locally
    df_features.to_csv(output_path)
    logger.info(f"Features saved locally to {output_path}")
    logger.info(f"Final shape: {df_features.shape}")

    # Upload to S3 if enabled
    if USE_S3 and s3_client:
        try:
            s3_key = "features/features.csv"
            s3_client.upload_file(output_path, S3_BUCKET_FEATURES, s3_key)
            logger.info(f"Features uploaded to s3://{S3_BUCKET_FEATURES}/{s3_key}")
        except Exception as e:
            logger.error(f"Failed to upload to S3: {str(e)}")
            # Continue even if S3 upload fails

    return df_features


if __name__ == "__main__":
    # Example usage
    df = build_features()
    print(f"Features shape: {df.shape}")
    print(df.head())
