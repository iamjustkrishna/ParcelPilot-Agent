FROM python:3.11-slim

WORKDIR /app

# Install build essentials and curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Initialize DB and Embeddings if not already present
RUN python -m backend.db.seed || true
RUN python backend/rag/indexer.py || true

# Expose default port
EXPOSE 8000

ENV HOST=0.0.0.0
ENV PORT=8000

# Start FastAPI application
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
