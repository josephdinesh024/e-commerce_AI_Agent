import { useContext } from 'react';
import CopilotContext from './CopilotContext';

/**
 * useCopilot — consume the Copilot context.
 * Must be used inside CopilotProvider.
 */
export const useCopilot = () => {
  const context = useContext(CopilotContext);
  if (context === undefined) {
    throw new Error('useCopilot must be used within a CopilotProvider');
  }
  return context;
};

export default useCopilot;
