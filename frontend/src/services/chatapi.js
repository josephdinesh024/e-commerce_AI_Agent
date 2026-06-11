import { getSessionId } from './api';

const CHAT_API_URL = '/api';
const API_BASE_URL = 'http://localhost:8000';

// Determine page type from route
export const getPageType = (pathname) => {
  if (pathname === '/') return 'home';
  if (pathname.startsWith('/product/')) return 'product';
  if (pathname === '/cart') return 'cart';
  if (pathname === '/checkout') return 'checkout';
  if (pathname === '/orders') return 'orders';
  if (pathname === '/login') return 'login';
  if (pathname === '/register') return 'register';
  return 'home';
};

export const sendChatMessage = async (message, conversationHistory = [], mode = 'text') => {
  const sessionId = getSessionId();
  const currentPage = window.location.pathname;


  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      session_id: sessionId,
      mode: mode,  // NEW: pass mode
      conversation_history: conversationHistory.map(msg => ({
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp || new Date().toISOString()
      })),
      page_type: getPageType(currentPage),
      route: currentPage
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to send message');
  }

  return response.body;
};

export const sendChatAnalyze = async (message, mode = 'text') => {
  const sessionId = getSessionId();
  const currentPage = window.location.pathname;


  const response = await fetch(`${API_BASE_URL}/chat/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      session_id: sessionId,
      mode: mode,
      page_type: getPageType(currentPage),
      route: currentPage
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to send message');
  }

  return response.json();
};

export const getSessionHistory = async () => {
  const sessionId = getSessionId();
  const response = await fetch(`${API_BASE_URL}/chat/session/${sessionId}/history`);
  if (!response.ok) {
    throw new Error('Failed to get session history');
  }
  return response.json();
};

export const getSuggestions = async () => {
  const response = await fetch(`${API_BASE_URL}/chat/suggestions`);
  if (!response.ok) {
    throw new Error('Failed to get suggestions');
  }
  return response.json();
};

export const sendPageContext = async (context) => {
  const sessionId = getSessionId();
  try {
    const response = await fetch(`${API_BASE_URL}/chat/context`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        context: context
      })
    });

    if (!response.ok) {
      throw new Error('Failed to send page context');
    }

    return response.json();
  } catch (error) {
    console.error('Error sending page context:', error);
  }

};

// Parse Server-Sent Events stream
export const parseSSEStream = async (stream, onChunk, onComplete, onError) => {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');

      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));

            if (data.type === 'error') {
              onError(data.content);
              return;
            }

            if (data.type === 'stream' || data.type === 'done') {
              onChunk(data.content, data.done);

              if (data.done) {
                onComplete(data.content);
                return;
              }
            }
          } catch (e) {
            console.error('Error parsing SSE:', e);
          }
        }
      }
    }
  } catch (error) {
    onError(error.message);
  }
};