"""
Service de chunking sémantique optimisé pour textes religieux
"""

import os
from typing import List, Dict, Any
from loguru import logger

from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.core.schema import Document, TextNode
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from models import SefariaText, ChunkMetadata


class SemanticChunker:
    """Chunker sémantique pour textes Torah/Breslov"""

    def __init__(self):
        self.chunk_size = int(os.getenv('CHUNK_SIZE', 800))
        self.chunk_overlap = int(os.getenv('CHUNK_OVERLAP', 200))

        # Initialize embedding model for semantic chunking
        logger.info("Initialisation du modèle d'embedding pour chunking...")
        self.embed_model = HuggingFaceEmbedding(
            model_name=os.getenv('EMBEDDING_MODEL', 'BAAI/bge-base-en-v1.5'),
            cache_folder="./model_cache"
        )

        # Create semantic splitter
        self.splitter = SemanticSplitterNodeParser(
            buffer_size=3,  # Contexte de 3 phrases avant/après
            breakpoint_percentile_threshold=85,  # Seuil élevé pour cohérence
            embed_model=self.embed_model
        )

        logger.info(f"✅ Chunker initialisé (size={self.chunk_size}, overlap={self.chunk_overlap})")

    def chunk_sefaria_text(
        self,
        text: SefariaText,
        preserve_structure: bool = True
    ) -> List[TextNode]:
        """
        Chunker un texte Sefaria avec préservation de la structure

        Args:
            text: SefariaText à chunker
            preserve_structure: Préserver les paraboles/citations complètes

        Returns:
            Liste de TextNode avec métadonnées
        """
        try:
            # Prepare text content
            content = self._prepare_content(text)

            if not content or len(content.strip()) < 50:
                logger.warning(f"Texte trop court ignoré: {text.ref}")
                return []

            # Create document
            doc = Document(
                text=content,
                metadata={
                    'book': text.title,
                    'ref': text.ref,
                    'language': text.language,
                    'source_url': f"https://www.sefaria.org/{text.ref}",
                    'version': text.versionTitle or 'default'
                }
            )

            # Apply semantic chunking
            nodes = self.splitter.get_nodes_from_documents([doc])

            # Enhance metadata for each chunk
            for i, node in enumerate(nodes):
                node.metadata.update({
                    'chunk_index': i,
                    'total_chunks': len(nodes),
                    'book': text.title,
                    'ref': text.ref,
                    'language': text.language
                })

                # Extract chapter/verse from ref
                self._extract_ref_parts(node, text.ref)

            logger.debug(f"Chunked {text.ref}: {len(nodes)} chunks")
            return nodes

        except Exception as e:
            logger.error(f"Error chunking {text.ref}: {e}")
            return []

    def _prepare_content(self, text: SefariaText) -> str:
        """Préparer le contenu pour chunking"""
        # Combine Hebrew and English if both available
        if text.hebrew and text.text:
            # Bilingual format
            return f"{text.hebrew}\n\n{text.text}"
        elif text.hebrew:
            return text.hebrew
        elif text.text:
            return text.text
        return ""

    def _extract_ref_parts(self, node: TextNode, ref: str) -> None:
        """Extraire chapter/verse de la référence"""
        try:
            # Format: "Book.Chapter" ou "Book.Chapter:Verse"
            parts = ref.split('.')
            if len(parts) >= 2:
                chapter_part = parts[1].split(':')
                node.metadata['chapter'] = chapter_part[0]

                if len(chapter_part) > 1:
                    node.metadata['verse'] = chapter_part[1]

        except Exception as e:
            logger.debug(f"Could not extract ref parts from {ref}: {e}")

    def chunk_batch(
        self,
        texts: List[SefariaText],
        progress_callback=None
    ) -> List[TextNode]:
        """
        Chunker un batch de textes

        Args:
            texts: Liste de SefariaText
            progress_callback: Fonction appelée avec (current, total)

        Returns:
            Liste de tous les TextNode
        """
        all_nodes = []
        total = len(texts)

        logger.info(f"Chunking {total} textes...")

        for i, text in enumerate(texts):
            nodes = self.chunk_sefaria_text(text)
            all_nodes.extend(nodes)

            if progress_callback:
                progress_callback(i + 1, total)

            if (i + 1) % 50 == 0:
                logger.info(f"  Progression: {i+1}/{total} textes ({len(all_nodes)} chunks)")

        logger.info(f"✅ Chunking terminé: {len(all_nodes)} chunks créés")
        return all_nodes

    def optimize_chunks_for_rag(self, nodes: List[TextNode]) -> List[TextNode]:
        """
        Optimiser les chunks pour RAG

        Règles:
        1. Supprimer chunks trop courts (< 100 chars)
        2. Fusionner chunks très similaires
        3. Ajouter contexte si nécessaire
        """
        optimized = []

        for node in nodes:
            text = node.text.strip()

            # Skip too short chunks
            if len(text) < 100:
                logger.debug(f"Chunk trop court ignoré: {len(text)} chars")
                continue

            # Add contextual prefix based on book type
            node.text = self._add_context_prefix(node)

            optimized.append(node)

        logger.info(f"Optimisation: {len(nodes)} → {len(optimized)} chunks")
        return optimized

    def _add_context_prefix(self, node: TextNode) -> str:
        """Ajouter un préfixe contextuel au chunk"""
        book = node.metadata.get('book', '')
        chapter = node.metadata.get('chapter', '')
        verse = node.metadata.get('verse', '')

        # Construct reference
        ref_parts = [book]
        if chapter:
            ref_parts.append(f"chapitre {chapter}")
        if verse:
            ref_parts.append(f"verset {verse}")

        prefix = " - ".join(ref_parts)

        # Add prefix to text
        return f"[{prefix}]\n\n{node.text}"

    def get_chunk_stats(self, nodes: List[TextNode]) -> Dict[str, Any]:
        """Obtenir des statistiques sur les chunks"""
        if not nodes:
            return {}

        chunk_lengths = [len(node.text) for node in nodes]
        books = {}

        for node in nodes:
            book = node.metadata.get('book', 'Unknown')
            books[book] = books.get(book, 0) + 1

        return {
            'total_chunks': len(nodes),
            'avg_length': sum(chunk_lengths) / len(chunk_lengths),
            'min_length': min(chunk_lengths),
            'max_length': max(chunk_lengths),
            'books': books
        }
