import React, { createContext, useState, useCallback, useRef, useEffect } from 'react';
import { getSessionId } from '../../services/api';
import { getPageType, getSuggestions } from '../../services/chatapi.js';
import { toast } from 'react-hot-toast';

/**
 * Utility to generate a stable session ID for the tracking
 */
const generateSessionId = () => {
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem('ai_session_id');
    if (saved) return saved;
    const newId = 'user_' + Math.random().toString(36).substr(2, 9) + Date.now();
    localStorage.setItem('ai_session_id', newId);
    return newId;
  }
  return 'user_' + Math.random().toString(36).substr(2, 9) + Date.now();
};

/**
 * CopilotContext - Provides global state for the AI Assistant.
 * Flexible SDK: supports Auto-Fetch or Custom Handlers.
 */
const CopilotContext = createContext(undefined);

export const CopilotProvider = ({ children, config = {}, apiConfig, handlers }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [mode, setMode] = useState('text'); // 'text' | 'voice'
  const [messages, setMessages] = useState([]);
  const [pageContext, setPageContextState] = useState({});
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [pendingActions, setPendingActions] = useState([]);
  const [isWaiting, setIsWaiting] = useState(false);
  const [suggestions, setSuggestions] = useState([]);

  const [sessionId] = useState(() => getSessionId());

  const recognitionRef = useRef(null);

  // Load session history on mount
  useEffect(() => {
    const loadSessionHistory = async () => {
      try {
        if (!apiConfig || !apiConfig.endpoint) return;
        // Strip out '/agent' to get the base chat router path
        const baseUrl = apiConfig.endpoint.replace('/agent', '');
        const historyUrl = `${baseUrl}/session/${sessionId}/history`;

        const response = await fetch(historyUrl, {
          method: 'GET',
          headers: apiConfig.headers || { 'Content-Type': 'application/json' }
        });

        if (!response.ok) return;
        const data = await response.json();

        if (data && data.history && Array.isArray(data.history) && data.history.length > 0) {
          const historyMessages = data.history
            .filter(msg => !(msg.content && (msg.content.includes('[SYSTEM_DOM_CONTEXT]') || msg.content.includes('request page context') || msg.content.includes('Your previous response failed'))))
            .map(msg => ({
              id: Math.random().toString(36).substr(2, 9),
              role: msg.role === 'agent' ? 'agent' : 'user',
              content: msg.content ? msg.content.replace(/\[\(SYSTEM\) Current Page[^\]]*\]\n?/g, '').replace('User Message: ', '').trim() : '',
              html_content: msg.html_content || '',
              actions: msg.action || [],
              timestamp: new Date().toISOString()
            }));
            setMessages(historyMessages);
          } else {
            try {
              const sugData = await getSuggestions();
              setSuggestions(Array.isArray(sugData) ? sugData : (sugData.suggestions || []));
            } catch (err) {
              console.error("Failed to load suggestions:", err);
            }
          }
      } catch (err) {
        console.error("Failed to load session history:", err);
      }
    };

    loadSessionHistory();
  }, [sessionId, apiConfig]);

  // Toggle Copilot visibility
  const toggleCopilot = useCallback(() => {
    setIsOpen((prev) => !prev);
  }, []);

  // Add a message to the history
  const addMessage = useCallback((message) => {
    const newMessage = {
      id: Math.random().toString(36).substr(2, 9),
      role: 'agent',
      content: '',
      html_content: '',
      actions: [],
      timestamp: new Date().toISOString(),
      ...message,
    };
    setMessages((prev) => [...prev, newMessage]);
    return newMessage;
  }, []);

  // Text-to-Speech (TTS)
  const speakMessage = useCallback((text) => {
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);

      const utterance = new SpeechSynthesisUtterance(text);

      // Listen for when speech starts and stops
      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);

      window.speechSynthesis.speak(utterance);
    }
  }, []);

  // Send Message (Dual-Mode Networking + God Mode Loop)
  const sendMessage = useCallback(async (text, isSystemHidden = false, currentMode = mode) => {
    if (!text || !text.trim()) return;

    // 1. Add user message (unless it's a hidden system context loop)
    if (!isSystemHidden) {
      addMessage({ role: 'user', content: text });
      setIsWaiting(true);
    }

    let responseData = null;

    try {
      // --- NETWORK CALL ---
      if (handlers && handlers.onSendMessage) {
        // Custom Handler Mode
        responseData = await handlers.onSendMessage(text, sessionId);
      } else if (apiConfig && apiConfig.endpoint) {
        // Auto-Fetch Mode
        const currentPage = window.location.pathname;

        const res = await fetch(apiConfig.endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(apiConfig.headers || {})
          },
          body: JSON.stringify({ message: text, session_id: sessionId, page_type: getPageType(currentPage), route: currentPage })
        });
        if (!res.ok) throw new Error(`API error: ${res.status}`);
        responseData = await res.json();
      } else {
        // Fallback Mock (if neither provided)
        console.warn('CopilotProvider: No apiConfig or handlers provided. Using mock response.');
        await new Promise(resolve => setTimeout(resolve, 1000));
        responseData = {
          message: `Mock response to "${isSystemHidden ? '[Hidden Context]' : text}"`,
          html_content: '',
          action: [],
          speak: true,
          context_requested: false
        };
      }

      // --- HANDLE RESPONSE ---
      if (responseData) {
        let { message, html_content, action, speak, context_requested } = responseData;

        // Detect if the backend LLM leaked raw JSON tool calls into the 'message' string
        if (typeof message === 'string' && (message.trim().startsWith('{"name"') || message.trim().startsWith('{"type"'))) {
          toast.error("Agent returned unformatted JSON payload.");
          console.error("LLM JSON serialization leak detected:", message);

          // Extract salvaged conversational message if it exists anywhere in the raw dump
          const msgMatch = message.match(/"message"\s*:\s*"([^"]+)"/);
          message = msgMatch ? msgMatch[1] : "I experienced an error formatting my response. Please try again.";
          html_content = "";
          action = [];
        }

        // Display Agent Message
        if ((message || html_content) && !context_requested) {
          const agentMessage = addMessage({
            role: 'agent',
            content: message || '',
            html_content: html_content || '',
          });

          // Speak if allowed
          if (speak && currentMode === 'voice') {
            speakMessage(agentMessage.content);
          }
        }

        // Action Interception (Step 1)
        if (action && Array.isArray(action) && action.length > 0) {
          import('../../util/agentAction.js').then(({ executeActions }) => {
            if (isOpen) {
              const autoActions = action.filter(a => !a.require_confirmation);
              const confirmActions = action.filter(a => a.require_confirmation);

              if (autoActions.length > 0) executeActions(autoActions);
              if (confirmActions.length > 0) {
                setPendingActions(prev => [...prev, ...confirmActions]);
              }
            } else {
              executeActions(action);
            }
          }).catch(err => console.error("Failed to load agentAction utility", err));
        }

        // --- GOD MODE PAGE CONTEXT LOOP --- (Steps 2 - 6)
        if (context_requested) {
          // Step 3: Wait for DOM to settle
          setTimeout(async () => {
            try {
              // Step 4: Execute buildPageContext
              const { buildPageContext } = await import('../../util/pageContext.js');
              const domContext = buildPageContext();
              const fullContext = {
                ...domContext,
                appStateContext: pageContext
              };

              // Step 5: POST context
              const baseUrl = apiConfig.endpoint.replace('/agent-stream', '').replace('/agent', '');
              const res = await fetch(`${baseUrl}/context`, {
                method: 'POST',
                headers: apiConfig.headers || { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  session_id: sessionId,
                  context: fullContext
                })
              });

              // Step 6: Silently call sendMessage
              if (res.ok) {
                sendMessage("Page context provided. Please proceed with the next step.", true, currentMode);
              } else {
                console.error("Failed to POST page context", res.status);
              }
            } catch (err) {
              console.error("Failed to execute God Mode Page Context Loop:", err);
            }
          }, 1000); // 1000ms delay to let navigation settle
        }
      }

    } catch (error) {
      console.error("CopilotProvider sendMessage error:", error);
      addMessage({ role: 'agent', content: 'Connection error. Please try again.' });
    } finally {
      setIsWaiting(false);
    }

  }, [addMessage, mode, pageContext, speakMessage, apiConfig, handlers, sessionId, isOpen]);


  // Speech-to-Text (STT): Start Recording
  const startRecording = useCallback(() => {

    // Stop the agent from speaking instantly!
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }

    const SpeechRecognition = typeof window !== 'undefined' && (window.SpeechRecognition || window.webkitSpeechRecognition);

    if (!SpeechRecognition) {
      console.warn("Speech Recognition API not supported in this browser.");
      return;
    }

    if (!recognitionRef.current) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        setIsRecording(true);
      };

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        if (transcript) {
          sendMessage(transcript, false, 'voice'); // Explicitly pass 'voice' mode to ensure closure is correct
        }
      };

      recognition.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        setIsRecording(false);
      };

      recognition.onend = () => {
        setIsRecording(false);
      };

      recognitionRef.current = recognition;
    }

    try {
      recognitionRef.current.start();
    } catch (err) {
      console.error("Failed to start speech recognition:", err);
    }
  }, [sendMessage]);

  // STT: Stop Recording
  const stopRecording = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
  }, []);

  // Silent update for page context
  const setPageContext = useCallback((data) => {
    setPageContextState((prev) => ({ ...prev, ...data }));
  }, []);

  // Context value exposed to hooks
  const value = {
    // State
    isOpen,
    mode,
    messages,
    config,
    pageContext,
    isRecording,
    isSpeaking,
    sessionId,
    pendingActions,
    isWaiting,
    suggestions,

    // Methods
    toggleCopilot,
    setMode: (newMode) => setMode(newMode),
    setPageContext,
    addMessage,
    sendMessage,
    startRecording,
    stopRecording,
    speakMessage,
    clearPendingActions: () => setPendingActions([]), // helper utility
    removePendingAction: (index) => setPendingActions(prev => prev.filter((_, i) => i !== index)),
  };

  return (
    <CopilotContext.Provider value={value}>
      {children}
    </CopilotContext.Provider>
  );
};

export default CopilotContext;
