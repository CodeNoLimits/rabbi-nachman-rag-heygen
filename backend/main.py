"""
FastAPI Backend pour RAG Rabbi Nachman avec HeyGen Avatar
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import List, Optional
import os
from dotenv import load_dotenv
from loguru import logger

from services.rag_engine import RAGEngine
from services.heygen import HeyGenService
from models import QueryRequest, QueryResponse, HealthResponse
from utils.rate_limiter import RateLimiter

# Load environment variables
load_dotenv()

# Initialize services
rag_engine: Optional[RAGEngine] = None
heygen_service: Optional[HeyGenService] = None
rate_limiter = RateLimiter(
    per_minute=int(os.getenv('RATE_LIMIT_PER_MINUTE', 30)),
    per_hour=int(os.getenv('RATE_LIMIT_PER_HOUR', 500))
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager pour l'application"""
    global rag_engine, heygen_service

    logger.info("🚀 Démarrage de l'application RAG Rabbi Nachman")

    # Initialize RAG Engine
    logger.info("Initialisation du RAG Engine...")
    rag_engine = RAGEngine()
    await rag_engine.initialize()

    # Initialize HeyGen Service
    logger.info("Initialisation du service HeyGen...")
    heygen_service = HeyGenService()

    logger.info("✅ Application prête!")

    yield

    # Cleanup
    logger.info("🛑 Arrêt de l'application")
    if rag_engine:
        await rag_engine.cleanup()


# Create FastAPI app
app = FastAPI(
    title="RAG Rabbi Nachman API",
    description="API pour système RAG avec avatar HeyGen",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=dict)
async def root():
    """Root endpoint"""
    return {
        "message": "RAG Rabbi Nachman API",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        rag_engine_ready=rag_engine is not None and rag_engine.is_ready(),
        heygen_ready=heygen_service is not None,
        environment=os.getenv('ENVIRONMENT', 'development')
    )


@app.post("/api/query", response_model=QueryResponse)
async def query_rag(
    request: QueryRequest,
    client_id: str = Depends(rate_limiter.check_rate_limit)
):
    """
    Query endpoint pour RAG

    Args:
        request: Question et paramètres

    Returns:
        QueryResponse avec réponse et sources
    """
    if not rag_engine or not rag_engine.is_ready():
        raise HTTPException(status_code=503, detail="RAG engine not ready")

    try:
        logger.info(f"Query: {request.question[:100]}...")

        # Perform RAG query
        result = await rag_engine.query(
            question=request.question,
            language=request.language,
            top_k=request.top_k
        )

        return QueryResponse(
            answer=result['answer'],
            sources=result['sources'],
            metadata=result.get('metadata', {})
        )

    except Exception as e:
        logger.error(f"Error in query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint pour chat temps réel avec avatar HeyGen
    """
    await websocket.accept()

    # Create HeyGen session
    try:
        session = await heygen_service.create_session()
        await websocket.send_json({
            "type": "session_created",
            "session_url": session['url'],
            "access_token": session['access_token'],
            "session_id": session['session_id']
        })

        logger.info(f"WebSocket session créée: {session['session_id']}")

        while True:
            # Receive message
            data = await websocket.receive_json()
            question = data.get('question')
            language = data.get('language', 'fr')

            if not question:
                continue

            logger.info(f"WS Query: {question[:100]}...")

            # RAG query
            result = await rag_engine.query(
                question=question,
                language=language,
                top_k=10
            )

            # Send answer to HeyGen for TTS + Avatar
            await heygen_service.send_text(
                session_id=session['session_id'],
                text=result['answer']
            )

            # Send response to client
            await websocket.send_json({
                "type": "answer",
                "answer": result['answer'],
                "sources": result['sources'][:3],  # Top 3 sources
                "metadata": result.get('metadata', {})
            })

    except WebSocketDisconnect:
        logger.info("WebSocket déconnecté")
        if session:
            await heygen_service.close_session(session['session_id'])

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
        if session:
            await heygen_service.close_session(session['session_id'])


@app.get("/api/books", response_model=List[dict])
async def list_books():
    """Liste tous les livres disponibles dans la base"""
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG engine not ready")

    return await rag_engine.list_books()


@app.get("/api/stats", response_model=dict)
async def get_stats():
    """Statistiques de la base de données"""
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG engine not ready")

    return await rag_engine.get_stats()


@app.post("/api/admin/reindex", response_model=dict)
async def trigger_reindex():
    """
    Déclencher une réindexation complète
    NOTE: Endpoint admin - devrait être protégé en production
    """
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG engine not ready")

    try:
        result = await rag_engine.reindex()
        return {"status": "success", "message": "Réindexation démarrée", "result": result}
    except Exception as e:
        logger.error(f"Reindex error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv('BACKEND_PORT', 8000))

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv('ENVIRONMENT') == 'development',
        log_level=os.getenv('LOG_LEVEL', 'info').lower()
    )
