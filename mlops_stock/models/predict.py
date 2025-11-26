"""Make predictions using trained model"""

import pandas as pd
import pickle
from pathlib import Path
from mlops_stock.utils.logger import setup_logger

logger = setup_logger()


def load_model(model_path: str = "models/baseline_model.pkl"):
    logger.info(f"Loading model from {model_path}")
    if not Path(model_path).exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    with open(model_path, "rb") as f:
        model = pickle.load(f)

    logger.info("Model loaded successfully")
    return model


def predict_next_day(
    features_path: str = "data/processed/features.csv",
    model_path: str = "models/baseline_model.pkl",
    features_list: list = None,
) -> float:
    logger.info("Making prediction for next day")

    # Load model
    model = load_model(model_path)

    # Load features
    df = pd.read_csv(features_path, index_col=0, parse_dates=True)

    # Use model's feature names if not specified
    if features_list is None:
        features_list = list(model.feature_names_in_)

    # Get the most recent row (last available data)
    latest_features = df[features_list].iloc[-1:].values

    # Make prediction
    prediction = model.predict(latest_features)[0]
    logger.info(f"Predicted next day close price: ${prediction:.2f}")

    return prediction


if __name__ == "__main__":
    # Example usage
    prediction = predict_next_day()
    print(f"Next day prediction: ${prediction:.2f}")
