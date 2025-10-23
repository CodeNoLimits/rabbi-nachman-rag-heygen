"""
Service HeyGen pour avatar streaming temps réel
"""

import os
from typing import Dict, Any, Optional
import httpx
from loguru import logger

from models import HeyGenSession


class HeyGenService:
    """Service pour intégration HeyGen Streaming API"""

    def __init__(self):
        self.api_key = os.getenv('HEYGEN_API_KEY')
        self.avatar_id = os.getenv('HEYGEN_AVATAR_ID')
        self.voice_id = os.getenv('HEYGEN_VOICE_ID', 'fr-FR-DeniseNeural')
        self.voice_rate = float(os.getenv('HEYGEN_VOICE_RATE', 1.0))
        self.emotion = os.getenv('HEYGEN_EMOTION', 'friendly')

        self.base_url = "https://api.heygen.com/v1/streaming"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        self.active_sessions: Dict[str, HeyGenSession] = {}

    async def create_session(self) -> Dict[str, Any]:
        """
        Créer une nouvelle session streaming avatar

        Returns:
            Dict contenant session_id, url, access_token
        """
        try:
            logger.info("🎬 Création d'une session HeyGen...")

            async with httpx.AsyncClient(timeout=30.0) as client:
                # 1. Create new session
                response = await client.post(
                    f"{self.base_url}.new",
                    headers=self.headers,
                    json={
                        "version": "v2",
                        "avatar_id": self.avatar_id,
                        "voice": {
                            "voice_id": self.voice_id,
                            "rate": self.voice_rate,
                            "emotion": self.emotion
                        },
                        "video_encoding": "H264",
                        "quality": "high"
                    }
                )

                response.raise_for_status()
                session_data = response.json()

                session_id = session_data['data']['session_id']
                logger.info(f"Session créée: {session_id}")

                # 2. Start session
                start_response = await client.post(
                    f"{self.base_url}.start",
                    headers=self.headers,
                    json={
                        "session_id": session_id
                    }
                )

                start_response.raise_for_status()
                start_data = start_response.json()

                # Extract LiveKit connection info
                session_info = {
                    "session_id": session_id,
                    "url": start_data['data']['url'],  # LiveKit URL
                    "access_token": start_data['data']['access_token'],
                    "avatar_id": self.avatar_id,
                    "voice_id": self.voice_id
                }

                # Store active session
                self.active_sessions[session_id] = HeyGenSession(**session_info)

                logger.info(f"✅ Session HeyGen démarrée: {session_id}")
                return session_info

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error creating session: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error creating HeyGen session: {e}")
            raise

    async def send_text(self, session_id: str, text: str) -> Dict[str, Any]:
        """
        Envoyer du texte à l'avatar pour qu'il parle

        Args:
            session_id: ID de la session
            text: Texte à faire dire par l'avatar

        Returns:
            Response data
        """
        try:
            if session_id not in self.active_sessions:
                raise ValueError(f"Session {session_id} not found")

            logger.info(f"📢 Envoi de texte à l'avatar: {text[:100]}...")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}.task",
                    headers=self.headers,
                    json={
                        "session_id": session_id,
                        "text": text,
                        "task_type": "talk"
                    }
                )

                response.raise_for_status()
                data = response.json()

                logger.info(f"✅ Texte envoyé à l'avatar")
                return data

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error sending text: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error sending text to avatar: {e}")
            raise

    async def send_task(
        self,
        session_id: str,
        task_type: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Envoyer une tâche personnalisée à l'avatar

        Args:
            session_id: ID de la session
            task_type: Type de tâche (talk, repeat, etc.)
            data: Données supplémentaires

        Returns:
            Response data
        """
        try:
            if session_id not in self.active_sessions:
                raise ValueError(f"Session {session_id} not found")

            payload = {
                "session_id": session_id,
                "task_type": task_type
            }

            if data:
                payload.update(data)

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}.task",
                    headers=self.headers,
                    json=payload
                )

                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Error sending task: {e}")
            raise

    async def close_session(self, session_id: str) -> None:
        """
        Fermer une session HeyGen

        Args:
            session_id: ID de la session à fermer
        """
        try:
            if session_id not in self.active_sessions:
                logger.warning(f"Session {session_id} not found in active sessions")
                return

            logger.info(f"🛑 Fermeture de la session: {session_id}")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}.stop",
                    headers=self.headers,
                    json={
                        "session_id": session_id
                    }
                )

                response.raise_for_status()

                # Remove from active sessions
                del self.active_sessions[session_id]

                logger.info(f"✅ Session fermée: {session_id}")

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error closing session: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error closing session: {e}")

    async def get_session_info(self, session_id: str) -> Optional[HeyGenSession]:
        """
        Obtenir les infos d'une session active

        Args:
            session_id: ID de la session

        Returns:
            HeyGenSession ou None
        """
        return self.active_sessions.get(session_id)

    async def list_active_sessions(self) -> Dict[str, HeyGenSession]:
        """Lister toutes les sessions actives"""
        return self.active_sessions.copy()

    async def cleanup_all_sessions(self) -> None:
        """Fermer toutes les sessions actives (pour cleanup)"""
        logger.info(f"🧹 Nettoyage de {len(self.active_sessions)} sessions...")

        for session_id in list(self.active_sessions.keys()):
            await self.close_session(session_id)

        logger.info("✅ Toutes les sessions fermées")
