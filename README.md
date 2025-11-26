# MLOps Stock Forecasting

A production-ready MLOps pipeline for stock price forecasting using XGBoost, featuring data versioning with DVC, Docker containerization, CI/CD with GitHub Actions, and a FastAPI inference service.

## 1. Installation

```bash
# Clone the repository
git clone
cd MLops-Stock-Forecasting

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize DVC
dvc init
```

## 2. Run the Pipeline

#### Option A: Using Makefile

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

### Unit Testing

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

## 3. Docker

```bash
# Build Image
docker build -t mlops-stock:latest .

# Download data
docker run --rm -v $(pwd)/data:/app/data mlops-stock:latest \
  python -m mlops_stock.data.download_data

# Build features
docker run --rm -v $(pwd)/data:/app/data mlops-stock:latest \
  python -m mlops_stock.features.build_features

# Train model
docker run --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/models:/app/models \
  mlops-stock:latest \
  python -m mlops_stock.models.train
```

## 4. FastAPI 

```bash
# Local
python -m mlops_stock.serve.app

# Or with Docker
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/models:/app/models \
  mlops-stock:latest \
  python -m mlops_stock.serve.app### API Endpoints
```

- `GET /` - API information
- `GET /health` - Health check (model loaded, files exist)
- `GET /predict` - Predict next day price using latest features
- `POST /predict/custom` - Predict with custom feature values

### Example Usage

```bash
# Health check
curl http://localhost:8000/health

# Get prediction
curl http://localhost:8000/predict

# Custom prediction
curl -X POST "http://localhost:8000/predict/custom" \
  -H "Content-Type: application/json" \
  -d '{"features": [150.0, 0.01, 149.5, 149.0, 148.5, 55.0, 60.0]}'
```

### Interactive API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 5. Using GitHub Container Registry

The Docker image is automatically built and pushed to GHCR on every push to main.

```bash
#Login to GHRC
docker login ghcr.io -u <username> -p <token>

# Pull the image with Github Container Registry
docker pull ghcr.io/duarte3333/mlops-stock:latest

# Run tests
docker run --rm ghcr.io/duarte3333/mlops-stock:latest pytest tests/ -v

export IMAGE=ghcr.io/duarte3333/mlops-stock:latest

# Step 1: Download data
docker run --rm \
  -v $(pwd)/data:/app/data \
  $IMAGE \
  python -m mlops_stock.data.download_data

# Step 2: Build features
docker run --rm \
  -v $(pwd)/data:/app/data \
  $IMAGE \
  python -m mlops_stock.features.build_features

# Step 3: Train model
docker run --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/models:/app/models \
  $IMAGE \
  python -m mlops_stock.models.train

# Step 4: Run the API
echo "6. Running the API..."
docker run -d -p 8000:8000 \
  --name mlops-api \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/models:/app/models \
  $IMAGE \
  python -m mlops_stock.serve.app

```
### Access the API

Once running, visit:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health


## 6. Format liting

```bash
#Automatically reformats your Python code to a strict, consistent style (PEP 8-like but with its own rules).
pip install black 
black mlops_stock/ tests/

# Check syntax errors, PEP 8 style violations, Undefined variables, Unused imports, Complexity issues (via plugins)
pip install flake8
flake8 mlops_stock/ tests/
```

## 7. CI/CD

The project includes GitHub Actions workflows that:

- Run tests on every push/PR
- Build Docker images
- Push images to GitHub Container Registry (GHCR)
- Check code formatting with black and flake8