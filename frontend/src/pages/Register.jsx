import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { registerUser } from '../services/api';
import { toast } from 'react-hot-toast';

const Register = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '', username: '', password: '', confirmPassword: '', fullname: '', phone: ''
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const sessionId = localStorage.getItem('ai_session_id');

  // Copilot form fill
  useEffect(() => {
    const handleCopilotFill = (e) => {
      const data = e.detail;
      setFormData(prev => ({ ...prev, ...data }));
      setErrors({});
      toast.success('✅ Form filled by AI!');
    };
    window.addEventListener('copilot-fill-form', handleCopilotFill);
    return () => window.removeEventListener('copilot-fill-form', handleCopilotFill);
  }, []);


  const validateForm = () => {
    const newErrors = {};
    if (!formData.email.includes('@')) newErrors.email = 'Valid email required';
    if (formData.username.length < 3) newErrors.username = 'Min 3 characters';
    if (formData.password.length < 6) newErrors.password = 'Min 6 characters';
    if (formData.password !== formData.confirmPassword) newErrors.confirmPassword = "Passwords don't match";
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    let forms = new FormData(e.target);
    forms.forEach((v,k)=>{
      if (k in formData && formData[k] == '')
        formData[k] = v;
    });

    if (!validateForm()) return;
    
    setLoading(true);
    try {
      const {  user } = await registerUser({
        email: formData.email,
        username: formData.username,
        password: formData.password,
        fullname: formData.fullname || '',
        phone: formData.phone || ''
      });

    console.log({
        email: formData.email,
        username: formData.username,
        password: formData.password,
        fullname: formData.fullname || '',
        phone: formData.phone || ''
      });

    //   localStorage.setItem('access_token', access_token);
    //   localStorage.setItem('user_id', user.id.toString());
    //   localStorage.setItem('user_name', user.username);

      toast.success(`Welcome, ${formData.username}! 🎉`);
      navigate('/login', { replace: true });
    } catch (error) {
      toast.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 via-pink-50 to-indigo-50 p-4">
      <div className="max-w-md w-full bg-white/90 backdrop-blur-xl rounded-3xl shadow-2xl p-8 border border-white/50">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 via-pink-600 to-indigo-600 bg-clip-text text-transparent mb-3">
            Join Us
          </h1>
          <p className="text-gray-600">Create your account in seconds</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Email */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Email</label>
            <input
              id="register-email"
              name='email'
              type="email"
              required
              value={formData.email}
              onChange={(e) => {
                setFormData({ ...formData, email: e.target.value });
                if (errors.email) setErrors({ ...errors, email: '' });
              }}
              className={`w-full px-4 py-3 rounded-2xl border-2 transition-all ${
                errors.email 
                  ? 'border-red-300 focus:border-red-500 focus:ring-red-100' 
                  : 'border-gray-200 focus:border-purple-500 focus:ring-purple-100'
              }`}
              placeholder="your@email.com"
            />
            {errors.email && <p className="text-xs text-red-500 mt-1">{errors.email}</p>}
          </div>

          {/* Username */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Username</label>
            <input
              id="register-username"
              type="text"
              name='username'
              required
              minLength={3}
              value={formData.username}
              onChange={(e) => {
                setFormData({ ...formData, username: e.target.value });
                if (errors.username) setErrors({ ...errors, username: '' });
              }}
              className={`w-full px-4 py-3 rounded-2xl border-2 transition-all ${
                errors.username 
                  ? 'border-red-300 focus:border-red-500 focus:ring-red-100' 
                  : 'border-gray-200 focus:border-purple-500 focus:ring-purple-100'
              }`}
              placeholder="yourusername"
            />
            {errors.username && <p className="text-xs text-red-500 mt-1">{errors.username}</p>}
          </div>

          {/* Full Name */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Full Name</label>
            <input
              id="register-fullname"
              type="text"
              name='fullname'
              value={formData.fullname}
              onChange={(e) => setFormData({ ...formData, fullname: e.target.value })}
              className="w-full px-4 py-3 rounded-2xl border-2 border-gray-200 focus:border-purple-500 focus:ring-purple-100 transition-all"
              placeholder="John Doe"
            />
          </div>

          {/* Phone */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Phone (Optional)</label>
            <input
              id="register-phone"
              name='phone'
              type="tel"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              className="w-full px-4 py-3 rounded-2xl border-2 border-gray-200 focus:border-purple-500 focus:ring-purple-100 transition-all"
              placeholder="+91 12345 67890"
            />
          </div>

          {/* Password */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Password</label>
            <input
              id="register-password"
              name='password'
              type="password"
              required
              minLength={6}
              value={formData.password}
              onChange={(e) => {
                setFormData({ ...formData, password: e.target.value });
                if (errors.password) setErrors({ ...errors, password: '' });
              }}
              className={`w-full px-4 py-3 rounded-2xl border-2 transition-all ${
                errors.password 
                  ? 'border-red-300 focus:border-red-500 focus:ring-red-100' 
                  : 'border-gray-200 focus:border-purple-500 focus:ring-purple-100'
              }`}
              placeholder="••••••••"
            />
            {errors.password && <p className="text-xs text-red-500 mt-1">{errors.password}</p>}
          </div>

          {/* Confirm Password */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Confirm Password</label>
            <input
              id="register-password-confirm"
              name='confirmPassword'
              type="password"
              required
              value={formData.confirmPassword}
              onChange={(e) => {
                setFormData({ ...formData, confirmPassword: e.target.value });
                if (errors.confirmPassword) setErrors({ ...errors, confirmPassword: '' });
              }}
              className={`w-full px-4 py-3 rounded-2xl border-2 transition-all ${
                errors.confirmPassword 
                  ? 'border-red-300 focus:border-red-500 focus:ring-red-100' 
                  : 'border-gray-200 focus:border-purple-500 focus:ring-purple-100'
              }`}
              placeholder="••••••••"
            />
            {errors.confirmPassword && <p className="text-xs text-red-500 mt-1">{errors.confirmPassword}</p>}
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white py-4 rounded-2xl font-bold text-lg shadow-xl hover:shadow-2xl hover:from-purple-700 hover:to-pink-700 transform hover:-translate-y-0.5 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>

        <div className="mt-8 text-center pt-6 border-t border-gray-100">
          <button
            type="button"
            onClick={() => navigate('/login')}
            className="text-sm text-gray-600 hover:text-gray-900 font-semibold px-4 py-2 hover:bg-gray-100 rounded-xl transition-all"
          >
            Already have account? Sign In
          </button>
        </div>

        <div className="text-xs text-center text-gray-500 p-4 bg-blue-50 rounded-2xl mt-6">
          🤖 AI Copilot can <strong>auto-fill</strong> this form! Say "help me register"
        </div>
      </div>
    </div>
  );
};

export default Register;
