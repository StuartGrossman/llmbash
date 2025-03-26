import React, { useState, useEffect } from 'react';
import './App.css';
import { ref, onValue, DatabaseReference } from 'firebase/database';
import { database } from './firebase';
import { useAuth } from './contexts/AuthContext';
import Login from './components/Login';
import Profile from './components/Profile';

interface Message {
  content: string;
  timestamp: number;
  id: string;
}

interface LLMResponse {
  answer: string;
  timestamp: number;
  error?: string;
}

interface ModelResponses {
  [key: string]: LLMResponse;
}

interface AnalysisResponse {
  summary: string;
  bestModel: string;
  estimatedTime: number;
}

function ChatInterface() {
  const { user, logout } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [currentMessageId, setCurrentMessageId] = useState<string | null>(null);
  const [modelResponses, setModelResponses] = useState<ModelResponses>({});
  const [allResponses, setAllResponses] = useState<{ [key: string]: ModelResponses }>({});
  const [showProfile, setShowProfile] = useState(false);
  const [analyzing, setAnalyzing] = useState<{ [key: string]: boolean }>({});
  const [analysisResults, setAnalysisResults] = useState<{ [key: string]: AnalysisResponse }>({});
  const [estimatedTimes, setEstimatedTimes] = useState<{ [key: string]: number }>({});

  useEffect(() => {
    if (!user) return;
    
    const messagesRef = ref(database, `/users/${user.uid}/question`);
    onValue(messagesRef, (snapshot) => {
      const data = snapshot.val();
      console.log('Messages data:', data);
      if (data) {
        const messageList = Object.entries(data).map(([id, value]: [string, any]) => ({
          id,
          content: value.content,
          timestamp: value.timestamp,
        }));
        setMessages(messageList.sort((a, b) => b.timestamp - a.timestamp));

        // Fetch responses for each message
        messageList.forEach(message => {
          const modelRefs: { [key: string]: DatabaseReference } = {
            deepseek: ref(database, `/users/${user.uid}/question/${message.id}/deepseek`),
            grok: ref(database, `/users/${user.uid}/question/${message.id}/grok`),
            gemini: ref(database, `/users/${user.uid}/question/${message.id}/gemini`),
            openai: ref(database, `/users/${user.uid}/question/${message.id}/openai`),
          };

          Object.entries(modelRefs).forEach(([model, modelRef]) => {
            onValue(modelRef, (responseSnapshot) => {
              const responseData = responseSnapshot.val();
              console.log(`Response data for ${model}:`, responseData);
              if (responseData) {
                setAllResponses(prev => ({
                  ...prev,
                  [message.id]: {
                    ...prev[message.id],
                    [model]: responseData
                  }
                }));
              }
            });
          });
        });
      } else {
        // Initialize empty messages array if no data exists
        setMessages([]);
      }
    });
  }, [user]);

  useEffect(() => {
    if (currentMessageId && user) {
      const modelRefs: { [key: string]: DatabaseReference } = {
        deepseek: ref(database, `/users/${user.uid}/question/${currentMessageId}/deepseek`),
        grok: ref(database, `/users/${user.uid}/question/${currentMessageId}/grok`),
        gemini: ref(database, `/users/${user.uid}/question/${currentMessageId}/gemini`),
        openai: ref(database, `/users/${user.uid}/question/${currentMessageId}/openai`),
      };

      const unsubscribes = Object.entries(modelRefs).map(([model, modelRef]) => {
        return onValue(modelRef, (snapshot) => {
          const data = snapshot.val();
          if (data) {
            setModelResponses(prev => ({
              ...prev,
              [model]: data
            }));
            // Also update allResponses for the current message
            setAllResponses(prev => ({
              ...prev,
              [currentMessageId]: {
                ...prev[currentMessageId],
                [model]: data
              }
            }));
          }
        });
      });

      return () => {
        unsubscribes.forEach(unsubscribe => unsubscribe());
      };
    }
  }, [currentMessageId, user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || isSubmitting || !user) return;

    setIsSubmitting(true);
    setModelResponses({});

    const messageId = generateId();
    setCurrentMessageId(messageId);

    try {
      const response = await fetch('http://localhost:8000/api/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: newMessage,
          id: messageId,
          userId: user.uid
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      setNewMessage('');
    } catch (error) {
      console.error('Error:', error);
      setIsSubmitting(false);
    }
  };

  const generateId = () => {
    return 'q' + Math.random().toString(36).substring(2, 15);
  };

  const handleAnalysis = async (messageId: string, responses: ModelResponses) => {
    if (!user) return;
    
    setAnalyzing(prev => ({ ...prev, [messageId]: true }));
    
    try {
      const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messageId,
          responses,
          userId: user.uid
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to analyze responses');
      }

      const data = await response.json();
      setAnalysisResults(prev => ({ ...prev, [messageId]: data }));
      
      // Update estimated time every second
      const startTime = Date.now();
      const interval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        setEstimatedTimes(prev => ({ ...prev, [messageId]: elapsed }));
      }, 1000);

      // Clear interval and loading state when analysis is complete
      setAnalyzing(prev => ({ ...prev, [messageId]: false }));
      clearInterval(interval);

    } catch (error) {
      console.error('Error:', error);
      setAnalyzing(prev => ({ ...prev, [messageId]: false }));
    }
  };

  if (!user) {
    return <Login />;
  }

  if (showProfile) {
    return <Profile onBack={() => setShowProfile(false)} />;
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>LLM Chat</h1>
        <div className="user-info">
          <button onClick={() => setShowProfile(true)} className="profile-button">
            Profile
          </button>
          <span>{user.email}</span>
          <button onClick={logout} className="logout-button">Logout</button>
        </div>
      </header>
      <div className="terminal-container">
        <div className="messages-list">
          {messages.map((message) => (
            <div key={message.id} className="message-group">
              <div className="message-item user-message">
                <span className="timestamp">{new Date(message.timestamp).toLocaleString()}</span>
                <span className="content">{message.content}</span>
              </div>
              <div className="model-responses">
                {['deepseek', 'grok', 'gemini', 'openai'].map((model) => (
                  <div 
                    key={model} 
                    className={`model-response ${
                      analysisResults[message.id]?.bestModel === model ? 'best-response' : ''
                    }`}
                  >
                    <h4>{model.charAt(0).toUpperCase() + model.slice(1)}</h4>
                    {message.id === currentMessageId ? (
                      modelResponses[model] ? (
                        <div className="response-content">
                          {modelResponses[model].answer || `Error: ${modelResponses[model].error || 'Unknown error'}`}
                        </div>
                      ) : (
                        <div className="loading">Waiting for response...</div>
                      )
                    ) : (
                      allResponses[message.id]?.[model] ? (
                        <div className="response-content">
                          {allResponses[message.id][model].answer || `Error: ${allResponses[message.id][model].error || 'Unknown error'}`}
                        </div>
                      ) : (
                        <div className="loading">No response yet</div>
                      )
                    )}
                  </div>
                ))}
              </div>
              {allResponses[message.id] && Object.keys(allResponses[message.id]).length === 4 && (
                <div className="analysis-section">
                  <button 
                    onClick={() => handleAnalysis(message.id, allResponses[message.id])}
                    className="analyze-button"
                    disabled={analyzing[message.id]}
                  >
                    {analyzing[message.id] ? (
                      <>
                        <span className="spinner"></span>
                        Analyzing... ({estimatedTimes[message.id]}s)
                      </>
                    ) : (
                      'Analyze Responses'
                    )}
                  </button>
                  {analysisResults[message.id] && (
                    <div className="analysis-result">
                      <h3>Analysis Summary</h3>
                      <p>{analysisResults[message.id].summary}</p>
                      <p className="best-model">
                        Best Model: {analysisResults[message.id].bestModel}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
        <form onSubmit={handleSubmit} className="input-form">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Type your message..."
            disabled={isSubmitting}
          />
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Processing...' : 'Send'}
          </button>
        </form>
      </div>
    </div>
  );
}

function App() {
  return <ChatInterface />;
}

export default App; 