#!/bin/bash

IMAGE_NAME="localhost:32000/faas-frontend:latest"
DEPLOYMENT_FILE="frontend-deployment.yaml"
DEPLOYMENT_NAME="faas-frontend"
BACKEND_URL="${BACKEND_URL:-http://backend-api-service}"

set -e  # Arrêter le script à la première erreur

echo "Build de l'image frontend avec BACKEND_URL=$BACKEND_URL..."
podman build --build-arg REACT_APP_BACKEND_URL=$BACKEND_URL -t $IMAGE_NAME .

echo "Push de l'image dans le registre local..."
podman push $IMAGE_NAME --tls-verify=false

echo "Application du déploiement Kubernetes..."
microk8s kubectl apply -f $DEPLOYMENT_FILE

echo "Redémarrage du déploiement frontend pour prendre en compte la nouvelle image..."
microk8s kubectl rollout restart deployment $DEPLOYMENT_NAME

echo "Attente que le déploiement soit prêt..."
microk8s kubectl rollout status deployment $DEPLOYMENT_NAME --timeout=120s

echo "Frontend rebuild, pushed, et redeployé avec succès."