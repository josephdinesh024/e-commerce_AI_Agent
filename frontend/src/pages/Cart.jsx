import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCart, updateCartItem, removeFromCart, getSessionId } from '../services/api';
import { useCart } from '../context/CartContext';
import toast from 'react-hot-toast'

const Cart = () => {
  const navigate = useNavigate();
  const { refreshCart } = useCart();
  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCart();
  }, []);

  const fetchCart = async () => {
    try {
      const sessionId = getSessionId();
      const response = await getCart(sessionId);
      setCart(response.data);
    } catch (error) {
      console.error('Error fetching cart:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateQuantity = async (itemId, newQuantity) => {
    try {
      const sessionId = getSessionId();
      await updateCartItem(itemId, sessionId, newQuantity);
      await fetchCart();
      refreshCart();
    } catch (error) {
      console.error('Error updating quantity:', error);
      toast('Error updating quantity');
    }
  };

  const handleRemoveItem = async (itemId) => {
    try {
      const sessionId = getSessionId();
      await removeFromCart(itemId, sessionId);
      await fetchCart();
      refreshCart();
    } catch (error) {
      console.error('Error removing item:', error);
      toast('Error removing item');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-pink-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        <h1 className="text-3xl font-bold text-gray-800 mb-8">Shopping Cart</h1>

        {!cart || cart.items.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-lg shadow">
            <p className="text-gray-500 text-xl mb-4">Your cart is empty</p>
            <button
              onClick={() => navigate('/')}
              className="bg-pink-600 text-white px-6 py-3 rounded-lg hover:bg-pink-700"
            >
              Continue Shopping
            </button>
          </div>
        ) : (
          <div className="grid lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-4">
              {cart.items.map((item) => (
                <div key={item.id} className="bg-white rounded-lg shadow p-6 flex items-center space-x-6">
                  {item.product.image_url ? (
                    <img
                      src={item.product.image_url}
                      alt={item.product.name}
                      className="w-24 h-24 object-cover rounded"
                    />
                  ) : (
                    <div className="w-24 h-24 flex items-center justify-center bg-gradient-to-br from-pink-100 to-purple-100 rounded">
                      <span className="text-4xl">👗</span>
                    </div>
                  )}

                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-800">{item.product.name}</h3>
                    <p className="text-pink-600 font-bold">${item.product.price.toFixed(2)}</p>
                  </div>

                  <div className="flex items-center space-x-4">
                    <div className="flex items-center border rounded">
                      <button
                        id={`${item.id}-decrease_quantity`}
                        onClick={() => handleUpdateQuantity(item.id, Math.max(1, item.quantity - 1))}
                        className="px-3 py-1 bg-gray-100 hover:bg-gray-200"
                      >
                        -
                      </button>
                      <span className="px-4 py-1">{item.quantity}</span>
                      <button
                        id={`${item.id}-increase_quantity`}
                        onClick={() => handleUpdateQuantity(item.id, Math.min(item.product.stock, item.quantity + 1))}
                        className="px-3 py-1 bg-gray-100 hover:bg-gray-200"
                      >
                        +
                      </button>
                    </div>

                    <button
                      id={`${item.id}-remove_item`}
                      onClick={() => handleRemoveItem(item.id)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>

                  <div className="text-right">
                    <p className="text-lg font-bold text-gray-800">
                      ${(item.product.price * item.quantity).toFixed(2)}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg shadow p-6 sticky top-4">
                <h2 className="text-xl font-bold text-gray-800 mb-4">Order Summary</h2>
                
                <div className="space-y-2 mb-6">
                  <div className="flex justify-between text-gray-600">
                    <span>Subtotal</span>
                    <span>${cart.total_amount.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-gray-600">
                    <span>Shipping</span>
                    <span>Free</span>
                  </div>
                  <div className="border-t pt-2 flex justify-between text-lg font-bold text-gray-800">
                    <span>Total</span>
                    <span>${cart.total_amount.toFixed(2)}</span>
                  </div>
                </div>

                <button
                  id='checkout-page'
                  onClick={() => navigate('/checkout')}
                  className="w-full bg-pink-600 text-white py-3 rounded-lg font-semibold hover:bg-pink-700 transition"
                >
                  Proceed to Checkout
                </button>

                <button
                  id='continue-shopping'
                  onClick={() => navigate('/')}
                  className="w-full mt-4 border border-pink-600 text-pink-600 py-3 rounded-lg font-semibold hover:bg-pink-50 transition"
                >
                  Continue Shopping
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Cart;