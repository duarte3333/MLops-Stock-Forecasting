.PHONY: download features train predict all clean test install

# Default target
all: download features train

# Install dependencies
install:
	pip install -r requirements.txt

# Download raw stock data
download:
	python -m mlops_stock.data.download_data

# Download raw stock data (with S3)
download-s3:
	USE_S3=true python -m mlops_stock.data.download_data

# Build features from raw data
features:
	python -m mlops_stock.features.build_features

# Build features from raw data (with S3)
features-s3:
	USE_S3=true python -m mlops_stock.features.build_features

# Train the model
train:
	python -m mlops_stock.models.train

# Train the model (with S3)
train-s3:
	USE_S3=true python -m mlops_stock.models.train

# Make predictions
predict:
	python -m mlops_stock.models.predict

# Run all tests
test:
	python -m pytest tests/ -v

# Clean generated files
clean:
	rm -rf data/raw/*.csv
	rm -rf data/processed/*.csv
	rm -rf data/predictions/*.csv
	rm -rf models/*.pkl
	rm -rf logs/*.log
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Help target
help:
	@echo "Available targets:"
	@echo "  make install      - Install dependencies"
	@echo "  make download     - Download raw stock data (local)"
	@echo "  make download-s3  - Download raw stock data (with S3 upload)"
	@echo "  make features     - Build features from raw data (local)"
	@echo "  make features-s3  - Build features from raw data (with S3)"
	@echo "  make train        - Train the model (local)"
	@echo "  make train-s3     - Train the model (with S3)"
	@echo "  make predict      - Make predictions"
	@echo "  make test         - Run unit tests"
	@echo "  make all          - Run download, features, and train (local)"
	@echo "  make clean        - Clean generated files"
	@echo "  make help         - Show this help message"
	@echo ""
	@echo "S3 Environment Variables (optional):"
	@echo "  USE_S3=true                    - Enable S3 mode"
	@echo "  S3_BUCKET_RAW=mlops-stock-raw  - Raw data bucket"
	@echo "  S3_BUCKET_FEATURES=...         - Features bucket"
	@echo "  S3_BUCKET_MODELS=...          - Models bucket"
	@echo "  AWS_REGION=us-east-1          - AWS region"

