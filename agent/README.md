# Agent - LangGraph AI Reasoning Engine

Advanced multi-step reasoning agent powered by LangGraph, LangChain, and GPT-4 for hybrid RAG compliance checking with regulatory documents and architectural drawings.

## 🎯 Overview

The agent is the core intelligence of the Hybrid RAG system, combining:
- **🗄️ Persistent Data**: Semantic search over regulatory PDFs in ChromaDB
- **⚡ Ephemeral Data**: Real-time geometry analysis of architectural drawings from JSON
- **🧠 Multi-Step Reasoning**: LangGraph workflow with retrieval, analysis, reasoning, critique, and response
- **📐 Spatial Intelligence**: Custom geometry tools using Shapely for compliance calculations

## ✨ Key Features

### 1. **LangGraph Multi-Step Workflow**
Sophisticated reasoning pipeline with 5 nodes:
- **Retrieve**: Semantic search over regulatory documents in ChromaDB
- **Analyze Ephemeral**: Parse and analyze architectural drawing geometry
- **Reason**: LLM synthesizes regulations + measurements
- **Critique**: Self-validation of response quality
- **Respond**: Structured output with citations and reasoning steps

### 2. **Advanced PDF Processing with Table Extraction**
Powered by `unstructured` library with hi_res strategy:
- **Complex Layouts**: Multi-column documents, nested sections
- **Table Extraction**: Preserves structure of zoning tables and compliance matrices
- **Format Preservation**: Tables stored as HTML/Markdown, not plain text
- **Metadata Tagging**: Element type classification (table, text, title, heading)
- **Hierarchical Chunking**: Parent (2000 chars) + Child (400 chars) strategy

### 3. **Intelligent Geometry Analysis Tool**
Custom LangChain tool using Shapely for spatial reasoning:
- **Area Calculations**: Polygon areas for 50% curtilage rule
- **Distance Measurements**: Boundary clearances for 2m setback rule
- **Spatial Relationships**: Overlaps, intersections, containment
- **Layer-Based Analysis**: Categorized by drawing layers (Walls, Plot Boundary, etc.)
- **Zero-Shot Reasoning**: LLM can "see" drawings through geometric calculations

### 4. **Parent Document Retriever Strategy**
Hierarchical chunking for complex regulatory documents:
- **Parent Chunks**: 2000 characters - preserves context and structure
- **Child Chunks**: 400 characters - precise semantic matching
- **Linked Retrieval**: Search at child level, return parent context
- **Overlap**: 100 characters - maintains continuity

### 5. **Structured Output with Citations**
Pydantic-validated responses:
- **Compliance Verdict**: Boolean is_compliant field
- **Detailed Explanation**: Full reasoning with findings
- **Regulatory Citations**: Source documents with specific sections and references
- **Reasoning Trace**: Step-by-step workflow execution log

### 6. **Redis Integration for Ephemeral Data**
- Fetches session-specific drawing data from Redis
- No persistence in vector database
- 1-hour TTL for session data
- User-isolated storage

### 7. **Production-Ready API**
FastAPI service with:
- Health check endpoint
- Query processing endpoint
- OpenAPI documentation
- Async request handling

## 🏗️ Architecture

### LangGraph Workflow

```
                    User Query + Drawing Data
                              ↓
                  ┌───────────────────────┐
                  │   RETRIEVE NODE       │
                  │  • Query ChromaDB     │
                  │  • Semantic search    │
                  │  • Retrieve top-k     │
                  │    regulations        │
                  └──────────┬────────────┘
                             ↓
                  ┌───────────────────────┐
                  │  ANALYZE EPHEMERAL    │
                  │  • Parse drawing JSON │
                  │  • Geometry tool      │
                  │  • Calculate areas    │
                  │  • Measure distances  │
                  └──────────┬────────────┘
                             ↓
                  ┌───────────────────────┐
                  │    REASON NODE        │
                  │  • LLM synthesis      │
                  │  • Combine both       │
                  │    contexts           │
                  │  • Generate answer    │
                  └──────────┬────────────┘
                             ↓
                  ┌───────────────────────┐
                  │   CRITIQUE NODE       │
                  │  • Validate quality   │
                  │  • Check citations    │
                  │  • Verify compliance  │
                  └──────────┬────────────┘
                             ↓
                    ┌────────┴────────┐
                    │                 │
         Needs Revision?            Quality OK?
                    │                 │
                    ▼                 ▼
            ┌───────────┐   ┌────────────────┐
            │  Loop to  │   │  RESPOND NODE  │
            │   REASON  │   │  • Format      │
            └───────────┘   │    output      │
                            │  • Structure   │
                            │    citations   │
                            └────────────────┘
                                    ↓
                              Final Response
```

### Data Handling Strategy

| Data Type | Storage | Lifetime | Indexed | Purpose |
|-----------|---------|----------|---------|---------|
| **Regulatory PDFs** | ChromaDB | Permanent | Yes | Semantic search across sessions |
| **Drawing JSON** | Redis | 1 hour | No | Session-specific geometry analysis |
| **Session Data** | Redis | 1 hour | No | User context and history |

### Component Architecture

```
agent/
├── graph.py               ⭐ LangGraph workflow (primary implementation)
├── agent.py               (Legacy, deprecated)
├── geometry_tool.py       📐 Shapely-based spatial analysis
├── vector_store.py        🗄️  ChromaDB client
├── ingest.py              📄 PDF ingestion logic
├── ingest_pdf.py          🔧 CLI tool for ingestion
├── state.py               📊 GraphState definition
├── config.py              ⚙️  Settings & environment
└── main.py                🚀 FastAPI service
```

## 📚 Detailed Feature Documentation

### 1. Advanced PDF Ingestion with Table Extraction

#### Why Advanced Parsing?

Regulatory documents contain:
- ✅ Complex multi-column layouts
- ✅ Nested hierarchical structures (Class A, B, C with subconditions)
- ✅ Tables with zoning rules and compliance matrices
- ✅ Cross-references between sections

**Standard chunking loses this structure.**

#### Solution: `unstructured` Library with `hi_res` Strategy

```python
from unstructured.partition.pdf import partition_pdf

# Parse PDF with table detection
elements = partition_pdf(
    filename="regulations.pdf",
    strategy="hi_res",           # High-resolution parsing
    infer_table_structure=True,  # Extract tables
    include_page_breaks=True
)

# Elements are classified
for element in elements:
    if element.category == "Table":
        print(f"Found table: {element.text}")
        print(f"Metadata: {element.metadata}")
```

#### Table-Specific Handling

Tables are stored separately with special metadata:

```python
{
    'is_table': True,
    'element_type': 'table',
    'content_format': 'html',  # or 'markdown'
    'contains_structured_rules': True,
    'page_number': 5,
    'table_index': 2
}
```

**Benefits**:
- Direct retrieval without chunking
- Preserved formatting for accurate interpretation
- Filtered searches for structured rules
- Better LLM understanding of tabular data

#### Ingestion Commands

**Single PDF**:
```bash
python ingest_pdf.py /path/to/document.pdf
```

**Entire Directory**:
```bash
python ingest_pdf.py /pdfs
```

**With Docker**:
```bash
docker-compose run --rm agent python ingest_pdf.py /pdfs
```

**Programmatic Usage**:
```python
from ingest import RegulatoryDocumentIngester

ingester = RegulatoryDocumentIngester(
    parent_chunk_size=2000,
    child_chunk_size=400,
    chunk_overlap=100
)

stats = ingester.ingest_pdf(
    pdf_path="regulations.pdf",
    source_name="Zoning Regulations",
    document_type="regulation",
    use_parent_retriever=True
)

print(f"Pages: {stats['total_pages']}")
print(f"Tables: {stats.get('table_chunks', 0)}")
print(f"Parent chunks: {stats['parent_chunks']}")
```

#### Output Example

```
================================================================================
Ingesting Permitted Development Rights PDF
================================================================================
✓ Loaded 45 pages from PDF
✓ Extracted 12 tables with structure preservation
✓ Created 156 parent chunks (2000 chars each)
✓ Created 624 child chunks (400 chars each)
✓ Indexed in ChromaDB collection: regulatory_documents
================================================================================
```

### 2. Geometry Analysis Tool

#### Overview

The **AnalyzeGeometry** tool enables the LLM to reason about architectural drawings **without visual images** using computational geometry.

#### Key Capabilities

| Capability | Use Case | Example |
|------------|----------|---------|
| **Area Calculations** | 50% curtilage rule | "Is the extension <50% of plot?" |
| **Distance Measurements** | 2m boundary rule | "Is building 2m from boundary?" |
| **Spatial Relationships** | Overlap detection | "Do structures overlap?" |
| **Layer Analysis** | Object categorization | "Analyze Walls layer" |

#### How It Works

##### 1. Parse Drawing Objects

```python
# INPUT: Raw JSON drawing data
drawing_data = [
    {
        "type": "LINE",
        "layer": "Highway",
        "start": [0, 0],
        "end": [1000, 0]
    },
    {
        "type": "POLYLINE",
        "layer": "Plot Boundary",
        "points": [[0, 0], [1000, 0], [1000, 1000], [0, 1000]],
        "closed": True
    }
]

# CONVERSION: JSON → Shapely geometries
LINE → shapely.LineString([start, end])
POLYLINE (open) → shapely.LineString(points)
POLYLINE (closed) → shapely.Polygon(points)
```

##### 2. Categorize by Layer

```python
geometries_by_layer = {
    "Highway": [LineString(...)],
    "Plot Boundary": [Polygon(...)],
    "Walls": [Polygon(...), Polygon(...)],
    "Doors": [LineString(...), LineString(...)]
}
```

##### 3. Perform Calculations

**Area Analysis**:
```python
plot_area = Polygon(plot_boundary_points).area
building_area = sum([p.area for p in wall_polygons])
percentage = (building_area / plot_area) * 100
```

**Distance Analysis**:
```python
min_distance = walls.distance(boundary)
nearest_pts = nearest_points(walls, boundary)
```

##### 4. Format Results

```
GEOMETRY ANALYSIS REPORT
========================

AREA ANALYSIS:
  Plot Boundary:
    Area: 250,000,000.00 sq units
    Polygons: 1
  Walls:
    Area: 75,000,000.00 sq units
    Polygons: 2
  
  AREA PERCENTAGES:
    Walls coverage: 30.00%

DISTANCE ANALYSIS:
  Walls to Plot Boundary:
    Minimum distance: 2,500.00 units
    Maximum distance: 5,660.00 units
    Average distance: 3,845.50 units

LAYER SUMMARY:
  Total layers: 4
  Total objects: 127
  Lines: 85
  Polylines: 42
```

#### Usage Examples

**Standalone Usage**:
```python
from geometry_tool import AnalyzeGeometryTool

tool = AnalyzeGeometryTool()

result = tool._run(
    question="What percentage of plot is covered by building?",
    drawing_data=drawing_json
)

print(result)
```

**In LangGraph Workflow**:
```python
# Automatically invoked in ANALYZE EPHEMERAL node
state = {
    "user_question": "Does this comply with the 2m boundary rule?",
    "drawing_data": drawing_json,
    ...
}

# Tool is called by the agent
geometry_analysis = geometry_tool._run(
    question=state["user_question"],
    drawing_data=state["drawing_data"]
)
```

### 3. Parent Document Retriever Strategy

#### Problem: Regulatory Document Complexity

Regulatory documents have:
- **Hierarchical structure**: Classes, subclasses, conditions
- **Cross-references**: "As per Section 2.1..."
- **Nested conditions**: "If A and B, then C unless D"
- **Context dependencies**: Rules reference earlier definitions

**Traditional chunking** (simple 500-char splits) **breaks this structure**.

#### Solution: Hierarchical Chunking

```
Original Document (regulatory_doc.pdf)
            ↓
    ┌───────────────────┐
    │  PARENT CHUNKS    │
    │  2000 characters  │  ← Large context preservation
    │  156 chunks       │
    └─────────┬─────────┘
              ↓
    ┌─────────────────────┐
    │   CHILD CHUNKS      │
    │   400 characters    │  ← Precise semantic search
    │   624 chunks        │
    │   (linked to parent)│
    └─────────────────────┘
              ↓
        Vector Embeddings
              ↓
         ChromaDB Storage
```

#### How It Works

1. **Create parent chunks** (2000 chars): Preserve full context
2. **Split into child chunks** (400 chars): Enable precise search
3. **Link children → parents**: Maintain relationships
4. **Search at child level**: Fine-grained semantic matching
5. **Return parent content**: Full context in results

#### Configuration

```python
from ingest import RegulatoryDocumentIngester

ingester = RegulatoryDocumentIngester(
    parent_chunk_size=2000,  # Context window
    child_chunk_size=400,     # Search granularity
    chunk_overlap=100         # Continuity between chunks
)

stats = ingester.ingest_pdf(
    pdf_path="document.pdf",
    use_parent_retriever=True  # Enable parent-child strategy
)
```

#### Comparison

| Strategy | Chunk Size | Pros | Cons |
|----------|------------|------|------|
| **Simple Chunking** | 500 chars | Fast, simple | Loses context, breaks structure |
| **Parent-Child** | 2000 (parent) + 400 (child) | Preserves context, precise search | More complex, slight overhead |

### 4. Structured Output with Citations

#### Pydantic Schema

```python
class Citation(BaseModel):
    source: str         # "PDR Technical Guidance"
    reference: str      # "Section 2.1, Page 5"
    content: str        # "Extensions must maintain 2m..."
    relevance: str      # "Defines the 2m requirement"

class ComplianceResult(BaseModel):
    answer: str         # Full explanation
    is_compliant: bool  # Verdict
    citations: List[Citation]
```

#### Example Output

