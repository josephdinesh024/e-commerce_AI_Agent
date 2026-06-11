import React from 'react';
import ChatModal from './ChatModal';
import { isSpeaking } from '../../util/tts';

const ChatButton = ({ agentHandler }) => {
  const { 
    isOpen, 
    setIsOpen, 
    mode, 
    isListening, 
    currentSpeaker, 
    isLoading,
    setIsListening
  } = agentHandler;

  // Manual check for "isSpeaking" if your utility doesn't sync to state automatically
  // Assuming your agentHandler provides these states
  const isAssistantSpeaking = currentSpeaker === 'assistant' && isSpeaking() && !isLoading;
  const isUserSpeaking = isListening && currentSpeaker === 'user';

  const handleOpen = () => {
    setIsOpen(true);
  };

  return (
    <>
      <div className="fixed bottom-6 right-6 z-50">
        {/* Soundwaves */}
        {isAssistantSpeaking && (
          <>
            <div className="animate-wave text-green-400"></div>
            <div className="animate-wave animate-wave-delayed text-white"></div>
          </>
        )}
        {isUserSpeaking && (
          <>
            <div className="animate-wave text-pink-400"></div>
            <div className="animate-wave animate-wave-delayed text-pink-400"></div>
          </>
        )}

        <button
          onClick={handleOpen}
          onMouseOverCapture={()=>{
            if(isListening == false && mode == 'voice' && !isSpeaking())
              setIsListening(true);
          }}
          className="relative bg-gradient-to-r from-pink-600 to-purple-600 text-white rounded-full p-4 shadow-2xl hover:shadow-3xl transform hover:scale-110 transition-all duration-300 group"
          aria-label="AI Assistant"
        >
          {/* Icon Switching Logic */}
          {mode === 'voice' ? (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
          )}

          {/* Sparkle (Only show when idle) */}
          {!isAssistantSpeaking && !isUserSpeaking && (
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-yellow-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-yellow-500"></span>
            </span>
          )}
        </button>

        {/* Tooltip */}
        <div className="absolute bottom-full right-0 mb-4 hidden group-hover:block">
          <div className="bg-gray-900 text-white text-xs rounded py-1 px-2">
            {isListening ? "Listening..." : "AI Assistant"}
          </div>
        </div>
      </div>

      {isOpen && <ChatModal agentHandler={agentHandler} />}
    </>
  );
};

export default ChatButton;