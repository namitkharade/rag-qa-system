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

      queryClient.setQueryData(['chatHistory', sessionId], (old) => {
        if (!old) return { messages: [userMessage] };
        return {
          ...old,
          messages: [...(old.messages || []), userMessage],
        };
      });

      return { previousMessages };
    },
    onSuccess: async (response) => {
      await queryClient.invalidateQueries({ queryKey: ['chatHistory', sessionId] });
    },
    onError: (error, messageData, context) => {
      queryClient.setQueryData(['chatHistory', sessionId], context.previousMessages);
      
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, there was an error processing your message.',
        timestamp: new Date().toISOString(),
      };

      queryClient.setQueryData(['chatHistory', sessionId], (old) => {
        if (!old) return { messages: [errorMessage] };
        return {
          ...old,
          messages: [...(old.messages || []), errorMessage],
        };
      });
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
    <div className="flex flex-col h-full bg-white rounded-xl shadow-xl border border-gray-100">
      {/* Header */}
      <div className="flex-shrink-0 px-6 py-4 bg-white border-b border-gray-100 flex justify-between items-center shadow-sm z-10 rounded-t-xl">
        <div>
          <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
            AI Assistant
          </h2>
          {ephemeralData && (
            <p className="text-xs text-green-600 mt-0.5 font-medium flex items-center gap-1">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              Context Loaded
            </p>
          )}
        </div>
        <div className="text-xs text-gray-400 font-mono bg-gray-50 px-2 py-1 rounded">
          {sessionId ? sessionId.slice(0, 8) : '...'}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-gray-50/50" style={{ minHeight: 0 }}>
        {isLoadingHistory && (
          <div className="flex justify-center items-center h-full">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        )}

        {!isLoadingHistory && messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-500 space-y-4">
            <div className="bg-blue-50 p-4 rounded-full">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <div>
              <p className="text-xl font-semibold text-gray-700">Ready to help</p>
              <p className="text-sm text-gray-400 mt-1 max-w-xs mx-auto">
                Ask about construction regulations or details from your architectural drawing.
              </p>
            </div>
          </div>
        )}

        {messages.map((msg, index) => {
          const isUser = msg.role === 'user';
          
          // Try to parse structured content for assistant messages
          let parsedContent = null;
          if (!isUser && msg.content) {
            try {
              const parsed = JSON.parse(msg.content);
              if (parsed.answer !== undefined) {
                parsedContent = parsed;
              }
            } catch (e) {
              // Not JSON, use regular content
            }
          }
          
          return (
            <div
              key={index}
              className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2 duration-300`}
            >
              <div className={`flex max-w-[85%] ${isUser ? 'flex-row-reverse' : 'flex-row'} items-start gap-3`}>
                
                {/* Avatar */}
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm ${
                  isUser ? 'bg-indigo-600 text-white' : 'bg-white border border-gray-200 text-indigo-600'
                }`}>
                  {isUser ? (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                       <path d="M2 10a8 8 0 018-8v8h8a8 8 0 11-16 0z" />
                       <path d="M12 2.252A8.014 8.014 0 0117.748 8H12V2.252z" />
                    </svg>
                  )}
                </div>

                {/* Bubble */}
                <div
                  className={`relative rounded-2xl shadow-sm ${
                    isUser
                      ? 'bg-indigo-600 text-white rounded-tr-none p-4'
                      : 'bg-white text-gray-800 border border-gray-100 rounded-tl-none'
                  }`}
                >
                  {parsedContent ? (
                    // Structured response format
                    <div className="space-y-4">
                      {/* Compliance Badge */}
                      {parsedContent.is_compliant !== undefined && (
                        <div className="mb-3">
                          <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${
                            parsedContent.is_compliant 
                              ? 'bg-green-100 text-green-700 border border-green-200' 
                              : 'bg-red-100 text-red-700 border border-red-200'
                          }`}>
                            {parsedContent.is_compliant ? (
                              <>
                                <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                </svg>
                                Compliant
                              </>
                            ) : (
                              <>
                                <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                                </svg>
                                Non-Compliant
                              </>
                            )}
                          </span>
                        </div>
                      )}
                      
                      {/* Answer */}
                      <div className="p-4">
                        <p className="text-sm leading-relaxed whitespace-pre-wrap">{parsedContent.answer}</p>
                      </div>
                      
                      {/* Citations */}
                      {parsedContent.citations && parsedContent.citations.length > 0 && (
                        <div className="border-t border-gray-100 pt-4 px-4">
                          <p className="text-xs font-semibold text-gray-600 mb-3 flex items-center gap-1.5">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            Citations ({parsedContent.citations.length})
                          </p>
                          <div className="space-y-3">
                            {parsedContent.citations.map((citation, idx) => (
                              <details key={idx} className="group">
                                <summary className="cursor-pointer list-none">
                                  <div className="bg-gray-50 hover:bg-gray-100 rounded-lg p-3 transition-colors">
                                    <div className="flex items-start justify-between">
                                      <div className="flex-1">
                                        <p className="text-xs font-medium text-gray-700">{citation.source}</p>
                                        {citation.reference && (
                                          <p className="text-[10px] text-gray-500 mt-0.5">{citation.reference}</p>
                                        )}
                                      </div>
                                      <svg className="w-4 h-4 text-gray-400 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                      </svg>
                                    </div>
                                  </div>
                                </summary>
                                <div className="mt-2 pl-3 pr-2">
                                  <div className="bg-blue-50 border-l-2 border-blue-300 rounded p-2">
                                    <p className="text-[11px] text-gray-600 leading-relaxed whitespace-pre-wrap">{citation.content}</p>
                                  </div>
                                  {citation.relevance && (
                                    <p className="text-[10px] text-gray-500 mt-2 italic">{citation.relevance}</p>
                                  )}
                                </div>
                              </details>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* Reasoning Steps */}
                      {parsedContent.reasoning_steps && parsedContent.reasoning_steps.length > 0 && (
                        <div className="border-t border-gray-100 pt-4 px-4">
                          <p className="text-xs font-semibold text-gray-600 mb-3 flex items-center gap-1.5">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                            </svg>
                            Analysis Steps
                          </p>
                          <ol className="space-y-2">
                            {parsedContent.reasoning_steps.map((step, idx) => (
                              <li key={idx} className="text-[11px] text-gray-600 leading-relaxed flex gap-2">
                                <span className="font-semibold text-indigo-600 flex-shrink-0">{idx + 1}.</span>
                                <span>{step}</span>
                              </li>
                            ))}
                          </ol>
                        </div>
                      )}
                      
                      {/* Geometry Analysis */}
                      {parsedContent.geometry_analysis && (
                        <div className="border-t border-gray-100 pt-4 px-4">
                          <p className="text-xs font-semibold text-gray-600 mb-2 flex items-center gap-1.5">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
                            </svg>
                            Geometry Analysis
                          </p>
                          <div className="bg-gray-50 rounded p-2 mt-2">
                            <p className="text-[11px] text-gray-600 leading-relaxed whitespace-pre-wrap">{parsedContent.geometry_analysis}</p>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    // Regular text message
                    <div className="p-4">
                      <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</p>
                    </div>
                  )}
                  
                  {/* Sources */}
                  {msg.sources && msg.sources.length > 0 && !parsedContent && (
                    <div className="mt-3 pt-3 border-t border-gray-100/20 px-4 pb-1">
                      <p className="text-xs font-semibold mb-2 opacity-80 flex items-center gap-1">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                        </svg>
                        Sources
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {msg.sources.map((source, idx) => (
                          <span key={idx} className={`text-[10px] px-2 py-1 rounded-full ${
                            isUser ? 'bg-indigo-700 text-indigo-100' : 'bg-gray-100 text-gray-600'
                          }`}>
                            {source.document || 'Document'}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}

        {sendMessageMutation.isPending && (
          <div className="flex justify-start animate-pulse">
             <div className="flex max-w-[80%] flex-row items-start gap-3">
               <div className="w-8 h-8 rounded-full bg-white border border-gray-200 flex items-center justify-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-indigo-600" viewBox="0 0 20 20" fill="currentColor">
                       <path d="M2 10a8 8 0 018-8v8h8a8 8 0 11-16 0z" />
                       <path d="M12 2.252A8.014 8.014 0 0117.748 8H12V2.252z" />
                  </svg>
               </div>
               <div className="bg-white rounded-2xl rounded-tl-none p-4 border border-gray-100 shadow-sm flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></div>
               </div>
             </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="flex-shrink-0 p-4 bg-white border-t border-gray-100 rounded-b-xl">
        <div className="flex items-end gap-2 bg-gray-50 p-2 rounded-xl border border-gray-200 focus-within:ring-2 focus-within:ring-indigo-500/20 focus-within:border-indigo-500 transition-all">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            disabled={!sessionId}
            className="flex-1 resize-none bg-transparent border-none focus:ring-0 text-gray-700 text-sm max-h-32 py-2 px-2"
            rows="1"
            style={{ minHeight: '44px' }}
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || sendMessageMutation.isPending || !sessionId}
            className="p-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors shadow-sm mb-0.5"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
            </svg>
          </button>
        </div>
        <p className="text-[10px] text-gray-400 mt-2 text-center">
          AI can make mistakes. Please verify important information.
        </p>
      </div>
    </div>
  );
};

export default ChatInterface;
