"""Download stock data using yfinance with optional S3 support"""

import os
import yfinance as yf
import pandas as pd
from pathlib import Path
from mlops_stock.utils.logger import setup_logger

logger = setup_logger()

# S3 configuration from environment variables
USE_S3 = os.getenv("USE_S3", "false").lower() == "true"
S3_BUCKET_RAW = os.getenv("S3_BUCKET_RAW", "mlops-stock-raw")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Initialize S3 client if using S3
s3_client = None
if USE_S3:
    try:
        import boto3
        s3_client = boto3.client("s3", region_name=AWS_REGION)
        logger.info(f"S3 enabled. Bucket: {S3_BUCKET_RAW}")
    except ImportError:
        logger.warning("boto3 not installed. S3 functionality disabled.")
        USE_S3 = False


def download_data(
    ticker: str = "AAPL",
    period: str = "5y",
    output_path: str = "data/raw/stock_data.csv",
) -> pd.DataFrame:

    logger.info(f"Downloading data for {ticker} for period {period}")

    try:
        df = yf.download(ticker, period=period, auto_adjust=False)

        # Handle multi-level columns (yfinance sometimes returns MultiIndex)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)

        logger.info(f"Downloaded {len(df)} rows of data")
        logger.info(f"Date range: {df.index.min()} to {df.index.max()}")

        # Create output directory if it doesn't exist
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Save to CSV locally
        df.to_csv(output_path)
        logger.info(f"Data saved locally to {output_path}")

        # Upload to S3 if enabled
        if USE_S3 and s3_client:
            try:
                s3_key = f"{ticker}/stock_data.csv"
                s3_client.upload_file(output_path, S3_BUCKET_RAW, s3_key)
                logger.info(f"Data uploaded to s3://{S3_BUCKET_RAW}/{s3_key}")
            except Exception as e:
                logger.error(f"Failed to upload to S3: {str(e)}")
                # Continue even if S3 upload fails

        return df

    except Exception as e:
        logger.error(f"Error downloading data: {str(e)}")
        raise


if __name__ == "__main__":
    # Example usage
    df = download_data()
    print(f"Downloaded {len(df)} rows")
    print(df.head())
