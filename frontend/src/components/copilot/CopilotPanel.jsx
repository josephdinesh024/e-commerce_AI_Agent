import React, { useState, useEffect, useRef } from 'react';

const CopilotPanel = ({ copilot }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    scrollToBottom();
  }, [copilot.history]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = () => {
    if (!input.trim()) return;
    copilot.processInput(input, copilot.mode);
    setInput('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleMode = () => {
    const newMode = copilot.mode === 'text' ? 'voice' : 'text';
    copilot.setMode(newMode);
    if (newMode === 'voice') {
      copilot.startListening();
    } else {
      copilot.stopListening();
    }
  };

  return (
    <>
      {/* Floating Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 bg-gradient-to-r from-pink-600 to-purple-600 text-white rounded-full p-4 shadow-2xl hover:shadow-3xl transform hover:scale-110 transition-all duration-300 z-50 group"
          aria-label="Open AI Copilot"
        >
          <div className="relative">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-8 w-8"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
              />
            </svg>
            
            {/* Active indicator */}
            {copilot.mode === 'voice' && (
              <span className="absolute -top-1 -right-1 flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
              </span>
            )}
          </div>

          {/* Tooltip */}
          <div className="absolute bottom-full right-0 mb-2 hidden group-hover:block">
            <div className="bg-gray-900 text-white text-sm rounded-lg py-2 px-4 whitespace-nowrap">
              AI Copilot
              <div className="absolute top-full right-4 w-0 h-0 border-l-8 border-r-8 border-t-8 border-transparent border-t-gray-900"></div>
            </div>
          </div>
        </button>
      )}

      {/* Panel */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-96 h-[600px] bg-white rounded-2xl shadow-2xl flex flex-col z-50 overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-pink-600 to-purple-600 text-white p-4 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-white bg-opacity-20 rounded-full p-2">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <div>
                <h3 className="font-bold text-lg">AI Copilot</h3>
                <p className="text-xs text-pink-100">
                  {copilot.mode === 'voice' ? '🎤 Voice Mode' : '⌨️ Text Mode'}
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              {/* Mode Toggle */}
              <button
                onClick={toggleMode}
                className="px-3 py-1 bg-white/20 rounded-full text-sm hover:bg-white/30 transition"
              >
                {copilot.mode === 'text' ? '🎤' : '⌨️'}
              </button>

              {/* Close */}
              <button
                onClick={() => setIsOpen(false)}
                className="hover:bg-white/20 rounded-full p-2 transition"
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
            {copilot.history.length === 0 && (
              <div className="text-center text-gray-500 mt-20">
                <div className="mb-4">
                  <svg className="w-16 h-16 mx-auto text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                </div>
                <p className="text-sm">Start a conversation</p>
                <p className="text-xs mt-2">
                  {copilot.mode === 'voice' 
                    ? 'Click the microphone to speak'
                    : 'Type your message below'}
                </p>
              </div>
            )}

            {copilot.history.map((msg, index) => (
              <div
                key={index}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                    msg.role === 'user'
                      ? 'bg-gradient-to-r from-pink-600 to-purple-600 text-white'
                      : 'bg-white shadow-md text-gray-800'
                  }`}
                >
                  {msg.role === 'assistant' && (
                    <div className="flex items-center space-x-2 mb-1">
                      <svg className="h-4 w-4 text-pink-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                      <span className="text-xs text-gray-500 font-semibold">
                        AI {msg.type === 'voice' && '🎤'}
                      </span>
                    </div>
                  )}
                  <div className="text-sm">
                    {msg.content}
                  </div>
                  <div className="text-xs opacity-70 mt-1">
                    {new Date(msg.timestamp).toLocaleTimeString([], { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </div>
                </div>
              </div>
            ))}

            {/* Listening indicator */}
            {copilot.isListening && (
              <div className="flex justify-start">
                <div className="bg-blue-100 rounded-2xl px-4 py-3 flex items-center space-x-2">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                  <span className="text-sm text-blue-700">Listening...</span>
                </div>
              </div>
            )}

            {/* Speaking indicator */}
            {copilot.isSpeaking && (
              <div className="flex justify-start">
                <div className="bg-purple-100 rounded-2xl px-4 py-3 flex items-center space-x-2">
                  <div className="flex space-x-1">
                    <div className="w-1 h-4 bg-purple-500 rounded animate-pulse"></div>
                    <div className="w-1 h-6 bg-purple-500 rounded animate-pulse" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-1 h-5 bg-purple-500 rounded animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                    <div className="w-1 h-4 bg-purple-500 rounded animate-pulse" style={{ animationDelay: '0.3s' }}></div>
                  </div>
                  <span className="text-sm text-purple-700">Speaking...</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-4 bg-white border-t">
            {copilot.mode === 'voice' ? (
              /* Voice Input */
              <div className="flex items-center justify-center space-x-4">
                <div className="flex-1 text-center text-sm text-gray-500">
                  {copilot.isListening ? 'Listening...' : 'Tap to speak'}
                </div>
                <button
                  onClick={() => {
                    if (copilot.isListening) {
                      copilot.stopListening();
                    } else {
                      copilot.startListening();
                    }
                  }}
                  className={`p-4 rounded-full transition-all ${
                    copilot.isListening
                      ? 'bg-red-500 animate-pulse'
                      : 'bg-blue-500 hover:bg-blue-600'
                  }`}
                >
                  <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            ) : (
              /* Text Input */
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message..."
                  className="flex-1 border rounded-full px-4 py-3 focus:outline-none focus:ring-2 focus:ring-pink-500"
                />
                <button
                  onClick={handleSend}
                  disabled={!input.trim()}
                  className="bg-gradient-to-r from-pink-600 to-purple-600 text-white rounded-full p-3 hover:shadow-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
};

export default CopilotPanel;