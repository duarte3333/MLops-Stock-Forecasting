from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List  # <-- THIS IS MISSING!
import pandas as pd
from pathlib import Path
from mlops_stock.models.predict import load_model, predict_next_day
from mlops_stock.utils.logger import setup_logger

logger = setup_logger()
app = FastAPI(title="Stock Price Prediction API", version="1.0.0")

# Global model cache
_model = None
_model_path = "models/baseline_model.pkl"
_features_path = "data/processed/features.csv"
# Pydantic - validates request/response data
from pydantic import BaseModel

# Your existing prediction functions
from mlops_stock.models.predict import load_model, predict_next_day

# Global variables
_model = None  # Will hold the loaded model (cached in memory)
_model_path = "models/baseline_model.pkl"  # Where model file is
_features_path = "data/processed/features.csv"  # Where features are


class PredictionRequest(BaseModel):
    features: List[float]  # User provides: [150.0, 0.01, 149.5, ...]
    feature_names: Optional[List[str]] = None  # Optional feature names

class PredictionResponse(BaseModel):
    prediction: float  # API returns: {"prediction": 152.34, "message": "..."}
    message: str


@app.on_event("startup")
async def load_model_on_startup():
    """Load model when the API starts"""
    global _model
    try:
        if Path(_model_path).exists():
            _model = load_model(_model_path)
            logger.info("Model loaded successfully on startup")
        else:
            logger.warning(f"Model file not found at {_model_path}")
    except Exception as e:
        logger.error(f"Error loading model on startup: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint - returns API information"""
    return {
        "message": "Stock Price Prediction API",
        "version": "1.0.0",
        "endpoints": {
            "/predict": "Predict next day price using latest features",
            "/predict/custom": "Predict with custom features",
            "/health": "Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    model_loaded = _model is not None
    model_exists = Path(_model_path).exists()
    features_exist = Path(_features_path).exists()
    
    return {
        "status": "healthy" if (model_loaded or model_exists) else "degraded",
        "model_loaded": model_loaded,
        "model_exists": model_exists,
        "features_exist": features_exist
    }


@app.get("/predict", response_model=PredictionResponse)
async def predict_next_day_price():
    """
    Predict next day's stock price using the most recent features.
    """
    global _model  # Move this to the top of the function
    try:
        if _model is None:
            # Try to load model if not loaded
            if not Path(_model_path).exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"Model file not found at {_model_path}. Please train the model first."
                )
            _model = load_model(_model_path)
        
        # Use the predict function
        prediction = predict_next_day(
            features_path=_features_path,
            model_path=_model_path
        )
        
        return PredictionResponse(
            prediction=float(prediction),
            message="Prediction successful"
        )
    
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/predict/custom", response_model=PredictionResponse)
async def predict_custom(request: PredictionRequest):
    """
    Make prediction with custom feature values.
    
    Expected features (in order): Close, Return, MA5, MA10, MA30, RSI, STOCH_D
    """
    global _model  # Move this to the top of the function
    try:
        if _model is None:
            if not Path(_model_path).exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"Model file not found at {_model_path}"
                )
            _model = load_model(_model_path)
        
        # Get feature names from model
        if request.feature_names is None:
            feature_names = list(_model.feature_names_in_)
        else:
            feature_names = request.feature_names
        
        # Validate feature count
        if len(request.features) != len(feature_names):
            raise HTTPException(
                status_code=400,
                detail=f"Expected {len(feature_names)} features, got {len(request.features)}"
            )
        
        # Create DataFrame for prediction
        features_df = pd.DataFrame([request.features], columns=feature_names)
        
        # Make prediction
        prediction = _model.predict(features_df.values)[0]
        
        return PredictionResponse(
            prediction=float(prediction),
            message="Custom prediction successful"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Custom prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)