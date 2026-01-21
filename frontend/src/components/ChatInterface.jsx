import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';
import { chatAPI } from '../api/api';

const ChatInterface = ({ sessionId, ephemeralData }) => {
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef(null);
  const queryClient = useQueryClient();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const { data: chatHistory, isLoading: isLoadingHistory } = useQuery({
    queryKey: ['chatHistory', sessionId],
    queryFn: () => chatAPI.getChatHistory(sessionId),
    enabled: !!sessionId,
    select: (data) => data.messages || [],
  });

  const messages = chatHistory || [];

  const sendMessageMutation = useMutation({
    mutationFn: async (messageData) => {
      return await chatAPI.sendMessage(
        sessionId,
        messageData.content,
        messageData.ephemeralData ? { ephemeral_data: messageData.ephemeralData } : null
      );
    },
    onMutate: async (messageData) => {
      await queryClient.cancelQueries({ queryKey: ['chatHistory', sessionId] });

      const previousMessages = queryClient.getQueryData(['chatHistory', sessionId]);

      const userMessage = {
        role: 'user',
        content: messageData.content,
        timestamp: new Date().toISOString(),
      };

      queryClient.setQueryData(['chatHistory', sessionId], (old) => [...(old || []), userMessage]);

      return { previousMessages };
    },
    onSuccess: (response) => {
      const assistantMessage = {
        role: 'assistant',
        content: response.message,
        sources: response.sources,
        metadata: response.metadata,
        timestamp: new Date().toISOString(),
      };

      queryClient.setQueryData(['chatHistory', sessionId], (old) => [
        ...(old || []),
        assistantMessage,
      ]);
    },
    onError: (error, messageData, context) => {
      queryClient.setQueryData(['chatHistory', sessionId], context.previousMessages);
      
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, there was an error processing your message.',
        timestamp: new Date().toISOString(),
      };

      queryClient.setQueryData(['chatHistory', sessionId], (old) => [
        ...(old || []),
        errorMessage,
      ]);
    },
  });

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !sessionId) return;

    sendMessageMutation.mutate({
      content: inputMessage,
      ephemeralData: ephemeralData,
    });

    setInputMessage('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-800">Chat Interface</h2>
        {ephemeralData && (
          <p className="text-sm text-green-600 mt-1">
            ✓ Architectural drawing loaded
          </p>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {isLoadingHistory && (
          <div className="text-center text-gray-500 mt-8">
            <p className="text-lg">Loading chat history...</p>
          </div>
        )}

        {!isLoadingHistory && messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <p className="text-lg">Start a conversation</p>
            <p className="text-sm mt-2">
              Ask questions about regulations or your architectural drawing
            </p>
          </div>
        )}

        {messages.map((msg, index) => (
          <div
            key={index}
            className={`flex ${
              msg.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-[70%] rounded-lg p-3 ${
                msg.role === 'user'
                  ? 'bg-primary text-white'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-2 pt-2 border-t border-gray-300">
                  <p className="text-xs font-semibold mb-1">Sources:</p>
                  {msg.sources.map((source, idx) => (
                    <p key={idx} className="text-xs">
                      • {source.document || 'Document'}
                    </p>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {sendMessageMutation.isPending && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg p-3">
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

      {/* Input */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex space-x-2">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            disabled={!sessionId}
            className="flex-1 resize-none border border-gray-300 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-primary"
            rows="2"
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || sendMessageMutation.isPending || !sessionId}
            className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
