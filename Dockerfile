FROM python:3.11-slim

WORKDIR /app

# System deps for faiss-cpu + lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the sentence-transformer model so startup is fast
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy source
COPY . .

# The catalog must exist before the image is useful
# Ensure the data directory exists even if catalog.json is volume-mounted
RUN mkdir -p data

EXPOSE 8000

# Make start script executable
RUN chmod +x start.sh

# start.sh seeds catalog.json if missing, then launches uvicorn
CMD ["./start.sh"]
