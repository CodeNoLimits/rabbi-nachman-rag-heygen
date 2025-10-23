import React from 'react';

export function Header({ connected }) {
  return (
    <header className="bg-white bg-opacity-80 backdrop-blur-md shadow-lg sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo & Title */}
          <div className="flex items-center space-x-4">
            <div className="text-4xl">🕎</div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                Rabbi Nachman RAG
              </h1>
              <p className="text-sm text-gray-600">
                Enseignements avec avatar IA temps réel
              </p>
            </div>
          </div>

          {/* Status */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <span className={`w-3 h-3 rounded-full ${connected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></span>
              <span className="text-sm text-gray-600">
                {connected ? 'Connecté' : 'Déconnecté'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
