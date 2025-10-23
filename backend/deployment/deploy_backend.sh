#!/bin/bash
# Script de déploiement du backend FastAPI sur Cloud Run

set -e

echo "🚀 Déploiement du backend RAG sur Cloud Run"

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
REGION="${GCP_REGION:-europe-west1}"
SERVICE_NAME="rabbi-rag-api"

echo "📋 Configuration:"
echo "   Project: $PROJECT_ID"
echo "   Region: $REGION"
echo "   Service: $SERVICE_NAME"

# 1. Build et push de l'image Docker
echo ""
echo "1️⃣ Construction de l'image Docker..."
cd "$(dirname "$0")/.."

gcloud builds submit \
    --tag "gcr.io/${PROJECT_ID}/${SERVICE_NAME}" \
    --project "$PROJECT_ID" \
    .

# 2. Déployer sur Cloud Run
echo ""
echo "2️⃣ Déploiement sur Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --image "gcr.io/${PROJECT_ID}/${SERVICE_NAME}" \
    --platform managed \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --port 8000 \
    --memory 2Gi \
    --cpu 2 \
    --min-instances 0 \
    --max-instances 10 \
    --timeout 300 \
    --concurrency 80 \
    --set-env-vars-file .env.production \
    --execution-environment gen2 \
    --allow-unauthenticated

# 3. Obtenir l'URL du service
echo ""
echo "3️⃣ Obtention de l'URL du service..."
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --platform managed \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --format 'value(status.url)')

echo ""
echo "✅ Backend déployé avec succès!"
echo ""
echo "📍 URL de l'API: $SERVICE_URL"
echo ""
echo "🧪 Tester l'API:"
echo "   curl ${SERVICE_URL}/health"
echo ""
echo "📝 Prochaines étapes:"
echo "   1. Mettre à jour frontend/.env.production avec:"
echo "      REACT_APP_API_URL=${SERVICE_URL}"
echo "      REACT_APP_WS_URL=${SERVICE_URL/https:/wss:}/ws/chat"
echo "   2. Déployer le frontend sur Netlify"
echo ""
