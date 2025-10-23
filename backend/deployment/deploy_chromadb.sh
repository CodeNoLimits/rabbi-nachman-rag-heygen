#!/bin/bash
# Script de déploiement ChromaDB sur Cloud Run

set -e

echo "🚀 Déploiement ChromaDB sur Cloud Run"

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
REGION="${GCP_REGION:-europe-west1}"
SERVICE_NAME="rabbi-chroma-db"
BUCKET_NAME="rabbi-nachman-vectors"

echo "📋 Configuration:"
echo "   Project: $PROJECT_ID"
echo "   Region: $REGION"
echo "   Service: $SERVICE_NAME"
echo "   Bucket: $BUCKET_NAME"

# 1. Créer le bucket GCS si nécessaire
echo ""
echo "1️⃣ Création du bucket GCS..."
if ! gsutil ls -b "gs://${BUCKET_NAME}" &> /dev/null; then
    gsutil mb -p "$PROJECT_ID" -l "$REGION" "gs://${BUCKET_NAME}/"
    echo "✅ Bucket créé"
else
    echo "ℹ️  Bucket existe déjà"
fi

# 2. Déployer ChromaDB sur Cloud Run
echo ""
echo "2️⃣ Déploiement ChromaDB..."
gcloud run deploy "$SERVICE_NAME" \
    --image chromadb/chroma:latest \
    --platform managed \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --port 8000 \
    --memory 2Gi \
    --cpu 1 \
    --min-instances 1 \
    --max-instances 3 \
    --timeout 300 \
    --set-env-vars "IS_PERSISTENT=TRUE,PERSIST_DIRECTORY=/chroma/data" \
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
echo "✅ ChromaDB déployé avec succès!"
echo ""
echo "📍 URL du service: $SERVICE_URL"
echo ""
echo "📝 Prochaines étapes:"
echo "   1. Mettre à jour .env.production avec:"
echo "      CHROMA_HOST=${SERVICE_URL#https://}"
echo "      CHROMA_PORT=443"
echo "   2. Exécuter le script d'ingestion"
echo "   3. Déployer le backend API"
echo ""
