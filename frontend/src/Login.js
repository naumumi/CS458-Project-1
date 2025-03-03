import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

/**
 * Login Component
 * 
 * Handles user authentication through:
 * - Email/phone and password login
 * - Google OAuth integration
 * 
 * Features:
 * - Client-side input validation
 * - Error feedback display
 * - Form submission handling
 * - Redirect after successful login
 */
function Login() {
  // Form state management
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  
  // UI feedback state
  const [message, setMessage] = useState('');
  const [alertType, setAlertType] = useState('danger'); // 'success' | 'danger' | 'warning'
  
  const navigate = useNavigate();

  /**
   * Validates form inputs
   * @returns {Object} Validation result {isValid, errorMessage}
   */
  const validateForm = () => {
    // Check for empty fields with proper trimming
    if (!identifier.trim() || !password.trim()) {
      return {
        isValid: false,
        errorMessage: "Email/Phone and Password are required."
      };
    }
    
    // Check identifier length
    if (identifier.length > 255) {
      return {
        isValid: false,
        errorMessage: "Email/Phone is too long."
      };
    }
    
    // Check password length
    if (password.length > 1000) {
      return {
        isValid: false,
        errorMessage: "Password is too long."
      };
    }

    return { isValid: true };
  };

  /**
   * Displays feedback message to user
   * @param {string} msg - Message to display
   * @param {string} type - Alert type: 'success', 'danger', or 'warning'
   */
  const showFeedback = (msg, type = 'danger') => {
    setMessage(msg);
    setAlertType(type);
  };

  /**
   * Handles form submission and authentication logic
   * @param {Event} e - Form submission event
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    
    // Disable submit button to prevent multiple submissions
    const submitButton = e.target.querySelector('button[type="submit"]');
    submitButton.disabled = true;

    try {
      // Validate form inputs
      const validation = validateForm();
      if (!validation.isValid) {
        showFeedback(validation.errorMessage, 'danger');
        submitButton.disabled = false;
        return;
      }

      // Send login request to API
      const response = await axios.post('http://localhost:5000/api/login', {
        identifier,
        password,
      });

      // Handle response based on success status
      if (response.data.success) {
        showFeedback('Login successful', 'success');

        // Navigate to welcome page after a short delay
        setTimeout(() => {
          navigate('/welcome', { state: { user: identifier } });
        }, 10000);
      } else {
        // Determine alert type based on error message
        const feedbackType = response.data.message === "Too many failed attempts" ? 'warning' : 'danger';
        showFeedback(response.data.message, feedbackType);
      }
    } catch (err) {
      console.error('Login error:', err);
      showFeedback('An error occurred. Please try again.');
    } finally {
      submitButton.disabled = false;
    }
  };

  /**
   * Initiates Google OAuth authentication flow
   */
  const handleGoogleLogin = () => {
    window.location.href = 'http://localhost:5000/api/auth/google';
  };

  return (
    <div className="container-fluid bg-light vh-100 d-flex justify-content-center align-items-center">
      <div className="card p-4 shadow" style={{ maxWidth: '400px', width: '100%' }}>
        <h2 className="text-center mb-4">Login</h2>

        <form onSubmit={handleSubmit}>
          {/* Email/Phone Input Field */}
          <div className="mb-3">
            <label htmlFor="identifier" className="form-label">
              Email/Phone
            </label>
            <input
              id="identifier"
              type="text"
              className="form-control"
              placeholder="Enter your email or phone"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              autoFocus
            />
          </div>

          {/* Password Input Field */}
          <div className="mb-3">
            <label htmlFor="password" className="form-label">
              Password
            </label>
            <input
              id="password"
              type="password"
              className="form-control"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            className="btn btn-primary w-100"
          >
            Login
          </button>
        </form>

        <hr className="my-4" />

        {/* Google OAuth Login Button */}
        <button
          className="btn btn-outline-danger w-100 mb-3"
          onClick={handleGoogleLogin}
        >
          <i className="bi bi-google me-2"></i>
          Login with Google
        </button>
        
        {/* Alert Message Display */}
        {message && (
          <div className={`alert alert-${alertType}`} role="alert">
            {message}
          </div>
        )}

        {/* Registration Link */}
        <p className="mt-3 text-center">
          Don't have an account? <a href="/register">Register here</a>
        </p>
      </div>
    </div>
  );
}

export default Login;