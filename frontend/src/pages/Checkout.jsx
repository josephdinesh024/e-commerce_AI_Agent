import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCart, getAddresses, createAddress, createOrder, getSessionId } from '../services/api';
import { useCart } from '../context/CartContext';
import toast from 'react-hot-toast'

const Checkout = () => {
  const navigate = useNavigate();
  const { refreshCart } = useCart();
  const [cart, setCart] = useState(null);
  const [addresses, setAddresses] = useState([]);
  const [selectedAddressId, setSelectedAddressId] = useState(null);
  const [showAddressForm, setShowAddressForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [addressData, setAddressData] = useState({
    name: '',
    phone: '',
    address: '',
    city: '',
    state: '',
    pincode: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const sessionId = getSessionId();
      const [cartRes, addressesRes] = await Promise.all([
        getCart(sessionId),
        getAddresses(sessionId)
      ]);
      
      setCart(cartRes.data);
      setAddresses(addressesRes.data);
      
      if (addressesRes.data.length > 0) {
        setSelectedAddressId(addressesRes.data[0].id);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddAddress = async (e) => {
    e.preventDefault();
    let forms = new FormData(e.target);
    forms.forEach((v,k)=>{
      if(k in addressData && addressData[k] != ""){
        addressData[k] = v;
      }
    });
    
    try {
      const sessionId = getSessionId();
      await createAddress({ ...addressData, session_id: sessionId });
      await fetchData();
      setShowAddressForm(false);
      setAddressData({ name: '', phone: '', address: '', city: '', state: '', pincode: '' });
      toast('Address added successfully!');
    } catch (error) {
      console.error('Error adding address:', error);
      toast('Error adding address');
    }
  };

  const handlePlaceOrder = async () => {
    if (!selectedAddressId) {
      toast('Please select a shipping address');
      return;
    }

    setSubmitting(true);
    try {
      const sessionId = getSessionId();
      const response = await createOrder({
        session_id: sessionId,
        address_id: selectedAddressId
      });
      
      refreshCart();
      toast('Order placed successfully!');
      navigate(`/order-confirmation/${response.data.id}`);
    } catch (error) {
      console.error('Error placing order:', error);
      toast(error.response?.data?.detail || 'Error placing order');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-pink-600"></div>
      </div>
    );
  }

  if (!cart || cart.items.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="container mx-auto px-4 text-center">
          <p className="text-xl text-gray-600 mb-4">Your cart is empty</p>
          <button
            onClick={() => navigate('/')}
            className="bg-pink-600 text-white px-6 py-3 rounded-lg hover:bg-pink-700"
          >
            Continue Shopping
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        <h1 className="text-3xl font-bold text-gray-800 mb-8">Checkout</h1>

        <div className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-8">
            {/* Shipping Address */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold text-gray-800">Shipping Address</h2>
                <button
                  id='show-address-form'
                  onClick={() => setShowAddressForm(!showAddressForm)}
                  className="bg-pink-600 text-white px-4 py-2 rounded-lg hover:bg-pink-700"
                >
                  {showAddressForm ? 'Cancel' : 'Add New Address'}
                </button>
              </div>

              {showAddressForm && (
                <form id='new-address-form' onSubmit={handleAddAddress} className="mb-6 p-4 bg-gray-50 rounded-lg">
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-semibold mb-2">Full Name</label>
                      <input
                        id='full-name'
                        type="text"
                        name='name'
                        required
                        value={addressData.name}
                        onChange={(e) => setAddressData({ ...addressData, name: e.target.value })}
                        className="w-full border rounded-lg px-3 py-2"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold mb-2">Phone</label>
                      <input
                        id='phone-number'
                        type="tel"
                        name='phone'
                        required
                        value={addressData.phone}
                        onChange={(e) => setAddressData({ ...addressData, phone: e.target.value })}
                        className="w-full border rounded-lg px-3 py-2"
                      />
                    </div>
                  </div>

                  <div className="mt-4">
                    <label className="block text-sm font-semibold mb-2">Address</label>
                    <textarea
                      required
                      id='full-address'
                      name='address'
                      value={addressData.address}
                      onChange={(e) => setAddressData({ ...addressData, address: e.target.value })}
                      className="w-full border rounded-lg px-3 py-2"
                      rows="3"
                    />
                  </div>

                  <div className="grid md:grid-cols-3 gap-4 mt-4">
                    <div>
                      <label className="block text-sm font-semibold mb-2">City</label>
                      <input
                        id='city'
                        type="text"
                        name='city'
                        required
                        value={addressData.city}
                        onChange={(e) => setAddressData({ ...addressData, city: e.target.value })}
                        className="w-full border rounded-lg px-3 py-2"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold mb-2">State</label>
                      <input
                        id='state'
                        type="text"
                        name='state'
                        required
                        value={addressData.state}
                        onChange={(e) => setAddressData({ ...addressData, state: e.target.value })}
                        className="w-full border rounded-lg px-3 py-2"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold mb-2">Pincode</label>
                      <input
                        type="text"
                        id='pincode'
                        name='pincode'
                        required
                        value={addressData.pincode}
                        onChange={(e) => setAddressData({ ...addressData, pincode: e.target.value })}
                        className="w-full border rounded-lg px-3 py-2"
                      />
                    </div>
                  </div>

                  <button
                    id='submit-address-form'
                    type="submit"
                    className="mt-4 bg-pink-600 text-white px-6 py-2 rounded-lg hover:bg-pink-700"
                  >
                    Save Address
                  </button>
                </form>
              )}

              {addresses.length === 0 ? (
                <p className="text-gray-500">No saved addresses. Please add one.</p>
              ) : (
                <div className="space-y-4">
                  {addresses.map((addr,ixd) => (
                    <div
                      key={addr.id}
                      className={`p-4 border rounded-lg cursor-pointer transition ${
                        selectedAddressId === addr.id
                          ? 'border-pink-600 bg-pink-50'
                          : 'border-gray-300 hover:border-pink-400'
                      }`}
                      onClick={() => setSelectedAddressId(addr.id)}
                    >
                      <div className="flex items-start">
                        <input
                          id={`address-line-${ixd+1}`}
                          type="radio"
                          checked={selectedAddressId === addr.id}
                          onChange={() => setSelectedAddressId(addr.id)}
                          className="mt-1 mr-3"
                        />
                        <div>
                          <p className="font-semibold">{addr.name}</p>
                          <p className="text-gray-600">{addr.phone}</p>
                          <p className="text-gray-600">{addr.address}</p>
                          <p className="text-gray-600">
                            {addr.city}, {addr.state} - {addr.pincode}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Order Items */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-4">Order Items</h2>
              <div className="space-y-4">
                {cart.items.map((item) => (
                  <div key={item.id} className="flex items-center space-x-4 pb-4 border-b">
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
                      <p className="text-gray-600">Quantity: {item.quantity}</p>
                    </div>
                    <p className="font-bold text-pink-600">
                      ${(item.product.price * item.quantity).toFixed(2)}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Order Summary */}
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
                onClick={handlePlaceOrder}
                id='place-order'
                disabled={!selectedAddressId || submitting}
                className="w-full bg-pink-600 text-white py-3 rounded-lg font-semibold hover:bg-pink-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {submitting ? 'Placing Order...' : 'Place Order'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Checkout;