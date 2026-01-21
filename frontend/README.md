# Frontend - React Web Application

Modern, responsive chat interface with JSON editor for the Hybrid RAG System, built with React 18, Tailwind CSS, and Vite.

## 🎯 Overview

The frontend provides an intuitive user interface for interacting with the Hybrid RAG compliance checking system. It combines a real-time chat interface with an integrated JSON editor for architectural drawing data management.

## ✨ Key Features

### 1. **Real-Time Chat Interface**
- **Message History**: Persistent conversation display with user/assistant messages
- **Compliance Results**: Visual indicators for compliance verdicts (✅/❌)
- **Citations Display**: Expandable regulatory source references
- **Reasoning Steps**: Transparent workflow execution traces
- **Auto-Scroll**: Automatic scrolling to latest messages
- **Loading States**: Clear feedback during agent processing

### 2. **Monaco JSON Editor**
- **Syntax Highlighting**: Full JSON syntax highlighting
- **Schema Validation**: Real-time Pydantic schema validation
- **Error Detection**: Inline error messages for invalid JSON
- **Example Templates**: Pre-loaded architectural drawing examples
- **Apply Button**: One-click ephemeral data upload
- **Visual Feedback**: Success/error toasts for operations

### 3. **Session Management**
- **Auto-Creation**: Automatic session initialization on load
- **Session Display**: Current session ID and name in header
- **New Session**: Create fresh sessions with one click
- **Session Persistence**: Maintained across page refreshes (via React Query)

### 4. **Ephemeral Data Handling**
- **Upload Indicator**: Visual cue when drawing data is loaded
- **TTL Display**: 1-hour ephemeral data lifetime shown
- **Metadata Display**: Object counts, layer statistics
- **Clear Feedback**: Success messages with metadata summary

### 5. **Responsive Design**
- **Mobile-First**: Optimized for all screen sizes
- **Tailwind CSS**: Utility-first styling for rapid development
- **Grid Layout**: Adaptive 2-column layout (stacks on mobile)
- **Beautiful Gradients**: Modern gradient backgrounds
- **Smooth Animations**: Transition effects for interactions

### 6. **State Management**
- **React Query**: Server state synchronization with caching
- **Automatic Refetching**: Smart data revalidation
- **Optimistic Updates**: Immediate UI feedback
- **Cache Invalidation**: Proper cache management

### 7. **Information Panel**
- **System Overview**: Persistent vs ephemeral data explanation
- **Feature Highlights**: Key capabilities displayed
- **User Guidance**: Clear instructions for usage

## 🏗️ Architecture

### Component Structure

```
frontend/
├── src/
│   ├── App.jsx                      # Main application wrapper
│   ├── index.jsx                    # React DOM entry point
│   ├── index.css                    # Global styles & Tailwind imports
│   ├── components/
│   │   ├── ChatInterface.jsx        # Chat UI with message display
│   │   ├── ComplianceWorkbench.tsx  # Compliance features (TypeScript)
│   │   └── JsonEditor.jsx           # Monaco editor integration
│   └── api/
│       └── api.js                   # API client & endpoints
├── index.html                       # HTML template
├── vite.config.js                   # Vite build configuration
├── tailwind.config.js               # Tailwind CSS configuration
├── postcss.config.js                # PostCSS configuration
├── tsconfig.json                    # TypeScript configuration
├── package.json                     # Dependencies & scripts
└── Dockerfile                       # Production container image
```

### Technology Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 18.x | UI framework |
| **Vite** | 5.x | Build tool & dev server |
| **Tailwind CSS** | 3.x | Utility-first CSS |
| **React Query** | 5.x | Server state management |
| **Monaco Editor** | 0.45.x | Code editor (VS Code engine) |
| **TypeScript** | 5.x | Type safety (partial) |

## 📦 Component Details

### 1. App.jsx - Main Application

