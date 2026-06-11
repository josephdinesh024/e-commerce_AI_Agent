import { useState, useEffect, useCallback } from 'react';
// import { useLocation } from 'react-router-dom';

const API_BASE_URL = 'http://localhost:8000';

export const useContextAgent = () => {
  // const location = useLocation();
  const [popupData, setPopupData] = useState(null);
  const [idleTime, setIdleTime] = useState(0);
  const [lastActivity, setLastActivity] = useState(Date.now());

  // Determine page type from route
  const getPageType = (pathname) => {
    if (pathname === '/') return 'home';
    if (pathname.startsWith('/product/')) return 'product';
    if (pathname === '/cart') return 'cart';
    if (pathname === '/checkout') return 'checkout';
    if (pathname === '/orders') return 'orders';
    if (pathname === '/login') return 'login';
    return 'home';
  };

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
      // Show popup if suggested
      if (data.show_popup && data.confidence >= 0.6) {
        setPopupData(data);
      }

    } catch (error) {
      console.error('Context agent error:', error);
    }
  }, [window.location.pathname, idleTime]);

  // Auto-analyze on idle time changes
  useEffect(() => {
    // Only analyze at specific idle thresholds to avoid spam
    if ([8, 12, 20, 30].includes(idleTime)) {
      analyzeContext();
    }
  }, [idleTime, analyzeContext]);

  // Close popup
  const closePopup = () => {
    setPopupData(null);
  };

  return {
    popupData,
    analyzeContext,
    closePopup,
    idleTime
  };
};