```json
{
  "answer": "Based on the analysis, the proposed extension DOES NOT comply with the 2m boundary rule. The minimum distance from the eastern wall to the plot boundary is 1.85m, which is below the required 2m clearance specified in the Permitted Development Rights guidelines.",
  "is_compliant": false,
  "citations": [
    {
      "source": "Permitted Development Rights - Technical Guidance",
      "reference": "Section 2.1: Boundary Clearances, Page 5",
      "content": "All extensions must maintain a minimum distance of 2 meters from any plot boundary to ensure adequate spacing and prevent overcrowding.",
      "relevance": "This regulation defines the mandatory 2m boundary clearance requirement that the proposed extension violates."
    },
    {
      "source": "Permitted Development Rights - Technical Guidance",
      "reference": "Section 3.4: Measurement Guidelines, Page 12",
      "content": "Distances shall be measured perpendicular from the nearest point of the structure to the boundary line.",
      "relevance": "Explains the methodology for measuring boundary distances used in this assessment."
    }
  ]
}
```

## 🚀 Running the Agent

### Prerequisites
- Python 3.11+
- ChromaDB running (localhost:8001 or via Docker)
- Redis running (localhost:6379 or via Docker)
- OpenAI API key

### Local Setup

```bash
cd agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY=sk-your-key-here
export CHROMA_HOST=localhost
export CHROMA_PORT=8001
export REDIS_HOST=localhost
export REDIS_PORT=6379

# Run the agent service
python main.py
```

Agent API: **http://localhost:8001**

### Docker Setup

```bash
# Build and run
docker-compose up -d agent

# View logs
docker-compose logs -f agent

# Access API
curl http://localhost:8002/health
```

### API Endpoints

#### `POST /process`

Process a compliance query with drawing data.

**Request**:
```json
{
  "query": "Does this building comply with the 2m boundary rule?",
  "user_id": "user_123",
  "session_id": "session-uuid"
}
```

**Response**:
```json
{
  "answer": "The building complies...",
  "is_compliant": true,
  "citations": [...],
  "reasoning_steps": [
    "Retrieved 5 regulatory documents",
    "Analyzed drawing geometry",
    "Calculated distances",
    "Verified compliance"
  ],
  "geometry_analysis": "DISTANCE ANALYSIS: ..."
}
```

#### `GET /health`

Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "chromadb": "connected",
  "redis": "connected"
}
```

## 🧪 Testing

### Run All Tests

```bash
# Integration tests
python tests/test_graph.py
python tests/test_retrieval.py

# Geometry tool tests
python tests/test_geometry.py
```

### Test Geometry Tool Standalone

```bash
cd agent
python -c "
from geometry_tool import AnalyzeGeometryTool
import json

tool = AnalyzeGeometryTool()

drawing = [
    {'type': 'POLYLINE', 'layer': 'Plot Boundary', 
     'points': [[0,0], [100,0], [100,100], [0,100]], 'closed': True},
    {'type': 'POLYLINE', 'layer': 'Walls',
     'points': [[10,10], [50,10], [50,50], [10,50]], 'closed': True}
]

result = tool._run('What percentage is covered?', drawing)
print(result)
"
```

### Test LangGraph Workflow

```python
from graph import HybridRAGGraph

graph = HybridRAGGraph()

result = graph.process(
    user_question="Does this comply?",
    user_id="test_user",
    drawing_data=[...]
)

print(result["final_answer"])
print(result["reasoning_steps"])
```

## 📊 Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-your-key-here

# Optional - ChromaDB
CHROMA_HOST=localhost
CHROMA_PORT=8001
CHROMA_COLLECTION_NAME=regulatory_documents

# Optional - Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Optional - LangChain Tracing
LANGCHAIN_API_KEY=your-langchain-key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=hybrid-rag

# Optional - Agent Settings
AGENT_HOST=0.0.0.0
AGENT_PORT=8001
```

### Ingestion Configuration

```python
# config.py or environment
PARENT_CHUNK_SIZE = 2000
CHILD_CHUNK_SIZE = 400
CHUNK_OVERLAP = 100
RETRIEVER_K = 5  # Number of documents to retrieve
```


## 📦 Dependencies

Key Python packages:
- **langgraph**: Graph-based agent orchestration
- **langchain**: LLM framework and tools
- **langchain-openai**: OpenAI integration
- **chromadb**: Vector database client
- **redis**: Redis client
- **shapely**: Computational geometry
- **unstructured**: Advanced PDF parsing
- **fastapi**: Web framework
- **pydantic**: Data validation

See [requirements.txt](requirements.txt) for complete list.


## 📖 Additional Resources

- **LangGraph Documentation**: https://langchain-ai.github.io/langgraph/
- **LangChain Tools**: https://python.langchain.com/docs/modules/agents/tools/
- **Shapely Documentation**: https://shapely.readthedocs.io/
- **ChromaDB Guide**: https://docs.trychroma.com/
- **Unstructured Library**: https://unstructured-io.github.io/unstructured/
