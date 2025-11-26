# Use Python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if needed for some packages)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies during build stage
RUN pip install --no-cache-dir -r requirements.txt 

# Install linting tools
RUN pip install --no-cache-dir black flake8

# Copy the entire project
COPY . .

# Create necessary directories
RUN mkdir -p data/raw data/processed models logs

# Set Python path
ENV PYTHONPATH=/app

# Default command (can be overridden)
CMD ["python", "-m", "mlops_stock.models.train"] 
# To start the container with the training process