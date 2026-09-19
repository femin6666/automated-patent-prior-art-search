FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered output logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install minimal build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# STEP 1: Install CPU-only PyTorch from official PyTorch CPU wheel index
# This reduces PyTorch installation size from ~4.6 GB (with CUDA) down to ~600 MB
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# STEP 2: Copy requirements and install remaining dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# STEP 3: Copy backend application code
COPY . .

# Expose backend port
EXPOSE 8000

# Start FastAPI application using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
