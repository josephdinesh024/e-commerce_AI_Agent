import React, { useState, useEffect } from 'react';

const VoiceInput = ({ agentHandler }) => {

  if (agentHandler.error && agentHandler.error !== 'no-speech') {
    return (
      <div className="text-xs text-red-500">
        {agentHandler.error}
      </div>
    );
  }

  return (
    <button
      onClick={() => agentHandler.setIsListening(!agentHandler.isListening)}
      disabled={!agentHandler.recognition}
      className={`p-3 rounded-full transition ${
        agentHandler.isListening
          ? 'bg-red-500 animate-pulse'
          : agentHandler.recognition
          ? 'bg-blue-500 hover:bg-blue-600'
          : 'bg-gray-300 cursor-not-allowed'
      }`}
    >
      {agentHandler.isListening ? (
        <svg className="w-6 h-6" fill="white" viewBox="0 0 20 20">
          <path d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" />
        </svg>
      ) : (
        <svg className="w-6 h-6" fill="white" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
        </svg>
      )}
    </button>
  );
};

export default VoiceInput;