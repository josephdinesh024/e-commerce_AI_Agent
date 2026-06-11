import React, { useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { CartProvider, useCart } from './context/CartContext';
import Navbar from './components/Navbar';
import { CopilotProvider } from './components/agentCopilot/CopilotContext';
import CopilotWidget from './components/agentCopilot/CopilotWidget';
import Home from './pages/Home';
import ProductDetail from './pages/ProductDetail';
import Cart from './pages/Cart';
import Checkout from './pages/Checkout';
import Orders from './pages/Orders';
import Admin from './pages/Admin';
import Login from './pages/Login';
import Register from './pages/Register';
import { Toaster } from 'react-hot-toast';

/**
 * Inner component — has access to CartContext so it can pass refreshCart
 * to CopilotProvider as the onCartRefresh callback.
 *
 * When the agent calls add_to_cart_tool / update_cart_item_tool / remove_from_cart_tool
 * it returns { "type": "cart_refresh" } in the action array.
 * CopilotContext calls onCartRefresh() → CartContext.refreshCart() re-fetches cart count.
 */
function AppInner() {
  const { refreshCart } = useCart();   // expose this from your CartContext

  return (
    <CopilotProvider
      config={{ position: 'bottom-right' }}
      apiConfig={{
        endpoint: 'http://localhost:8000/chat/agent',
        headers: { 'Content-Type': 'application/json' },
      }}
      onCartRefresh={refreshCart}   // ← wires cart_refresh action to CartContext
    >
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <Routes>
          <Route path="/"             element={<Home />} />
          <Route path="/product/:id"  element={<ProductDetail />} />
          <Route path="/cart"         element={<Cart />} />
          <Route path="/checkout"     element={<Checkout />} />
          <Route path="/orders"       element={<Orders />} />
          <Route path="/admin"        element={<Admin />} />
          <Route path="/login"        element={<Login />} />
          <Route path="/register"     element={<Register />} />
        </Routes>
        <CopilotWidget />
      </div>
    </CopilotProvider>
  );
}

function App() {
  return (
    <Router>
      <CartProvider>
        <Toaster
          position="bottom-right"
          reverseOrder={false}
          containerStyle={{ zIndex: 99999 }}
        />
        <AppInner />
      </CartProvider>
    </Router>
  );
}

export default App;

/**
 * CartContext — add this method if not already present:
 *
 * const refreshCart = useCallback(async () => {
 *   const data = await fetchCart(sessionId);   // your existing cart API call
 *   setCart(data);
 * }, [sessionId]);
 *
 * // Also listen for the custom event as a fallback (if prop wiring isn't possible):
 * useEffect(() => {
 *   const handler = () => refreshCart();
 *   window.addEventListener('agent:cart_refresh', handler);
 *   return () => window.removeEventListener('agent:cart_refresh', handler);
 * }, [refreshCart]);
 */