import { useState, useEffect, useCallback, use } from 'react';
import { getPageType, sendChatAnalyze, sendPageContext, getSessionHistory } from '../services/chatapi';
import { confirmActionToast } from '../components/toasts';
import { executeActions } from '../util/agentAction';
import { speak, stopSpeaking, isSpeaking } from '../util/tts';
import { getSessionId } from '../services/api';
import buildPageContext from '../util/pageContext';
import toast from 'react-hot-toast'

const API_BASE_URL = 'http://localhost:8000';

export const useContextAgentToast = () => {
  const [idleTime, setIdleTime] = useState(0);
  const [lastActivity, setLastActivity] = useState(Date.now());
  const [recognition, setRecognition] = useState(null);
  const [currentSpeaker, setCurrentSpeaker] = useState('assistant'); // Track who is speaking for TTS
  const [aiAgentIds, setAiAgentIds] = useState(Date.now()); // Track which agents have been triggered
  var idleThresholds = [30]; // seconds

  const [error, setError] = useState(null);
  const [isListening, setIsListening] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hi 👋 Welcome to Dress Store AI Assistant. How can I help you today?",
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [mode, setMode] = useState('text'); // 'text' or 'voice'
  const [isLoading, setIsLoading] = useState(false);

  useEffect(()=>{
    // Load session history on mount
    getSessionHistory().then(res => {
      setMessages(res.history.slice(-15).map(msg =>({
        role: msg.role,
        content: agentMessages(msg.content),
        timestamp: new Date(msg.timestamp)
      })));
      const last_elm = res.history.slice(-1)[0];
      setMode(last_elm?.type)
    }).catch(err => {
      console.error('Failed to load session history:', err);
    });

      // console.log(JSON.parse("msg 'hello'"));
  },[])

  const agentMessages = (content) => {
    if (content) {
      
      try {
        const json = JSON.parse(content);
        return (json['message'] + json['html_content']) || ''
      } catch (error) {
        return content
      }
    }else
      return content;
  }

  useEffect(() => {
    if (error) toast.error(error);
  }, [error]);

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
      // onTranscript(transcript);
      setInput(transcript);
      setMode('voice');
      handleSend(transcript, 'voice');
    };

    recognitionInstance.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      setError(event.error);
      setIsListening(false);
    };

    recognitionInstance.onend = () => {
      setIsListening(false);
    };


    setRecognition(recognitionInstance);
  }, []);

  useEffect(() => {
    if (!recognition) return;

    if (isListening && !isSpeaking()) {
      try {
        recognition.start();
        setCurrentSpeaker('user');
        setError(null);
      } catch (e) {
        console.error('Error starting recognition:', e);
        setError(e.message);
        setIsListening(false);
      }
    } else {
      try {
        recognition.stop();
      } catch (e) {
        // Ignore errors when stopping
      }
    }
  }, [isListening, recognition]);

  useEffect(() => {
      if (!isSpeaking() && isListening == false && mode == 'voice' && isOpen == false) {
        setTimeout(() => {setIsListening(true)}, 1000);
      }
  },[isSpeaking()]);
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
  }, [resetActivity, isOpen]);

  // Update idle time
  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      const idleSeconds = Math.floor((now - lastActivity) / 1000);
      setIdleTime(idleSeconds);

      // if(idleSeconds > 20 && mode == 'voice' && isOpen == true) {
      //   setIsOpen(false);
      //   toast('Agent interface closed, you can continue voice chatting in background', {
      //     icon: '🔊',
      //   });
      // }

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
                const aiMessage = {
                  id: Date.now(),
                  role: 'assistant',
                  content: data.popup_message,
                  timestamp: new Date(),
                  streaming: false
                };
                setMessages(prev => [...prev, aiMessage]);
                setMode('voice');
                handleSend("yeah sure","voice")
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
  }, [idleTime]);

  // Auto-analyze on idle time changes
  useEffect(() => {
    // Only analyze at specific idle thresholds to avoid spam
    if (idleThresholds.includes(idleTime) && isOpen == false && isListening == false) {
      analyzeContext();
    }
  }, [idleTime, analyzeContext]);

  // Close popup
  const closePopup = () => {
    setIsOpen(false);
    setInput('');
    setIdleTime(0);
    setIsLoading(false);
  };

  // ** Chat Agent calls **
  const handlePageContext = (contents) => {
    // Build and send page context
    const context = buildPageContext();
    // console.log("Agent requested context. Sending page context:", context);
    if (contents?.message && !contents?.message.includes('context_requested')) {
      speak(contents?.message);
      setCurrentSpeaker('assistant');
    }

    sendPageContext(context).then(res => {
      console.log('Page context sent:', res, context);
      setTimeout(() => {
        handleSend('shared current page context', mode);
      }, 2000);
    });
  }


  const handleSend = async (messageText = input, inputMode = mode) => {
    if (!messageText.trim() || isLoading) return;

    if (messageText != 'shared current page context') {
      const userMessage = {
        role: 'user',
        content: messageText,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, userMessage]);
      setInput('');

      setAiAgentIds(Date.now()); // Generate new ID for this agent interaction
      const aiMessage = {
        id: aiAgentIds,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        streaming: true
      };
      setMessages(prev => [...prev, aiMessage]);
    }
    setIsLoading(true);
    if (inputMode === 'voice')
      setIsListening(false);

    try {
      const stream = await sendChatAnalyze(messageText, inputMode);  // Pass mode
      if (stream && stream?.type == "done") {
        const contents = JSON.parse(stream.content);

        if (contents.context_requested) {
          handlePageContext(contents);
        } else {

          // Extract just the message for display
          const displayContent = (contents.message + contents.html_content);

          // Update message with the actual message content (not full JSON)
          setMessages(prev =>
            prev.map(msg =>
              msg.id === aiAgentIds
                ? { ...msg, content: displayContent, streaming: false }
                : msg
            )
          );

          // Handle voice output
          if (contents.speak && contents.message) {
            speak(contents.message);
            setCurrentSpeaker('assistant');
          }
          
          if (contents.action) {
            console.log(contents.action);
            executeActions(contents.action);
          }

        }
      }

      setIsLoading(false);
    } catch (error) {
      console.error('Error sending message:', error);
      setIsLoading(false);
    }
    // if (inputMode === 'voice')
      // setIsListening(true);
  };


  return {
    // State
    recognition,
    error,
    isListening,
    isOpen,
    messages,
    input,
    mode,
    isLoading,
    currentSpeaker,

    // Actions
    setError,
    setIsListening,
    setIsOpen,
    setMessages,
    setInput,
    setMode,
    setIsLoading,
    analyzeContext,
    closePopup,
    handleSend
  };
};