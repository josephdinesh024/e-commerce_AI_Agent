import { toast } from 'react-hot-toast';
import { confirmActionToast } from '../components/toasts';

export const executeActions = async (actions) => {

  for (let i = 0; i < actions.length; i++) {
    const action = actions[i];

    // Skip none actions
    if (action.type === 'none') continue;

    // Navigate
    if (action.type === 'navigate') {
      const path = action.target.startsWith('/') ? action.target : action.data || '/';
      window.location.href = path;
      return; // Navigation stops execution
    }

    // Find element with multiple strategies
    const element = await findElementWithRetry(action.target, 2000);
    if (!element) {
      toast.error(`Element not found: ${action.target}`);
      continue;
    }

    try {
      switch (action.type) {
        case 'click':
          action.require_confirmation ? confirmActionToast("Need confirmation to " + action.data, () => safeClick(element), "Confirm") : await safeClick(element);
          break;

        case 'focus':
          element.focus();
          element.scrollIntoView({ behavior: 'smooth', block: 'center' });
          break;

        case 'enter':
          action.require_confirmation ? confirmActionToast("Need confirmation to " + action.data, () => safeInput(element, action.data), "Confirm") : await safeInput(element, action.data);
          break;

        case 'scroll':
          element.scrollIntoView({ behavior: 'smooth' });
          break;

        default:
          console.warn(`⚠️ Unknown action type: ${action.type}`);
      }

      // Small delay between actions
      if (i < actions.length - 1) {
        await new Promise(r => setTimeout(r, 300));
      }

    } catch (error) {
      toast.error(`Action failed: ${action.type}`);
    }
  }

  // toast.success('✅ All actions completed!');
};

// 🔧 ROBUST ELEMENT FINDER - Handles React SPA
const findElementWithRetry = (selector, timeout = 3000) => {
  return new Promise((resolve) => {
    let attempts = 0;
    const maxAttempts = 20;

    const tryFind = () => {
      // Use attribute selector [id=""] instead of # for number-prefixed IDs
      if (selector.startsWith('#')) {
        const idValue = selector.substring(1); // Remove the '#'
        const el = document.querySelector(`[id="${idValue}"]`);
        if (el) return resolve(el);
      }

      // Strategy 2: CSS selector
      try {
        const el = document.querySelector(selector);
        if (el) return resolve(el);
      } catch (e) {
        console.warn("Invalid selector strategy 2:", selector);
      }

      // Strategy 3: Text content match (for buttons)
      if (!selector.startsWith('#') && !selector.includes('.')) {
        const allButtons = document.querySelectorAll('button, input[type="submit"]');
        for (const btn of allButtons) {
          if (btn.textContent?.toLowerCase().includes(selector.toLowerCase())) {
            return resolve(btn);
          }
        }
      }

      attempts++;
      if (attempts < maxAttempts) {
        setTimeout(tryFind, 150); // Retry faster
      } else {
        resolve(null);
      }
    };

    tryFind();
  });
};

// 🛡️ SAFE CLICK - Handles disabled/sticky elements
const safeClick = async (element) => {
  // Scroll into view first
  element.scrollIntoView({ behavior: 'smooth', block: 'center' });
  await new Promise(r => setTimeout(r, 200));

  // Remove disabled temporarily for React
  const wasDisabled = element.disabled;
  element.disabled = false;

  // Try multiple click methods
  try {
    // Method 1: Native click
    element.click();
      // Dispatch 'input' so React updates its state
  element.dispatchEvent(new Event('click', { bubbles: true }));
  } catch {
    try {
      // Method 2: Dispatch click event
      element.dispatchEvent(new MouseEvent('click', {
        bubbles: true,
        cancelable: true,
        view: window
      }));
    } catch {
      // Method 3: Force click via protocol
      element.click();
    }
  }

  // Restore disabled state
  if (wasDisabled) element.disabled = true;

};

// 📝 REACT-SAFE INPUT - Dispatches ALL React events
const safeInput = async (element, value) => {
  // Scroll to element
  element.scrollIntoView({ behavior: 'smooth', block: 'center' });
  await new Promise(r => setTimeout(r, 200));

  // Focus first
  element.focus();

  // 🚀 CRITICAL: React 16+ overrides the value setter on the DOM element instance.
  // To correctly trigger React's internal state mechanism, we must call the native HTML element
  // prototype setter directly, and then dispatch the input event so React catches the diff.
  const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
    window.HTMLInputElement.prototype,
    'value'
  )?.set;
  const nativeTextAreaValueSetter = Object.getOwnPropertyDescriptor(
    window.HTMLTextAreaElement.prototype,
    'value'
  )?.set;

  const setter = element.tagName === 'TEXTAREA' ? nativeTextAreaValueSetter : nativeInputValueSetter;

  if (setter) {
    setter.call(element, value);
  } else {
    element.value = value;
  }

  // Dispatch standard input and change events which React explicitly listens to
  element.dispatchEvent(new Event('input', { bubbles: true }));
  element.dispatchEvent(new Event('change', { bubbles: true }));
  element.dispatchEvent(new Event('blur', { bubbles: true }));
};

// 🎯 CUSTOM DISPATCH FOR FORMS
export const dispatchCopilotFill = (data) => {
  // For agent to fill forms via copilot event
  window.dispatchEvent(new CustomEvent('copilot-fill-form', {
    detail: data
  }));
};

// 📡 MONITOR FORM CHANGES (for debugging)
export const monitorFormChanges = () => {
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.type === 'attributes' && mutation.attributeName === 'value') {
        console.log('Form value changed:', mutation.target);
      }
    });
  });

  document.querySelectorAll('input, textarea, select').forEach(el => {
    observer.observe(el, { attributes: true, attributeFilter: ['value'] });
  });
};
