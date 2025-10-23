# 🚀 Guide de Démarrage Rapide

Ce guide vous permettra de lancer le projet RAG Rabbi Nachman en moins de 10 minutes.

## ⚡ Installation Express

### 1. Prérequis

```bash
# Vérifier Python 3.10+
python --version

# Vérifier Node.js 18+
node --version

# Installer ChromaDB
pip install chromadb
```

### 2. Setup Backend

```bash
# Cloner le projet
git clone https://github.com/[votre-username]/rabbi-nachman-rag-heygen.git
cd rabbi-nachman-rag-heygen/backend

# Créer environnement virtuel
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installer dépendances
pip install -r requirements.txt

# Copier et configurer .env
cp .env.example .env
# Éditer .env avec vos API keys (Claude, HeyGen)
```

### 3. Ingestion des Données

```bash
# Lancer ChromaDB local (terminal 1)
python -m chromadb.cli run --path ./chroma_data

# Ingérer les textes (terminal 2)
cd backend
python scripts/ingest_sefaria.py --all

# Durée: ~30 minutes
# Volume: ~10M tokens → 50,000 chunks
```

### 4. Lancer le Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Vérifier: http://localhost:8000/health

### 5. Setup Frontend

```bash
# Terminal 3
cd frontend
npm install

# Configurer
cp .env.example .env.local
# Éditer .env.local:
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws/chat

# Lancer
npm start
```

Ouvrir: http://localhost:3000

## ✅ Vérification

### Test 1: Health Check

```bash
curl http://localhost:8000/health
```

Réponse attendue:
```json
{
  "status": "healthy",
  "rag_engine_ready": true,
  "heygen_ready": true,
  "environment": "development"
}
```

### Test 2: Query RAG

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Que dit Rabbi Nachman sur la joie?",
    "language": "fr",
    "top_k": 5
  }'
```

### Test 3: Interface Web

1. Ouvrir http://localhost:3000
2. Poser une question: "Qu'est-ce que le Hitbodedut?"
3. Vérifier:
   - ✅ WebSocket connecté
   - ✅ Avatar vidéo chargé
   - ✅ Réponse générée
   - ✅ Sources affichées

## 🎨 Personnalisation Rapide

### Changer l'avatar HeyGen

```bash
# .env
HEYGEN_AVATAR_ID=new_avatar_id
HEYGEN_VOICE_ID=fr-FR-HenriNeural  # Voix masculine
```

### Changer le modèle LLM

```bash
# .env
LLM_MODEL=claude-3-opus-20240229  # Version plus puissante
```

### Limiter les livres ingérés

```bash
# Ingérer seulement Likutei Moharan
python scripts/ingest_sefaria.py --book Likutei_Moharan

# Plusieurs livres
python scripts/ingest_sefaria.py --books Likutei_Moharan,Sichot_HaRan
```

## 🐛 Résolution Rapide

### Erreur: ChromaDB not found

```bash
# Vérifier que ChromaDB tourne
ps aux | grep chroma

# Si absent, relancer:
python -m chromadb.cli run --path ./chroma_data
```

### Erreur: RAG engine not ready

```bash
# Vérifier ingestion terminée
cd backend
python scripts/test_rag.py
```

### Erreur: WebSocket connection failed

```bash
# Vérifier backend actif
curl http://localhost:8000/health

# Vérifier CORS dans .env
CORS_ORIGINS=http://localhost:3000
```

### Erreur: HeyGen session failed

```bash
# Vérifier API key HeyGen valide
# Vérifier crédits HeyGen suffisants
# Tester sans avatar (mode text-only)
```

## 📊 Dashboard Admin

Accéder: http://localhost:8000/docs

Swagger UI interactif avec:
- Endpoints API testables
- Schémas de données
- Exemples de requêtes

## 🚀 Prochaines Étapes

1. **Mode Production**: Voir [DEPLOYMENT.md](DEPLOYMENT.md)
2. **Optimisations**: Voir [RAG_OPTIMIZATION.md](RAG_OPTIMIZATION.md)
3. **API Reference**: Voir [API.md](API.md)

## 💡 Tips

- Utilisez `--reset` avec ingestion pour vider la base
- Testez avec `scripts/test_rag.py` avant de lancer l'interface
- Logs détaillés dans `backend/logs/app.log`
- ChromaDB UI: http://localhost:8001 (si activé)

## 🆘 Support

- Issues: https://github.com/[username]/rabbi-nachman-rag-heygen/issues
- Docs complètes: `/docs`
- Sefaria API: https://github.com/Sefaria/Sefaria-Project/wiki/API-Documentation

---

**Temps total setup**: ~45 minutes (dont 30min ingestion)

**Prêt à déployer en production?** → [DEPLOYMENT.md](DEPLOYMENT.md)
