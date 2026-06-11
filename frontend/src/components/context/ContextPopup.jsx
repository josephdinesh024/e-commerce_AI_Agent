import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const ContextPopup = ({ 
  show, 
  message, 
  type, 
  action, 
  requireConfirmation,
  onClose,
  onConfirm 
}) => {
  const navigate = useNavigate();
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (show) {
      // Trigger animation
      setTimeout(() => setIsVisible(true), 10);
    } else {
      setIsVisible(false);
    }
  }, [show]);

  if (!show) return null;

  const handleConfirm = () => {
    if (action?.type === 'navigate' && action?.target) {
      navigate(action.target);
    }
    if (onConfirm) {
      onConfirm(action);
    }
    onClose();
  };

  const handleClose = () => {
    setIsVisible(false);
    setTimeout(onClose, 300); // Wait for animation
  };

  // Icon based on type
  const Icon = () => {
    if (type === 'assist') {
      return (
        <svg className="w-6 h-6 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      );
    }
    if (type === 'warning') {
      return (
        <svg className="w-6 h-6 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      );
    }
    return (
      <svg className="w-6 h-6 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    );
  };

  return (
    <div
      className={`fixed bottom-24 right-6 z-40 transition-all duration-300 ease-in-out ${
        isVisible ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'
      }`}
      style={{ maxWidth: '320px' }}
    >
      <div className="bg-white rounded-lg shadow-2xl border border-gray-200 overflow-hidden">
        {/* Header */}
        <div className={`p-3 flex items-center space-x-3 ${
          type === 'assist' ? 'bg-blue-50' :
          type === 'warning' ? 'bg-orange-50' :
          'bg-green-50'
        }`}>
          <Icon />
          <div className="flex-1">
            <p className="text-sm font-semibold text-gray-800">AI Assistant</p>
          </div>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 transition"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-4">
          <p className="text-sm text-gray-700 leading-relaxed">
            {message}
          </p>
        </div>

        {/* Actions */}
        <div className="p-3 bg-gray-50 flex space-x-2 justify-end">
          <button
            onClick={handleClose}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 transition"
          >
            Not now
          </button>
          {requireConfirmation && (
            <button
              onClick={handleConfirm}
              className="px-4 py-2 text-sm bg-gradient-to-r from-pink-600 to-purple-600 text-white rounded-lg hover:shadow-md transition"
            >
              {action?.type === 'navigate' ? 'Take me there' : 'Yes, help me'}
            </button>
          )}
        </div>
      </div>

      {/* Pointer to AI button */}
      <div className="absolute -bottom-2 right-8 w-0 h-0 border-l-8 border-r-8 border-t-8 border-transparent border-t-white"></div>
    </div>
  );
};

export default ContextPopup;