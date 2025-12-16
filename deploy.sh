#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# Configuration
SERVICE_NAME="iot-api"
REGION="us-central1"
MOUNT_PATH="/mnt/data"

# Check if PROJECT_ID is provided
if [ -z "$1" ]; then
    echo "Usage: ./deploy.sh <PROJECT_ID> <BUCKET_NAME>"
    echo "Example: ./deploy.sh my-gcp-project my-sqlite-bucket"
    exit 1
fi

PROJECT_ID=$1
BUCKET_NAME=$2

echo "Deploying to Project: $PROJECT_ID"
echo "Using Bucket for SQLite: $BUCKET_NAME"

# Prepare Environment Variables
ENV_STRING="DB_PATH=$MOUNT_PATH/database.db"
if [ -f .env ]; then
    echo "Found .env file, loading environment variables..."
    # Read .env, ignore comments/empty lines, join with comma
    FILE_ENV_VARS=$(grep -v '^#' .env | grep -v '^$' | paste -sd, -)
    if [ ! -z "$FILE_ENV_VARS" ]; then
        ENV_STRING="$ENV_STRING,$FILE_ENV_VARS"
    fi
fi
echo "Environment variables prepared."

# 1. Enable Services (idempotent)
echo "Enabling Cloud Run and Cloud Build API..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com --project $PROJECT_ID

# 2. Build Container
echo "Building Container Image..."
IMAGE_URL="gcr.io/$PROJECT_ID/$SERVICE_NAME"
gcloud builds submit --tag $IMAGE_URL --project $PROJECT_ID

# 3. Deploy to Cloud Run with Volume Mount
echo "Deploying to Cloud Run..."

gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_URL \
  --platform managed \
  --region $REGION \
  --project $PROJECT_ID \
  --allow-unauthenticated \
  --execution-environment gen2 \
  --add-volume=name=db-volume,type=cloud-storage,bucket=$BUCKET_NAME \
  --add-volume-mount=volume=db-volume,mount-path=$MOUNT_PATH \
  --set-env-vars="$ENV_STRING" \
  --port 8000

echo "Deployment Complete!"
gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --project $PROJECT_ID --format 'value(status.url)'
