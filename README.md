Projet Etudiants TC - SIR - Plateforme FaaS
VERDET Tristan - COHELEACH Damien - MALIKI Ilhême - GRAUL Alexis

# Démarrage du noyau avec l'option de groupes spécifiques
     Utiliser l'image : [2025-microk8s](https://github.com/sfrenot/iso/tree/main/2025-microk8s). Elle est accessible sur demande   
     L'image brute se trouve [ici](wget http://tc-net.insa-lyon.fr/iso/2025-microk8s.iso)   
     Démarrer le réseau : ./startnet.sh

## Installer microk8s 
      ./startmicrok8s.sh # Lire le shell pour comprendre ce que le programme réalise

## Tester l'installation de knative
      microk8s kn-func version 
      Tester l'installation avec le script
      ./startfaas.sh

      Tester l'appel de fonction avec le retour du script d'installation
      
      curl http://hello.default.$ipaddr.sslip.io


# Partie interface web 
## FaaS Portal

Plateforme web complète pour gérer des fonctions serverless (FaaS) déployées sur un cluster Kubernetes avec Knative.


## Table des matières

1. [Prérequis](#prérequis)  
2. [Préparation des certificats Kubernetes](#préparation-des-certificats-kubernetes)  
3. [Installation hors production (dev)](#installation-hors-production-dev)  
   3.1. [Backend](#backend)  
   3.2. [Frontend](#frontend)  
4. [Installation et déploiement automatisé (prod)](#installation-et-déploiement-automatisé-prod)  
5. [Architecture générale](#architecture-générale)  
6. [Fonctionnement](#fonctionnement)  
7. [Principaux fichiers et dossiers](#principaux-fichiers-et-dossiers)  


---

## Prérequis

- Git  
- Python ≥ 3.9  
- Node.js ≥ 14 + npm (ou yarn)  
- microk8s (ou tout cluster Kubernetes local)  
- Docker ou Podman  
- `kubectl` configuré  

---

## Préparation des certificats Kubernetes

Pour que le backend puisse communiquer en TLS avec votre cluster, placez dans `faas-backend/certs/` :

- `client.crt` : certificat client (PEM)  
- `client.key` : clé privée du client (PEM)  
- `cert.crt`   : certificat de l’autorité (CA) (PEM)  

### Extraction depuis `~/.kube/config` (déjà en base64)

```bash
# Récupérer et décoder le certificat client
microk8s kubectl config view --raw \
  -o jsonpath='{.users[0].user.client-certificate-data}' \
  | base64 -d > faas-backend/certs/client.crt

# Récupérer et décoder la clé privée client
microk8s kubectl config view --raw \
  -o jsonpath='{.users[0].user.client-key-data}' \
  | base64 -d > faas-backend/certs/client.key

# Récupérer et décoder le certificat CA
microk8s kubectl config view --raw \
  -o jsonpath='{.clusters[0].cluster.certificate-authority-data}' \
  | base64 -d > faas-backend/certs/cert.crt
```

### Encodage d’un `.crt` ou `.key` existant en base64

Si vous possédez déjà les fichiers `.crt`/`.key` et que vous souhaitez générer la chaîne base64 (pour un inclusion YAML par exemple) :

```bash
base64 -w 0 < client.crt   # -w 0 désactive le retour à la ligne
base64 -w 0 < client.key
base64 -w 0 < cert.crt
```

---

## Installation hors production (dev)

### Backend

```bash
git clone https://…/faas-portal.git
cd faas-portal/faas-backend

# 1. Créer & activer un environnement virtuel
python3 -m venv .venv
source .venv/bin/activate

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Lancer FastAPI en mode dev
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- API disponible sur http://localhost:8000  
- Swagger UI : http://localhost:8000/docs  

### Frontend

```bash
cd ../faas-frontend

# 1. Installer les dépendances
npm install    # ou yarn install

# 2. Configurer l’URL du backend
echo "REACT_APP_BACKEND_URL=http://localhost:8000" > .env.local

# 3. Lancer en mode dev
npm start      # ou yarn start
```

- Interface disponible sur http://localhost:3000
- Si variable .env configurer (host et port) interface disponible sur host:port

---

## Installation et déploiement automatisé (prod)

### Backend

```bash
cd faas-backend
./deployment.sh
```

Ce script :

- Nettoie l’ancienne image et archives temporaires  
- Build l’image Docker (`Dockerfile`)  
- Importe l’image dans microk8s  
- Applique `backend-deploy.yaml` et `backend-rbac.yaml`  
- Redémarre le déploiement et vérifie l’état du pod  

### Frontend

```bash
cd ../faas-frontend
./redeploy-frontend.sh
```

Ce script :

- Build l’image Docker (injection de `REACT_APP_BACKEND_URL`)  
- Pousse l’image dans le registre local  
- Applique `frontend-deployment.yaml`   
- Redémarre le déploiement et attend sa disponibilité  

### Ingress

```bash
kubectl apply -f faas-frontend/ingress.yaml
```

Expose la SPA et l’API sous un même domaine/local.

---

## Architecture générale

- Backend : FastAPI + Kubernetes/Knative, conteneurisé, RBAC  
- Frontend : React + Tailwind CSS, servi par Nginx  
- Ingress Nginx pour router trafic SPA ↔ API  

---

## Fonctionnement

1. Création de fonction : upload de code + métadonnées → Knative Service  
2. Liste & états : frontend interroge l’API pour URL & statut  
3. Modif. & suppression : endpoints REST exposés  
4. Sécurité : TLS entre backend & cluster via `certs/`  

---

## Principaux fichiers et dossiers

- faas-backend/  
  - `main.py` : code FastAPI & logiques Kubernetes  
  - `backend-deploy.yaml`, `backend-rbac.yaml` : manifests  
  - `deployment.sh` : script build & déploiement  
  - `certs/` : certificats TLS  
- faas-frontend/  
  - `src/` : code React + tests  
  - `frontend-deployment.yaml` : manifests  
  - `ingress.yaml` : Ingress pour SPA & API  
  - `nginx.conf` : config Nginx SPA + proxy  
  - `redeploy-frontend.sh` : script build & déploiement  
- `func-linux-amd64` : binaire CLI (optionnel)  
- `installation-kube-knative.sh` : script d’installation Knative  


