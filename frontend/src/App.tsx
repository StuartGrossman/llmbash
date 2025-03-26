import React, { useState, useEffect } from 'react';
import './App.css';
import { ref, onValue, DatabaseReference } from 'firebase/database';
import { database } from './firebase';
import { useAuth } from './contexts/AuthContext';
import Login from './components/Login';
import Profile from './components/Profile';

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

interface Message {
  content: string;
  timestamp: number;
  id: string;
  responses?: {
    [modelKey: string]: LLMResponse;
  };
  analysis?: {
    summary: string;
    bestModel: string;
    timestamp: number;
  };
}

interface MessageResponses {
  responses: {
    [modelKey: string]: LLMResponse;
  };
  analysis?: {
    summary: string;
    bestModel: string;
    timestamp: number;
  };
}

interface AllResponses {
  [key: string]: MessageResponses;
}

interface LLMStatus {
  enabled: boolean;
  name: string;
  key: string;
}

function ChatInterface() {
  const { user, logout } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [currentMessageId, setCurrentMessageId] = useState<string | null>(null);
  const [modelResponses, setModelResponses] = useState<ModelResponses>({});
  const [allResponses, setAllResponses] = useState<AllResponses>({});
  const [showProfile, setShowProfile] = useState(false);
  const [analyzing, setAnalyzing] = useState<{ [key: string]: boolean }>({});
  const [analysisResults, setAnalysisResults] = useState<{ [key: string]: AnalysisResponse }>({});
  const [estimatedTimes, setEstimatedTimes] = useState<{ [key: string]: number }>({});
  const [llmStatus, setLlmStatus] = useState<LLMStatus[]>([
    { enabled: true, name: 'Deepseek', key: 'deepseek' },
    { enabled: true, name: 'Grok', key: 'grok' },
    { enabled: true, name: 'Gemini', key: 'gemini' },
    { enabled: true, name: 'GPT', key: 'openai' }
  ]);

  const toggleLLM = (key: string) => {
    setLlmStatus(prev => prev.map(llm => 
      llm.key === key ? { ...llm, enabled: !llm.enabled } : llm
    ));
  };

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
                    responses: {
                      ...prev[message.id]?.responses,
                      [model]: responseData
                    }
                  }
                }));
              }
            });
          });
        });
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
                responses: {
                  ...prev[currentMessageId]?.responses,
                  [model]: data
                }
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
          userId: user.uid,
          enabledLLMs: llmStatus.filter(llm => llm.enabled).map(llm => llm.key)
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

  const handleAnalysis = async (messageId: string) => {
    try {
      setAnalyzing(prev => ({ ...prev, [messageId]: true }));
      setEstimatedTimes(prev => ({ ...prev, [messageId]: 0 }));

      const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${await user?.getIdToken()}`
        },
        body: JSON.stringify({
          messageId,
          userId: user?.uid
        })
      });

      if (!response.ok) {
        throw new Error('Failed to analyze responses');
      }

      const data = await response.json();
      
      // Update analysis results
      setAnalysisResults(prev => ({
        ...prev,
        [messageId]: {
          summary: data.summary,
          bestModel: data.bestModel,
          estimatedTime: data.estimatedTime
        }
      }));

      // Update all responses with the new analysis data
      setAllResponses(prev => {
        const currentResponses = prev[messageId] || { responses: {} };
        const updatedResponses: MessageResponses = {
          ...currentResponses,
          analysis: {
            summary: data.summary,
            bestModel: data.bestModel,
            timestamp: Date.now()
          }
        };
        return {
          ...prev,
          [messageId]: updatedResponses
        };
      });

      // Update messages with the new analysis data
      setMessages(prev => prev.map(msg => 
        msg.id === messageId 
          ? {
              ...msg,
              analysis: {
                summary: data.summary,
                bestModel: data.bestModel,
                timestamp: Date.now()
              }
            }
          : msg
      ));

      setAnalyzing(prev => ({ ...prev, [messageId]: false }));
      setEstimatedTimes(prev => ({ ...prev, [messageId]: 0 }));
    } catch (error) {
      console.error('Error analyzing responses:', error);
      setAnalyzing(prev => ({ ...prev, [messageId]: false }));
      setEstimatedTimes(prev => ({ ...prev, [messageId]: 0 }));
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
        <div className="llm-controls">
          {llmStatus.map(llm => (
            <div key={llm.key} className="llm-toggle">
              <label className="switch">
                <input
                  type="checkbox"
                  checked={llm.enabled}
                  onChange={() => toggleLLM(llm.key)}
                />
                <span className="slider round"></span>
              </label>
              <span className="llm-name">{llm.name}</span>
            </div>
          ))}
        </div>
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
                {llmStatus
                  .filter(llm => llm.enabled)
                  .map((llm) => (
                    <div 
                      key={llm.key} 
                      className={`model-response ${
                        analysisResults[message.id]?.bestModel === llm.key ? 'best-response' : ''
                      }`}
                    >
                      <h4>{llm.name}</h4>
                      {message.id === currentMessageId ? (
                        modelResponses[llm.key] ? (
                          <div className="response-content">
                            {modelResponses[llm.key].answer || `Error: ${modelResponses[llm.key].error || 'Unknown error'}`}
                          </div>
                        ) : (
                          <div className="loading">Waiting for response...</div>
                        )
                      ) : (
                        allResponses[message.id]?.responses[llm.key] ? (
                          <div className="response-content">
                            {allResponses[message.id].responses[llm.key].answer || `Error: ${allResponses[message.id].responses[llm.key].error || 'Unknown error'}`}
                          </div>
                        ) : (
                          <div className="loading">No response yet</div>
                        )
                      )}
                    </div>
                  ))}
              </div>
              {allResponses[message.id] && 
               Object.keys(allResponses[message.id].responses).length === llmStatus.filter(llm => llm.enabled).length && (
                <div className="analysis-section">
                  <button 
                    onClick={() => handleAnalysis(message.id)}
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