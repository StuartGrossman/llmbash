import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from '../App';
import { AuthProvider } from '../contexts/AuthContext';
import { vi } from 'vitest';

// Mock Firebase
vi.mock('../firebase', () => ({
  database: {
    ref: vi.fn(),
  },
}));

// Mock fetch
global.fetch = vi.fn();

// Mock Firebase Auth
vi.mock('firebase/auth', () => ({
  getAuth: vi.fn(),
  signInWithEmailAndPassword: vi.fn(),
  createUserWithEmailAndPassword: vi.fn(),
  signOut: vi.fn(),
  onAuthStateChanged: vi.fn(),
}));

// Test data
const mockUser = {
  uid: 'test-user-123',
  email: 'test@example.com',
  getIdToken: vi.fn().mockResolvedValue('mock-token'),
};

const mockResponses = {
  deepseek: { answer: 'Test response from Deepseek', timestamp: Date.now() },
  grok: { answer: 'Test response from Grok', timestamp: Date.now() },
  gemini: { answer: 'Test response from Gemini', timestamp: Date.now() },
  openai: { answer: 'Test response from OpenAI', timestamp: Date.now() },
};

describe('App Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ status: 'success' }),
    });
  });

  const renderApp = () => {
    return render(
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    );
  };

  describe('Authentication', () => {
    it('should show login form when not authenticated', () => {
      renderApp();
      expect(screen.getByText(/login/i)).toBeInTheDocument();
    });

    it('should show chat interface when authenticated', () => {
      // Mock authenticated user
      vi.mocked(onAuthStateChanged).mockImplementation((auth, callback) => {
        callback(mockUser);
        return () => {};
      });

      renderApp();
      expect(screen.getByText(/LLM Chat/i)).toBeInTheDocument();
    });
  });

  describe('Message Sending', () => {
    beforeEach(() => {
      // Mock authenticated user
      vi.mocked(onAuthStateChanged).mockImplementation((auth, callback) => {
        callback(mockUser);
        return () => {};
      });
    });

    it('should send message to enabled LLMs', async () => {
      renderApp();
      
      // Fill in message input
      const input = screen.getByPlaceholderText(/type your message/i);
      fireEvent.change(input, { target: { value: 'Test message' } });
      
      // Submit message
      const submitButton = screen.getByText(/send/i);
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          'http://localhost:8000/api/message',
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('Test message'),
          })
        );
      });
    });

    it('should handle message sending errors', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      renderApp();
      
      const input = screen.getByPlaceholderText(/type your message/i);
      fireEvent.change(input, { target: { value: 'Test message' } });
      
      const submitButton = screen.getByText(/send/i);
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/processing/i)).toBeInTheDocument();
      });
    });
  });

  describe('LLM Toggles', () => {
    beforeEach(() => {
      vi.mocked(onAuthStateChanged).mockImplementation((auth, callback) => {
        callback(mockUser);
        return () => {};
      });
    });

    it('should toggle LLM states', () => {
      renderApp();
      
      const toggles = screen.getAllByRole('checkbox');
      expect(toggles).toHaveLength(4); // One for each LLM
      
      // Toggle first LLM
      fireEvent.click(toggles[0]);
      expect(toggles[0]).not.toBeChecked();
    });
  });

  describe('Response Analysis', () => {
    beforeEach(() => {
      vi.mocked(onAuthStateChanged).mockImplementation((auth, callback) => {
        callback(mockUser);
        return () => {};
      });
    });

    it('should analyze responses when all enabled LLMs have responded', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          summary: 'Test summary',
          bestModel: 'deepseek',
          estimatedTime: 0,
        }),
      });

      renderApp();
      
      // Simulate receiving responses from all LLMs
      await waitFor(() => {
        expect(screen.getByText(/analyze responses/i)).toBeInTheDocument();
      });

      // Click analyze button
      const analyzeButton = screen.getByText(/analyze responses/i);
      fireEvent.click(analyzeButton);

      await waitFor(() => {
        expect(screen.getByText(/Test summary/i)).toBeInTheDocument();
        expect(screen.getByText(/Best Model: deepseek/i)).toBeInTheDocument();
      });
    });

    it('should handle analysis errors', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 422,
      });

      renderApp();
      
      const analyzeButton = screen.getByText(/analyze responses/i);
      fireEvent.click(analyzeButton);

      await waitFor(() => {
        expect(screen.getByText(/analyzing/i)).toBeInTheDocument();
      });
    });
  });

  describe('UI Components', () => {
    beforeEach(() => {
      vi.mocked(onAuthStateChanged).mockImplementation((auth, callback) => {
        callback(mockUser);
        return () => {};
      });
    });

    it('should show profile section when profile button is clicked', () => {
      renderApp();
      
      const profileButton = screen.getByText(/profile/i);
      fireEvent.click(profileButton);

      expect(screen.getByText(/user profile/i)).toBeInTheDocument();
    });

    it('should show loading states during API calls', async () => {
      (global.fetch as jest.Mock).mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

      renderApp();
      
      const input = screen.getByPlaceholderText(/type your message/i);
      fireEvent.change(input, { target: { value: 'Test message' } });
      
      const submitButton = screen.getByText(/send/i);
      fireEvent.click(submitButton);

      expect(screen.getByText(/processing/i)).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.queryByText(/processing/i)).not.toBeInTheDocument();
      });
    });
  });
}); 