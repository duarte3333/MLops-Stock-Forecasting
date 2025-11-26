# MLOps Stock Forecasting

A production-ready MLOps pipeline for stock price forecasting using XGBoost, featuring data versioning with DVC, modular code structure, and comprehensive testing.

### 1. Installation

```bash
# Clone the repository
git clone
cd MLops-Stock-Forecasting

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize DVC
dvc init
```

### 2. Run the Pipeline

#### Option A: Using Makefile (Recommended)

```bash
# Run the entire pipeline
make all

# Or run individual steps
make download    # Download raw stock data
make features    # Build features from raw data
make train       # Train the model
make predict     # Make predictions

# Run tests
make test

# Clean generated files
make clean
```

#### Option B: Using DVC Pipeline

```bash
# Run the entire pipeline
dvc repro

# Run specific stage
dvc repro download
dvc repro features
dvc repro train

# Check pipeline status
dvc status

# View pipeline graph
dvc dag
```

#### Option C: Direct Python Execution

```bash
# Download data
python -m mlops_stock.data.download_data

# Build features
python -m mlops_stock.features.build_features

# Train model
python -m mlops_stock.models.train

# Make prediction
python -m mlops_stock.models.predict
```

## Unit Testing

Run the test suite:

```bash
# Run all tests
make test
# or
pytest tests/ -v

# Run specific test file
pytest tests/test_data.py -v
pytest tests/test_features.py -v
pytest tests/test_models.py -v
```

## DVC Workflow

This project uses DVC for data and model versioning. See [DVC_SETUP.md](DVC_SETUP.md) for detailed information.

### Basic DVC Commands

```bash
# Check what changed
dvc status

# Run the pipeline
dvc repro

# View pipeline stages
dvc stage list

# Show pipeline graph
dvc dag
```
## 3. Docker

Build docker image:
```
docker build -t mlops-stock:latest .
```

Test training inside docker:
```
docker run mlops-stock:latest python mlops_stock/models/train.py
```

## 4. FastAPI 

### 1. Check if server is running
curl http://localhost:8000/

### 2. Health check
curl http://localhost:8000/health

### 3. Get prediction (using latest features)
curl http://localhost:8000/predict

### 4. Custom prediction
curl -X POST "http://localhost:8000/predict/custom" \
  -H "Content-Type: application/json" \
  -d '{
    "features": [150.0, 0.01, 149.5, 149.0, 148.5, 55.0, 60.0]
  }'
### Run API in container
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/logs:/app/logs \
  mlops-stock:latest python -m mlops_stock.serve.app

  Understanding the endpoints
GET / — API info
GET /health — Health check (model loaded, files exist)
GET /predict — Predict using the latest features from data/processed/features.csv
POST /predict/custom — Predict with custom feature values

1. User sends: GET http://localhost:8000/predict
                    ↓
2. FastAPI receives request
                    ↓
3. Calls predict_next_day_price() function
                    ↓
4. Checks: Is _model loaded? 
   - If NO → Load from disk
   - If YES → Use cached model
                    ↓
5. Calls predict_next_day() function:
   - Reads data/processed/features.csv
   - Gets last row (most recent data)
   - Extracts: [Close, Return, MA5, MA10, MA30, RSI, STOCH_D]
                    ↓
6. Model.predict([features]) → Returns price
                    ↓
7. Returns JSON: {"prediction": 152.34, "message": "..."}