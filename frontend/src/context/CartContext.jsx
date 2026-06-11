import React, { createContext, useContext, useState, useEffect } from 'react';
import { getCart, getSessionId } from '../services/api';

const CartContext = createContext();

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within CartProvider');
  }
  return context;
};

export const CartProvider = ({ children }) => {
  const [cart, setCart] = useState(null);
  const [cartCount, setCartCount] = useState(0);
  const [loading, setLoading] = useState(true);

  const fetchCart = async () => {
    try {
      const sessionId = getSessionId();
      const response = await getCart(sessionId);
      setCart(response.data);
      const count = response.data.items.reduce((sum, item) => sum + item.quantity, 0);
      setCartCount(count);
    } catch (error) {
      console.error('Error fetching cart:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCart();
  }, []);

  const refreshCart = () => {
    fetchCart();
  };

  return (
    <CartContext.Provider value={{ cart, cartCount, loading, refreshCart }}>
      {children}
    </CartContext.Provider>
  );
};