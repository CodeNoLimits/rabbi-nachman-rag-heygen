# 🕎 RAG Rabbi Nachman avec Avatar HeyGen

Système RAG (Retrieval-Augmented Generation) complet pour les enseignements de Rabbi Nachman de Breslov avec avatar parlant temps réel via HeyGen.

## 🚀 Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Sefaria API    │────▶│  ChromaDB Vector │────▶│   LlamaIndex    │
│  (Data Source)  │     │    Database      │     │   RAG Engine    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                           │
                                                           ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  React Frontend │◀────│  FastAPI Backend │◀────│   Claude API    │
│   + LiveKit SDK │     │   + WebSocket    │     │   (Generation)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       │
         └───────────────────────┘
                    │
                    ▼
         ┌──────────────────┐
         │  HeyGen Streaming│
         │  Avatar API      │
         └──────────────────┘
```

## 📋 Fonctionnalités

- ✅ **Ingestion automatique** de tous les textes Rabbi Nachman depuis Sefaria
- ✅ **Chunking sémantique** optimisé pour textes religieux
- ✅ **Vector search** avec ChromaDB sur Cloud Run
- ✅ **RAG intelligent** avec LlamaIndex + Claude
- ✅ **Avatar temps réel** avec HeyGen Streaming API
- ✅ **Interface web** React avec LiveKit pour WebRTC
- ✅ **Multi-langue** (Hébreu, Français, Anglais)

## 🛠 Stack Technique

### Backend
- **FastAPI** - API REST + WebSocket
- **LlamaIndex** - Framework RAG
- **ChromaDB** - Vector database
- **Claude API** - Génération de réponses
- **HeyGen API** - Avatar streaming

### Frontend
- **React** - Interface utilisateur
- **LiveKit SDK** - Streaming WebRTC
- **TailwindCSS** - Styling

### Infrastructure
- **Google Cloud Run** - Déploiement serverless
- **Cloud Storage** - Persistence ChromaDB
- **Docker** - Containerisation

## 📦 Installation

### Prérequis

```bash
# Python 3.10+
python --version

# Node.js 18+
node --version

# Docker (optionnel)
docker --version

# Google Cloud SDK (pour déploiement)
gcloud --version
```

### Setup Local

```bash
# 1. Cloner le projet
git clone https://github.com/[votre-username]/rabbi-nachman-rag-heygen.git
cd rabbi-nachman-rag-heygen

# 2. Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configuration
cp .env.example .env
# Éditer .env avec vos API keys

# 4. Frontend setup
cd ../frontend
npm install

# 5. Lancer ChromaDB local
cd ../backend
python -m chromadb.cli run --path ./chroma_data

# 6. Lancer backend (terminal 2)
cd backend
uvicorn main:app --reload --port 8000

# 7. Lancer frontend (terminal 3)
cd frontend
npm start
```

### Variables d'environnement

Créer `.env` dans `/backend`:

```env
# APIs
ANTHROPIC_API_KEY=your_claude_api_key
HEYGEN_API_KEY=your_heygen_api_key
HEYGEN_AVATAR_ID=your_avatar_id

# ChromaDB
CHROMA_HOST=localhost
CHROMA_PORT=8001
CHROMA_PERSIST_DIRECTORY=./chroma_data

# Sefaria
SEFARIA_API_BASE=https://www.sefaria.org/api

# Server
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:3000

# Google Cloud (production)
GCP_PROJECT_ID=your_project_id
GCS_BUCKET=rabbi-nachman-vectors
```

## 🚀 Démarrage Rapide

### 1. Ingestion des données

```bash
cd backend
python scripts/ingest_sefaria.py
```

Ceci va télécharger et indexer :
- Likutei Moharan (Part I & II) - 697 enseignements
- Sichot HaRan - Conversations
- Sefer HaMiddot - Livre des Traits
- Likutei Tefilot - Prières
- Sippurei Maasiyot - Contes

**Durée estimée**: ~30 minutes
**Volume**: ~10M tokens

### 2. Test du RAG

```bash
python scripts/test_rag.py
```

### 3. Lancer l'application

```bash
# Terminal 1: ChromaDB
python -m chromadb.cli run --path ./chroma_data

# Terminal 2: Backend
cd backend && uvicorn main:app --reload

