import React from 'react';
import Markdown from 'markdown-to-jsx';

export function ChatMessage({ message }) {
  const isUser = message.type === 'user';
  const isError = message.type === 'error';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
        isUser
          ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white'
          : isError
          ? 'bg-red-100 text-red-800 border border-red-300'
          : 'bg-white border border-gray-200 text-gray-800'
      }`}>
        {/* Content */}
        <div className={`text-sm ${isUser ? 'text-white' : ''}`}>
          {isUser ? (
            <p>{message.content}</p>
          ) : (
            <Markdown>{message.content}</Markdown>
          )}
        </div>

        {/* Timestamp */}
        <div className={`text-xs mt-2 ${
          isUser ? 'text-purple-100' : 'text-gray-400'
        }`}>
          {message.timestamp.toLocaleTimeString('fr-FR', {
            hour: '2-digit',
            minute: '2-digit'
          })}
        </div>
      </div>
    </div>
  );
}
