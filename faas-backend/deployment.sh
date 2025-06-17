#!/bin/bash

set -e  # Arrêter le script en cas d'erreur

IMAGE_NAME="localhost/faas-backend:v1"
TAR_FILE="backend.tar"
DEPLOYMENT_YAML="backend-deploy.yaml"

# Adresse IP et port pour tester l'API (à adapter)
API_HOST="134.214.202.225"
API_PORT="30081"
API_URL="http://${API_HOST}:${API_PORT}/"

echo "=== Nettoyage ==="
podman rmi $IMAGE_NAME --force 2>/dev/null || true
microk8s ctr image rm $IMAGE_NAME 2>/dev/null || true
[ -f "$TAR_FILE" ] && rm "$TAR_FILE"

echo "=== Build ==="
podman build -t $IMAGE_NAME . --no-cache

echo "=== Export et Import ==="
podman save $IMAGE_NAME -o $TAR_FILE
microk8s ctr image import $TAR_FILE

echo "=== Déploiement ==="
if microk8s kubectl get deployment backend-api >/dev/null 2>&1; then
    echo "Redémarrage du déploiement existant..."
    microk8s kubectl rollout restart deployment backend-api
else
    echo "Création du déploiement..."
    microk8s kubectl apply -f $DEPLOYMENT_YAML
fi

echo "=== Attente du déploiement ==="
microk8s kubectl rollout status deployment backend-api --timeout=300s

echo "V Déploiement réussi!"

echo "Attete que le pod soit prêt..."
microk8s kubectl wait --for=condition=ready pod -l app=backend-api --timeout=60s

echo "=== Test de l'API ==="
sleep 5  # Petit délai pour que l'API démarre

if curl -s "$API_URL" >/dev/null; then
    echo " API accessible sur: $API_URL"
    echo "v Test API réussi!"
else
    echo "x  API pas encore accessible, vérifiez les logs"
fi

echo "=== État final ==="
microk8s kubectl get pods -l app=backend-api

# Nettoyage
rm -f $TAR_FILE
echo "Archive supprimée."