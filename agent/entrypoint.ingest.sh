#!/bin/bash
set -e

export CHROMA_DEFAULT_EMBEDDING="none"
export ANONYMIZED_TELEMETRY="False"

echo "🚀 Starting One-Time PDF Ingestion..."

# Wait for ChromaDB to be ready
echo "⏳ Waiting for ChromaDB to be ready..."
max_attempts=30
attempt=1
while [ $attempt -le $max_attempts ]; do
    if nc -z $CHROMA_HOST $CHROMA_PORT 2>/dev/null; then
        echo "ChromaDB is ready!"
        break
    fi
    echo "   Attempt $attempt/$max_attempts - ChromaDB not ready yet..."
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -gt $max_attempts ]; then
    echo "ChromaDB failed to start within timeout"
    exit 1
fi

# Initialize ChromaDB connection
echo "Initializing ChromaDB connection..."
python -c "
import httpx
try:
    # Use raw HTTP request to test ChromaDB without importing chromadb module
    response = httpx.get('http://$CHROMA_HOST:$CHROMA_PORT/api/v1/heartbeat', timeout=10)
    if response.status_code == 200:
        print('ChromaDB connection established')
    else:
        print(f'ChromaDB returned status {response.status_code}')
        exit(1)
except Exception as e:
    print(f'ChromaDB connection failed: {e}')
    exit(1)
" || exit 1

# Run PDF ingestion
if [ -d "/pdfs" ] && [ -n "$(ls -A /pdfs/*.pdf 2>/dev/null)" ]; then
    echo "Ingesting PDFs from /pdfs..."
    python ingest_pdf.py /pdfs
    echo "PDF ingestion completed successfully!"
else
    echo "No PDFs found in /pdfs - nothing to ingest"
fi

echo "Ingestion service completed!"
exit 0
