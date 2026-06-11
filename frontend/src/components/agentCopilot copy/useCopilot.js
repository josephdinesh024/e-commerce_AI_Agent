import { useContext } from 'react';
import CopilotContext from './CopilotContext';

/**
 * useCopilot - Custom hook to consume the Copilot context.
 * Throws an error if used outside of a CopilotProvider.
 */
export const useCopilot = () => {
  const context = useContext(CopilotContext);

  if (context === undefined) {
    throw new Error('useCopilot must be used within a CopilotProvider');
  }

  return context;
};

export default useCopilot;
