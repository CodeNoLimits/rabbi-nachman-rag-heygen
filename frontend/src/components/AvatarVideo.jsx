import React, { useEffect, useRef, useState } from 'react';
import { Room } from 'livekit-client';

export function AvatarVideo({ session, connected }) {
  const videoRef = useRef(null);
  const audioRef = useRef(null);
  const [room, setRoom] = useState(null);
  const [avatarConnected, setAvatarConnected] = useState(false);

  useEffect(() => {
    if (!session || !session.url || !session.access_token) {
      return;
    }

    connectToAvatar();

    return () => {
      if (room) {
        room.disconnect();
      }
    };
  }, [session]);

  const connectToAvatar = async () => {
    try {
      console.log('Connecting to avatar session...');

      const newRoom = new Room();

      // Handle track subscribed (video/audio from avatar)
      newRoom.on('trackSubscribed', (track, publication, participant) => {
        console.log('Track subscribed:', track.kind);

        if (track.kind === 'video' && videoRef.current) {
          track.attach(videoRef.current);
        } else if (track.kind === 'audio' && audioRef.current) {
          track.attach(audioRef.current);
        }
      });

      // Handle disconnection
      newRoom.on('disconnected', () => {
        console.log('Avatar disconnected');
        setAvatarConnected(false);
      });

      // Connect to LiveKit room
      await newRoom.connect(session.url, session.access_token);

      console.log('✅ Connected to avatar room');
      setRoom(newRoom);
      setAvatarConnected(true);

    } catch (error) {
      console.error('Error connecting to avatar:', error);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-white">
            🕎 Rabbi Nachman Avatar
          </h2>
          <div className="flex items-center space-x-2">
            <span className={`w-3 h-3 rounded-full ${avatarConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}></span>
            <span className="text-white text-sm">
              {avatarConnected ? 'Connecté' : 'En attente...'}
            </span>
          </div>
        </div>
      </div>

      {/* Video Container */}
      <div className="relative bg-gray-900 aspect-video">
        {!avatarConnected && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4">
                <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-white"></div>
              </div>
              <p className="text-white text-lg">
                Connexion à l'avatar...
              </p>
            </div>
          </div>
        )}

        {/* Video element */}
        <video
          ref={videoRef}
          autoPlay
          playsInline
          className="w-full h-full object-cover"
        />

        {/* Audio element */}
        <audio
          ref={audioRef}
          autoPlay
        />
      </div>

      {/* Footer */}
      <div className="px-6 py-3 bg-gray-50 border-t border-gray-200">
        <p className="text-sm text-gray-600 text-center">
          {session && session.session_id
            ? `Session: ${session.session_id.substring(0, 8)}...`
            : 'En attente de connexion...'}
        </p>
      </div>
    </div>
  );
}
