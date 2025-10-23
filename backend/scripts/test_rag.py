#!/usr/bin/env python3
"""
Script de test du système RAG

Usage:
    python scripts/test_rag.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from services.rag_engine import RAGEngine
from loguru import logger


TEST_QUESTIONS = [
    {
        "question": "Que dit Rabbi Nachman sur la joie?",
        "language": "fr"
    },
    {
        "question": "מה רבי נחמן אומר על השמחה?",
        "language": "he"
    },
    {
        "question": "What does Rabbi Nachman teach about prayer?",
        "language": "en"
    },
    {
        "question": "Parle-moi du Hitbodedut",
        "language": "fr"
    },
    {
        "question": "Qu'est-ce que le Tikun Haklali?",
        "language": "fr"
    }
]


async def test_rag():
    """Tester le système RAG"""

    logger.info("🧪 Test du système RAG")
    logger.info("=" * 60)

    # Initialize RAG engine
    logger.info("\n1️⃣ Initialisation du RAG Engine...")
    rag = RAGEngine()
    await rag.initialize()

    if not rag.is_ready():
        logger.error("❌ RAG Engine non prêt")
        return

    logger.info("✅ RAG Engine prêt")

    # Get stats
    logger.info("\n2️⃣ Statistiques de la base:")
    stats = await rag.get_stats()
    for key, value in stats.items():
        logger.info(f"   {key}: {value}")

    # Test queries
    logger.info("\n3️⃣ Test des requêtes:")
    logger.info("=" * 60)

    for i, test in enumerate(TEST_QUESTIONS, 1):
        question = test['question']
        language = test['language']

        logger.info(f"\n[Test {i}/{len(TEST_QUESTIONS)}]")
        logger.info(f"Question ({language}): {question}")
        logger.info("-" * 60)

        try:
            result = await rag.query(
                question=question,
                language=language,
                top_k=5
            )

            # Display answer
            logger.info(f"\n📝 Réponse:")
            logger.info(result['answer'])

            # Display sources
            logger.info(f"\n📚 Sources ({len(result['sources'])}):")
            for j, source in enumerate(result['sources'][:3], 1):
                logger.info(f"\n   [{j}] {source['book']} - {source.get('chapter', 'N/A')}")
                logger.info(f"       Score: {source['score']:.3f}")
                logger.info(f"       {source['text'][:200]}...")

            # Display metadata
            metadata = result['metadata']
            logger.info(f"\n⏱️  Temps: {metadata.get('query_time', 0)}s")
            logger.info(f"📊 Chunks: {metadata.get('chunks_retrieved', 0)}")

        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()

        logger.info("\n" + "=" * 60)

    # Cleanup
    await rag.cleanup()
    logger.info("\n✅ Tests terminés")


async def main():
    """Main function"""
    try:
        await test_rag()
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
