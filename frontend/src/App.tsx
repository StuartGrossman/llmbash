import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ref, onValue } from 'firebase/database';
import { database } from './firebase';
import './App.css';

function App() {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [messages, setMessages] = useState<Array<{id: string, content: string, timestamp: number}>>([]);
  const [error, setError] = useState<string | null>(null);

  // Generate a unique ID
  const generateId = () => {
    return Math.random().toString(36).substring(2) + Date.now().toString(36);
  };

  useEffect(() => {
    // Listen for messages in Firebase
    const messagesRef = ref(database, 'question');
    console.log('Setting up Firebase listener for /question');
    
    const unsubscribe = onValue(messagesRef, (snapshot) => {
      console.log('Received Firebase update:', snapshot.val());
      const data = snapshot.val();
      if (data) {
        const messageList = Object.entries(data).map(([id, value]: [string, any]) => ({
          id,
          content: value.content,
          timestamp: value.timestamp
        }));
        console.log('Processed messages:', messageList);
        setMessages(messageList.sort((a, b) => b.timestamp - a.timestamp));
      } else {
        console.log('No data in Firebase');
        setMessages([]);
      }
    }, (error) => {
      console.error('Firebase listener error:', error);
      setError('Error connecting to Firebase');
    });

    return () => {
      console.log('Cleaning up Firebase listener');
      unsubscribe();
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    const messageId = generateId();
    console.log('Submitting message:', message, 'with ID:', messageId);
    
    try {
      // Send to backend
      const result = await axios.post('http://localhost:8000/api/message', {
        content: message,
        id: messageId
      });
      console.log('Backend response:', result.data);
      setResponse(result.data.response);
      setError(null);

      setMessage(''); // Clear input after sending
    } catch (error) {
      console.error('Error sending message:', error);
      setError(error instanceof Error ? error.message : 'Error sending message');
      setResponse('Error sending message');
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <div className="terminal-container">
          <h1>LLM Terminal Interface</h1>
          <div className="message-box">
            <p className="prompt">{'>'} {response || 'Welcome to the LLM Terminal'}</p>
            {error && <p className="error">{'>'} Error: {error}</p>}
          </div>
          <div className="messages-list">
            {messages.map((msg) => (
              <div key={msg.id} className="message-item">
                <span className="timestamp">{new Date(msg.timestamp).toLocaleTimeString()}</span>
                <span className="content">{msg.content}</span>
              </div>
            ))}
          </div>
          <form onSubmit={handleSubmit} className="input-form">
            <div className="input-container">
              <span className="prompt">{'>'}</span>
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Type your message..."
                className="terminal-input"
                autoFocus
              />
            </div>
            <button type="submit" className="terminal-button">SEND</button>
          </form>
        </div>
      </header>
    </div>
  );
}

export default App; 