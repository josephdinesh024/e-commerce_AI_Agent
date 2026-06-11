
export const executeActions = async (actions) => {
  for (const action of actions) {
    

    if (action.type === 'navigate') {
      let path = action.target.startsWith('/') ? action.target : action.data ? action.data : null;
        if (path)
            window.location.href = path;
        continue;
    }
    if (action.type === 'none')
        continue;

    const element = document.querySelector(action.target);
    if (!element) {
      console.warn(`Element ${action.target} not found`);
      continue;
    }

    switch (action.type) {
      case 'click':
        element.click();
        break;
      case 'enter':
        // For React inputs, you sometimes need to trigger the 'input' event
        element.value = action.data;
        element.dispatchEvent(new Event('input', { bubbles: true }));
        break;
      case 'focus':
        element.focus();
        break;
      default:
        console.log("Unknown action type");
    }

    // Optional: Add a small delay between steps
    await new Promise(resolve => setTimeout(resolve, 500));
  }
};