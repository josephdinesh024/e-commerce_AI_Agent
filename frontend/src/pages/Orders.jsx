import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getOrders, getSessionId } from '../services/api';

const Orders = () => {
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      const sessionId = getSessionId();
      const response = await getOrders(sessionId);
      setOrders(response.data);
    } catch (error) {
      console.error('Error fetching orders:', error);
    } finally {
      setLoading(false);
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
        <h1 className="text-3xl font-bold text-gray-800 mb-8">My Orders</h1>

        {orders.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-lg shadow">
            <p className="text-gray-500 text-xl mb-4">You haven't placed any orders yet</p>
            <button
              onClick={() => navigate('/')}
              className="bg-pink-600 text-white px-6 py-3 rounded-lg hover:bg-pink-700"
            >
              Start Shopping
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            {orders.map((order) => (
              <div key={order.id} className="bg-white rounded-lg shadow p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-800">
                      Order #{order.id}
                    </h3>
                    <p className="text-sm text-gray-600">
                      Placed on {new Date(order.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-pink-600">
                      ${order.total_amount.toFixed(2)}
                    </p>
                    <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${
                      order.status === 'Confirmed' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {order.status}
                    </span>
                  </div>
                </div>

                <div className="border-t pt-4 mb-4">
                  <h4 className="font-semibold mb-2">Shipping Address:</h4>
                  <p className="text-gray-600">{order.address.name}</p>
                  <p className="text-gray-600">{order.address.phone}</p>
                  <p className="text-gray-600">{order.address.address}</p>
                  <p className="text-gray-600">
                    {order.address.city}, {order.address.state} - {order.address.pincode}
                  </p>
                </div>

                <div className="border-t pt-4">
                  <h4 className="font-semibold mb-3">Items:</h4>
                  <div className="space-y-3">
                    {order.items.map((item) => (
                      <div key={item.id} className="flex items-center space-x-4">
                        {item.product.image_url ? (
                          <img
                            src={item.product.image_url}
                            alt={item.product.name}
                            className="w-16 h-16 object-cover rounded"
                          />
                        ) : (
                          <div className="w-16 h-16 flex items-center justify-center bg-gradient-to-br from-pink-100 to-purple-100 rounded">
                            <span className="text-2xl">👗</span>
                          </div>
                        )}
                        <div className="flex-1">
                          <p className="font-semibold">{item.product.name}</p>
                          <p className="text-gray-600">
                            Quantity: {item.quantity} × ${item.price.toFixed(2)}
                          </p>
                        </div>
                        <p className="font-bold text-gray-800">
                          ${(item.price * item.quantity).toFixed(2)}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Orders;