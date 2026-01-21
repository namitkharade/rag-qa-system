import Editor from '@monaco-editor/react';
import axios from 'axios';
import React, { useEffect, useRef, useState } from 'react';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  regulations?: any[];
  geometryAnalysis?: string;
}

interface ComplianceWorkbenchProps {
  userId: string;
  initialDrawing?: string;
}

const ComplianceWorkbench: React.FC<ComplianceWorkbenchProps> = ({
  userId,
  initialDrawing = '[]'
}: ComplianceWorkbenchProps) => {
  // Chat state
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // JSON editor state
  const [jsonContent, setJsonContent] = useState(initialDrawing);
  const [isValidJson, setIsValidJson] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  
  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  
  // Scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  // Validate and update JSON
  const handleJsonChange = (value: string | undefined) => {
    if (value === undefined) return;
    
    setJsonContent(value);
    
    // Validate JSON
    try {
      JSON.parse(value);
      setIsValidJson(true);
      
      // Debounce the save to Redis
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
      
      debounceTimerRef.current = setTimeout(() => {
        saveToRedis(value);
      }, 1000); // 1 second debounce
      
    } catch (error) {
      setIsValidJson(false);
    }
  };
  
  // Save drawing to Redis
  const saveToRedis = async (jsonString: string) => {
    try {
      setIsSaving(true);
      
      const drawingData = JSON.parse(jsonString);
      
      await axios.post(`${API_BASE_URL}/upload_drawing`, {
        user_id: userId,
        drawing: drawingData
      });
      
      setLastSaved(new Date());
      setIsSaving(false);
      
    } catch (error) {
      console.error('Error saving to Redis:', error);
      setIsSaving(false);
    }
  };
  
  // Send message to AI agent
  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;
    
    // Clear any pending debounced saves
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    
    // Ensure latest drawing is saved before querying
    if (isValidJson) {
      try {
        await saveToRedis(jsonContent);
      } catch (error) {
        console.error('Failed to sync drawing before query:', error);
      }
    }
    
    const userMessage: Message = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date()
    };
    
    setMessages((prev: Message[]) => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    
    try {
      // Call the agent's /process endpoint
      const response = await axios.post(`${API_BASE_URL}/api/agent/process`, {
        message: inputMessage,
        user_id: userId
      });
      
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.answer,
        timestamp: new Date(),
        regulations: response.data.regulations,
        geometryAnalysis: response.data.geometry_analysis
      };
      
      setMessages((prev: Message[]) => [...prev, assistantMessage]);
      
    } catch (error: any) {
      console.error('Error sending message:', error);
      
      const errorMessage: Message = {
        role: 'assistant',
        content: `Error: ${error.response?.data?.detail || error.message || 'Failed to get response from agent'}`,
        timestamp: new Date()
      };
      
      setMessages((prev: Message[]) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Handle Enter key in input
  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };
  
  // Load sample drawing
  const loadSampleDrawing = () => {
    const sample = [
      {
        "type": "POLYLINE",
        "layer": "Plot Boundary",
        "points": [
          [-13160.59, 19584.96],
          [-3160.59, 19584.96],
          [-3160.59, 44584.96],
          [-13160.59, 44584.96]
        ],
        "closed": true
      },
      {
        "type": "POLYLINE",
        "layer": "Walls",
        "points": [
          [-9660.59, 29584.96],
          [-10660.59, 29584.96],
          [-10660.59, 22084.96],
          [-8560.59, 22084.96],
          [-8560.59, 29584.96]
        ],
        "closed": true
      }
    ];
    
    const jsonString = JSON.stringify(sample, null, 2);
    setJsonContent(jsonString);
    handleJsonChange(jsonString);
  };
  
  return (
    <div className="flex h-screen bg-gray-100">
      {/* Left Panel - Chat Interface */}
      <div className="w-1/2 flex flex-col bg-white border-r border-gray-300">
        {/* Chat Header */}
        <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-blue-500 to-indigo-600">
          <h2 className="text-xl font-bold text-white">
            🤖 Compliance AI Agent
          </h2>
          <p className="text-sm text-blue-100 mt-1">
            Ask about regulations and compliance
          </p>
        </div>
        
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 mt-8">
              <div className="text-6xl mb-4">💬</div>
              <p className="text-lg font-medium">Start a conversation</p>
              <p className="text-sm mt-2">
                Ask about regulations, compliance rules, or specific measurements
              </p>
              <div className="mt-6 space-y-2">
                <p className="text-xs text-gray-400">Try asking:</p>
                <button
                  onClick={() => setInputMessage("Does this comply with the 50% curtilage rule?")}
                  className="block mx-auto px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm text-gray-700"
                >
                  "Does this comply with the 50% curtilage rule?"
                </button>
                <button
                  onClick={() => setInputMessage("Are the walls at least 2m from the boundary?")}
                  className="block mx-auto px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm text-gray-700"
                >
                  "Are the walls at least 2m from the boundary?"
                </button>
              </div>
            </div>
          )}
          
          {messages.map((msg: Message, index: number) => (
            <div
              key={index}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-4 ${
                  msg.role === 'user'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.content}</div>
                
                {/* Show regulations if available */}
                {msg.regulations && msg.regulations.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-300">
                    <p className="text-xs font-semibold mb-2">
                      📚 Referenced Regulations:
                    </p>
                    {msg.regulations.slice(0, 3).map((reg: any, idx: number) => (
                      <div key={idx} className="text-xs mb-1">
                        • {reg.metadata?.source_name || 'Regulation'}
                      </div>
                    ))}
                  </div>
                )}
                
                {/* Show geometry analysis indicator */}
                {msg.geometryAnalysis && (
                  <div className="mt-2 text-xs opacity-75">
                    📐 Geometric analysis performed
                  </div>
                )}
                
                <div className="text-xs opacity-75 mt-2">
                  {msg.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 rounded-lg p-4">
                <div className="flex space-x-2">
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-100"></div>
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-200"></div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
        
        {/* Input Area */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <div className="flex space-x-2">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about compliance..."
              disabled={isLoading}
              className="flex-1 resize-none border border-gray-300 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              rows={2}
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isLoading}
              className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium"
            >
              Send
            </button>
          </div>
        </div>
      </div>
      
      {/* Right Panel - JSON Editor */}
      <div className="w-1/2 flex flex-col bg-white">
        {/* Editor Header */}
        <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-indigo-500 to-purple-600">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-bold text-white">
                📐 Drawing JSON Editor
              </h2>
              <p className="text-sm text-indigo-100 mt-1">
                Architectural drawing data (ephemeral)
              </p>
            </div>
            <button
              onClick={loadSampleDrawing}
              className="px-4 py-2 bg-white text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors text-sm font-medium"
            >
              Load Sample
            </button>
          </div>
        </div>
        
        {/* Status Bar */}
        <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 flex justify-between items-center">
          <div className="flex items-center space-x-4">
            {/* JSON Validation Status */}
            <div className="flex items-center space-x-2">
              {isValidJson ? (
                <>
                  <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                  <span className="text-xs text-green-700">Valid JSON</span>
                </>
              ) : (
                <>
                  <span className="w-2 h-2 bg-red-500 rounded-full"></span>
                  <span className="text-xs text-red-700">Invalid JSON</span>
                </>
              )}
            </div>
            
            {/* Save Status */}
            <div className="flex items-center space-x-2">
              {isSaving ? (
                <>
                  <div className="w-3 h-3 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                  <span className="text-xs text-gray-600">Saving...</span>
                </>
              ) : lastSaved ? (
                <>
                  <span className="text-xs text-gray-600">
                    ✓ Saved to Redis at {lastSaved.toLocaleTimeString()}
                  </span>
                </>
              ) : (
                <span className="text-xs text-gray-400">Not saved</span>
              )}
            </div>
          </div>
          
          <div className="text-xs text-gray-500">
            User ID: {userId}
          </div>
        </div>
        
        {/* Monaco Editor */}
        <div className="flex-1">
          <Editor
            height="100%"
            defaultLanguage="json"
            value={jsonContent}
            onChange={handleJsonChange}
            theme="vs-dark"
            options={{
              minimap: { enabled: false },
              fontSize: 14,
              lineNumbers: 'on',
              roundedSelection: false,
              scrollBeyondLastLine: false,
              automaticLayout: true,
              tabSize: 2,
              formatOnPaste: true,
              formatOnType: true
            }}
          />
        </div>
        
        {/* Info Panel */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <div className="text-xs text-gray-600 space-y-1">
            <p className="font-semibold text-gray-700">📝 Instructions:</p>
            <p>• Paste your architectural drawing JSON here</p>
            <p>• Changes auto-save to Redis after 1 second</p>
            <p>• Data is ephemeral (1 hour TTL)</p>
            <p>• Format: Array of LINE and POLYLINE objects</p>
            <p className="mt-2 text-xs text-gray-500">
              💡 This data is NOT stored in Vector DB - it's session-specific
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComplianceWorkbench;