**Responsibilities**:
- Application layout and structure
- Session creation and management
- Global state coordination
- React Query provider setup

**Key Features**:
```jsx
- QueryClient configuration with caching
- Session mutation for creation
- Ephemeral data mutation for updates
- Header with session info
- Two-column grid layout (chat + editor)
- Information panel with system details
```

**State Management**:
```jsx
const createSessionMutation = useMutation({
  mutationFn: () => sessionAPI.createSession(),
  onSuccess: (session) => {
    queryClient.setQueryData(['currentSession'], session);
  }
});

const updateEphemeralDataMutation = useMutation({
  mutationFn: ({ sessionId, jsonData }) =>
    sessionAPI.updateEphemeralData(sessionId, jsonData),
  onSuccess: (_, variables) => {
    queryClient.setQueryData(['ephemeralData'], variables.jsonData);
  }
});
```

### 2. ChatInterface.jsx - Chat UI

**Responsibilities**:
- Display message history
- Handle user input
- Send messages to backend
- Show compliance results and citations

**Key Features**:
```jsx
- Message list with user/assistant distinction
- Citation accordion (expandable)
- Reasoning steps display
- Compliance verdict badges
- Auto-scroll to latest message
- Loading spinner during processing
- Error handling with toasts
```

**Message Display**:
```jsx
// User message
<div className="flex justify-end">
  <div className="bg-blue-600 text-white rounded-lg px-4 py-2">
    {message.content}
  </div>
</div>

// Assistant message with citations
<div className="flex justify-start">
  <div className="bg-white rounded-lg px-4 py-2 shadow">
    <p>{message.answer}</p>
    <div className="mt-2">
      {message.citations.map(citation => (
        <CitationCard citation={citation} />
      ))}
    </div>
  </div>
</div>
```

### 3. JsonEditor.jsx - Monaco Editor

**Responsibilities**:
- JSON editing with syntax highlighting
- Real-time validation
- Apply ephemeral data to session
- Display validation errors

**Key Features**:
```jsx
- Monaco Editor integration
- JSON schema validation
- Example architectural drawing template
- Apply button with loading state
- Error toast notifications
- Success feedback with metadata
```

**Validation Flow**:
```jsx
const handleApply = async () => {
  try {
    const parsed = JSON.parse(jsonValue);
    
    // Validate schema (LINE/POLYLINE objects)
    validateDrawingSchema(parsed);
    
    // Upload to backend
    await onJsonUpdate(parsed);
    
    // Show success
    toast.success('Drawing data applied!');
  } catch (error) {
    toast.error(`Invalid JSON: ${error.message}`);
  }
};
```

**Example Template**:
```json
[
  {
    "type": "POLYLINE",
    "layer": "Plot Boundary",
    "points": [[0, 0], [1000, 0], [1000, 1000], [0, 1000]],
    "closed": true
  },
  {
    "type": "POLYLINE",
    "layer": "Walls",
    "points": [[100, 100], [500, 100], [500, 500], [100, 500]],
    "closed": true
  }
]
```

### 4. ComplianceWorkbench.tsx - Compliance Features

**Responsibilities**:
- TypeScript-based compliance components
- Advanced compliance visualization
- Feature-rich workbench interface

**Status**: Optional enhancement component

### 5. api.js - API Client

**Responsibilities**:
- HTTP client configuration
- API endpoint definitions
- Request/response handling
- Error handling

**API Methods**:
```javascript
export const sessionAPI = {
  createSession: () => axios.post('/api/session/create'),
  
  getSession: (sessionId) => 
    axios.get(`/api/session/${sessionId}`),
  
  updateEphemeralData: (sessionId, jsonData) =>
    axios.post('/api/session/update-ephemeral', {
      session_id: sessionId,
      drawing_data: jsonData
    }),
  
  deleteSession: (sessionId) =>
    axios.delete(`/api/session/${sessionId}`)
};

export const chatAPI = {
  sendMessage: (sessionId, message) =>
    axios.post('/api/chat/message', {
      session_id: sessionId,
      message: message
    }),
  
  getHistory: (sessionId) =>
    axios.get(`/api/chat/history/${sessionId}`)
};
```

