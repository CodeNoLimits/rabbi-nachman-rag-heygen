"""
Pydantic models pour l'API
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class Language(str, Enum):
    """Langues supportées"""
    HEBREW = "he"
    FRENCH = "fr"
    ENGLISH = "en"


class QueryRequest(BaseModel):
    """Request model pour query endpoint"""
    question: str = Field(..., min_length=1, max_length=1000, description="Question de l'utilisateur")
    language: Language = Field(default=Language.FRENCH, description="Langue de réponse")
    top_k: int = Field(default=10, ge=1, le=50, description="Nombre de chunks à récupérer")

    class Config:
        json_schema_extra = {
            "example": {
                "question": "Que dit Rabbi Nachman sur la joie?",
                "language": "fr",
                "top_k": 10
            }
        }


class SourceDocument(BaseModel):
    """Modèle pour un document source"""
    book: str = Field(..., description="Nom du livre")
    chapter: Optional[str] = Field(None, description="Chapitre")
    verse: Optional[str] = Field(None, description="Verset")
    text: str = Field(..., description="Texte du passage")
    score: float = Field(..., ge=0, le=1, description="Score de similarité")
    language: str = Field(..., description="Langue du texte")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Métadonnées supplémentaires")


class QueryResponse(BaseModel):
    """Response model pour query endpoint"""
    answer: str = Field(..., description="Réponse générée")
    sources: List[SourceDocument] = Field(..., description="Documents sources utilisés")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Métadonnées de la requête")

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Rabbi Nachman enseigne que la joie est essentielle...",
                "sources": [
                    {
                        "book": "Likutei Moharan",
                        "chapter": "24",
                        "verse": "1",
                        "text": "Il faut toujours se réjouir...",
                        "score": 0.92,
                        "language": "fr",
                        "metadata": {}
                    }
                ],
                "metadata": {
                    "query_time": 2.3,
                    "chunks_retrieved": 10
                }
            }
        }


class HealthResponse(BaseModel):
    """Response model pour health check"""
    status: str = Field(..., description="Statut global")
    rag_engine_ready: bool = Field(..., description="RAG engine initialisé")
    heygen_ready: bool = Field(..., description="Service HeyGen prêt")
    environment: str = Field(..., description="Environment (dev/prod)")


class Book(BaseModel):
    """Modèle pour un livre"""
    title: str
    title_hebrew: Optional[str] = None
    slug: str
    category: str
    num_chapters: int
    num_verses: int
    languages: List[str] = Field(default_factory=list)


class WebSocketMessage(BaseModel):
    """Modèle pour messages WebSocket"""
    type: str = Field(..., description="Type de message")
    data: Dict[str, Any] = Field(default_factory=dict, description="Données du message")


class HeyGenSession(BaseModel):
    """Modèle pour session HeyGen"""
    session_id: str
    url: str
    access_token: str
    avatar_id: str
    voice_id: str


class ChunkMetadata(BaseModel):
    """Métadonnées pour un chunk de texte"""
    book: str
    chapter: Optional[str] = None
    verse: Optional[str] = None
    language: str
    chunk_index: int
    total_chunks: int
    source_url: Optional[str] = None


class SefariaText(BaseModel):
    """Modèle pour texte Sefaria"""
    title: str
    ref: str
    hebrew: str
    text: str
    language: str = "he"
    versionTitle: Optional[str] = None
    versionSource: Optional[str] = None
