import React, { createContext, useState, useCallback, useRef, useEffect } from 'react';
import { getSessionId, updateSessionId } from '../../services/api';
import { getPageType } from '../../services/chatapi.js';
import { toast } from 'react-hot-toast';

/**
 * CopilotContext — Global state for the AI shopping assistant.
 *
 * Changes from previous version:
 * - Removed: god-mode DOM context loop (context_requested, buildPageContext, hidden messages)
 * - Removed: click / enter / focus action handling — backend owns all mutations now
 * - Added:   cart_refresh action → triggers CartContext refetch
 * - Added:   suggestions per message → shown as clickable chips in widget
 * - Improved: voice STT — tap-to-toggle instead of hold, auto-stop on silence
 * - Improved: TTS queue — interrupts cleanly when user starts speaking
 */

const CopilotContext = createContext(undefined);

export const CopilotProvider = ({ children, config = {}, apiConfig, handlers, onCartRefresh }) => {
  const [isOpen, setIsOpen]           = useState(false);
  const [mode, setMode]               = useState('text');       // 'text' | 'voice'
  const [messages, setMessages]       = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking]   = useState(false);
  const [isWaiting, setIsWaiting]     = useState(false);
  // confirmation_required state — shown as a blocking confirm banner in the widget
  const [pendingConfirm, setPendingConfirm] = useState(null); // { message, onConfirm }

  const [sessionId] = useState(() => getSessionId());

  // Voice refs
  const recognitionRef  = useRef(null);
  const isRecordingRef  = useRef(false);   // stable ref for async closures
  const ttsQueueRef     = useRef([]);
  const isSpeakingRef   = useRef(false);

  // ─── Session history ────────────────────────────────────────────────────────
  useEffect(() => {
    if (!apiConfig?.endpoint) return;
    const baseUrl   = apiConfig.endpoint.replace('/agent-stream', '').replace('/agent', '');
    const historyUrl = `${baseUrl}/session/${sessionId}/history`;

    fetch(historyUrl, { headers: apiConfig.headers || {} })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!data?.history?.length) return;
        const cleaned = data.history
          // strip internal system messages that should never appear in UI
          .filter(m => m.content && !m.content.includes('[SYSTEM_DOM_CONTEXT]'))
          .map(m => ({
            id:           Math.random().toString(36).slice(2),
            role:         m.role === 'agent' ? 'agent' : 'user',
            content:      m.content.replace(/\(SYSTEM\)[^\n]*\n?/g, '').replace('User Message: ', '').trim(),
            html_content: m.html_content || '',
            suggestions:  m.suggestions  || [],
            timestamp:    new Date().toISOString(),
          }));
        setMessages(cleaned);
      })
      .catch(() => {/* non-fatal */});
  }, [sessionId, apiConfig]);

  // ─── Message helpers ────────────────────────────────────────────────────────
  const addMessage = useCallback((msg) => {
    const full = {
      id:           Math.random().toString(36).slice(2),
      role:         'agent',
      content:      '',
      html_content: '',
      suggestions:  [],
      timestamp:    new Date().toISOString(),
      ...msg,
    };
    setMessages(prev => [...prev, full]);
    return full;
  }, []);

  const toggleCopilot = useCallback(() => setIsOpen(p => !p), []);

  // ─── TTS helpers ────────────────────────────────────────────────────────────
  /**
   * Speak text via browser TTS.
   * Cancels any ongoing speech first, then processes the queue.
   */
  const speakMessage = useCallback((text) => {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    isSpeakingRef.current = false;
    setIsSpeaking(false);

    if (!text?.trim()) return;

    // Split on sentence boundaries for lower latency first-word output
    const sentences = text.match(/[^.!?]+[.!?]*/g) || [text];

    sentences.forEach((sentence, i) => {
      const utt   = new SpeechSynthesisUtterance(sentence.trim());
      utt.rate    = 1.05;   // slightly faster feels more natural
      utt.pitch   = 1.0;

      if (i === 0) {
        utt.onstart = () => { isSpeakingRef.current = true; setIsSpeaking(true); };
      }
      if (i === sentences.length - 1) {
        utt.onend   = () => { isSpeakingRef.current = false; setIsSpeaking(false); };
        utt.onerror = () => { isSpeakingRef.current = false; setIsSpeaking(false); };
      }
      window.speechSynthesis.speak(utt);
    });
  }, []);

  /** Interrupt TTS immediately — called when user starts speaking */
  const stopSpeaking = useCallback(() => {
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    isSpeakingRef.current = false;
    setIsSpeaking(false);
  }, []);

  // ─── Action handler ─────────────────────────────────────────────────────────
  /**
   * Handles the simplified action array from the backend.
   * Only two meaningful types now: navigate and cart_refresh.
   * All DOM mutation actions (click, enter, focus) are gone.
   */
  const handleActions = useCallback((actions) => {
    if (!Array.isArray(actions)) return;

    actions.forEach(action => {
      switch (action.type) {
        case 'navigate':
          if (action.target) {
            // Small delay so the agent message renders before navigation
            setTimeout(() => { window.location.href = action.target; }, 400);
          }
          break;

        case 'cart_refresh':
          // Notify CartContext to re-fetch cart count
          // onCartRefresh is passed from App.jsx via CopilotProvider prop
          if (typeof onCartRefresh === 'function') {
            onCartRefresh();
          } else {
            // Fallback: fire a custom event CartContext can listen to
            window.dispatchEvent(new CustomEvent('agent:cart_refresh'));
          }
          break;

        case 'update_session_id':
          if (action.new_session_id) {
            updateSessionId(action.new_session_id);
            toast.success('Session updated successfully.');
          }

        case 'none':
        default:
          break;
      }
    });
  }, [onCartRefresh]);

  // ─── Core send message ──────────────────────────────────────────────────────
  const sendMessage = useCallback(async (text, currentMode = mode) => {
    if (!text?.trim()) return;

    // Stop agent speaking when user sends a message
    stopSpeaking();

    addMessage({ role: 'user', content: text });
    setIsWaiting(true);

    try {
      let responseData = null;

      if (handlers?.onSendMessage) {
        // Custom handler mode (for external integrations)
        responseData = await handlers.onSendMessage(text, sessionId);
      } else if (apiConfig?.endpoint) {
        const res = await fetch(apiConfig.endpoint, {
          method:  'POST',
          headers: { 'Content-Type': 'application/json', ...(apiConfig.headers || {}) },
          body:    JSON.stringify({
            message:    text,
            session_id: sessionId,
            route:      window.location.pathname,
            page_type:  getPageType(window.location.pathname),
            mode:       currentMode,
          }),
        });
        if (!res.ok) throw new Error(`API ${res.status}`);
        responseData = await res.json();
      }

      if (!responseData) return;

      const { message, html_content, action, speak, suggestions, confirmation_required } = responseData;

      // Guard against LLM JSON serialisation leaks
      let safeMessage = message;
      if (typeof message === 'string' && message.trim().startsWith('{')) {
        const match = message.match(/"message"\s*:\s*"([^"]+)"/);
        safeMessage = match ? match[1] : 'Sorry, I had a formatting error. Please try again.';
        toast.error('Agent response formatting issue detected.');
      }

      // If backend needs confirmation before a destructive action
      if (confirmation_required) {
        // Show the message describing what will happen
        addMessage({ role: 'agent', content: safeMessage, html_content: html_content || '', suggestions: [] });
        // Store the confirm state — widget renders the confirm banner
        setPendingConfirm({
          message: safeMessage,
          onConfirm: () => {
            setPendingConfirm(null);
            sendMessage('Yes, confirm', currentMode);
          },
          onDecline: () => {
            setPendingConfirm(null);
            addMessage({ role: 'agent', content: 'Got it — action cancelled.', suggestions: ['Go back to shopping', 'View my cart'] });
          },
        });
        return;
      }

      // Normal response
      if (safeMessage || html_content) {
        addMessage({
          role:         'agent',
          content:      safeMessage || '',
          html_content: html_content || '',
          suggestions:  Array.isArray(suggestions) ? suggestions : [],
        });

        if (speak && currentMode === 'voice' && safeMessage) {
          speakMessage(safeMessage);
        }
      }

      // Handle UI actions
      handleActions(action);

    } catch (err) {
      console.error('sendMessage error:', err);
      addMessage({ role: 'agent', content: 'Connection error. Please try again.', suggestions: [] });
    } finally {
      setIsWaiting(false);
    }
  }, [mode, sessionId, apiConfig, handlers, addMessage, handleActions, speakMessage, stopSpeaking]);

  // ─── Voice: STT ─────────────────────────────────────────────────────────────
  /**
   * Tap-to-toggle recording (replaces hold-to-speak).
   * Uses webkitSpeechRecognition with continuous=false and silence detection.
   *
   * Auto-submits transcript on end — no need to hold a button.
   */
  const initRecognition = useCallback(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { toast.error('Speech recognition not supported in this browser.'); return null; }

    const recognition         = new SR();
    recognition.continuous    = false;     // single utterance per tap
    recognition.interimResults = true;     // show interim for UI feedback
    recognition.lang          = 'en-US';
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      isRecordingRef.current = true;
      setIsRecording(true);
      stopSpeaking();   // interrupt agent if it was talking
    };

    recognition.onresult = (event) => {
      // Take the best final result
      let finalTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        }
      }
      if (finalTranscript.trim()) {
        sendMessage(finalTranscript.trim(), 'voice');
      }
    };

    recognition.onerror = (e) => {
      console.error('STT error:', e.error);
      if (e.error !== 'no-speech') toast.error(`Mic error: ${e.error}`);
      isRecordingRef.current = false;
      setIsRecording(false);
    };

    recognition.onend = () => {
      isRecordingRef.current = false;
      setIsRecording(false);
      recognitionRef.current = null;   // allow re-init on next tap
    };

    return recognition;
  }, [sendMessage, stopSpeaking]);

  /** Tap to start recording. Tapping again while recording stops it. */
  const toggleRecording = useCallback(() => {
    if (isRecordingRef.current) {
      recognitionRef.current?.stop();
      return;
    }
    const rec = initRecognition();
    if (!rec) return;
    recognitionRef.current = rec;
    try { rec.start(); }
    catch (e) { console.error('STT start failed:', e); }
  }, [initRecognition]);

  // Keep legacy startRecording/stopRecording for backward compat with widget
  const startRecording = useCallback(() => {
    if (isRecordingRef.current) return;
    const rec = initRecognition();
    if (!rec) return;
    recognitionRef.current = rec;
    try { rec.start(); }
    catch (e) { console.error('STT start failed:', e); }
  }, [initRecognition]);

  const stopRecording = useCallback(() => {
    recognitionRef.current?.stop();
  }, []);

  // ─── Context value ───────────────────────────────────────────────────────────
  const value = {
    // State
    isOpen, mode, messages, isRecording, isSpeaking,
    isWaiting, sessionId, pendingConfirm,

    // Methods
    toggleCopilot,
    setMode:       (m) => setMode(m),
    addMessage,
    sendMessage,
    startRecording,
    stopRecording,
    toggleRecording,
    speakMessage,
    stopSpeaking,
    clearPendingConfirm: () => setPendingConfirm(null),
  };

  return (
    <CopilotContext.Provider value={value}>
      {children}
    </CopilotContext.Provider>
  );
};

export default CopilotContext;

