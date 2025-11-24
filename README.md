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