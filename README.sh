#!/bin/bash

set -e  # Quit on error

echo "=== [1] Mise à jour du système et installation de base ==="
sudo apt update && sudo apt install -y openssh-server curl podman snap snapd

echo "=== [2] Montage du disque et préparation dossier MicroK8s ==="
sudo mount /dev/sda /mnt
sudo mkdir -p /mnt/my-microk8s/
cd /var/snap
sudo ln -s /mnt/my-microk8s microk8s

echo "=== [3] Installation de MicroK8s ==="
sudo snap install core
sudo snap install microk8s --classic

echo "=== [4] Configuration utilisateur MicroK8s ==="
sudo usermod -a -G microk8s $USER
sudo chown -R $USER ~/.kube || true
newgrp microk8s
mkdir -p ~/.kube
microk8s config > ~/.kube/config
chmod 600 ~/.kube/config
microk8s start

echo "=== [5] Montage du registry et répertoire tmp ==="
sudo mkdir -p /mnt/my-microk8s/registry /mnt/my-microk8s/tmp
cd /var/lib
sudo ln -s /mnt/my-microk8s/registry registry || true
cd /var
sudo ln -s /mnt/my-microk8s/tmp tmp || true

echo "=== [6] Activation du registry MicroK8s ==="
microk8s enable registry

echo "=== [7] Installation et configuration de Knative ==="
microk8s enable community
microk8s enable knative
microk8s enable metallb:134.214.202.225-134.214.202.225
microk8s kubectl patch configmap -n knative-serving config-domain -p '{"data": {"134.214.202.225.sslip.io": ""}}'

echo "=== [8] Ajout des plugins Knative au PATH ==="
echo 'export PATH=$PATH:/var/snap/microk8s/common/plugins' >> ~/.bashrc
source ~/.bashrc

echo "=== [9] Réglage des permissions knative ==="
sudo chown -R $(id -u):$(id -g) /mnt/my-microk8s/common/run

echo "=== [10] Test de l'installation kn-func ==="
microk8s kn-func version

echo "=== [11] Création d'une fonction exemple ==="
cd ~
microk8s kn-func create hello -l node
cd hello
microk8s kn-func deploy --image localhost:32000/hello:latest --build --builder s2i

echo "=== [12] Configuration de /etc/hosts ==="
echo "134.214.202.225 hello.default.134.214.202.225.sslip.io" | sudo tee -a /etc/hosts > /dev/null

echo "=== [13] Test HTTP de la fonction ==="
curl http://hello.default.134.214.202.225.sslip.io || echo "⚠️ L'appel HTTP a échoué (la fonction n'est peut-être pas encore prête)"

echo "=== [14] Déploiement du backend FaaS ==="
chmod +x backend/deployment.sh
./backend/deployment.sh

echo "=== [15] Déploiement du frontend FaaS ==="
chmod +x frontend/redeploy-frontend.sh
./frontend/redeploy-frontend.sh

echo "=== [16] Déploiement de l'Ingress ==="
microk8s kubectl apply -f ingress/faas-ingress.yaml

echo "=== ✅ FaaS Portal déployé ! Accédez à : http://faas.local (ou IP .sslip.io selon Ingress) ==="
