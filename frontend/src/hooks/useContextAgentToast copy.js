import { useState, useEffect, useCallback } from 'react';
import { getPageType, sendChatAnalyze, sendPageContext } from '../services/chatapi';
import { confirmActionToast } from '../components/toasts';
import { executeActions } from '../util/agentAction';
import { speak, stopSpeaking } from '../util/tts';
import { getSessionId } from '../services/api';
import buildPageContext from '../util/pageContext';

const API_BASE_URL = 'http://localhost:8000';

export const useContextAgentToast = () => {
  const [idleTime, setIdleTime] = useState(0);
  const [lastActivity, setLastActivity] = useState(Date.now());
  const [recognition, setRecognition] = useState(null);
  const [error, setError] = useState(null);
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hi 👋 Welcome to Dress Store AI Assistant. How can I help you today?",
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  var idleThresholds = [15, 30, 45]; // seconds



  useEffect(() => {
    // Check for browser support
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setError('Speech recognition not supported in this browser');
      return;
    }

    const recognitionInstance = new SpeechRecognition();
    recognitionInstance.continuous = false;
    recognitionInstance.interimResults = false;
    recognitionInstance.lang = 'en-US';

    recognitionInstance.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      onTranscript(transcript);
    };

    recognitionInstance.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      setError(event.error);
      onToggle(false);
    };

    recognitionInstance.onend = () => {
      onToggle(false);
    };

    setRecognition(recognitionInstance);
  }, []);

  useEffect(() => {
    if (!recognition) return;

    if (isListening) {
      try {
        recognition.start();
        setError(null);
      } catch (e) {
        console.error('Error starting recognition:', e);
        setError(e.message);
        onToggle(false);
      }
    } else {
      try {
        recognition.stop();
      } catch (e) {
        // Ignore errors when stopping
      }
    }
  }, [isListening, recognition]);

  // Reset activity
  const resetActivity = useCallback(() => {
    setLastActivity(Date.now());
    setIdleTime(0);
  }, []);

  // Track user activity
  useEffect(() => {
    const events = ['mousedown', 'keydown', 'scroll', 'touchstart'];

    events.forEach(event => {
      window.addEventListener(event, resetActivity);
    });

    return () => {
      events.forEach(event => {
        window.removeEventListener(event, resetActivity);
      });
    };
  }, [resetActivity]);

  // Update idle time
  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      const idleSeconds = Math.floor((now - lastActivity) / 1000);
      setIdleTime(idleSeconds);
    }, 1000);

    return () => clearInterval(interval);
  }, [lastActivity]);

  // Analyze context
  const analyzeContext = useCallback(async (additionalContext = {}) => {
    try {
      const pageType = getPageType(window.location.pathname);

      // Build context
      const context = {
        page_type: pageType,
        route: window.location.pathname,
        user_idle_seconds: idleTime,
        session_id: getSessionId(),
        ...additionalContext
      };
      console.log(context);
      // Call context API
      const response = await fetch(`${API_BASE_URL}/context/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(context)
      });

      if (!response.ok) {
        throw new Error('Context analysis failed');
      }

      const data = await response.json();
      console.log(data);
      try {
        // Show popup if suggested
        if (data.show_popup && data.confidence >= 0.6) {
          var actions = data?.action ? data.action?.type != null && data.action?.type !== "none" ? true : false : false;
          confirmActionToast(
            data.popup_message,
            () => {
              if (actions)
                executeActions(Array.isArray(data.action) ? data.action : [data.action]);
              else {
                // Chat agent call
                sendChatAnalyze("yeah sure", "voice").then(res => {
                  if (res.type === "done") {
                    const contents = JSON.parse(res.content);

                    if (contents.context_requested) {
                      // Build and send page context
                      const context = buildPageContext();
                      sendPageContext(context).then(res => {
                      });
                      return; // Don't display this message
                    }

                    // Handle voice output
                    if (contents.speak && contents.message) {
                      speak(contents.message);
                    }
                  }
                })
              }
            },
            "Assistant Suggestion",
            "yeah sure"
          )
          idleThresholds = idleThresholds * 5; // increase thresholds to avoid multiple popups
        }
      } catch (error) {
        console.log('Error showing popup:', error);
      }


    } catch (error) {
      console.error('Context agent error:', error);
    }
  }, [window.location.pathname, idleTime]);

  // Auto-analyze on idle time changes
  useEffect(() => {
    // Only analyze at specific idle thresholds to avoid spam
    if (idleThresholds.includes(idleTime)) {
      analyzeContext();
    }
  }, [idleTime, analyzeContext]);

  // Close popup
  const closePopup = () => {
  };

  return {
    analyzeContext,
    closePopup,
    idleTime
  };
};