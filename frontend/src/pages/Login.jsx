import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { loginUser } from '../services/api';
import { toast } from 'react-hot-toast';
import { getSessionId, updateSessionId } from '../services/api';

const Login = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const sessionId = getSessionId(); // Get current session ID for context
  // ✅ Copilot form fill event
  useEffect(() => {
    const handleCopilotFill = (e) => {
      const data = e.detail;
      setFormData(prev => ({ ...prev, ...data }));
      toast.success('✅ Form filled by AI Copilot!');
    };
    
    window.addEventListener('copilot-fill-form', handleCopilotFill);
    return () => window.removeEventListener('copilot-fill-form', handleCopilotFill);
  }, []);


  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    
    let forms = new FormData(e.target);
    forms.forEach((v,k)=>{
      if (k in formData && formData[k] == '')
        formData[k] = v;
    });

    // formData['temp_session_id'] = sessionId; // Pass current session ID for context and potential session linking

    try {
      console.log('Submitting login with data:', formData);
      const { data: user } = await loginUser(formData);
      console.log('User logged in:', user);
      // // Store auth state
      // localStorage.setItem('access_token', access_token);
      // localStorage.setItem('user_id', user.id.toString());
      // localStorage.setItem('user_name', user.username);
      // console.log(formData);

      updateSessionId(user.session_id); // Update session ID in local storage
      
      toast.success(`Welcome back, ${formData.email}! 👋`);
      navigate('/', { replace: true });
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message || 'Login failed';
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-pink-50 via-white to-purple-50 p-4">
      <div className="max-w-sm w-full bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl p-8 border border-white/50">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-pink-600 to-purple-600 bg-clip-text text-transparent mb-2">
            Welcome Back
          </h1>
          <p className="text-gray-600">Sign in to continue shopping</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Email */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Email
            </label>
            <input
              id="email-input"
              type="email"
              name='email'
              autoComplete="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-4 py-3 rounded-2xl border-2 border-gray-200 focus:border-pink-500 focus:ring-4 focus:ring-pink-100 transition-all duration-300 text-lg"
              placeholder="your@email.com"
            />
          </div>

          {/* Password */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Password
            </label>
            <input
              id="password-input"
              name='password'
              type="password"
              autoComplete="current-password"
              required
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full px-4 py-3 rounded-2xl border-2 border-gray-200 focus:border-pink-500 focus:ring-4 focus:ring-pink-100 transition-all duration-300 text-lg"
              placeholder="••••••••"
            />
          </div>

          {/* Submit */}
          <button
            id="login-submit"
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-pink-600 to-purple-600 text-white py-4 rounded-2xl font-bold text-lg shadow-xl hover:shadow-2xl hover:from-pink-700 hover:to-purple-700 transform hover:-translate-y-0.5 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5" fill="none" viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                </svg>
                Signing In...
              </span>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        <div className="mt-8 text-center space-y-4">
          <button
            type="button"
            onClick={() => navigate('/register')}
            className="w-full py-3 px-4 border-2 border-dashed border-gray-300 rounded-2xl text-gray-600 hover:border-pink-400 hover:text-pink-600 hover:bg-pink-50 transition-all font-semibold"
          >
            Create New Account
          </button>
          
          <div className="text-xs text-gray-500 bg-blue-50 p-3 rounded-xl">
            🤖 <strong>AI Copilot</strong> can help fill this form! Just ask "help me login"
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
