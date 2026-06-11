// Page Context Builder - Dynamically extracts page structure
// This runs in the browser and builds a JSON representation of the current page

export const buildPageContext = () => {
  const context = {
    page: {
      title: document.title,
      url: window.location.href,
      pathname: window.location.pathname,
      type: getPageType(window.location.pathname)
    },
    forms: extractForms(),
    buttons: extractButtons(),
    links: extractLinks(),
    inputs: extractInputs(),
    products: extractProducts(),
    cart: extractCartInfo(),
    user: extractUserInfo()
  };

  return context;
};

// Determine page type
const getPageType = (pathname) => {
  if (pathname === '/') return 'home';
  if (pathname.startsWith('/product/')) return 'product';
  if (pathname === '/cart') return 'cart';
  if (pathname === '/checkout') return 'checkout';
  if (pathname === '/orders') return 'orders';
  if (pathname === '/login') return 'login';
  if (pathname === '/register') return 'register';
  return 'other';
};

// Extract all forms on the page
const extractForms = () => {
  const forms = [];
  document.querySelectorAll('form').forEach((form, index) => {
    const formData = {
      id: form.id || `form-${index}`,
      name: form.name || '',
      action: form.action || '',
      method: form.method || 'GET',
      selector: getUniqueSelector(form),
      fields: []
    };

    // Extract form fields
    form.querySelectorAll('input, textarea, select').forEach(field => {
      if (field.type !== 'hidden' && field.type !== 'submit') {
        formData.fields.push({
          name: field.name || field.id || '',
          type: field.type || field.tagName.toLowerCase(),
          label: getFieldLabel(field),
          placeholder: field.placeholder || '',
          required: field.required,
          value: field.value || getReactValue(field) || '',
          selector: getUniqueSelector(field)
        });
      }
    });

    // Extract submit buttons
    form.querySelectorAll('button[type="submit"], input[type="submit"]').forEach(btn => {
      formData.submitButton = {
        text: btn.textContent?.trim() || btn.value || 'Submit',
        selector: getUniqueSelector(btn)
      };
    });

    forms.push(formData);
  });

  return forms;
};

// Extract all buttons (not in forms)
const extractButtons = () => {
  const buttons = [];
  document.querySelectorAll('button:not([type="submit"])').forEach(btn => {
    // Skip if inside a form (already captured)
    if (btn.closest('form')) return;

    buttons.push({
      text: btn.textContent?.trim() || '',
      type: btn.type || 'button',
      class: btn.className || '',
      selector: getUniqueSelector(btn),
      action: inferButtonAction(btn)
    });
  });

  return buttons.slice(0, 20); // Limit to first 20 buttons
};

// Extract important links
const extractLinks = () => {
  const links = [];
  document.querySelectorAll('a[href]').forEach(link => {
    const href = link.getAttribute('href');
    if (href && !href.startsWith('#')) {
      links.push({
        text: link.textContent?.trim() || '',
        href: href,
        selector: getUniqueSelector(link)
      });
    }
  });

  return links.slice(0, 30); // Limit to first 30 links
};

// Extract all visible inputs
const extractInputs = () => {
  const inputs = [];
  document.querySelectorAll('input:not([type="hidden"])').forEach(input => {
    // Skip if inside a form (already captured)
    if (input.closest('form')) return;

    inputs.push({
      name: input.name || input.id || '',
      type: input.type || 'text',
      placeholder: input.placeholder || '',
      value: input.value || '',
      selector: getUniqueSelector(input)
    });
  });

  return inputs;
};

// Extract product information (for product pages)
const extractProducts = () => {
  const products = [];
  
  // Try to find product elements by common selectors
  const productSelectors = [
    '[data-product-id]',
    '.product',
    '.product-card',
    '[itemtype*="Product"]'
  ];

  productSelectors.forEach(selector => {
    document.querySelectorAll(selector).forEach(product => {
      const productData = {
        id: product.getAttribute('data-product-id') || '',
        name: product.querySelector('h1, h2, h3, .product-name')?.textContent?.trim() || '',
        price: product.querySelector('.price, [data-price]')?.textContent?.trim() || '',
        image: product.querySelector('img')?.src || '',
        selector: getUniqueSelector(product)
      };

      // Find add to cart button
      const addToCartBtn = product.querySelector('[data-action="add-to-cart"], .add-to-cart, button[name*="cart"]');
      if (addToCartBtn) {
        productData.addToCartButton = getUniqueSelector(addToCartBtn);
      }

      if (productData.name || productData.id) {
        products.push(productData);
      }
    });
  });

  return products.slice(0, 10); // Limit to first 10 products
};

