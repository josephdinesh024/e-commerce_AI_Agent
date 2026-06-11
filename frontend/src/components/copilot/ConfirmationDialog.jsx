import React from 'react';

const ConfirmationDialog = ({ show, action, onConfirm, onCancel }) => {
  if (!show || !action) return null;

  const renderActionDetails = () => {
    if (action.type === 'update_form' && action.data) {
      return (
        <div className="space-y-2">
          <p className="text-sm text-gray-600 mb-3">
            The AI wants to fill the form with:
          </p>
          {Object.entries(action.data).map(([key, value]) => (
            <div key={key} className="flex items-start space-x-2 bg-gray-50 p-2 rounded">
              <span className="text-sm font-medium text-gray-700 capitalize min-w-[80px]">
                {key}:
              </span>
              <span className="text-sm text-gray-900">
                {key.toLowerCase().includes('password') 
                  ? '•'.repeat(value.length)
                  : value
                }
              </span>
            </div>
          ))}
        </div>
      );
    }

    if (action.type === 'navigate' && action.target) {
      return (
        <div>
          <p className="text-sm text-gray-600 mb-2">
            Navigate to:
          </p>
          <div className="bg-gray-50 p-3 rounded">
            <code className="text-sm text-blue-600">{action.target}</code>
          </div>
        </div>
      );
    }

    return (
      <p className="text-sm text-gray-600">
        Perform action: <span className="font-medium">{action.type}</span>
      </p>
    );
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full overflow-hidden transform transition-all">
        {/* Header */}
        <div className="bg-gradient-to-r from-pink-600 to-purple-600 text-white p-4">
          <div className="flex items-center space-x-3">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="font-bold text-lg">Confirm Action</h3>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {renderActionDetails()}

          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg flex items-start space-x-2">
            <svg className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <p className="text-xs text-yellow-800">
              Review the information carefully before confirming.
              {action.type === 'update_form' && ' The form will be filled but NOT auto-submitted.'}
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="bg-gray-50 px-6 py-4 flex space-x-3 justify-end">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-pink-600 to-purple-600 rounded-lg hover:shadow-lg transition"
          >
            Confirm
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmationDialog;