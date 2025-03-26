import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import './Login.css';

const Login: React.FC = () => {
  const { signInWithGoogle } = useAuth();

  const handleGoogleSignIn = async () => {
    try {
      await signInWithGoogle();
    } catch (error) {
      console.error('Failed to sign in with Google:', error);
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h1>Welcome to LLMBash</h1>
        <p>Please sign in to continue</p>
        <button 
          className="google-sign-in-button"
          onClick={handleGoogleSignIn}
        >
          <img 
            src="https://www.google.com/favicon.ico" 
            alt="Google" 
            className="google-icon"
          />
          Sign in with Google
        </button>
      </div>
    </div>
  );
};

export default Login; 