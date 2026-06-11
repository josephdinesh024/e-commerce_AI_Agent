import React, { useState, useEffect, useRef } from 'react';
import { sendChatMessage, getSuggestions, parseSSEStream, sendPageContext, getSessionHistory, sendChatAnalyze } from '../../services/chatapi';
import { useNavigate } from 'react-router-dom';
import VoiceInput from './VoiceInput';
import { speak, stopSpeaking } from '../../util/tts';
import { executeActions } from '../../util/agentAction';
import buildPageContext from '../../util/pageContext';

const ChatModal = ({ agentHandler }) => {
  const [suggestions, setSuggestions] = useState([]);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Load suggestions
    loadSuggestions();
    // Focus input
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    // Scroll to bottom when messages change
    scrollToBottom();
  }, [agentHandler.messages]);

  useEffect(() => {
    return () => {
      stopSpeaking();  // Stop speech when modal closes
    };
  }, []);

  const loadSuggestions = async () => {
    try {
      const data = await getSuggestions();
      setSuggestions(data.suggestions);
    } catch (error) {
      console.error('Error loading suggestions:', error);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // const handleSend = async (messageText = input, inputMode = mode) => {
  //   if (!messageText.trim() || agentHandler.isLoading) return;
  //   if (messageText != 'shared current page context') {
  //     const userMessage = {
  //       role: 'user',
  //       content: messageText,
  //       timestamp: new Date()
  //     };

  //     setMessages(prev => [...prev, userMessage]);
  //     setInput('');
  //   }
  //   setIsLoading(true);

  //   const aiMessageId = Date.now();
  //   const aiMessage = {
  //     id: aiMessageId,
  //     role: 'assistant',
  //     content: '',
  //     timestamp: new Date(),
  //     streaming: true
  //   };
  //   setMessages(prev => [...prev, aiMessage]);

  //   try {
  //     const stream = await sendChatAnalyze(messageText, inputMode);  // Pass mode
  //     if (stream && stream?.type == "done") {
  //       const contents = JSON.parse(stream.content);
  //       if (contents.context_requested) {
  //         // Build and send page context
  //         const context = buildPageContext();
  //         // console.log("Agent requested context. Sending page context:", context);
  //         if(contents?.message){
  //           speak(contents?.message);
  //         }

  //         sendPageContext(context).then(res => {
  //           console.log('Page context sent:', res, context);
  //           setTimeout(() => {
  //             handleSend('shared current page context', inputMode);
  //           }, 2000);
  //         });

  //         return; // Don't display this message
  //       } else {

  //         // Extract just the message for display
  //         const displayContent = (contents.message + contents.html_content);

  //         // Update message with the actual message content (not full JSON)
  //         setMessages(prev =>
  //           prev.map(msg =>
  //             msg.id === aiMessageId
  //               ? { ...msg, content: displayContent, streaming: false }
  //               : msg
  //           )
  //         );

  //         // Handle voice output
  //         if (contents.speak && contents.message) {
  //           speak(contents.message);
  //         }
  //         if (contents.action) {
  //           console.log(contents.action);
  //           executeActions(contents.action);
  //         }

  //       }
  //     }

  //     setIsLoading(false);
  //   } catch (error) {
  //     console.error('Error sending message:', error);
  //     setIsLoading(false);
  //   }
  // };

  const handleSuggestionClick = (suggestion) => {
    agentHandler.handleSend(suggestion,"text");
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      agentHandler.handleSend();
    }
  };

  const handleVoiceTranscript = (transcript) => {
    agentHandler.setInput(transcript);
    agentHandler.handleSend(transcript, 'voice');
  };

  function HtmlContent({ htmlString }) {
    // Ensure the HTML string is sanitized if it comes from user input
    // A common library for sanitization is DOMPurify
    // import DOMPurify from 'dompurify';
    // const sanitizedHtml = DOMPurify.sanitize(htmlString); 

    return (
      <div dangerouslySetInnerHTML={{ __html: htmlString }} />
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl h-full flex flex-col overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-pink-600 to-purple-600 text-white p-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-white bg-opacity-20 rounded-full p-2">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <div>
              <h3 className="font-bold text-lg">AI Shopping Assistant</h3>
              <p className="text-xs text-pink-100">
                {agentHandler.mode === 'voice' ? '🎤 Voice Mode' : '⌨️ Text Mode'}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => {
                stopSpeaking();
                agentHandler.setMode(agentHandler.mode === 'text' ? 'voice' : 'text');
              }}
              className="px-3 py-1 bg-white/20 rounded-full text-sm hover:bg-white/30 transition"
            >
              {agentHandler.mode === 'text' ? '🎤 Voice' : '⌨️ Text'}
            </button>
            <button onClick={() => agentHandler.setIsOpen(false)} className="hover:bg-white/20 rounded-full p-2 transition">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
          {agentHandler.messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${message.role === 'user'
                  ? 'bg-gradient-to-r from-pink-600 to-purple-600 text-white'
                  : 'bg-white shadow-md text-gray-800'
                  }`}
              >
                {message.role === 'assistant' && (
                  <div className="flex items-center space-x-2 mb-1">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-pink-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                    <span className="text-xs text-gray-500 font-semibold">AI Assistant</span>
                  </div>
                )}
                <div className="whitespace-pre-wrap break-words">
                  {/* {message.content} */}
                  {<HtmlContent key={message?.id} htmlString={message.content} />}
                  {message.streaming && (
                    <span className="inline-block ml-1 w-2 h-4 bg-current animate-pulse"></span>
                  )}
                </div>
                <div className="text-xs opacity-70 mt-1">
                  {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Suggestions */}
        {agentHandler.messages.length === 1 && suggestions.length > 0 && (
          <div className="px-4 py-3 bg-white border-t">
            <p className="text-xs text-gray-500 mb-2 font-semibold">Quick queries:</p>
            <div className="flex flex-wrap gap-2">
              {suggestions.slice(0, 4).map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="text-xs bg-pink-50 hover:bg-pink-100 text-pink-700 px-3 py-2 rounded-full border border-pink-200 transition"
                  disabled={agentHandler.isLoading}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <div className="p-4 bg-white border-t">
          <div className="flex space-x-2">
            {agentHandler.mode === 'voice' ? (
              <>
                <div className="flex-1 border rounded-full px-4 py-3 flex items-center justify-center bg-gray-50">
                  {agentHandler.ChatModalisListening ? (
                    <span className="text-gray-600">🎤 Listening...</span>
                  ) : (
                    <span className="text-gray-400">Tap microphone to speak</span>
                  )}
                </div>
                <VoiceInput agentHandler = {agentHandler}
                />
              </>
            ) : (
              <>
                <input
                  ref={inputRef}
                  type="text"
                  value={agentHandler.input}
                  onChange={(e) => agentHandler.setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask me anything about dresses..."
                  className="flex-1 border rounded-full px-4 py-3 focus:outline-none focus:ring-2 focus:ring-pink-500"
                  disabled={agentHandler.isLoading}
                />
                <button
                  onClick={() => agentHandler.handleSend()}
                  disabled={!agentHandler.input.trim() || agentHandler.isLoading}
                  className="bg-linear-to-r from-pink-600 to-purple-600 text-white rounded-full p-3 hover:shadow-lg transition disabled:opacity-50"
                >
                  {agentHandler.isLoading ? (
                    <svg className="animate-spin h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                  )}
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatModal;