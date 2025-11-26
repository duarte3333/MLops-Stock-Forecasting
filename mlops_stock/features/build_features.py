"""Feature engineering for stock forecasting"""

import pandas as pd
import ta
from pathlib import Path
from mlops_stock.utils.logger import setup_logger

logger = setup_logger()


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
) -> pd.DataFrame:
    logger.info(f"Loading data from {input_path}")

    # Load data
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

    # Save features
    df_features.to_csv(output_path)
    logger.info(f"Features saved to {output_path}")
    logger.info(f"Final shape: {df_features.shape}")

    return df_features


if __name__ == "__main__":
    # Example usage
    df = build_features()
    print(f"Features shape: {df.shape}")
    print(df.head())
