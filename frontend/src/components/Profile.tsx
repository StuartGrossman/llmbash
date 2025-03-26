import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import './Profile.css';

interface ProfileProps {
  onBack: () => void;
}

const Profile: React.FC<ProfileProps> = ({ onBack }) => {
  const { user } = useAuth();

  return (
    <div className="profile-container">
      <div className="profile-box">
        <h1>Profile Settings</h1>
        <div className="user-info">
          <img 
            src={user?.photoURL || 'https://via.placeholder.com/100'} 
            alt="Profile" 
            className="profile-picture"
          />
          <div className="user-details">
            <h2>{user?.displayName || 'User'}</h2>
            <p>{user?.email}</p>
          </div>
        </div>

        <div className="api-keys-section">
          <h2>API Keys</h2>
          <p className="section-description">
            Enter your API keys below. These will be used to access the respective LLM services.
          </p>

          <div className="api-key-input">
            <label htmlFor="openai-key">OpenAI API Key</label>
            <input
              type="password"
              id="openai-key"
              placeholder="Enter your OpenAI API key"
              className="api-key-field"
            />
            <div className="example-key">
              Example: sk-1234567890abcdef1234567890abcdef1234567890abcdef
            </div>
          </div>

          <div className="api-key-input">
            <label htmlFor="gemini-key">Google Gemini API Key</label>
            <input
              type="password"
              id="gemini-key"
              placeholder="Enter your Gemini API key"
              className="api-key-field"
            />
            <div className="example-key">
              Example: AIzaSyDxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxX
            </div>
          </div>

          <div className="api-key-input">
            <label htmlFor="grok-key">Grok API Key</label>
            <input
              type="password"
              id="grok-key"
              placeholder="Enter your Grok API key"
              className="api-key-field"
            />
            <div className="example-key">
              Example: xai_1234567890abcdef1234567890abcdef
            </div>
          </div>

          <div className="api-key-input">
            <label htmlFor="deepseek-key">Deepseek API Key</label>
            <input
              type="password"
              id="deepseek-key"
              placeholder="Enter your Deepseek API key"
              className="api-key-field"
            />
            <div className="example-key">
              Example: dsk_1234567890abcdef1234567890abcdef
            </div>
          </div>
        </div>

        <button onClick={onBack} className="back-button">
          Back to Chat
        </button>
      </div>
    </div>
  );
};

export default Profile; 