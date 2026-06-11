import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getProduct, getProductReviews, addToCart, getSessionId, createReview, getMyReview, updateReview, deleteReview } from '../services/api';
import StarRating from '../components/StarRating';
import { useCart } from '../context/CartContext';
import { executeActions } from '../util/agentAction';
import toast from 'react-hot-toast';

const ProductDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { refreshCart } = useCart();
  const [product, setProduct] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [myReview, setMyReview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [reviewData, setReviewData] = useState({ rating: 5, comment: '' });

  const actions = [
    {
        "type": "click",
        "target": "#3-star-rate-btn",
        "data": null,
        "require_confirmation": false
    },
    {
        "type": "enter",
        "target": "#review-comments",
        "data": "This dress is good and awesome!",
        "require_confirmation": false
    },
    {
        "type": "click",
        "target": "#submit-review-form",
        "data": "Submit Review",
        "require_confirmation": true
    }
]

  useEffect(() => {
    fetchProductData();
    // executeActions(actions);
  }, [id]);

  const fetchProductData = async () => {
    try {
      const [productRes, reviewsRes] = await Promise.all([
        getProduct(id),
        getProductReviews(id)
      ]);
      
      setProduct(productRes.data);
      setReviews(reviewsRes.data);
      
      // Check if user has already reviewed
      const sessionId = getSessionId();
      const myReviewRes = await getMyReview(id, sessionId);
      if (myReviewRes.data) {
        setMyReview(myReviewRes.data);
        setReviewData({ rating: myReviewRes.data.rating, comment: myReviewRes.data.comment || '' });
      }
    } catch (error) {
      console.error('Error fetching product:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = async () => {
    try {
      const sessionId = getSessionId();
      await addToCart({
        session_id: sessionId,
        product_id: parseInt(id),
        quantity: quantity
      });
      refreshCart();
      toast('Added to cart successfully!');
    } catch (error) {
      console.error('Error adding to cart:', error);
      toast(error.response?.data?.detail || 'Error adding to cart');
    }
  };

  const handleSubmitReview = async (e) => {
    e.preventDefault();
    const forms = new FormData(e.target);
    forms.forEach((v,k)=>{
      if (k in reviewData && reviewData[k] !== v)
        reviewData[k] = v;
    });
    
    try {
      const sessionId = getSessionId();
      
      if (myReview) {
        // Update existing review
        await updateReview(myReview.id, sessionId, reviewData);
        toast('Review updated successfully!');
      } else {
        // Create new review
        await createReview({
          ...reviewData,
          product_id: parseInt(id),
          session_id: sessionId
        });
        toast('Review submitted successfully!');
      }
      
      setShowReviewForm(false);
      fetchProductData();
    } catch (error) {
      console.error('Error submitting review:', error);
      toast(error.response?.data?.detail || 'Error submitting review');
    }
  };

  const handleDeleteReview = async () => {
    if (!window.confirm('Are you sure you want to delete your review?')) return;
    
    try {
      const sessionId = getSessionId();
      await deleteReview(myReview.id, sessionId);
      toast('Review deleted successfully!');
      setMyReview(null);
      setReviewData({ rating: 5, comment: '' });
      fetchProductData();
    } catch (error) {
      console.error('Error deleting review:', error);
      toast('Error deleting review');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-pink-600"></div>
      </div>
    );
  }

  if (!product) {
    return <div className="text-center py-16">Product not found</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        <button
          onClick={() => navigate('/')}
          className="mb-6 text-pink-600 hover:text-pink-700 flex items-center"
        >
          ← Back to Shop
        </button>

        <div className="grid md:grid-cols-2 gap-8 bg-white rounded-lg shadow-lg p-8">
          <div>
            {product.image_url ? (
              <img 
                src={product.image_url} 
                alt={product.name}
                className="w-full h-96 object-cover rounded-lg"
              />
            ) : (
              <div className="w-full h-96 flex items-center justify-center bg-gradient-to-br from-pink-100 to-purple-100 rounded-lg">
                <span className="text-9xl">👗</span>
              </div>
            )}
          </div>

          <div>
            <h1 className="text-3xl font-bold text-gray-800 mb-4">{product.name}</h1>
            
            <div className="flex items-center space-x-4 mb-4">
              <span className="text-4xl font-bold text-pink-600">${product.price.toFixed(2)}</span>
              <span className="text-gray-600">Stock: {product.stock}</span>
            </div>

            {product.total_reviews > 0 && (
              <div className="flex items-center space-x-2 mb-6">
                <StarRating rating={Math.round(product.average_rating)} readonly />
                <span className="text-lg text-gray-700">
                  {product.average_rating.toFixed(1)} ({product.total_reviews} reviews)
                </span>
              </div>
            )}

            <p className="text-gray-700 mb-6">{product.description}</p>

            {product.stock > 0 ? (
              <div className="space-y-4">
                <div className="flex items-center space-x-4">
                  <label className="font-semibold">Quantity:</label>
                  <div className="flex items-center border rounded">
                    <button
                      id='decrease_quantity'
                      onClick={() => setQuantity(Math.max(1, quantity - 1))}
                      className="px-3 py-1 bg-gray-100 hover:bg-gray-200"
                    >
                      -
                    </button>
                    <input
                      id='product_quantity'
                      type="number"
                      value={quantity}
                      onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                      className="w-16 text-center border-x"
                      min="1"
                      max={product.stock}
                    />
                    <button
                      id='increase_quantity'
                      onClick={() => setQuantity(Math.min(product.stock, quantity + 1))}
                      className="px-3 py-1 bg-gray-100 hover:bg-gray-200"
                    >
                      +
                    </button>
                  </div>
                </div>

                <button
                  id='add_to_cart'
                  onClick={handleAddToCart}
                  className="w-full bg-pink-600 text-white py-3 rounded-lg font-semibold hover:bg-pink-700 transition"
                >
                  Add to Cart
                </button>
              </div>
            ) : (
              <div className="text-red-600 font-semibold text-lg">Out of Stock</div>
            )}
          </div>
        </div>

        {/* Reviews Section */}
        <div className="mt-12 bg-white rounded-lg shadow-lg p-8">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-800">Customer Reviews</h2>
            {!showReviewForm && (
              <button
                id='show-review-form-btn'
                onClick={() => setShowReviewForm(true)}
                className="bg-pink-600 text-white px-4 py-2 rounded-lg hover:bg-pink-700"
              >
                {myReview ? 'Edit My Review' : 'Write a Review'}
              </button>
            )}
          </div>

          {showReviewForm && (
            <form id='review-form' onSubmit={handleSubmitReview} className="mb-8 p-6 bg-gray-50 rounded-lg">
              <h3 className="text-lg font-semibold mb-4">
                {myReview ? 'Edit Your Review' : 'Write Your Review'}
              </h3>
              
              <div className="mb-4">
                <label className="block mb-2 font-semibold">Rating</label>
                <StarRating
                  rating={reviewData.rating}
                  onRatingChange={(rating) => setReviewData({ ...reviewData, rating })}
                  size="lg"
                />
              </div>

              <div className="mb-4">
                <label className="block mb-2 font-semibold">Comment</label>
                <textarea
                  id='review-comments'
                  name='comment'
                  value={reviewData.comment}
                  onChange={(e) => setReviewData({ ...reviewData, comment: e.target.value })}
                  className="w-full border rounded-lg p-3"
                  rows="4"
                  placeholder="Share your thoughts about this dress..."
                />
              </div>

              <div className="flex space-x-4">
                <button
                  id='submit-review-form'
                  type="submit"
                  className="bg-pink-600 text-white px-6 py-2 rounded-lg hover:bg-pink-700"
                >
                  {myReview ? 'Update Review' : 'Submit Review'}
                </button>
                <button
                  type="button"
                  id='close-review-form-btn'
                  onClick={() => setShowReviewForm(false)}
                  className="bg-gray-300 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-400"
                >
                  Cancel
                </button>
                {myReview && (
                  <button
                    type="button"
                    id='delete-review-btn'
                    onClick={handleDeleteReview}
                    className="bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700"
                  >
                    Delete Review
                  </button>
                )}
              </div>
            </form>
          )}

          {reviews.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No reviews yet. Be the first to review!</p>
          ) : (
            <div className="space-y-6">
              {reviews.map((review) => (
                <div key={review.id} className="border-b pb-6">
                  <div className="flex items-center justify-between mb-2">
                    <StarRating rating={review.rating} readonly />
                    <span className="text-sm text-gray-500">
                      {new Date(review.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  {review.comment && (
                    <p className="text-gray-700 mt-2">{review.comment}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProductDetail;