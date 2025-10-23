"""
RAG Engine avec LlamaIndex et ChromaDB
"""

import os
from typing import List, Dict, Any, Optional
from loguru import logger
import asyncio

from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.anthropic import Anthropic
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SemanticSplitterNodeParser
import chromadb
from chromadb.config import Settings as ChromaSettings

from models import SourceDocument


class RAGEngine:
    """Engine RAG complet avec LlamaIndex + ChromaDB"""

    def __init__(self):
        self.chroma_client: Optional[chromadb.ClientAPI] = None
        self.collection = None
        self.index: Optional[VectorStoreIndex] = None
        self.query_engine = None
        self.embed_model: Optional[HuggingFaceEmbedding] = None
        self.llm: Optional[Anthropic] = None
        self._ready = False

        # Configuration
        self.collection_name = os.getenv('CHROMA_COLLECTION_NAME', 'rabbi_nachman')
        self.embedding_model_name = os.getenv('EMBEDDING_MODEL', 'BAAI/bge-base-en-v1.5')
        self.llm_model = os.getenv('LLM_MODEL', 'claude-3-5-sonnet-20241022')

    async def initialize(self):
        """Initialiser tous les composants"""
        try:
            logger.info("🔧 Initialisation du RAG Engine...")

            # 1. Initialize embedding model
            logger.info(f"Chargement du modèle d'embedding: {self.embedding_model_name}")
            self.embed_model = HuggingFaceEmbedding(
                model_name=self.embedding_model_name,
                cache_folder="./model_cache"
            )

            # 2. Initialize LLM
            logger.info(f"Configuration du LLM: {self.llm_model}")
            self.llm = Anthropic(
                api_key=os.getenv('ANTHROPIC_API_KEY'),
                model=self.llm_model,
                temperature=0.7,
                max_tokens=4096
            )

            # Set global settings for LlamaIndex
            Settings.embed_model = self.embed_model
            Settings.llm = self.llm
            Settings.chunk_size = int(os.getenv('CHUNK_SIZE', 800))
            Settings.chunk_overlap = int(os.getenv('CHUNK_OVERLAP', 200))

            # 3. Initialize ChromaDB
            await self._init_chromadb()

            # 4. Create/load index
            await self._init_index()

            self._ready = True
            logger.info("✅ RAG Engine initialisé avec succès")

        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation: {e}")
            raise

    async def _init_chromadb(self):
        """Initialiser la connexion ChromaDB"""
        chroma_host = os.getenv('CHROMA_HOST', 'localhost')
        chroma_port = int(os.getenv('CHROMA_PORT', 8001))
        persist_dir = os.getenv('CHROMA_PERSIST_DIRECTORY', './chroma_data')

        logger.info(f"Connexion à ChromaDB: {chroma_host}:{chroma_port}")

        try:
            # Try HTTP client first (for Cloud Run)
            if chroma_host != 'localhost':
                self.chroma_client = chromadb.HttpClient(
                    host=chroma_host,
                    port=chroma_port,
                    ssl=True,
                    headers={"Authorization": f"Bearer {os.getenv('CHROMA_AUTH_TOKEN', '')}"}
                )
            else:
                # Local persistent client
                self.chroma_client = chromadb.PersistentClient(
                    path=persist_dir,
                    settings=ChromaSettings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )

            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Enseignements de Rabbi Nachman de Breslov"}
            )

            logger.info(f"✅ Collection '{self.collection_name}' chargée")
            logger.info(f"   Nombre de documents: {self.collection.count()}")

        except Exception as e:
            logger.error(f"Erreur ChromaDB: {e}")
            raise

    async def _init_index(self):
        """Initialiser l'index LlamaIndex"""
        try:
            # Create vector store from ChromaDB collection
            vector_store = ChromaVectorStore(
                chroma_collection=self.collection
            )

            # Create storage context
            storage_context = StorageContext.from_defaults(
                vector_store=vector_store
            )

            # Check if index already exists
            if self.collection.count() > 0:
                logger.info("Chargement de l'index existant...")
                self.index = VectorStoreIndex.from_vector_store(
                    vector_store=vector_store,
                    storage_context=storage_context
                )
            else:
                logger.info("Index vide - utilisez le script d'ingestion pour le remplir")
                self.index = VectorStoreIndex.from_documents(
                    [],
                    storage_context=storage_context
                )

            # Create query engine
            self.query_engine = self.index.as_query_engine(
                similarity_top_k=int(os.getenv('TOP_K_RETRIEVAL', 10)),
                response_mode="compact",
                use_async=True,
                streaming=False
            )

            logger.info("✅ Index LlamaIndex créé")

        except Exception as e:
            logger.error(f"Erreur lors de la création de l'index: {e}")
            raise

    async def query(
        self,
        question: str,
        language: str = "fr",
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        Effectuer une requête RAG

        Args:
            question: Question de l'utilisateur
            language: Langue de réponse (fr, he, en)
            top_k: Nombre de chunks à récupérer

        Returns:
            Dict avec answer, sources, metadata
        """
        if not self._ready:
            raise RuntimeError("RAG Engine not initialized")

        try:
            import time
            start_time = time.time()

            # Prepare query with language instruction
            language_names = {"fr": "français", "he": "hébreu", "en": "anglais"}
            lang_instruction = f"\n\nRéponds en {language_names.get(language, 'français')}."

            enhanced_query = f"{question}{lang_instruction}"

            # Query the engine
            logger.info(f"Querying: {question[:100]}...")
            response = await asyncio.to_thread(
                self.query_engine.query,
                enhanced_query
            )

            # Extract sources
            sources = []
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes[:top_k]:
                    metadata = node.node.metadata or {}
                    sources.append(SourceDocument(
                        book=metadata.get('book', 'Unknown'),
                        chapter=metadata.get('chapter'),
                        verse=metadata.get('verse'),
                        text=node.node.text[:500],  # Limit text length
                        score=float(node.score) if hasattr(node, 'score') else 0.0,
                        language=metadata.get('language', language),
                        metadata=metadata
                    ))

            query_time = time.time() - start_time

            result = {
                'answer': str(response),
                'sources': [s.model_dump() for s in sources],
                'metadata': {
                    'query_time': round(query_time, 2),
                    'chunks_retrieved': len(sources),
                    'language': language
                }
            }

            logger.info(f"✅ Query completed in {query_time:.2f}s")
            return result

        except Exception as e:
            logger.error(f"Query error: {e}")
            raise

    async def list_books(self) -> List[Dict[str, Any]]:
        """Lister tous les livres dans la base"""
        try:
            # Query ChromaDB for unique books
            results = self.collection.get(
                include=['metadatas']
            )

            books = {}
            if results and results['metadatas']:
                for metadata in results['metadatas']:
                    book_name = metadata.get('book', 'Unknown')
                    if book_name not in books:
                        books[book_name] = {
                            'title': book_name,
                            'slug': book_name.lower().replace(' ', '_'),
                            'languages': set(),
                            'chapters': set()
                        }

                    if 'language' in metadata:
                        books[book_name]['languages'].add(metadata['language'])
                    if 'chapter' in metadata:
                        books[book_name]['chapters'].add(metadata['chapter'])

            # Convert sets to lists
            result = []
            for book in books.values():
                result.append({
                    'title': book['title'],
                    'slug': book['slug'],
                    'languages': list(book['languages']),
                    'num_chapters': len(book['chapters']),
                })

            return result

        except Exception as e:
            logger.error(f"Error listing books: {e}")
            return []

    async def get_stats(self) -> Dict[str, Any]:
        """Obtenir des statistiques sur la base"""
        try:
            total_docs = self.collection.count()

            # Get sample metadata to analyze
            sample = self.collection.get(limit=1000, include=['metadatas'])

            languages = set()
            books = set()

            if sample and sample['metadatas']:
                for metadata in sample['metadatas']:
                    if 'language' in metadata:
                        languages.add(metadata['language'])
                    if 'book' in metadata:
                        books.add(metadata['book'])

            return {
                'total_documents': total_docs,
                'total_books': len(books),
                'languages': list(languages),
                'books': list(books),
                'embedding_model': self.embedding_model_name,
                'llm_model': self.llm_model
            }

        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}

    async def reindex(self) -> Dict[str, Any]:
        """Réindexer toute la base (admin only)"""
        logger.warning("⚠️ Réindexation demandée - opération lourde!")
        # This would typically trigger the ingestion script
        return {"status": "reindexing", "message": "Utilisez le script d'ingestion"}

    def is_ready(self) -> bool:
        """Vérifier si le RAG engine est prêt"""
        return self._ready

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up RAG Engine...")
        # No explicit cleanup needed for ChromaDB client
        self._ready = False
