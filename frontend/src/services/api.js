import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Session ID management
export const getSessionId = () => {
  let sessionId = localStorage.getItem('sessionId');
  if (!sessionId) {
    sessionId = 'user_' + Math.random().toString(36).substr(2, 9) + Date.now();
    localStorage.setItem('sessionId', sessionId);
  }
  return sessionId;
};

export const updateSessionId = (newSessionId) => {
  localStorage.setItem('sessionId', newSessionId);
};

// Products
export const getProducts = (listedOnly = false) => 
  api.get(`/products/?listed_only=${listedOnly}`);

export const getProduct = (id) => 
  api.get(`/products/${id}`);

export const createProduct = (data) => 
  api.post('/products/', data);

export const updateProduct = (id, data) => 
  api.put(`/products/${id}`, data);

export const deleteProduct = (id) => 
  api.delete(`/products/${id}`);

// Reviews
export const getProductReviews = (productId) => 
  api.get(`/reviews/product/${productId}`);

export const getMyReview = (productId, sessionId) => 
  api.get(`/reviews/my-review/${productId}?session_id=${sessionId}`);

export const createReview = (data) => 
  api.post('/reviews/', data);

export const updateReview = (reviewId, sessionId, data) => 
  api.put(`/reviews/${reviewId}?session_id=${sessionId}`, data);

export const deleteReview = (reviewId, sessionId) => 
  api.delete(`/reviews/${reviewId}?session_id=${sessionId}`);

// Cart
export const getCart = (sessionId) => 
  api.get(`/cart/${sessionId}`);

export const addToCart = (data) => 
  api.post('/cart/items', data);

export const updateCartItem = (itemId, sessionId, quantity) => 
  api.put(`/cart/items/${itemId}?session_id=${sessionId}`, { quantity });

export const removeFromCart = (itemId, sessionId) => 
  api.delete(`/cart/items/${itemId}?session_id=${sessionId}`);

export const clearCart = (sessionId) => 
  api.delete(`/cart/${sessionId}`);

// Addresses
export const getAddresses = (sessionId) => 
  api.get(`/addresses/${sessionId}`);

export const createAddress = (data) => 
  api.post('/addresses/', data);

// Orders
export const getOrders = (sessionId) => 
  api.get(`/orders/${sessionId}`);

export const getOrder = (orderId) => 
  api.get(`/orders/detail/${orderId}`);

export const createOrder = (data) => 
  api.post('/orders/', data);

export const getAllOrders = () => 
  api.get('/orders/admin/all');

export const updateOrderStatus = (orderId, status) => 
  api.put(`/orders/${orderId}/status?status=${status}`);

export const loginUser = (data) => 
  api.post('/user/login', data);

export const registerUser = (data) => 
  api.post('/user/register', data);

export default api;