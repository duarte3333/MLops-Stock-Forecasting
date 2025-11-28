# Use Python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if needed for some packages)
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution (much faster than pip)
# uv resolves dependencies 10-100x faster than pip, solving the timeout issue
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies using uv (much faster than pip)
# --system flag installs into system Python (required for Docker)
RUN uv pip install --system --no-cache -r requirements.txt

# Install linting tools using uv
RUN uv pip install --system --no-cache black flake8

# Copy the entire project
COPY . .

# Create necessary directories
RUN mkdir -p data/raw data/processed models logs

# Set Python path
ENV PYTHONPATH=/app

# Default command (can be overridden)
CMD ["python", "-m", "mlops_stock.models.train"] 
# To start the container with the training process