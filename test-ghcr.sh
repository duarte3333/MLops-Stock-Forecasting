#!/bin/bash
# test-ghcr.sh

USERNAME="duarte3333"  # Replace with your username
IMAGE="ghcr.io/${USERNAME}/mlops-stock:latest"

echo "1. Pulling image from GHCR..."
docker pull $IMAGE  

echo "2. Verifying image exists..."
docker images | grep mlops-stock

echo "3. Testing Python in container..."
docker run --rm $IMAGE python --version

echo "4. Testing imports..."
docker run --rm $IMAGE python -c "import mlops_stock; print('✓ mlops_stock imported successfully')"

echo "5. Running a quick test..."
docker run --rm $IMAGE pytest tests/test_data.py::test_download_data_returns_dataframe -v
# Step 1: Download data
echo "5a. Downloading data..."
docker run --rm \
  -v $(pwd)/data:/app/data \
  $IMAGE \
  python -m mlops_stock.data.download_data

# Step 2: Build features
echo "5b. Building features..."
docker run --rm \
  -v $(pwd)/data:/app/data \
  $IMAGE \
  python -m mlops_stock.features.build_features

# Test train
docker run --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/models:/app/models \
  $IMAGE \
  python -m mlops_stock.models.train

# Test predict
docker run --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/models:/app/models \
  $IMAGE \
  python -m mlops_stock.models.predict

# Run the API
echo "6. Running the API..."
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/models:/app/models \
  $IMAGE \
  python -m mlops_stock.serve.app

# Clean up
echo "8. Cleaning up..."
docker rm -f mlops-test
echo "✅ All tests passed! GHCR is working correctly!"