// Extract cart information
const extractCartInfo = () => {
  const cartInfo = {
    items: [],
    total: '',
    checkoutButton: null
  };

  // Try to find cart items
  document.querySelectorAll('[data-cart-item], .cart-item').forEach(item => {
    cartInfo.items.push({
      name: item.querySelector('.item-name, .product-name')?.textContent?.trim() || '',
      price: item.querySelector('.price')?.textContent?.trim() || '',
      quantity: item.querySelector('.quantity, input[type="number"]')?.value || '1'
    });
  });

  // Find total
  const totalElement = document.querySelector('[data-cart-total], .cart-total, .total-price');
  if (totalElement) {
    cartInfo.total = totalElement.textContent?.trim() || '';
  }

  // Find checkout button
  const checkoutBtn = document.querySelector('[data-action="checkout"], .checkout-button, button[name*="checkout"]');
  if (checkoutBtn) {
    cartInfo.checkoutButton = getUniqueSelector(checkoutBtn);
  }

  return cartInfo;
};

// Extract user information (if visible on page)
const extractUserInfo = () => {
  const userInfo = {
    isLoggedIn: false,
    name: '',
    email: ''
  };

  // Check if user is logged in (look for logout button or user menu)
  const logoutBtn = document.querySelector('[data-action="logout"], .logout, button[name*="logout"]');
  const userMenu = document.querySelector('.user-menu, [data-user-menu]');
  
  userInfo.isLoggedIn = !!(logoutBtn || userMenu);

  // Try to find user name
  const userName = document.querySelector('[data-user-name], .user-name');
  if (userName) {
    userInfo.name = userName.textContent?.trim() || '';
  }

  return userInfo;
};

// Get field label
const getFieldLabel = (field) => {
  // Try to find associated label
  if (field.id) {
    const label = document.querySelector(`label[for="${field.id}"]`);
    if (label) return label.textContent?.trim() || '';
  }

  // Try to find label by proximity
  const parent = field.closest('div, fieldset');
  if (parent) {
    const label = parent.querySelector('label');
    if (label) return label.textContent?.trim() || '';
  }

  return field.placeholder || field.name || '';
};

// Infer button action from context
const inferButtonAction = (button) => {
  const text = button.textContent?.toLowerCase() || '';
  const classes = button.className.toLowerCase();
  
  if (text.includes('add to cart') || classes.includes('add-to-cart')) return 'add_to_cart';
  if (text.includes('buy now') || text.includes('purchase')) return 'buy_now';
  if (text.includes('checkout')) return 'checkout';
  if (text.includes('login') || text.includes('sign in')) return 'login';
  if (text.includes('register') || text.includes('sign up')) return 'register';
  if (text.includes('search')) return 'search';
  
  return 'unknown';
};

// Generate unique CSS selector for an element
const getUniqueSelector = (element) => {
  if (!element) return '';
  
  // Prefer ID
  if (element.id) {
    return `#${element.id}`;
  }

  // Try data attributes
  if (element.dataset && Object.keys(element.dataset).length > 0) {
    const firstDataAttr = Object.keys(element.dataset)[0];
    return `[data-${firstDataAttr}="${element.dataset[firstDataAttr]}"]`;
  }

  // Build path
  const path = [];
  let current = element;

  while (current && current !== document.body) {
    let selector = current.tagName.toLowerCase();
    
    if (current.className && typeof current.className === 'string') {
      const classes = current.className.trim().split(/\s+/).slice(0, 2); // First 2 classes
      if (classes.length > 0) {
        selector += '.' + classes.join('.');
      }
    }

    // Add nth-child if necessary
    const parent = current.parentElement;
    if (parent) {
      const siblings = Array.from(parent.children);
      const index = siblings.indexOf(current);
      if (siblings.filter(s => s.tagName === current.tagName).length > 1) {
        selector += `:nth-child(${index + 1})`;
      }
    }

    path.unshift(selector);
    current = parent;
  }

  return path.join(' > ');
};

// Helper to read React state values
const getReactValue = (element) => {
  // React 18+ - check for _valueTracker or React props
  if (element._valueTracker?.getValue()) {
    return element._valueTracker.getValue();
  }
  
  // Fallback: trigger input to sync
  element.dispatchEvent(new Event('input', { bubbles: true }));
  return element.value;
};

// Export for use
export default buildPageContext;