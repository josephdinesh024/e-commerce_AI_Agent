import React, { useEffect, useRef, useState } from 'react';
import { useCopilot } from './useCopilot';

// ─── Icons ───────────────────────────────────────────────────────────────────

const ChatIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
  </svg>
);

const MicIcon = ({ size = 24 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
    <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
    <line x1="12" y1="19" x2="12" y2="22" />
  </svg>
);

const StopIcon = ({ size = 24 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
    <rect x="4" y="4" width="16" height="16" rx="2" />
  </svg>
);

const KeyboardIcon = ({ size = 24 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="4" width="20" height="16" rx="2" />
    <line x1="6" y1="8" x2="6.01" y2="8" /><line x1="10" y1="8" x2="10.01" y2="8" />
    <line x1="14" y1="8" x2="14.01" y2="8" /><line x1="18" y1="8" x2="18.01" y2="8" />
    <line x1="8" y1="12" x2="16" y2="12" />
  </svg>
);

const SpeakerIcon = ({ size = 24 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
    <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />
  </svg>
);

const SendIcon = ({ size = 18 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
  </svg>
);

// ─── Sub-components ───────────────────────────────────────────────────────────

/** Typing indicator — three bouncing dots */
const TypingIndicator = () => (
  <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: '12px' }}>
    <div style={{
      padding: '10px 16px', borderRadius: '16px', borderBottomLeftRadius: '4px',
      backgroundColor: '#fff', boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
      border: '1px solid #e1e4e8', display: 'flex', gap: '4px', alignItems: 'center',
    }}>
      {[0, '-0.32s', '-0.16s'].map((delay, i) => (
        <div key={i} style={{
          width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#d500f9',
          animation: 'bounce-dots 1.4s infinite ease-in-out both',
          animationDelay: typeof delay === 'string' ? delay : undefined,
        }} />
      ))}
    </div>
  </div>
);

/** Single chat message bubble */
const MessageBubble = ({ msg, onSuggestionClick }) => {
  const isUser = msg.role === 'user';
  return (
    <div style={{ marginBottom: '12px' }}>
      <div style={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start' }}>
        <div style={{
          maxWidth: '85%', padding: '10px 14px', fontSize: '14px', lineHeight: '1.5',
          borderRadius: '16px',
          borderBottomRightRadius: isUser ? '4px' : '16px',
          borderBottomLeftRadius:  isUser ? '16px' : '4px',
          backgroundColor: isUser ? '#d500f9' : '#fff',
          color:           isUser ? 'white'    : '#333',
          boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
          border:    isUser ? 'none' : '1px solid #e1e4e8',
        }}>
          {msg.content && <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>}
          {msg.html_content && (
            <div
              style={{ marginTop: msg.content ? '10px' : 0 }}
              dangerouslySetInnerHTML={{ __html: msg.html_content }}
            />
          )}
        </div>
      </div>

      {/* Suggestion chips — shown below agent messages only */}
      {!isUser && msg.suggestions?.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '8px', paddingLeft: '4px' }}>
          {msg.suggestions.map((sug, i) => (
            <button
              key={i}
              onClick={() => onSuggestionClick(sug)}
              style={{
                padding: '5px 12px', fontSize: '12px', borderRadius: '14px',
                border: '1px solid #d500f9', color: '#d500f9',
                backgroundColor: 'white', cursor: 'pointer',
                transition: 'all 0.15s', whiteSpace: 'nowrap',
              }}
              onMouseEnter={e => { e.target.style.backgroundColor = '#fae1ff'; }}
              onMouseLeave={e => { e.target.style.backgroundColor = 'white'; }}
            >
              {sug}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

/** Order / destructive action confirmation banner */
const ConfirmBanner = ({ pendingConfirm }) => {
  if (!pendingConfirm) return null;
  return (
    <div style={{
      padding: '12px 14px', background: '#fff8e1',
      borderTop: '1px solid #ffe082', borderBottom: '1px solid #ffe082',
      flexShrink: 0,
    }}>
      <div style={{ fontSize: '12px', color: '#795548', marginBottom: '8px', fontWeight: '600' }}>
        Confirm action
      </div>
      <div style={{ display: 'flex', gap: '8px' }}>
        <button
          onClick={pendingConfirm.onConfirm}
          style={{
            flex: 1, padding: '8px', borderRadius: '8px', border: 'none',
            backgroundColor: '#4caf50', color: 'white', cursor: 'pointer',
            fontSize: '13px', fontWeight: '600',
          }}
        >
          Yes, confirm
        </button>
        <button
          onClick={pendingConfirm.onDecline}
          style={{
            flex: 1, padding: '8px', borderRadius: '8px', border: 'none',
            backgroundColor: '#f5f5f5', color: '#555', cursor: 'pointer',
            fontSize: '13px', fontWeight: '600',
          }}
        >
          Cancel
        </button>
      </div>
    </div>
  );
};

/** Voice mic button — tap to start, tap again to stop */
const VoiceMicButton = ({ isRecording, isSpeaking, toggleRecording, stopSpeaking }) => {
  let bg        = '#d500f9';
  let label     = 'Tap to speak';
  let animation = 'none';
  let icon      = <MicIcon size={20} />;

  if (isRecording) {
    bg        = '#ff4757';
    label     = 'Listening… tap to stop';
    animation = 'pulse-record 1.5s infinite';
    icon      = <StopIcon size={18} />;
  } else if (isSpeaking) {
    bg        = '#7b1fa2';
    label     = 'Agent speaking… tap to interrupt';
    animation = 'pulse-speak 2s infinite';
    icon      = <SpeakerIcon size={18} />;
  }

  const handleClick = () => {
    if (isSpeaking) { stopSpeaking(); return; }
    toggleRecording();
  };

  return (
    <button
      onClick={handleClick}
      style={{
        flex: 1, padding: '12px 16px', borderRadius: '24px', border: 'none',
        backgroundColor: bg, color: 'white', cursor: 'pointer',
        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
        fontWeight: '600', fontSize: '14px', transition: 'all 0.3s', animation,
      }}
    >
      {icon}
      {label}
    </button>
  );
};

// ─── Main Widget ──────────────────────────────────────────────────────────────

const CopilotWidget = () => {
  const {
    isOpen, mode, messages, isRecording, isSpeaking, isWaiting, pendingConfirm,
    toggleCopilot, setMode, sendMessage, startRecording, stopRecording,
    toggleRecording, stopSpeaking,
  } = useCopilot();

  const [inputValue, setInputValue]   = useState('');
  const messagesEndRef                = useRef(null);

  // Auto-scroll to bottom when messages change or widget opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 60);
    }
  }, [messages, isOpen]);

  const handleSend = () => {
    if (!inputValue.trim()) return;
    sendMessage(inputValue.trim());
    setInputValue('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  // Closed state — floating button
  if (!isOpen) {
    return (
      <div style={{ position: 'fixed', bottom: '24px', right: '24px', zIndex: 9999 }}>
        <style>{`
          @keyframes pulse-record {
            0%   { box-shadow: 0 0 0 0 rgba(255,71,87,0.7); }
            70%  { box-shadow: 0 0 0 14px rgba(255,71,87,0); }
            100% { box-shadow: 0 0 0 0 rgba(255,71,87,0); }
          }
          @keyframes pulse-speak {
            0%   { box-shadow: 0 0 0 0 rgba(213,0,249,0.7); }
            70%  { box-shadow: 0 0 0 14px rgba(213,0,249,0); }
            100% { box-shadow: 0 0 0 0 rgba(213,0,249,0); }
          }
          @keyframes bounce-dots {
            0%, 80%, 100% { transform: scale(0); }
            40%           { transform: scale(1); }
          }
        `}</style>
        <button
          onClick={toggleCopilot}
          style={{
            width: '60px', height: '60px', borderRadius: '50%',
            backgroundColor: '#d500f9', color: 'white', border: 'none',
            boxShadow: '0 4px 16px rgba(213,0,249,0.4)', cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'transform 0.2s',
            animation: isRecording ? 'pulse-record 1.5s infinite' : isSpeaking ? 'pulse-speak 2s infinite' : 'none',
          }}
          onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.08)'}
          onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
          title="Open AI Assistant"
        >
          {isRecording ? <StopIcon size={22} /> : isSpeaking ? <SpeakerIcon size={22} /> : <ChatIcon />}
        </button>
      </div>
    );
  }

  // Open state — chat panel
  return (
    <>
      <style>{`
        @keyframes pulse-record {
          0%   { box-shadow: 0 0 0 0 rgba(255,71,87,0.7); }
          70%  { box-shadow: 0 0 0 14px rgba(255,71,87,0); }
          100% { box-shadow: 0 0 0 0 rgba(255,71,87,0); }
        }
        @keyframes pulse-speak {
          0%   { box-shadow: 0 0 0 0 rgba(213,0,249,0.7); }
          70%  { box-shadow: 0 0 0 14px rgba(213,0,249,0); }
          100% { box-shadow: 0 0 0 0 rgba(213,0,249,0); }
        }
        @keyframes bounce-dots {
          0%, 80%, 100% { transform: scale(0); }
          40%           { transform: scale(1); }
        }
        .copilot-suggestions button:hover { background-color: #fae1ff !important; }
      `}</style>

      <div style={{
        position: 'fixed', bottom: '24px', right: '24px',
        width: '360px', height: '540px',
        backgroundColor: 'white', borderRadius: '16px',
        boxShadow: '0 8px 40px rgba(0,0,0,0.18)',
        display: 'flex', flexDirection: 'column',
        zIndex: 9999, overflow: 'hidden',
        border: '1px solid #e8e0f0',
        fontFamily: 'system-ui, -apple-system, sans-serif',
      }}>

        {/* ── Header ── */}
        <div style={{
          background: 'linear-gradient(135deg, #d500f9 0%, #aa00ff 100%)',
          color: 'white', padding: '14px 16px',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '32px', height: '32px', borderRadius: '50%',
              background: 'rgba(255,255,255,0.2)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              {isRecording ? <StopIcon size={16} /> : isSpeaking ? <SpeakerIcon size={16} /> : <ChatIcon />}
            </div>
            <div>
              <div style={{ fontWeight: '700', fontSize: '15px', lineHeight: 1 }}>AI Assistant</div>
              <div style={{ fontSize: '11px', opacity: 0.85, marginTop: '2px' }}>
                {isRecording ? 'Listening…' : isSpeaking ? 'Speaking…' : isWaiting ? 'Thinking…' : mode === 'voice' ? 'Voice mode' : 'Online'}
              </div>
            </div>
          </div>
          <button
            onClick={toggleCopilot}
            style={{ background: 'rgba(255,255,255,0.15)', border: 'none', color: 'white', cursor: 'pointer', borderRadius: '50%', width: '28px', height: '28px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '16px' }}
          >
            ✕
          </button>
        </div>

        {/* ── Messages ── */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '16px', backgroundColor: '#f8f9ff', display: 'flex', flexDirection: 'column' }}>
          {messages.length === 0 ? (
            <div style={{ textAlign: 'center', margin: 'auto', color: '#888' }}>
              <div style={{ fontSize: '32px', marginBottom: '8px' }}>👗</div>
              <div style={{ fontSize: '15px', fontWeight: '600', color: '#555', marginBottom: '6px' }}>Hi! I'm your style assistant.</div>
              <div style={{ fontSize: '13px', marginBottom: '16px' }}>Ask me anything about our dresses.</div>
            </div>
          ) : (
            messages.map(msg => (
              <MessageBubble
                key={msg.id}
                msg={msg}
                onSuggestionClick={(sug) => sendMessage(sug)}
              />
            ))
          )}

          {isWaiting && <TypingIndicator />}
          <div ref={messagesEndRef} />
        </div>

        {/* ── Confirmation banner (order placement) ── */}
        <ConfirmBanner pendingConfirm={pendingConfirm} />

        {/* ── Input area ── */}
        <div style={{
          padding: '10px 12px', borderTop: '1px solid #e8e0f0',
          backgroundColor: 'white', display: 'flex', gap: '8px', alignItems: 'center',
          flexShrink: 0,
        }}>
          {mode === 'text' ? (
            <>
              <input
                type="text"
                value={inputValue}
                onChange={e => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type a message…"
                style={{
                  flex: 1, padding: '10px 14px', borderRadius: '22px',
                  border: '1px solid #e0d4f0', outline: 'none',
                  fontSize: '14px', backgroundColor: '#faf8ff',
                  transition: 'border-color 0.2s',
                }}
                onFocus={e => e.target.style.borderColor = '#d500f9'}
                onBlur={e  => e.target.style.borderColor = '#e0d4f0'}
              />
              <button
                onClick={handleSend}
                disabled={!inputValue.trim()}
                style={{
                  width: '38px', height: '38px', borderRadius: '50%', border: 'none',
                  backgroundColor: inputValue.trim() ? '#d500f9' : '#e0d4f0',
                  color: 'white', cursor: inputValue.trim() ? 'pointer' : 'default',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  transition: 'background-color 0.2s', flexShrink: 0,
                }}
              >
                <SendIcon />
              </button>
            </>
          ) : (
            <VoiceMicButton
              isRecording={isRecording}
              isSpeaking={isSpeaking}
              toggleRecording={toggleRecording}
              stopSpeaking={stopSpeaking}
            />
          )}

          {/* Mode toggle */}
          <button
            onClick={() => setMode(mode === 'text' ? 'voice' : 'text')}
            title={`Switch to ${mode === 'text' ? 'Voice' : 'Text'} mode`}
            style={{
              width: '38px', height: '38px', borderRadius: '50%',
              border: '1px solid #e0d4f0', background: '#faf8ff',
              color: '#888', cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0, transition: 'all 0.2s',
            }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = '#d500f9'; e.currentTarget.style.color = '#d500f9'; }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = '#e0d4f0'; e.currentTarget.style.color = '#888'; }}
          >
            {mode === 'text' ? <MicIcon size={18} /> : <KeyboardIcon size={18} />}
          </button>
        </div>
      </div>
    </>
  );
};

export default CopilotWidget;