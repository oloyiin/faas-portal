#!/bin/bash

IMAGE_NAME="localhost/faas-backend:v1"
TAR_FILE="backend.tar"
DEPLOYMENT_YAML="backend-deploy.yaml"

echo "=== Nettoyage ==="
podman rmi $IMAGE_NAME --force 2>/dev/null || true
microk8s ctr image rm $IMAGE_NAME 2>/dev/null || true
[ -f "$TAR_FILE" ] && rm "$TAR_FILE"

echo "=== Build ==="
podman build -t $IMAGE_NAME . --no-cache

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors du build"
    exit 1
fi

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

if [ $? -eq 0 ]; then
    echo "✅ Déploiement réussi!"
    
    # Attendre que le pod soit vraiment prêt
    echo "Attente que le pod soit prêt..."
    microk8s kubectl wait --for=condition=ready pod -l app=backend-api --timeout=60s
    
    echo "=== Test de l'API ==="
    sleep 5  # Petit délai pour que l'API démarre
    if curl -s http://172.16.50.102:30081/ >/dev/null; then
        echo "🌐 API accessible sur: http://172.16.50.102:30081/"
        echo "✅ Test API réussi!"
    else
        echo "⚠️  API pas encore accessible, vérifiez les logs"
    fi
    
    echo "=== État final ==="
    microk8s kubectl get pods -l app=backend-api
    
else
    echo "❌ Échec du déploiement"
    microk8s kubectl logs -l app=backend-api --tail=20
fi

# Nettoyage
rm -f $TAR_FILE
echo "Archive supprimée."