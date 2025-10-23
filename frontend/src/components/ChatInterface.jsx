import React, { useState, useRef, useEffect } from 'react';
import { PaperAirplaneIcon } from '@heroicons/react/24/solid';
import { ChatMessage } from './ChatMessage';

export function ChatInterface({ messages, onSendMessage, loading, connected }) {
  const [input, setInput] = useState('');
  const [language, setLanguage] = useState('fr');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!input.trim() || !connected || loading) {
      return;
    }

    onSendMessage(input, language);
    setInput('');
  };

  const quickQuestions = [
    { text: "Que dit Rabbi Nachman sur la joie?", lang: "fr" },
    { text: "Qu'est-ce que le Hitbodedut?", lang: "fr" },
    { text: "Parle-moi du Tikun Haklali", lang: "fr" }
  ];

  return (
    <div className="bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col h-[600px]">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-pink-600 px-6 py-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-white">
            💬 Conversation
          </h2>

          {/* Language selector */}
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="bg-white bg-opacity-20 text-white rounded-lg px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-white"
          >
            <option value="fr">🇫🇷 Français</option>
            <option value="he">🇮🇱 עברית</option>
            <option value="en">🇬🇧 English</option>
          </select>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-gray-50">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🕎</div>
            <h3 className="text-xl font-semibold text-gray-700 mb-2">
              Bienvenue!
            </h3>
            <p className="text-gray-500 mb-6">
              Posez une question sur les enseignements de Rabbi Nachman
            </p>

            {/* Quick Questions */}
            <div className="space-y-2">
              <p className="text-sm font-medium text-gray-600 mb-3">
                Questions rapides:
              </p>
              {quickQuestions.map((q, i) => (
                <button
                  key={i}
                  onClick={() => onSendMessage(q.text, q.lang)}
                  disabled={!connected || loading}
                  className="block w-full text-left px-4 py-3 bg-white rounded-lg hover:bg-purple-50 hover:border-purple-300 border border-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span className="text-sm text-gray-700">{q.text}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <ChatMessage key={i} message={msg} />
        ))}

        {loading && (
          <div className="flex items-center space-x-2 text-gray-500">
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
            <span className="text-sm">Rabbi Nachman réfléchit...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 p-4 bg-white">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={connected ? "Posez votre question..." : "Connexion..."}
            disabled={!connected || loading}
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={!connected || loading || !input.trim()}
            className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            <PaperAirplaneIcon className="w-5 h-5" />
            <span>Envoyer</span>
          </button>
        </form>

        {!connected && (
          <p className="text-xs text-red-500 mt-2 text-center">
            ⚠️ Connexion au serveur perdue. Reconnexion...
          </p>
        )}
      </div>
    </div>
  );
}
