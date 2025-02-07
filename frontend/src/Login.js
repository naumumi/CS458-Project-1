import React, { useState } from 'react';
import axios from 'axios';

function Login() {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');

    try {
      const response = await axios.post('http://localhost:5000/api/login', {
        identifier,
        password
      });
      if (response.data.success) {
        setMessage('Login successful!');
        // Optionally redirect or do more logic
      } else {
        setMessage('Login failed: ' + response.data.message);
      }
    } catch (err) {
      console.error(err);
      setMessage('An error occurred. Please try again.');
    }
  };

  const handleGoogleLogin = () => {
    // This route on the backend initiates the Google OAuth flow
    window.location.href = 'http://localhost:5000/api/auth/google';
  };

  return (
    <div style={{ margin: '50px auto', width: '300px' }}>
      <h2>Login</h2>
      <form onSubmit={handleSubmit}>
        <label>Email/Phone:</label>
        <input
          type="text"
          required
          value={identifier}
          onChange={(e) => setIdentifier(e.target.value)}
          style={{ display: 'block', marginBottom: '10px', width: '100%' }}
        />

        <label>Password:</label>
        <input
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={{ display: 'block', marginBottom: '10px', width: '100%' }}
        />

        <button type="submit">Login</button>
      </form>

      <hr />
      <button onClick={handleGoogleLogin}>Login with Google</button>

      {message && (
        <p style={{ color: 'red', marginTop: '10px' }}>{message}</p>
      )}
    </div>
  );
}

export default Login;
