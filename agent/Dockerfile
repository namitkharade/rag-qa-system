FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for unstructured[pdf]
# - netcat for health checks
# - poppler-utils for PDF processing
# - tesseract-ocr for OCR in hi_res strategy
# - libmagic1 for file type detection
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    poppler-utils \
    tesseract-ocr \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
