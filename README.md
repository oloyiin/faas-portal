Projet Etudiants TC - SIR - Plateforme FaaS
VERDET Tristan - COHELEACH Damien - MALIKI Ilhême - GRAUL Alexis


# Prérequis & Installation pour MICROK8S fonctionnel + FaaS (Knative)

## Accès à distance (optionnel)
sudo apt update
sudo apt install openssh-server (pour accès ssh)
passwd (définir password)

## Installation de snap 
sudo apt install snap snapd
sudo snap install core

## Montage du disque de la machine hôte et définition du dossier de microk8s
sudo mount /dev/sda /mnt
mkdir /mnt/my-microk8s/
cd /var/snap
sudo ln -s /mnt/my-microk8s microk8s

## Installation de microk8s
sudo snap install microk8s --classic

## Configuration initiale de microk8s
sudo usermod -a -G microk8s ubuntu
sudo chown -R ubuntu ~/.kube
newgrp microk8s
mkdir -p ~/.kube
microk8s config > ~/.kube/config
chmod 600 ~/.kube/config
microk8s start

## Montage de l'emplacement du registry et lien
mkdir /mnt/my-microk8s/registry
cd /var/lib
sudo ln -s /mnt/my-microk8s/registry registry

## Installation du registry
microk8s enable registry

## Installation de Knative
microk8s enable community
microk8s enable knative #Installation de Knative
microk8s enable metallb:134.214.202.225-134.214.202.225 #Configuration de metallb (loadBalancer)
microk8s kubectl patch configmap -n knative-serving config-domain -p '{"data": {"134.214.202.225.sslip.io": ""}}' #Configuration de l'adresse d'écoute de Knative

## Installation d'un utilitaire de container (ici podman)
sudo apt install podman
sudo apt install curl

## Ajout au PATH les plugins de Knative
echo 'export PATH=$PATH:/var/snap/microk8s/common/plugins' >> ~/.bashrc
source ~/.bashrc

A partir d'ici, pour tester l'installation de Knative :
microk8s kn-func version 

##Regler les problemes de droits avec knative###
sudo chown -R $(id -u):$(id -g) /mnt/my-microk8s/common/run
source ~/.bashrc
Pour tester la creation d'une fonction basique avec KNATIVE : 
cd ~
microk8s kn-func create hello -l node
cd hello
microk8s kn-func deploy --image localhost:32000/hello:latest --build --builder s2i

Modifier le /etc/hosts
echo "134.214.202.225 hello.default.134.214.202.225.sslip.io" | sudo tee -a /etc/hosts > /dev/null

curl http://hello.default.134.214.202.225.sslip.io


# Partie interface web 
## FaaS Portal
### Présentation
FaaS Portal est une plateforme web complète pour gérer des fonctions serverless (FaaS) déployées sur un cluster Kubernetes avec Knative.
Elle permet de créer, lister, modifier, supprimer et surveiller des fonctions via une interface web intuitive et une API REST.
### Architecture générale
Le projet est composé de deux parties principales :
1. Backend (API)
Technologie : Python avec FastAPI
Rôle :

Communique avec l’API Kubernetes/Knative pour gérer les fonctions serverless.
Expose une API REST sécurisée pour le frontend et d’autres clients.
Gère la sécurité via certificats TLS pour accéder au cluster Kubernetes.


Déploiement :

Conteneurisé avec Docker.
Déployé dans Kubernetes avec un Deployment, Service et RBAC (permissions).
Utilise des variables d’environnement pour la configuration (ex: URL du serveur Kubernetes).


2. Frontend (Interface utilisateur)
Technologie : React avec Tailwind CSS
Rôle :

Interface utilisateur pour interagir avec les fonctions serverless.
Permet d’uploader du code, configurer les fonctions, visualiser leur état et URL.
Communique avec le backend via API REST.


Déploiement :

Buildé en application statique React.
Servi via Nginx dans un conteneur Docker.
Déployé dans Kubernetes avec un Deployment, Service et Ingress.
Configuration Nginx adaptée pour SPA et proxy des appels API.


Fonctionnement du projet

Création d’une fonction :
L’utilisateur sélectionne un fichier source, renseigne le nom, langage et version, puis soumet via le frontend.
Le frontend envoie le code au backend qui déploie la fonction sur Knative via l’API Kubernetes.



Liste et état des fonctions :
Le frontend interroge le backend pour récupérer la liste des fonctions déployées, leurs URLs et états (prêtes ou non).



Modification et suppression :
Le backend expose des endpoints pour patcher ou supprimer une fonction, accessibles via le frontend.



Sécurité :
Le backend utilise des certificats TLS pour communiquer avec Kubernetes.
Le frontend communique uniquement avec le backend via API REST.


Principaux fichiers et leur rôleFichier / DossierDescriptionbackend/main.pyCode principal backend FastAPI, routes API, gestion Kubernetes via certificats TLSbackend/backend-deploy.yamlManifest Kubernetes pour déployer backend (Deployment + Service)backend/backend-rbac.yamlPermissions Kubernetes (ServiceAccount, Role, RoleBinding) pour backendbackend/deployment.shScript bash pour builder, importer et déployer automatiquement le backendfrontend/src/App.jsComposant React principal, interface utilisateurfrontend/src/App.cssStyles Tailwind CSS et personnalisationsfrontend/faas-frontend-deployment.yamlManifest Kubernetes pour déployer frontend (Deployment + Service)frontend/redeploy-frontend.shScript bash pour builder, pousser et déployer automatiquement le frontendingress/faas-ingress.yamlIngress Kubernetes pour router le trafic vers frontend et backend selon les cheminsfrontend/nginx.confConfiguration Nginx pour servir React SPA et proxy API backend.env filesVariables d’environnement pour configurer URLs, certificats, etc.Déploiement

Backend :
Utilise deployment.sh pour automatiser build, push et déploiement dans Kubernetes.



Frontend :
Utilise redeploy-frontend.sh pour automatiser build, push et déploiement.



Ingress :
Applique le manifest Ingress pour exposer frontend et backend via un nom de domaine local.


Utilisation
Accéder à l’interface web via l’URL configurée dans l’Ingress (ex: http://faas.local).
Créer, gérer et supprimer des fonctions serverless facilement.
Visualiser l’état et l’URL des fonctions déployées.
Tests
Script Python dans backend pour tester les endpoints API.
Tests unitaires React dans frontend (ex: App.test.js).
Conclusion
FaaS Portal est une solution complète pour gérer des fonctions serverless sur Kubernetes, avec une architecture moderne, sécurisée et automatisée.
Les scripts de déploiement facilitent la mise à jour et la maintenance.



