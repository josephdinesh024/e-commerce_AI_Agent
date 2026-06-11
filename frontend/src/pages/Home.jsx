import React, { useEffect, useState } from 'react';
import { getProducts } from '../services/api';
import ProductCard from '../components/ProductCard';
import { confirmActionToast } from '../components/toasts';
import { useCopilot } from '../components/agentCopilot/useCopilot';

const Home = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  // const { setPageContext } = useCopilot();

  useEffect(() => {
    fetchProducts();
    
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await getProducts(true);
      setProducts(response.data);
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-pink-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 py-8">
      {/* Max-width container keeps the grid from going "full window" */}
      <div className="max-w-7xl mx-auto px-4"> 
        <div className="mb-8 border-b pb-4">
          <h1 className="text-2xl font-bold text-gray-800">Featured Collection</h1>
          <p className="text-gray-500">Curated styles for you</p>
        </div>

        {products.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-lg shadow-sm">
            <p className="text-gray-400">No products available.</p>
          </div>
        ) : (
          /* Grid forced to max 3 columns */
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {products.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Home;