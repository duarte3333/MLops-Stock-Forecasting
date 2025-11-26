"""Download stock data using yfinance"""

import yfinance as yf
import pandas as pd
from pathlib import Path
from mlops_stock.utils.logger import setup_logger

logger = setup_logger()


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

        # Save to CSV
        df.to_csv(output_path)
        logger.info(f"Data saved to {output_path}")

        return df

    except Exception as e:
        logger.error(f"Error downloading data: {str(e)}")
        raise


if __name__ == "__main__":
    # Example usage
    df = download_data()
    print(f"Downloaded {len(df)} rows")
    print(df.head())