## 🚀 Running the Frontend

### Prerequisites
- Node.js 18+ and npm
- Backend API running on http://localhost:8000

### Development Mode

```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
echo "REACT_APP_API_URL=http://localhost:8000" > .env

# Start dev server
npm run dev
```

Development server: **http://localhost:3000**

**Features in Dev Mode**:
- ⚡ Hot Module Replacement (HMR)
- 🔍 Fast refresh for React components
- 📊 Vite dev server with optimized bundling
- 🛠️ Source maps for debugging

### Production Build

```bash
# Build for production
npm run build

# Output directory: dist/

# Preview production build
npm run preview
```

**Build Optimizations**:
- Tree shaking for minimal bundle size
- Code splitting for lazy loading
- Asset optimization (images, fonts)
- Minification and compression

### Docker Deployment

```bash
# Build Docker image
docker build -t hybrid-rag-frontend .

# Run container
docker run -p 3000:80 hybrid-rag-frontend

# Or use docker-compose
docker-compose up -d frontend
```

**Nginx Configuration**:
The Docker image uses Nginx to serve the static build with:
- Gzip compression
- Cache headers for static assets
- SPA routing fallback to index.html
- Port 80 exposed (mapped to 3000 externally)

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the `frontend/` directory:

```bash
# Backend API URL (required)
REACT_APP_API_URL=http://localhost:8000

# Optional - feature flags
REACT_APP_ENABLE_COMPLIANCE_WORKBENCH=false
REACT_APP_SHOW_DEBUG_INFO=false
```

**Note**: Environment variables must be prefixed with `REACT_APP_` to be accessible in the React application.

### Tailwind Configuration

Customize styling in `tailwind.config.js`:

```javascript
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#2563eb',    // Blue-600
        secondary: '#4f46e5',  // Indigo-600
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
```

### Vite Configuration

Build settings in `vite.config.js`:

```javascript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})
```

## 🎨 Styling Guide

### Tailwind Utility Classes

The application uses Tailwind CSS utility classes extensively:

**Layout**:
```jsx
<div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
  <div className="max-w-7xl mx-auto px-4 py-8">
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
```

**Components**:
```jsx
<button className="px-4 py-2 bg-primary text-white rounded-lg 
                   hover:bg-blue-700 disabled:bg-gray-300 
                   transition-colors">
```

**Responsive Design**:
```jsx
// Mobile: full width, Desktop: 2 columns
<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

// Hide on mobile, show on tablet+
<div className="hidden md:block">
```

### Custom CSS

Global styles in `index.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer components {
  .chat-message {
    @apply rounded-lg px-4 py-2 shadow-sm;
  }
  
  .citation-card {
    @apply border-l-4 border-blue-500 pl-4 py-2 bg-blue-50;
  }
}
```

## 📦 Dependencies

### Core Dependencies

```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "@tanstack/react-query": "^5.0.0",
  "@monaco-editor/react": "^4.6.0",
  "axios": "^1.6.0"
}
```

### Dev Dependencies

```json
{
  "@vitejs/plugin-react": "^4.2.0",
  "vite": "^5.0.0",
  "tailwindcss": "^3.4.0",
  "postcss": "^8.4.0",
  "autoprefixer": "^10.4.0",
  "typescript": "^5.3.0"
}
```

See [package.json](package.json) for complete list.


## 📚 Additional Resources

- **React Documentation**: https://react.dev/
- **Vite Guide**: https://vitejs.dev/guide/
- **Tailwind CSS**: https://tailwindcss.com/docs
- **React Query**: https://tanstack.com/query/latest
- **Monaco Editor**: https://microsoft.github.io/monaco-editor/
