import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

function Login() {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [alertType, setAlertType] = useState('danger'); // 'success' | 'danger' | 'warning'
  
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');

    // Check for empty fields:
    if (!identifier.trim() || !password.trim()) {
      setAlertType('danger');
      setMessage("Email/Phone and Password are required.");
      return;
    }

    try {
      const response = await axios.post('http://localhost:5000/api/login', {
        identifier,
        password,
      });

      if (response.data.success) {
        // Mark success, show success alert
        setAlertType('success');
        setMessage('Login successful');
        
        // Navigate after a short delay
        setTimeout(() => {
          navigate('/welcome', { state: { user: identifier } });
        }, 10000);
      } else {
        // Check for "Too many failed attempts"
        if (response.data.message === "Too many failed attempts") {
          setAlertType('warning');
        } else {
          setAlertType('danger');
        }
        setMessage(response.data.message);
      }
    } catch (err) {
      console.error(err);
      setAlertType('danger');
      setMessage('An error occurred. Please try again.');
    }
  };

  const handleGoogleLogin = () => {
    window.location.href = 'http://localhost:5000/api/auth/google';
  };

  return (
    <div className="container-fluid bg-light vh-100 d-flex justify-content-center align-items-center">
      <div className="card p-4 shadow" style={{ maxWidth: '400px', width: '100%' }}>
        <h2 className="text-center mb-4">Login</h2>

        <form onSubmit={handleSubmit}>
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
            />
          </div>

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

          {/* We removed `disabled={!identifier.trim() || !password.trim()}` */}
          <button
            type="submit"
            className="btn btn-primary w-100"
          >
            Login
          </button>
        </form>

        <hr className="my-4" />

        <button
          className="btn btn-outline-danger w-100 mb-3"
          onClick={handleGoogleLogin}
        >
          <i className="bi bi-google me-2"></i>
          Login with Google
        </button>
        
        {message && (
          <div className={`alert alert-${alertType}`} role="alert">
            {message}
          </div>
        )}

        <p className="mt-3 text-center">
          Don't have an account? <a href="/register">Register here</a>
        </p>
      </div>
    </div>
  );
}

export default Login;
