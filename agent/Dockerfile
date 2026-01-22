FROM python:3.11-slim

WORKDIR /app

# Install minimal system dependencies for runtime only
# - netcat for health checks
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy runtime requirements (without heavy ingestion dependencies)
COPY requirements.runtime.txt .

# Install Python dependencies for runtime
RUN pip install --no-cache-dir -r requirements.runtime.txt

# Copy application code
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
