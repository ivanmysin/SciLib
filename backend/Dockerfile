FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install poetry==2.0.0

# Configure poetry for CPU-only PyTorch (reduces image size from ~3GB to ~1GB)
RUN poetry config virtualenvs.create false \
    && poetry source add --priority=explicit pytorch-cpu https://download.pytorch.org/whl/cpu

# Copy pyproject.toml and poetry.lock first for better caching
COPY pyproject.toml poetry.lock* ./

# Install dependencies (split into two layers for better cache utilization)
RUN poetry install --only main --no-interaction --no-ansi --no-root

# Copy application code
COPY . .

# Create storage directory
RUN mkdir -p /app/storage/blobs /app/storage/pdf

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
