#!/bin/bash

set -e  # Arrêter en cas d'erreur
export DEBIAN_FRONTEND=noninteractive

USER_HOME=$(eval echo ~$SUDO_USER)
USERNAME=${SUDO_USER:-$USER}

echo "=== [1] Mise à jour et installation de base ==="
sudo apt update && sudo apt install -y openssh-server curl podman snap snapd

echo "=== [2] Montage du disque et configuration MicroK8s ==="
sudo mount /dev/sda /mnt || echo "⚠️ Disque déjà monté ?"
sudo mkdir -p /mnt/my-microk8s/
sudo ln -sfn /mnt/my-microk8s /var/snap/microk8s

echo "=== [3] Installation de MicroK8s ==="
sudo snap install core
sudo snap install microk8s --classic

echo "=== [4] Ajout de l'utilisateur $USERNAME au groupe microk8s ==="
sudo usermod -a -G microk8s $USERNAME
sudo chown -R $USERNAME:$USERNAME $USER_HOME/.kube || true
sudo mkdir -p /mnt/my-microk8s/registry /mnt/my-microk8s/tmp

echo "=== [5] Liens pour registry et tmp ==="
sudo ln -sfn /mnt/my-microk8s/registry /var/lib/registry
sudo ln -sfn /mnt/my-microk8s/tmp /var/tmp

echo "=== [6] Démarrage de MicroK8s + configuration kube ==="
sg microk8s -c "microk8s start && microk8s status --wait-ready"
sg microk8s -c "microk8s config" > "$USER_HOME/.kube/config"
sudo chown $USERNAME:$USERNAME "$USER_HOME/.kube/config"
chmod 600 "$USER_HOME/.kube/config"

echo "=== [7] Activation du registre et des composants Knative ==="
sg microk8s -c "microk8s enable registry"
sg microk8s -c "microk8s enable community"
sg microk8s -c "microk8s enable knative"
sg microk8s -c "microk8s enable metallb:134.214.202.225-134.214.202.225"

echo "=== [8] Configuration du domaine Knative ==="
sg microk8s -c "microk8s kubectl patch configmap -n knative-serving config-domain -p '{\"data\": {\"134.214.202.225.sslip.io\": \"\"}}'"

echo "=== [9] Ajout des plugins Knative au PATH ==="
if ! grep -q "microk8s/common/plugins" "$USER_HOME/.bashrc"; then
  echo 'export PATH=$PATH:/var/snap/microk8s/common/plugins' >> "$USER_HOME/.bashrc"
fi
export PATH=$PATH:/var/snap/microk8s/common/plugins

echo "=== [10] Permissions pour knative (registry socket) ==="
sudo chown -R $USERNAME:$USERNAME /mnt/my-microk8s/common/run || true

echo "=== [11] Vérification kn-func ==="
sg microk8s -c "microk8s kn-func version"

echo "=== [12] Création et déploiement fonction Node.js ==="
cd "$USER_HOME"
sg microk8s -c "microk8s kn-func create hello -l node"
cd hello
sg microk8s -c "microk8s kn-func deploy --image localhost:32000/hello:latest --build --builder s2i"

echo "=== [13] Ajout dans /etc/hosts ==="
if ! grep -q "hello.default.134.214.202.225.sslip.io" /etc/hosts; then
  echo "134.214.202.225 hello.default.134.214.202.225.sslip.io" | sudo tee -a /etc/hosts > /dev/null
fi

echo "=== [14] Test CURL de la fonction ==="
curl http://hello.default.134.214.202.225.sslip.io || echo "⚠️ La fonction peut ne pas être prête"

echo "=== ✅ INSTALLATION DE MICROK8S + KNATIVE TERMINÉE ==="
echo "➡️ Vous pouvez maintenant déployer le portail FaaS frontend/backend"
