import { QueryClient, QueryClientProvider, useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { sessionAPI } from './api/api';
import ChatInterface from './components/ChatInterface.jsx';
import JsonEditor from './components/JsonEditor.jsx';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      refetchOnWindowFocus: false,
    },
  },
});


function AppContent() {
  const queryClientInstance = useQueryClient();
  const [currentSession, setCurrentSession] = useState(null);
  const [ephemeralData, setEphemeralData] = useState(null);

  const createSessionMutation = useMutation({
    mutationFn: () => sessionAPI.createSession(),
    onSuccess: (session) => {
      setCurrentSession(session);
      setEphemeralData(null);
      queryClientInstance.setQueryData(['currentSession'], session);
      queryClientInstance.setQueryData(['ephemeralData'], null);
    },
  });

  const updateEphemeralDataMutation = useMutation({
    mutationFn: ({ sessionId, jsonData }) =>
      sessionAPI.updateEphemeralData(sessionId, jsonData),
    onSuccess: (_, variables) => {
      setEphemeralData(variables.jsonData);
      queryClientInstance.setQueryData(['ephemeralData'], variables.jsonData);
    },
  });

  useEffect(() => {
    createSessionMutation.mutate();
  }, []);

  const createNewSession = () => {
    createSessionMutation.mutate();
  };

  const handleJsonUpdate = async (jsonData) => {
    if (!currentSession) return;

    updateEphemeralDataMutation.mutate({
      sessionId: currentSession.session_id,
      jsonData,
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Hybrid RAG System
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                AICI Challenge - Persistent + Ephemeral Data Analysis
              </p>
            </div>
            <div className="flex items-center space-x-4">
              {currentSession && (
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-700">
                    {currentSession.session_name}
                  </p>
                  <p className="text-xs text-gray-500">
                    ID: {currentSession.session_id.substring(0, 8)}...
                  </p>
                </div>
              )}
              <button
                onClick={createNewSession}
                disabled={createSessionMutation.isPending}
                className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 transition-colors"
              >
                New Session
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100vh-12rem)]">
          {/* Chat Interface */}
          <div className="h-full overflow-hidden">
            <ChatInterface
              sessionId={currentSession?.session_id}
              ephemeralData={ephemeralData}
            />
          </div>

          {/* JSON Editor */}
          <div className="h-full">
            <JsonEditor
              sessionId={currentSession?.session_id}
              onJsonUpdate={handleJsonUpdate}
            />
          </div>
        </div>

        {/* Info Panel */}
        <div className="mt-6 bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-3">
            System Information
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <h4 className="font-medium text-gray-700 mb-2">
                Persistent Data (Vector DB)
              </h4>
              <ul className="space-y-1 text-gray-600">
                <li>• Regulatory PDFs stored in ChromaDB</li>
                <li>• Searchable across all sessions</li>
                <li>• Permanent storage</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-gray-700 mb-2">
                Ephemeral Data (Runtime)
              </h4>
              <ul className="space-y-1 text-gray-600">
                <li>• Architectural drawing JSON</li>
                <li>• Session-specific only</li>
                <li>• NOT stored in Vector DB</li>
              </ul>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}

export default App;
