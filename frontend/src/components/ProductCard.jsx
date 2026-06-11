import React from 'react';
import { Link } from 'react-router-dom';

const ProductCard = ({ product }) => {
  // Fallback values to prevent crashes if data is missing
  const price = product.price || 0;
  const rating = product.average_rating || 0;
  const originalPrice = price * 1.25; // Simulated 25% discount

  return (
    <Link to={`/product/${product.id}`} className="group">
      <div className="bg-white border border-gray-200 rounded-sm overflow-hidden hover:shadow-md transition-shadow duration-200 h-full flex flex-col">
        
        {/* IMAGE SECTION: Fixed Aspect Ratio & Cropped */}
        <div className="relative aspect-3/4 w-full overflow-hidden bg-gray-100">
          {product.image_url ? (
            <img 
              src={product.image_url} 
              alt={product.name}
              className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-4xl">👗</div>
          )}
          
          {/* Discount Tag Overlay */}
          <div className="absolute top-2 left-2 bg-pink-600 text-white text-[10px] font-bold px-2 py-0.5 rounded-sm">
            SALE
          </div>
        </div>
        
        {/* CONTENT SECTION */}
        <div className="p-3 flex flex-col grow">
          {/* Title - Truncated to 2 lines to keep cards uniform */}
          <h3 className="text-sm font-medium text-gray-700 line-clamp-2 mb-1 group-hover:text-blue-600 min-h-[40px]">
            {product.name}
          </h3>
          
          {/* Rating Badge */}
          <div className="flex items-center gap-2 mb-2">
            <span className="flex items-center bg-green-700 text-white text-[11px] font-bold px-1.5 py-0.5 rounded-sm">
              {rating.toFixed(1)} ★
            </span>
            <span className="text-xs text-gray-400 font-medium">
              ({product.total_reviews || 0})
            </span>
          </div>
          
          {/* Pricing - Amazon/Flipkart Layout */}
          <div className="mt-auto">
            <div className="flex items-baseline gap-2">
              <span className="text-lg font-bold text-gray-900">${price.toFixed(2)}</span>
              <span className="text-xs text-gray-400 line-through">${originalPrice.toFixed(2)}</span>
              <span className="text-xs font-bold text-green-600">25% off</span>
            </div>
            <p className="text-[11px] text-gray-500 mt-0.5">Free delivery</p>
          </div>
        </div>
      </div>
    </Link>
  );
};

export default ProductCard;