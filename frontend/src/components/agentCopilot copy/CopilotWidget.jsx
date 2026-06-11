import React, { useEffect, useRef } from 'react';
import { useCopilot } from './useCopilot';

// --- Helper SVG Icons ---
const ChatIcon = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
);

const MicIcon = ({ size = 24 }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="22"></line></svg>
);

const KeyboardIcon = ({ size = 24 }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="4" width="20" height="16" rx="2" ry="2"></rect><line x1="6" y1="8" x2="6.01" y2="8"></line><line x1="10" y1="8" x2="10.01" y2="8"></line><line x1="14" y1="8" x2="14.01" y2="8"></line><line x1="18" y1="8" x2="18.01" y2="8"></line><line x1="8" y1="12" x2="16" y2="12"></line></svg>
);

// NEW: Speaker icon for when the agent is talking
const SpeakerIcon = ({ size = 24 }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>
);

const CopilotWidget = () => {
    const {
        isOpen, mode, messages, isRecording, isSpeaking, pendingActions, isWaiting, suggestions,
        toggleCopilot, setMode, sendMessage, startRecording, stopRecording, clearPendingActions, removePendingAction
    } = useCopilot();

    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        if (isOpen) {
            setTimeout(scrollToBottom, 50);
        }
    }, [messages, isOpen]);

    const handleTextSubmit = (e) => {
        if (e.key === 'Enter' && e.target.value.trim()) {
            sendMessage(e.target.value);
            e.target.value = '';
        }
    };

    // --- Dynamic Styling for the External Button ---
    let extBtnBg = 'white';
    let extBtnColor = '#d500f9';
    let extBtnIcon = <MicIcon size={20} />;
    let extBtnAnimation = 'none';

    if (isRecording) {
        extBtnBg = '#ff4757';
        extBtnColor = 'white';
        extBtnAnimation = 'pulse-record 1.5s infinite';
    } else if (isSpeaking) {
        extBtnBg = '#d500f9';
        extBtnColor = 'white';
        extBtnIcon = <SpeakerIcon size={20} />;
        extBtnAnimation = 'pulse-speak 2s infinite';
    }

    return (
        <>
            {/* Injecting CSS Keyframes for the pulse animations */}
            <style>{`
        @keyframes pulse-record {
          0% { box-shadow: 0 0 0 0 rgba(255, 71, 87, 0.7); }
          70% { box-shadow: 0 0 0 15px rgba(255, 71, 87, 0); }
          100% { box-shadow: 0 0 0 0 rgba(255, 71, 87, 0); }
        }
        @keyframes pulse-speak {
          0% { box-shadow: 0 0 0 0 rgba(213, 0, 249, 0.7); }
          70% { box-shadow: 0 0 0 15px rgba(213, 0, 249, 0); }
          100% { box-shadow: 0 0 0 0 rgba(213, 0, 249, 0); }
        }
        @keyframes bounce-dots {
          0%, 80%, 100% { transform: scale(0); }
          40% { transform: scale(1); }
        }
      `}</style>

            {/* --- CLOSED STATE --- */}
            {!isOpen && (
                <div style={{ position: 'fixed', bottom: '24px', right: '24px', display: 'flex', alignItems: 'center', gap: '12px', zIndex: 9999 }}>

                    <button
                        onClick={toggleCopilot}
                        style={{
                            width: '60px', height: '60px', borderRadius: '50%', backgroundColor: '#d500f9', color: 'white',
                            border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.15)', cursor: 'pointer', display: 'flex',
                            alignItems: 'center', justifyContent: 'center', transition: 'transform 0.2s',
                        }}
                        onMouseEnter={(e) => (e.currentTarget.style.transform = 'scale(1.05)')}
                        onMouseLeave={(e) => (e.currentTarget.style.transform = 'scale(1)')}
                    >
                        {mode === 'text' ? <ChatIcon /> : <MicIcon />}
                    </button>

                    {mode === 'voice' && (
                        <button
                            onMouseDown={startRecording}
                            onMouseUp={stopRecording}
                            onMouseLeave={stopRecording}
                            style={{
                                width: '36px', height: '36px', borderRadius: '50%',
                                backgroundColor: extBtnBg,
                                color: extBtnColor,
                                border: isRecording || isSpeaking ? 'none' : '2px solid #d500f9',
                                cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
                                transition: 'all 0.3s ease',
                                transform: isRecording || isSpeaking ? 'scale(1.1)' : 'scale(1)',
                                animation: extBtnAnimation, // <--- Applies the glowing pulse
                            }}
                            title="Hold to Speak"
                        >
                            {extBtnIcon}
                        </button>
                    )}
                </div>
            )}

            {/* --- OPEN STATE --- */}
            {isOpen && (
                <div style={{
                    position: 'fixed', bottom: '24px', right: '24px', width: '350px', height: '500px', backgroundColor: 'white',
                    borderRadius: '16px', boxShadow: '0 8px 32px rgba(0,0,0,0.15)', display: 'flex', flexDirection: 'column',
                    zIndex: 9999, overflow: 'hidden', border: '1px solid #e1e4e8', fontFamily: 'system-ui, -apple-system, sans-serif'
                }}>
                    {/* Header */}
                    <div style={{ backgroundColor: '#d500f9', color: 'white', padding: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontWeight: 'bold' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            AI Assistant {mode === 'voice' && '(Voice Mode)'}
                        </div>
                        <button onClick={toggleCopilot} style={{ background: 'transparent', border: 'none', color: 'white', cursor: 'pointer', fontSize: '16px', fontWeight: 'bold' }}>✕</button>
                    </div>

                    {/* Message Area */}
                    <div style={{ flex: 1, overflowY: 'auto', padding: '16px', backgroundColor: '#f8fbff', display: 'flex', flexDirection: 'column' }}>
                        {messages.length === 0 ? (
                            <div style={{ textAlign: 'center', margin: 'auto' }}>
                                <div style={{ color: '#888', marginBottom: '16px' }}>Hi! How can I help you today?</div>
                                {suggestions && suggestions.length > 0 && (
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', alignItems: 'center' }}>
                                        {suggestions.map((sug, idx) => (
                                            <button key={idx} onClick={() => sendMessage(sug.text || sug)} style={{
                                                backgroundColor: 'white', border: '1px solid #d500f9', color: '#d500f9', borderRadius: '16px', padding: '8px 12px', fontSize: '12px', cursor: 'pointer', transition: 'background-color 0.2s', width: '90%', textAlign: 'center'
                                            }} onMouseEnter={(e) => e.target.style.backgroundColor = '#fae1ff'} onMouseLeave={(e) => e.target.style.backgroundColor = 'white'}>
                                                {sug.text || sug}
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ) : (
                            messages.map((msg) => (
                                <div key={msg.id} style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start', marginBottom: '12px' }}>
                                    <div style={{
                                        maxWidth: '85%', padding: '10px 14px', borderRadius: '16px',
                                        borderBottomRightRadius: msg.role === 'user' ? '4px' : '16px', borderBottomLeftRadius: msg.role === 'user' ? '16px' : '4px',
                                        backgroundColor: msg.role === 'user' ? '#d500f9' : '#fff', color: msg.role === 'user' ? 'white' : '#333',
                                        boxShadow: '0 1px 2px rgba(0,0,0,0.1)', border: msg.role === 'agent' ? '1px solid #e1e4e8' : 'none', fontSize: '14px', lineHeight: '1.4'
                                    }}>
                                        {msg.content && <div>{msg.content}</div>}
                                        {msg.html_content && (
                                            <div
                                                style={{ marginTop: msg.content ? '12px' : '0', overflowX: 'auto', overflowY: 'auto' }}
                                                dangerouslySetInnerHTML={{ __html: msg.html_content }}
                                            />
                                        )}
                                    </div>
                                </div>
                            ))
                        )}
                        
                        {isWaiting && (
                            <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: '12px' }}>
                                <div style={{
                                    maxWidth: '85%', padding: '10px 14px', borderRadius: '16px', borderBottomLeftRadius: '4px',
                                    backgroundColor: '#fff', color: '#333', boxShadow: '0 1px 2px rgba(0,0,0,0.1)', border: '1px solid #e1e4e8',
                                    display: 'flex', gap: '4px', alignItems: 'center', height: '36px'
                                }}>
                                    <div style={{ width: '6px', height: '6px', backgroundColor: '#d500f9', borderRadius: '50%', animation: 'bounce-dots 1.4s infinite ease-in-out both' }}></div>
                                    <div style={{ width: '6px', height: '6px', backgroundColor: '#d500f9', borderRadius: '50%', animation: 'bounce-dots 1.4s infinite ease-in-out both', animationDelay: '-0.32s' }}></div>
                                    <div style={{ width: '6px', height: '6px', backgroundColor: '#d500f9', borderRadius: '50%', animation: 'bounce-dots 1.4s infinite ease-in-out both', animationDelay: '-0.16s' }}></div>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Pending Actions Area */}
                    {pendingActions && pendingActions.length > 0 && (
                        <div style={{ padding: '12px', background: '#fff0f2', borderTop: '1px solid #ffcdd2', borderBottom: '1px solid #ffcdd2', flexShrink: 0 }}>
                            <div style={{ fontSize: '13px', fontWeight: 'bold', color: '#d32f2f', marginBottom: '8px' }}>Action Required</div>
                            {pendingActions.map((act, idx) => (
                                <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'white', padding: '8px 12px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', marginBottom: idx < pendingActions.length - 1 ? '8px' : '0' }}>
                                    <span style={{ fontSize: '13px', color: '#d32f2f', flex: 1, marginRight: '12px', lineHeight: '1.4' }}>{act.data || `Agent needs to ${act.type} on ${act.target}`}</span>
                                    <div style={{ display: 'flex', gap: '6px' }}>
                                        <button
                                            onClick={() => {
                                                import('../../util/agentAction.js').then(({ executeActions }) => {
                                                    // override require_confirmation flag and execute securely
                                                    executeActions([{ ...act, require_confirmation: false }]);
                                                    if (removePendingAction) removePendingAction(idx);
                                                    else clearPendingActions();
                                                });
                                            }}
                                            style={{ backgroundColor: '#4caf50', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', fontSize: '12px', fontWeight: 'bold', minWidth: '70px' }}>
                                            Confirm
                                        </button>
                                        <button
                                            onClick={() => {
                                                if (removePendingAction) removePendingAction(idx);
                                                else clearPendingActions();
                                            }}
                                            style={{ backgroundColor: '#f44336', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', fontSize: '12px', fontWeight: 'bold', minWidth: '70px' }}>
                                            Decline
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Input Area */}
                    <div style={{ padding: '12px', borderTop: '1px solid #e1e4e8', backgroundColor: 'white', display: 'flex', gap: '8px', alignItems: 'center' }}>
                        {mode === 'text' ? (
                            <input
                                type="text" placeholder="Type a message..." onKeyDown={handleTextSubmit}
                                style={{ flex: 1, padding: '12px 16px', borderRadius: '24px', border: '1px solid #ced4da', outline: 'none' }}
                            />
                        ) : (
                            <button
                                onMouseDown={startRecording} onMouseUp={stopRecording} onMouseLeave={stopRecording}
                                style={{
                                    flex: 1, padding: '12px', borderRadius: '24px', border: 'none',
                                    background: isRecording ? '#ff4757' : (isSpeaking ? '#d500f9' : '#d500f9'), color: 'white',
                                    cursor: 'pointer', fontWeight: 'bold', transition: 'all 0.3s',
                                    animation: isRecording ? 'pulse-record 1.5s infinite' : (isSpeaking ? 'pulse-speak 2s infinite' : 'none')
                                }}
                            >
                                {isRecording ? 'Listening...' : (isSpeaking ? 'Agent Speaking...' : 'Hold to Speak')}
                            </button>
                        )}

                        {/* Inline Mode Changer */}
                        <button
                            onClick={() => setMode(mode === 'text' ? 'voice' : 'text')}
                            style={{ width: '44px', height: '44px', borderRadius: '50%', border: '1px solid #e1e4e8', background: '#f8fbff', color: '#555', cursor: 'pointer', display: 'flex', justifyContent: 'center', alignItems: 'center', flexShrink: 0 }}
                            title={`Switch to ${mode === 'text' ? 'Voice' : 'Text'}`}
                        >
                            {mode === 'text' ? <MicIcon size={20} /> : <KeyboardIcon size={20} />}
                        </button>
                    </div>
                </div>
            )}
        </>
    );
};

export default CopilotWidget;