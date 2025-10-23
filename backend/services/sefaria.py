"""
Service pour récupérer les textes depuis l'API Sefaria
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from models import SefariaText


class SefariaService:
    """Service pour API Sefaria.org"""

    # Liste complète des livres de Rabbi Nachman sur Sefaria
    RABBI_NACHMAN_BOOKS = {
        'Likutei_Moharan': {
            'name': 'Likutei Moharan',
            'parts': 2,
            'chapters': {1: 286, 2: 125}  # Part 1: 286, Part 2: 125
        },
        'Sichot_HaRan': {
            'name': 'Sichot HaRan',
            'parts': 1,
            'chapters': {1: 308}
        },
        'Sefer_HaMiddot': {
            'name': 'Sefer HaMiddot',
            'parts': 1,
            'chapters': {1: 150}  # Topics alphabétiques
        },
        'Likutei_Tefilot': {
            'name': 'Likutei Tefilot',
            'parts': 2,
            'chapters': {1: 211, 2: 25}
        },
        'Sippurei_Maasiyot': {
            'name': 'Sippurei Maasiyot',
            'parts': 1,
            'chapters': {1: 13}  # 13 contes
        },
        'Shivchei_HaRan': {
            'name': 'Shivchei HaRan',
            'parts': 1,
            'chapters': {1: 50}
        },
        'Chayei_Moharan': {
            'name': 'Chayei Moharan',
            'parts': 1,
            'chapters': {1: 600}
        }
    }

    def __init__(self):
        self.base_url = os.getenv('SEFARIA_API_BASE', 'https://www.sefaria.org/api')
        self.rate_limit_delay = 0.5  # 500ms entre requêtes

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def fetch_text(
        self,
        ref: str,
        languages: List[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Récupérer un texte depuis Sefaria

        Args:
            ref: Référence Sefaria (ex: "Likutei_Moharan.1")
            languages: Langues à récupérer (he, en, fr)

        Returns:
            Dict avec texte en différentes langues
        """
        if languages is None:
            languages = ['he', 'en', 'fr']

        try:
            url = f"{self.base_url}/texts/{ref}"
            params = {
                'context': 0,
                'commentary': 0,
                'pad': 0
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                # Rate limiting
                await asyncio.sleep(self.rate_limit_delay)

                return data

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Text not found: {ref}")
                return None
            logger.error(f"HTTP error fetching {ref}: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Error fetching {ref}: {e}")
            raise

    async def fetch_book_complete(
        self,
        book_slug: str,
        languages: List[str] = None
    ) -> List[SefariaText]:
        """
        Récupérer un livre complet

        Args:
            book_slug: Slug du livre (ex: 'Likutei_Moharan')
            languages: Langues à récupérer

        Returns:
            Liste de SefariaText
        """
        if book_slug not in self.RABBI_NACHMAN_BOOKS:
            raise ValueError(f"Unknown book: {book_slug}")

        book_info = self.RABBI_NACHMAN_BOOKS[book_slug]
        all_texts = []

        logger.info(f"📚 Récupération de {book_info['name']}...")

        for part in range(1, book_info['parts'] + 1):
            num_chapters = book_info['chapters'][part]

            # Construct part reference
            if book_info['parts'] > 1:
                part_ref = f"{book_slug},_Part_{part}" if part == 2 else book_slug
            else:
                part_ref = book_slug

            logger.info(f"  Part {part}: {num_chapters} chapitres")

            # Fetch all chapters in this part
            tasks = []
            for chapter in range(1, num_chapters + 1):
                ref = f"{part_ref}.{chapter}"
                tasks.append(self.fetch_text(ref, languages))

                # Batch requests to avoid overwhelming API
                if len(tasks) >= 10:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    for result in results:
                        if isinstance(result, dict) and result is not None:
                            all_texts.extend(self._parse_response(result, book_info['name']))
                    tasks = []

            # Process remaining tasks
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, dict) and result is not None:
                        all_texts.extend(self._parse_response(result, book_info['name']))

        logger.info(f"✅ {book_info['name']}: {len(all_texts)} textes récupérés")
        return all_texts

    def _parse_response(self, data: Dict[str, Any], book_name: str) -> List[SefariaText]:
        """Parser une réponse Sefaria en SefariaText"""
        texts = []

        ref = data.get('ref', '')

        # Hebrew text
        hebrew_text = data.get('he', [])
        if isinstance(hebrew_text, str):
            hebrew_text = [hebrew_text]

        # English text
        english_text = data.get('text', [])
        if isinstance(english_text, str):
            english_text = [english_text]

        # Combine all paragraphs
        for i, (he_para, en_para) in enumerate(zip(hebrew_text, english_text)):
            if he_para or en_para:
                texts.append(SefariaText(
                    title=book_name,
                    ref=f"{ref}:{i+1}" if len(hebrew_text) > 1 else ref,
                    hebrew=he_para if isinstance(he_para, str) else '',
                    text=en_para if isinstance(en_para, str) else '',
                    language='he',
                    versionTitle=data.get('versionTitle'),
                    versionSource=data.get('versionSource')
                ))

        return texts

    async def fetch_all_rabbi_nachman(
        self,
        books: Optional[List[str]] = None,
        languages: List[str] = None
    ) -> Dict[str, List[SefariaText]]:
        """
        Récupérer TOUS les textes de Rabbi Nachman

        Args:
            books: Liste des livres à récupérer (None = tous)
            languages: Langues à récupérer

        Returns:
            Dict {book_slug: [SefariaText]}
        """
        if books is None:
            books = list(self.RABBI_NACHMAN_BOOKS.keys())

        if languages is None:
            languages = ['he', 'en']

        all_books = {}

        logger.info(f"📖 Récupération de {len(books)} livres de Rabbi Nachman...")
        logger.info(f"   Langues: {', '.join(languages)}")

        for book_slug in books:
            try:
                texts = await self.fetch_book_complete(book_slug, languages)
                all_books[book_slug] = texts
            except Exception as e:
                logger.error(f"Erreur lors de la récupération de {book_slug}: {e}")
                all_books[book_slug] = []

        total_texts = sum(len(texts) for texts in all_books.values())
        logger.info(f"✅ Total: {total_texts} textes récupérés")

        return all_books

    async def get_book_index(self, book_slug: str) -> Dict[str, Any]:
        """
        Récupérer l'index d'un livre (structure, métadonnées)

        Args:
            book_slug: Slug du livre

        Returns:
            Dict avec métadonnées du livre
        """
        try:
            url = f"{self.base_url}/index/{book_slug}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Error fetching index for {book_slug}: {e}")
            return {}