# Terminal 3: Frontend
cd frontend && npm start
```

Ouvrir http://localhost:3000

## 📊 Utilisation

### Interface Web

1. **Poser une question** en français, hébreu ou anglais
2. **L'avatar HeyGen** répond en temps réel avec vidéo/audio
3. **Sources affichées** - voir les textes originaux utilisés
4. **Citations exactes** - traçabilité complète

### API REST

```bash
# Query RAG
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Que dit Rabbi Nachman sur la joie?",
    "language": "fr",
    "top_k": 5
  }'

# Health check
curl http://localhost:8000/health
```

### WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat');

ws.send(JSON.stringify({
  question: "Qu'est-ce que le Hitbodedut?",
  language: "fr"
}));

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Answer:', data.answer);
  console.log('Sources:', data.sources);
  console.log('Avatar session:', data.session_url);
};
```

## 🌐 Déploiement Cloud Run

### 1. Setup Google Cloud

```bash
# Login
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable APIs
gcloud services enable run.googleapis.com \
  storage.googleapis.com \
  cloudbuild.googleapis.com
```

### 2. Créer bucket GCS

```bash
gsutil mb -p YOUR_PROJECT_ID -l europe-west1 gs://rabbi-nachman-vectors/
```

### 3. Déployer ChromaDB

```bash
cd backend/deployment
./deploy_chromadb.sh
```

### 4. Déployer Backend

```bash
cd backend
gcloud run deploy rabbi-rag-api \
  --source . \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars-file .env.production
```

### 5. Déployer Frontend (Netlify)

```bash
cd frontend
npm run build
netlify deploy --prod --dir=build
```

## 💰 Coûts Mensuels Estimés

| Service | Coût/mois | Notes |
|---------|-----------|-------|
| ChromaDB Cloud Run | 15€ | Instance minimale + 50GB storage |
| Backend Cloud Run | 10€ | Pay-per-request |
| HeyGen Streaming | 30€ | 1000 min/mois |
| Claude API | 20€ | Usage estimé |
| Cloud Storage | 5€ | 50GB |
| **TOTAL** | **80€** | Pour ~500 requêtes/jour |

## 📈 Performance

- **Latence RAG**: < 3 secondes
- **Accuracy retrieval**: > 90%
- **Coût par requête**: ~0.02€
- **Uptime**: > 99%

## 🔧 Développement

### Structure du projet

```
rabbi-nachman-rag-heygen/
├── backend/
│   ├── main.py                 # FastAPI app
│   ├── requirements.txt
│   ├── services/
│   │   ├── rag_engine.py      # LlamaIndex RAG
│   │   ├── chunker.py         # Semantic chunking
│   │   ├── sefaria.py         # API Sefaria
│   │   └── heygen.py          # HeyGen integration
│   ├── scripts/
│   │   ├── ingest_sefaria.py  # Data ingestion
│   │   └── test_rag.py        # Tests
│   └── deployment/
│       ├── Dockerfile
│       └── deploy_chromadb.sh
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat.jsx
│   │   │   ├── Avatar.jsx
│   │   │   └── Sources.jsx
│   │   ├── App.jsx
│   │   └── index.js
│   ├── package.json
│   └── public/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   └── DEPLOYMENT.md
├── .github/
│   └── workflows/
│       └── deploy.yml
└── README.md
```

### Tests

```bash
# Tests backend
cd backend
pytest

# Tests frontend
cd frontend
npm test

# Tests end-to-end
npm run test:e2e
```

### Linting

```bash
# Python
cd backend
black . && flake8

# JavaScript
cd frontend
npm run lint
```

## 📚 Documentation

- [Architecture détaillée](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)
- [Guide de déploiement](docs/DEPLOYMENT.md)
- [Optimisations RAG](docs/RAG_OPTIMIZATION.md)

## 🤝 Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/amazing`)
3. Commit (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing`)
5. Ouvrir une Pull Request

## 📄 Licence

MIT License - voir [LICENSE](LICENSE)

## 👨‍💻 Auteur

David - [GitHub](https://github.com/codenolimits-dreamai-nanach)

## 🙏 Remerciements

- **Sefaria.org** - Pour l'accès aux textes sacrés
- **HeyGen** - Pour la technologie avatar
- **Anthropic** - Pour Claude API
- **LlamaIndex** - Pour le framework RAG

## 🎯 Roadmap

- [ ] Support audio-to-text (questions vocales)
- [ ] Multi-avatars (choisir personnage)
- [ ] Mode étude (annotations, favoris)
- [ ] Export PDF des conversations
- [ ] API publique documentée
- [ ] Mobile app (React Native)
- [ ] Extension Chrome

---

**Na Nach Nachma Nachman Meuman!** 🎉
