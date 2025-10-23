import React, { useState, useEffect } from 'react';
import { AvatarVideo } from './components/AvatarVideo';
import { ChatInterface } from './components/ChatInterface';
import { SourcesPanel } from './components/SourcesPanel';
import { Header } from './components/Header';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [sources, setSources] = useState([]);
  const [ws, setWs] = useState(null);
  const [connected, setConnected] = useState(false);
  const [avatarSession, setAvatarSession] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Connect to WebSocket on mount
    connectWebSocket();

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws/chat';

    console.log('Connecting to WebSocket:', wsUrl);
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log('✅ WebSocket connected');
      setConnected(true);
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('WebSocket message:', data);

      switch (data.type) {
        case 'session_created':
          setAvatarSession(data);
          console.log('Avatar session created:', data.session_id);
          break;

        case 'answer':
          setMessages(prev => [...prev, {
            type: 'assistant',
            content: data.answer,
            timestamp: new Date()
          }]);
          setSources(data.sources || []);
          setLoading(false);
          break;

        case 'error':
          console.error('WebSocket error:', data.message);
          setMessages(prev => [...prev, {
            type: 'error',
            content: `Erreur: ${data.message}`,
            timestamp: new Date()
          }]);
          setLoading(false);
          break;

        default:
          console.log('Unknown message type:', data.type);
      }
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnected(false);
    };

    socket.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);

      // Reconnect after 3s
      setTimeout(() => {
        console.log('Attempting to reconnect...');
        connectWebSocket();
      }, 3000);
    };

    setWs(socket);
  };

  const sendMessage = (question, language = 'fr') => {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected');
      return;
    }

    setLoading(true);

    // Add user message to chat
    setMessages(prev => [...prev, {
      type: 'user',
      content: question,
      timestamp: new Date()
    }]);

    // Send to backend
    ws.send(JSON.stringify({
      question,
      language
    }));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
      <Header connected={connected} />

      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* Left Column: Avatar Video */}
          <div className="space-y-4">
            <AvatarVideo
              session={avatarSession}
              connected={connected}
            />

            {/* Sources Panel */}
            <SourcesPanel sources={sources} />
          </div>

          {/* Right Column: Chat Interface */}
          <div className="space-y-4">
            <ChatInterface
              messages={messages}
              onSendMessage={sendMessage}
              loading={loading}
              connected={connected}
            />
          </div>

        </div>
      </div>

      {/* Footer */}
      <footer className="mt-12 py-6 bg-white bg-opacity-70 backdrop-blur-sm">
        <div className="container mx-auto px-4 text-center text-gray-600">
          <p className="text-sm">
            Na Nach Nachma Nachman Meuman 🎉
          </p>
          <p className="text-xs mt-2">
            Powered by Claude AI, HeyGen & Sefaria.org
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
