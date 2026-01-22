#!/bin/bash
set -e

echo "🚀 Starting Agent Service..."

# Wait for ChromaDB to be ready
echo "⏳ Waiting for ChromaDB to be ready..."
max_attempts=30
attempt=1
while [ $attempt -le $max_attempts ]; do
    if nc -z $CHROMA_HOST $CHROMA_PORT 2>/dev/null; then
        echo "✅ ChromaDB is ready!"
        break
    fi
    echo "   Attempt $attempt/$max_attempts - ChromaDB not ready yet..."
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ ChromaDB failed to start within timeout"
    exit 1
fi

# Verify ChromaDB connection
echo "🔧 Verifying ChromaDB connection..."
python -c "
import chromadb
try:
    client = chromadb.HttpClient(host='$CHROMA_HOST', port=$CHROMA_PORT)
    print('✅ ChromaDB connection established')
except Exception as e:
    print(f'⚠️  ChromaDB connection issue: {e}')
" || true

echo ""
echo "✅ Agent service ready. Starting FastAPI..."
echo ""

# Start the FastAPI agent service
exec uvicorn main:app --host 0.0.0.0 --port 8001
