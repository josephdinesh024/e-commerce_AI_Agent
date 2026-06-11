import { useState, useEffect, useCallback, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

const API_BASE_URL = 'http://localhost:8000';

export const useUnifiedCopilot = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [sessionId] = useState(() => `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`);
  const [mode, setMode] = useState('text');
  const [history, setHistory] = useState([]);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [popupData, setPopupData] = useState(null);
  const [pendingAction, setPendingAction] = useState(null);
  const [idleTime, setIdleTime] = useState(0);
  const [lastActivity, setLastActivity] = useState(Date.now());
  
  const recognitionRef = useRef(null);
  const utteranceRef = useRef(null);
  const interruptRef = useRef(false);

  // Initialize speech recognition
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        handleVoiceInput(transcript);
      };

      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    } else {
      console.warn('Speech recognition not supported');
    }
  }, []);

  // Track idle time
  useEffect(() => {
    const events = ['mousedown', 'keydown', 'scroll', 'touchstart'];
    const resetActivity = () => {
      setLastActivity(Date.now());
      setIdleTime(0);
    };

    events.forEach(event => {
      window.addEventListener(event, resetActivity);
    });

    const interval = setInterval(() => {
      const now = Date.now();
      const idle = Math.floor((now - lastActivity) / 1000);
      setIdleTime(idle);
    }, 1000);

    return () => {
      events.forEach(event => {
        window.removeEventListener(event, resetActivity);
      });
      clearInterval(interval);
    };
  }, [lastActivity]);

  // Get page type from route
  const getPageType = useCallback((pathname) => {
    if (pathname === '/') return 'home';
    if (pathname.startsWith('/product/')) return 'product';
    if (pathname === '/cart') return 'cart';
    if (pathname === '/checkout') return 'checkout';
    if (pathname === '/orders') return 'orders';
    if (pathname === '/login') return 'login';
    return 'home';
  }, []);

  // Process input through unified endpoint
  const processInput = useCallback(async (message, inputMode = mode, context = {}) => {
    try {
      // Stop current speech if interrupting
      if (isSpeaking) {
        window.speechSynthesis.cancel();
        setIsSpeaking(false);
        interruptRef.current = true;
      }

      const requestBody = {
        session_id: sessionId,
        mode: inputMode,
        page_type: getPageType(location.pathname),
        route: location.pathname,
        user_idle_seconds: idleTime,
        interrupt_previous: interruptRef.current,
        ...context
      };

      // Only add message if provided
      if (message) {
        requestBody.message = message;
      }

      const response = await fetch(`${API_BASE_URL}/unified/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Update session state
      if (data.session_update) {
        setHistory(data.session_update.history || []);
        setMode(data.session_update.mode);
        if (data.session_update.pending_action) {
          setPendingAction(data.session_update.pending_action);
        }
      }

      // Handle voice output
      if (data.response && data.response.speak && data.response.message) {
        speak(data.response.message);
      }

      // Handle UI actions
      if (data.ui_action && data.ui_action.type !== 'none') {
        handleUIAction(data.ui_action);
      }

      // Handle popup
      if (data.popup && data.popup.show) {
        setPopupData(data.popup);
      }

      interruptRef.current = false;
      return data;

    } catch (error) {
      console.error('Copilot error:', error);
      interruptRef.current = false;
      throw error;
    }
  }, [sessionId, mode, location.pathname, idleTime, isSpeaking, getPageType]);

  // Handle voice input
  const handleVoiceInput = useCallback((transcript) => {
    console.log('Voice transcript:', transcript);
    processInput(transcript, 'voice');
  }, [processInput]);

  // Start listening
  const startListening = useCallback(() => {
    if (recognitionRef.current && !isListening) {
      try {
        recognitionRef.current.start();
        setIsListening(true);
      } catch (error) {
        console.error('Error starting recognition:', error);
      }
    }
  }, [isListening]);

  // Stop listening
  const stopListening = useCallback(() => {
    if (recognitionRef.current && isListening) {
      try {
        recognitionRef.current.stop();
        setIsListening(false);
      } catch (error) {
        console.error('Error stopping recognition:', error);
      }
    }
  }, [isListening]);

  // Speak text
  const speak = useCallback((text) => {
    window.speechSynthesis.cancel();
    
    // Clean HTML tags
    const cleanText = text.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
    
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    utterance.lang = 'en-US';
    
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => {
      setIsSpeaking(false);
      // Auto-start listening for next input in voice mode
      if (mode === 'voice') {
        setTimeout(() => {
          startListening();
        }, 500);
      }
    };
    utterance.onerror = () => {
      setIsSpeaking(false);
    };

    utteranceRef.current = utterance;
    window.speechSynthesis.speak(utterance);
  }, [mode, startListening]);

  // Handle UI actions
  const handleUIAction = useCallback((action) => {
    if (action.type === 'update_form' && action.require_confirmation) {
      // Show confirmation dialog
      setPendingAction(action);
    } else if (action.type === 'navigate' && action.target) {
      // Navigate after small delay
      setTimeout(() => {
        navigate(action.target);
      }, 500);
    } else if (action.type === 'update_form' && !action.require_confirmation) {
      // Auto-fill without confirmation (rare case)
      triggerFormFill(action.data);
    }
  }, [navigate]);

  // Trigger form fill
  const triggerFormFill = useCallback((formData) => {
    const event = new CustomEvent('copilot-fill-form', {
      detail: formData
    });
    window.dispatchEvent(event);
  }, []);

  // Confirm pending action
  const confirmAction = useCallback(() => {
    if (pendingAction) {
      if (pendingAction.type === 'update_form') {
        triggerFormFill(pendingAction.data);
      } else if (pendingAction.type === 'navigate' && pendingAction.target) {
        navigate(pendingAction.target);
      }
      setPendingAction(null);
    }
  }, [pendingAction, triggerFormFill, navigate]);

  // Context awareness - auto-suggest at idle thresholds
  useEffect(() => {
    // Trigger at specific idle times
    if ([8, 12, 20, 30].includes(idleTime)) {
      processInput(null, mode);
    }
  }, [idleTime]); // Don't include processInput to avoid loops

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      window.speechSynthesis.cancel();
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (error) {
          // Ignore errors on cleanup
        }
      }
    };
  }, []);

  return {
    // State
    sessionId,
    mode,
    setMode,
    history,
    isListening,
    isSpeaking,
    popupData,
    pendingAction,
    idleTime,
    
    // Actions
    processInput,
    startListening,
    stopListening,
    confirmAction,
    closePopup: () => setPopupData(null),
    cancelAction: () => setPendingAction(null)
  };
};

export default useUnifiedCopilot;