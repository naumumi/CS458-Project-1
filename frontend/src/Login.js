import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
function Login() {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');

    try {
      const response = await axios.post('http://localhost:5000/api/login', {
        identifier,
        password,
      });
      if (response.data.success) {
        setMessage('Login successful!');
        setTimeout(() => {
          navigate('/welcome', { state: { user: identifier } });
        }, 1000);
      } else {
        setMessage('Login failed: ' + response.data.message);
      }
    } catch (err) {
      console.error(err);
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
              required
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
              required
            />
          </div>

          <button type="submit" className="btn btn-primary w-100">
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
          <div className="alert alert-info" role="alert">
            {message}
          </div>
        )}
      </div>
    </div>
  );
}

export default Login;
