import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate, Link } from 'react-router-dom';

function Register() {
  const [method, setMethod] = useState('email'); // 'email' or 'phone'
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [message, setMessage] = useState('');
  const navigate = useNavigate();

  const handleMethodChange = (e) => {
    setMethod(e.target.value);
    // Clear both fields when switching methods.
    setEmail('');
    setPhone('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');

    // Validate password confirmation
    if (password !== confirm) {
      setMessage("Passwords do not match.");
      return;
    }

    // Based on chosen method, set the data payload.
    const payload = { password };
    if (method === 'email') {
      if (!email.trim()) {
        setMessage("Email is required.");
        return;
      }
      payload.email = email.trim();
    } else if (method === 'phone') {
      if (!phone.trim()) {
        setMessage("Phone is required.");
        return;
      }
      payload.phone = phone.trim();
    }

    try {
      const response = await axios.post('http://localhost:5000/api/register', payload);
      if (response.data.success) {
        setMessage("Registration successful! Redirecting to login...");
        setTimeout(() => {
          navigate('/');
        }, 1500);
      } else {
        setMessage("Registration failed: " + response.data.message);
      }
    } catch (err) {
      console.error(err);
      setMessage("An error occurred. Please try again.");
    }
  };

  return (
    <div className="container-fluid bg-light vh-100 d-flex justify-content-center align-items-center">
      <div className="card p-4 shadow" style={{ maxWidth: '400px', width: '100%' }}>
        <h2 className="text-center mb-4">Register</h2>

        {/* Radio buttons to select registration method */}
        <div className="mb-3">
          <label className="form-label me-3">Register with:</label>
          <div className="form-check form-check-inline">
            <input
              className="form-check-input"
              type="radio"
              name="registerMethod"
              id="registerEmail"
              value="email"
              checked={method === 'email'}
              onChange={handleMethodChange}
            />
            <label className="form-check-label" htmlFor="registerEmail">
              Email
            </label>
          </div>
          <div className="form-check form-check-inline">
            <input
              className="form-check-input"
              type="radio"
              name="registerMethod"
              id="registerPhone"
              value="phone"
              checked={method === 'phone'}
              onChange={handleMethodChange}
            />
            <label className="form-check-label" htmlFor="registerPhone">
              Phone
            </label>
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Conditionally render email or phone input */}
          {method === 'email' && (
            <div className="mb-3">
              <label htmlFor="email" className="form-label">
                Email *
              </label>
              <input
                type="email"
                className="form-control"
                id="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required={method === 'email'}
              />
            </div>
          )}

          {method === 'phone' && (
            <div className="mb-3">
              <label htmlFor="phone" className="form-label">
                Phone *
              </label>
              <input
                type="text"
                className="form-control"
                id="phone"
                placeholder="Enter your phone"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                required={method === 'phone'}
              />
            </div>
          )}

          <div className="mb-3">
            <label htmlFor="password" className="form-label">
              Password *
            </label>
            <input
              type="password"
              className="form-control"
              id="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <div className="mb-3">
            <label htmlFor="confirm" className="form-label">
              Confirm Password *
            </label>
            <input
              type="password"
              className="form-control"
              id="confirm"
              placeholder="Confirm your password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="btn btn-primary w-100">
            Register
          </button>
        </form>

        {message && (
          <div className="alert alert-info mt-3" role="alert">
            {message}
          </div>
        )}

        <p className="mt-3 text-center">
          Already have an account? <Link to="/">Login here</Link>
        </p>
      </div>
    </div>
  );
}

export default Register;
