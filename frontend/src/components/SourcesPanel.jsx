import React, { useState } from 'react';
import { ChevronDownIcon, ChevronUpIcon, BookOpenIcon } from '@heroicons/react/24/outline';

export function SourcesPanel({ sources }) {
  const [expanded, setExpanded] = useState(false);

  if (!sources || sources.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-6 py-4 bg-gradient-to-r from-green-500 to-teal-500 flex items-center justify-between hover:from-green-600 hover:to-teal-600 transition-colors"
      >
        <div className="flex items-center space-x-2 text-white">
          <BookOpenIcon className="w-5 h-5" />
          <h3 className="font-semibold">
            Sources ({sources.length})
          </h3>
        </div>
        {expanded ? (
          <ChevronUpIcon className="w-5 h-5 text-white" />
        ) : (
          <ChevronDownIcon className="w-5 h-5 text-white" />
        )}
      </button>

      {/* Sources List */}
      {expanded && (
        <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
          {sources.map((source, i) => (
            <SourceCard key={i} source={source} index={i + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

function SourceCard({ source, index }) {
  const [showFull, setShowFull] = useState(false);

  const text = source.text || '';
  const shortText = text.length > 200 ? text.substring(0, 200) + '...' : text;

  return (
    <div className="border border-gray-200 rounded-lg p-4 bg-gray-50 hover:bg-gray-100 transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-1">
            <span className="text-xs font-bold text-white bg-green-500 rounded-full w-6 h-6 flex items-center justify-center">
              {index}
            </span>
            <h4 className="font-semibold text-gray-800">
              {source.book}
            </h4>
          </div>

          {/* Reference */}
          <div className="flex items-center space-x-2 text-xs text-gray-600">
            {source.chapter && (
              <span>Chapitre {source.chapter}</span>
            )}
            {source.verse && (
              <span>• Verset {source.verse}</span>
            )}
          </div>
        </div>

        {/* Score */}
        <div className="flex flex-col items-end">
          <span className="text-xs text-gray-500 mb-1">Pertinence</span>
          <div className="flex items-center space-x-1">
            {[...Array(5)].map((_, i) => (
              <div
                key={i}
                className={`w-2 h-2 rounded-full ${
                  i < Math.round(source.score * 5)
                    ? 'bg-green-500'
                    : 'bg-gray-300'
                }`}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Text */}
      <div className="mt-3">
        <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
          {showFull ? text : shortText}
        </p>

        {text.length > 200 && (
          <button
            onClick={() => setShowFull(!showFull)}
            className="text-xs text-green-600 hover:text-green-700 font-medium mt-2"
          >
            {showFull ? 'Voir moins' : 'Voir plus'}
          </button>
        )}
      </div>

      {/* Footer */}
      <div className="mt-3 pt-3 border-t border-gray-200 flex items-center justify-between">
        <span className="text-xs text-gray-500">
          {source.language === 'he' ? '🇮🇱 Hébreu' : source.language === 'fr' ? '🇫🇷 Français' : '🇬🇧 Anglais'}
        </span>

        {source.metadata && source.metadata.source_url && (
          <a
            href={source.metadata.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-green-600 hover:text-green-700 hover:underline"
          >
            Voir sur Sefaria →
          </a>
        )}
      </div>
    </div>
  );
}
