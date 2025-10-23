#!/usr/bin/env python3
"""
Script d'ingestion des textes Sefaria dans ChromaDB

Usage:
    python scripts/ingest_sefaria.py --all
    python scripts/ingest_sefaria.py --book Likutei_Moharan
    python scripts/ingest_sefaria.py --books Likutei_Moharan,Sichot_HaRan
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path
from loguru import logger
from tqdm import tqdm

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from services.sefaria import SefariaService
from services.chunker import SemanticChunker
import chromadb
from chromadb.config import Settings as ChromaSettings


async def ingest_books(
    books: list = None,
    languages: list = None,
    reset: bool = False
):
    """
    Ingérer les livres dans ChromaDB

    Args:
        books: Liste des livres à ingérer (None = tous)
        languages: Langues à récupérer
        reset: Reset la collection avant ingestion
    """
    logger.info("🚀 Démarrage de l'ingestion Sefaria → ChromaDB")

    # 1. Initialize services
    logger.info("Initialisation des services...")
    sefaria = SefariaService()
    chunker = SemanticChunker()

    # 2. Initialize ChromaDB
    persist_dir = os.getenv('CHROMA_PERSIST_DIRECTORY', './chroma_data')
    collection_name = os.getenv('CHROMA_COLLECTION_NAME', 'rabbi_nachman')

    logger.info(f"Connexion à ChromaDB: {persist_dir}")
    client = chromadb.PersistentClient(
        path=persist_dir,
        settings=ChromaSettings(
            anonymized_telemetry=False,
            allow_reset=True
        )
    )

    # Reset collection if requested
    if reset:
        logger.warning("⚠️ Reset de la collection demandé")
        try:
            client.delete_collection(name=collection_name)
            logger.info("Collection supprimée")
        except:
            pass

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"description": "Enseignements de Rabbi Nachman de Breslov"}
    )

    logger.info(f"Collection: {collection_name}")
    logger.info(f"Documents existants: {collection.count()}")

    # 3. Fetch texts from Sefaria
    logger.info("\n📖 Récupération des textes depuis Sefaria...")
    all_books = await sefaria.fetch_all_rabbi_nachman(books, languages)

    total_texts = sum(len(texts) for texts in all_books.values())
    logger.info(f"✅ {total_texts} textes récupérés")

    # 4. Chunk all texts
    logger.info("\n✂️  Chunking sémantique...")
    all_chunks = []

    with tqdm(total=total_texts, desc="Chunking") as pbar:
        for book_slug, texts in all_books.items():
            if not texts:
                continue

            logger.info(f"  Chunking {book_slug}: {len(texts)} textes")

            chunks = chunker.chunk_batch(
                texts,
                progress_callback=lambda c, t: pbar.update(1)
            )

            all_chunks.extend(chunks)

    logger.info(f"✅ {len(all_chunks)} chunks créés")

    # 5. Optimize chunks
    logger.info("\n⚙️  Optimisation des chunks pour RAG...")
    optimized_chunks = chunker.optimize_chunks_for_rag(all_chunks)

    # Stats
    stats = chunker.get_chunk_stats(optimized_chunks)
    logger.info("📊 Statistiques des chunks:")
    logger.info(f"   Total: {stats['total_chunks']}")
    logger.info(f"   Longueur moyenne: {stats['avg_length']:.0f} chars")
    logger.info(f"   Min: {stats['min_length']}, Max: {stats['max_length']}")
    logger.info(f"   Livres: {len(stats['books'])}")

    # 6. Insert into ChromaDB
    logger.info("\n💾 Insertion dans ChromaDB...")

    batch_size = 100
    total_batches = (len(optimized_chunks) + batch_size - 1) // batch_size

    with tqdm(total=len(optimized_chunks), desc="Insertion") as pbar:
        for i in range(0, len(optimized_chunks), batch_size):
            batch = optimized_chunks[i:i+batch_size]

            # Prepare batch data
            ids = [f"chunk_{i+j}" for j in range(len(batch))]
            documents = [node.text for node in batch]
            metadatas = [node.metadata for node in batch]

            # Insert batch
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )

            pbar.update(len(batch))

    logger.info(f"✅ {len(optimized_chunks)} chunks insérés")
    logger.info(f"📊 Total documents dans ChromaDB: {collection.count()}")

    # 7. Verification
    logger.info("\n✅ Vérification...")
    sample = collection.get(limit=3, include=['documents', 'metadatas'])

    if sample and sample['documents']:
        logger.info("Exemple de chunks stockés:")
        for i, (doc, meta) in enumerate(zip(sample['documents'], sample['metadatas'])):
            logger.info(f"\n  [{i+1}] {meta.get('book')} - {meta.get('ref')}")
            logger.info(f"      {doc[:150]}...")

    logger.info("\n🎉 INGESTION TERMINÉE AVEC SUCCÈS!")
    logger.info(f"   Livres: {len(all_books)}")
    logger.info(f"   Textes: {total_texts}")
    logger.info(f"   Chunks: {len(optimized_chunks)}")
    logger.info(f"   Base: {persist_dir}")


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Ingérer les textes de Rabbi Nachman depuis Sefaria"
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Ingérer tous les livres'
    )

    parser.add_argument(
        '--book',
        type=str,
        help='Ingérer un livre spécifique (ex: Likutei_Moharan)'
    )

    parser.add_argument(
        '--books',
        type=str,
        help='Ingérer plusieurs livres (séparés par des virgules)'
    )

    parser.add_argument(
        '--languages',
        type=str,
        default='he,en',
        help='Langues à récupérer (défaut: he,en)'
    )

    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset la collection avant ingestion'
    )

    args = parser.parse_args()

    # Determine which books to ingest
    books = None
    if args.book:
        books = [args.book]
    elif args.books:
        books = args.books.split(',')
    elif not args.all:
        logger.error("Spécifiez --all, --book ou --books")
        parser.print_help()
        sys.exit(1)

    languages = args.languages.split(',') if args.languages else ['he', 'en']

    # Run ingestion
    try:
        await ingest_books(
            books=books,
            languages=languages,
            reset=args.reset
        )
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Interruption utilisateur")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Configure logger
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )

    asyncio.run(main())
