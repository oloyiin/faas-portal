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
microk8s enable metallb:134.214.202.225-134.124.202.225 #Configuration de metallb (loadBalancer)
microk8s kubectl patch configmap -n knative-serving config-domain -p '{"data": {"134.214.202.225.sslip.io": ""}}' #Configuration de l'adresse d'écoute de Knative

## Installation d'un utilitaire de container (ici podman)
sudo apt install podman
sudo apt install curl (optionnel)

## Ajout au PATH les plugins de Knative
echo 'export PATH=$PATH:/var/snap/microk8s/common/plugins' >> ~/.bashrc
source ~/.bashrc

A partir d'ici, pour tester l'installation de Knative :
microk8s kn-func version 
