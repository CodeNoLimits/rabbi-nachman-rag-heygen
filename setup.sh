#!/bin/bash
# Script de setup automatique complet
# Usage: ./setup.sh

set -e

echo "🕎 RAG Rabbi Nachman - Setup Automatique"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${BLUE}1️⃣ Vérification des prérequis...${NC}"

# Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 non installé${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python: $(python3 --version)${NC}"

# Node
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js non installé${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node: $(node --version)${NC}"

# Backend setup
echo ""
echo -e "${BLUE}2️⃣ Configuration Backend...${NC}"
cd backend

# Virtual env
if [ ! -d "venv" ]; then
    echo "Création environnement virtuel..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install deps
echo "Installation dépendances Python..."
pip install -q -r requirements.txt

# .env
if [ ! -f ".env" ]; then
    echo "Copie .env.example → .env"
    cp .env.example .env
    echo -e "${RED}⚠️  IMPORTANT: Éditer backend/.env avec vos API keys!${NC}"
fi

# Frontend setup
echo ""
echo -e "${BLUE}3️⃣ Configuration Frontend...${NC}"
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo "Installation dépendances Node..."
    npm install
fi

# .env
if [ ! -f ".env.local" ]; then
    echo "Création .env.local"
    cat > .env.local <<EOL
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws/chat
EOL
fi

cd ..

# Summary
echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}✅ Setup terminé avec succès!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo -e "${BLUE}📝 Prochaines étapes:${NC}"
echo ""
echo "1. Configurer les API keys:"
echo "   ${BLUE}nano backend/.env${NC}"
echo "   - ANTHROPIC_API_KEY"
echo "   - HEYGEN_API_KEY"
echo "   - HEYGEN_AVATAR_ID"
echo ""
echo "2. Lancer ChromaDB (terminal 1):"
echo "   ${BLUE}cd backend && source venv/bin/activate${NC}"
echo "   ${BLUE}python -m chromadb.cli run --path ./chroma_data${NC}"
echo ""
echo "3. Ingérer les données (terminal 2):"
echo "   ${BLUE}cd backend && source venv/bin/activate${NC}"
echo "   ${BLUE}python scripts/ingest_sefaria.py --all${NC}"
echo "   ${RED}⏰ Durée: ~30 minutes${NC}"
echo ""
echo "4. Lancer le backend (terminal 3):"
echo "   ${BLUE}cd backend && source venv/bin/activate${NC}"
echo "   ${BLUE}uvicorn main:app --reload${NC}"
echo ""
echo "5. Lancer le frontend (terminal 4):"
echo "   ${BLUE}cd frontend && npm start${NC}"
echo ""
echo "6. Ouvrir l'application:"
echo "   ${BLUE}http://localhost:3000${NC}"
echo ""
echo -e "${GREEN}🕎 Na Nach Nachma Nachman Meuman!${NC}"
echo ""
