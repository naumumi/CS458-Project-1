import React from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';

function Welcome() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const user = searchParams.get('user') || 'User';

  const handleLogout = () => {
    // Implement logout logic if needed.
    navigate('/');
  };

  return (
    <div className="container-fluid bg-primary text-white vh-100 d-flex justify-content-center align-items-center">
      <div className="text-center">
        <h1>Welcome, {user}!</h1>
        <p>You have successfully logged in.</p>
        <button className="btn btn-light mt-3" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </div>
  );
}

export default Welcome;
