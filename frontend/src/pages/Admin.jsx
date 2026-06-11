import React, { useEffect, useState } from 'react';
import { getProducts, createProduct, updateProduct, deleteProduct } from '../services/api';
import toast from 'react-hot-toast'
const Admin = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: '',
    stock: '',
    image_url: '',
    is_listed: true
  });

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await getProducts(false); // Get all products
      setProducts(response.data);
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = {
        ...formData,
        price: parseFloat(formData.price),
        stock: parseInt(formData.stock)
      };

      if (editingProduct) {
        await updateProduct(editingProduct.id, data);
        toast('Product updated successfully!');
      } else {
        await createProduct(data);
        toast('Product created successfully!');
      }

      setShowForm(false);
      setEditingProduct(null);
      setFormData({ name: '', description: '', price: '', stock: '', image_url: '', is_listed: true });
      fetchProducts();
    } catch (error) {
      console.error('Error saving product:', error);
      toast('Error saving product');
    }
  };

  const handleEdit = (product) => {
    setEditingProduct(product);
    setFormData({
      name: product.name,
      description: product.description || '',
      price: product.price.toString(),
      stock: product.stock.toString(),
      image_url: product.image_url || '',
      is_listed: product.is_listed
    });
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this product?')) return;
    
    try {
      await deleteProduct(id);
      toast('Product deleted successfully!');
      fetchProducts();
    } catch (error) {
      console.error('Error deleting product:', error);
      toast('Error deleting product');
    }
  };

  const handleToggleListed = async (product) => {
    try {
      await updateProduct(product.id, { is_listed: !product.is_listed });
      fetchProducts();
    } catch (error) {
      console.error('Error toggling product:', error);
      toast('Error updating product');
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
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800">Product Management</h1>
          <button
            onClick={() => {
              setShowForm(!showForm);
              setEditingProduct(null);
              setFormData({ name: '', description: '', price: '', stock: '', image_url: '', is_listed: true });
            }}
            className="bg-pink-600 text-white px-6 py-3 rounded-lg hover:bg-pink-700 font-semibold"
          >
            {showForm ? 'Cancel' : 'Add New Product'}
          </button>
        </div>

        {showForm && (
          <div className="bg-white rounded-lg shadow p-6 mb-8">
            <h2 className="text-xl font-bold text-gray-800 mb-4">
              {editingProduct ? 'Edit Product' : 'Add New Product'}
            </h2>
            <form onSubmit={handleSubmit}>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold mb-2">Product Name</label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-2">Price ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={formData.price}
                    onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-2">Stock</label>
                  <input
                    type="number"
                    required
                    value={formData.stock}
                    onChange={(e) => setFormData({ ...formData, stock: e.target.value })}
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-2">Image URL</label>
                  <input
                    type="text"
                    value={formData.image_url}
                    onChange={(e) => setFormData({ ...formData, image_url: e.target.value })}
                    className="w-full border rounded-lg px-3 py-2"
                    placeholder="https://..."
                  />
                </div>
              </div>

              <div className="mt-4">
                <label className="block text-sm font-semibold mb-2">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                  rows="3"
                />
              </div>

              <div className="mt-4 flex items-center">
                <input
                  type="checkbox"
                  checked={formData.is_listed}
                  onChange={(e) => setFormData({ ...formData, is_listed: e.target.checked })}
                  className="mr-2"
                  id="is_listed"
                />
                <label htmlFor="is_listed" className="text-sm font-semibold">
                  Listed (visible to customers)
                </label>
              </div>

              <div className="mt-6">
                <button
                  type="submit"
                  className="bg-pink-600 text-white px-6 py-2 rounded-lg hover:bg-pink-700 font-semibold"
                >
                  {editingProduct ? 'Update Product' : 'Create Product'}
                </button>
              </div>
            </form>
          </div>
        )}

        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Product</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Price</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stock</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rating</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {products.map((product) => (
                <tr key={product.id}>
                  <td className="px-6 py-4">
                    <div className="flex items-center space-x-3">
                      {product.image_url ? (
                        <img src={product.image_url} alt={product.name} className="w-12 h-12 object-cover rounded" />
                      ) : (
                        <div className="w-12 h-12 flex items-center justify-center bg-gradient-to-br from-pink-100 to-purple-100 rounded">
                          <span className="text-2xl">👗</span>
                        </div>
                      )}
                      <div>
                        <p className="font-semibold text-gray-800">{product.name}</p>
                        <p className="text-sm text-gray-500">{product.description?.substring(0, 50)}...</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-gray-800 font-semibold">
                    ${product.price.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 text-gray-800">
                    {product.stock}
                  </td>
                  <td className="px-6 py-4 text-gray-800">
                    {product.total_reviews > 0 ? (
                      <div>
                        <span className="text-yellow-500">★</span> {product.average_rating.toFixed(1)}
                        <span className="text-gray-500 text-sm"> ({product.total_reviews})</span>
                      </div>
                    ) : (
                      <span className="text-gray-400">No reviews</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <button
                      onClick={() => handleToggleListed(product)}
                      className={`px-3 py-1 rounded-full text-sm font-semibold ${
                        product.is_listed
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {product.is_listed ? 'Listed' : 'Unlisted'}
                    </button>
                  </td>
                  <td className="px-6 py-4 text-right space-x-2">
                    <button
                      onClick={() => handleEdit(product)}
                      className="text-blue-600 hover:text-blue-800 font-semibold"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(product.id)}
                      className="text-red-600 hover:text-red-800 font-semibold"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Admin;