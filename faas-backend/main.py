# main.py — API FastAPI pour la gestion de fonctions FaaS via Knative et kn-func

import os
import logging
import tempfile
import shutil
import asyncio
import aiofiles

from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import urllib3
from dotenv import load_dotenv

# ──────────────────────────────────────────────
# CONFIGURATION GÉNÉRALE
# ──────────────────────────────────────────────

# Charge les variables d'environnement depuis le fichier .env
load_dotenv()

# Désactive les warnings liés aux certificats auto-signés
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Active le logging pour les erreurs, infos, etc.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Définition des chemins de base
BASE_DIR = Path(__file__).parent
CERTS_DIR = BASE_DIR / "certs"

# Chargement des certificats pour appel API Kubernetes
CERT = (str(CERTS_DIR / "client.crt"), str(CERTS_DIR / "client.key"))
CACERT = str(CERTS_DIR / "cert.crt")

# Adresse de l'API Kubernetes
API_SERVER = os.getenv("API_SERVER", "https://134.214.202.225:16443")

# Headers standards pour les appels REST
HEADERS = {"Content-Type": "application/json"}

# ──────────────────────────────────────────────
# VÉRIFICATION DES CERTIFICATS
# ──────────────────────────────────────────────

def verify_certificates():
    """
    Vérifie que tous les certificats nécessaires sont présents dans le dossier certs/.
    """
    required = ["client.crt", "client.key", "cert.crt"]
    missing = [str(CERTS_DIR / c) for c in required if not (CERTS_DIR / c).exists()]
    if missing:
        raise FileNotFoundError(f"Certificats manquants : {missing}")

# ──────────────────────────────────────────────
# AJOUT AUTOMATIQUE AU FICHIER /etc/hosts
# ──────────────────────────────────────────────
"""

def add_to_etc_hosts(service_name: str, ip_address: str = "127.0.0.1"):

    ##Ajoute une ligne à /etc/hosts pour rendre la fonction accessible via <nom>.example.com
    
    #hosts_path = "/etc/hosts"
    #entry = f"{ip_address} {service_name}.example.com"
    try:
        # Vérifie si l'entrée existe déjà
        with open(hosts_path, 'r') as f:
            lines = f.readlines()
            if any(service_name in line for line in lines):
                logger.info(f"{service_name} déjà présent dans /etc/hosts")
                return
        # Ajoute l'entrée si elle n’existe pas
        with open(hosts_path, 'a') as f:
            f.write(entry)
        logger.info(f"Ajouté à /etc/hosts : {entry.strip()}")
    except PermissionError:
        logger.error("X Permission refusée pour modifier /etc/hosts (lancer avec sudo)")
    except Exception as e:
        logger.error(f"Erreur écriture /etc/hosts : {e}")

        """ 

# ──────────────────────────────────────────────
# FASTAPI INITIALISATION
# ──────────────────────────────────────────────

app = FastAPI()

# Autorisation CORS (ici ouvert à tous pour développement)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """
    Vérification des certificats au lancement de l’API.
    """
    try:
        verify_certificates()
    except FileNotFoundError as e:
        logger.error(f"Erreur de certificat : {e}")

@app.get("/")
def root():
    """Route de test pour voir si l'API tourne."""
    return {"message": "Bienvenue sur l'API FaaS 🚀"}

# ──────────────────────────────────────────────
# MODÈLES Pydantic
# ──────────────────────────────────────────────

class Fonction(BaseModel):
    nom: str
    langage: str
    version: str
    commande: Optional[List[str]] = []
    dependances: Optional[List[str]] = []

class CreationFonction(BaseModel):
    nom: str
    langage: str

class DeploiementFonction(BaseModel):
    nom: str
    image_registry: Optional[str] = "localhost:32000"
    builder: Optional[str] = "s2i"

# ──────────────────────────────────────────────
# OUTILS GÉNÉRIQUES
# ──────────────────────────────────────────────

async def execute_command(command: List[str], cwd: Optional[str] = None) -> dict:
    """
    Exécute une commande shell de manière asynchrone.
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )
        stdout, stderr = await proc.communicate()
        return {
            "success": proc.returncode == 0,
            "stdout": stdout.decode(),
            "stderr": stderr.decode()
        }
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e)}

async def save_uploaded_file(upload_file: UploadFile, destination: Path) -> bool:
    """
    Sauvegarde un fichier envoyé par l'utilisateur via FastAPI.
    """
    try:
        async with aiofiles.open(destination, 'wb') as f:
            await f.write(await upload_file.read())
        return True
    except Exception as e:
        logger.error(f"Erreur fichier : {e}")
        return False

# ──────────────────────────────────────────────
# ENDPOINTS KUBERNETES KNATIVE
# ──────────────────────────────────────────────

@app.get("/fonctions")
def get_fonctions():
    """
    Récupère la liste des services Knative déployés dans le namespace 'default'.
    """
    try:
        r = requests.get(f"{API_SERVER}/apis/serving.knative.dev/v1/namespaces/default/services",
                         cert=CERT, verify=CACERT, headers=HEADERS, timeout=30)
        r.raise_for_status()
        return [item["metadata"]["name"] for item in r.json().get("items", [])]
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.get("/fonctions/{nom}")
def get_fonction(nom: str):
    """
    Récupère les détails d’une fonction (nom + URL publique).
    """
    try:
        r = requests.get(f"{API_SERVER}/apis/serving.knative.dev/v1/namespaces/default/services/{nom}",
                         cert=CERT, verify=CACERT, headers=HEADERS, timeout=30)
        if r.status_code == 404:
            return {"message": "Fonction non trouvée"}
        return {"nom": nom, "url": r.json()["status"].get("url")}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.get("/fonctions/{nom}/etat")
def get_etat_fonction(nom: str):
    """
    Vérifie si la fonction est prête à recevoir du trafic (Ready=True).
    """
    try:
        r = requests.get(f"{API_SERVER}/apis/serving.knative.dev/v1/namespaces/default/services/{nom}",
                         cert=CERT, verify=CACERT, headers=HEADERS, timeout=30)
        conditions = r.json().get("status", {}).get("conditions", [])
        for cond in conditions:
            if cond.get("type") == "Ready":
                return {"etat": cond.get("status")}
        return {"etat": "Inconnu"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.delete("/fonctions/{nom}")
def delete_fonction(nom: str):
    """
    Supprime un service Knative.
    """
    try:
        r = requests.delete(f"{API_SERVER}/apis/serving.knative.dev/v1/namespaces/default/services/{nom}",
                            cert=CERT, verify=CACERT, headers=HEADERS, timeout=30)
        if r.status_code == 404:
            return {"message": "Fonction non trouvée"}
        return {"message": f"Fonction '{nom}' supprimée"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

# ──────────────────────────────────────────────
# ENDPOINTS LOCAUX AVEC kn-func (création/déploiement)
# ──────────────────────────────────────────────

@app.post("/fonctions/creer")
async def creer_fonction(nom: str = Form(...), langage: str = Form(...)):
    """
    Crée une fonction Knative via kn-func, puis ajoute l'entrée à /etc/hosts.
    """
    try:
        command = ["microk8s", "kn-func", "create", nom, "-l", langage]
        result = await execute_command(command)
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["stderr"])
        #add_to_etc_hosts(nom)
        return {"message": f"Fonction '{nom}' créée", "stdout": result["stdout"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fonctions/{nom}/deployer")
async def deployer_fonction(nom: str, fichier: UploadFile = File(...),
                            image_registry: str = Form("localhost:32000"),
                            builder: str = Form("s2i")):
    """
    Déploie une fonction en copiant un fichier source puis en lançant `kn-func deploy`.
    """
    temp_dir = tempfile.mkdtemp()
    try:
        function_dir = Path(nom)
        if not function_dir.exists():
            raise HTTPException(status_code=404, detail="Fonction inexistante")
        temp_file_path = Path(temp_dir) / fichier.filename
        await save_uploaded_file(fichier, temp_file_path)
        shutil.copy2(temp_file_path, function_dir / fichier.filename)
        command = ["microk8s", "kn-func", "deploy",
                   "--image", f"{image_registry}/{nom}:latest",
                   "--builder", builder]
        result = await execute_command(command, cwd=str(function_dir))
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["stderr"])
        return {"message": f"Fonction '{nom}' déployée", "stdout": result["stdout"]}
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

@app.post("/fonctions/creer-et-deployer")
async def creer_et_deployer(nom: str = Form(...), langage: str = Form(...),
                             fichier: UploadFile = File(...),
                             image_registry: str = Form("localhost:32000"),
                             builder: str = Form("s2i")):
    """
    Crée une fonction, copie le code, puis la déploie.
    """
    await creer_fonction(nom, langage)
    return await deployer_fonction(nom, fichier, image_registry, builder)

@app.get("/fonctions/{nom}/logs")
async def get_logs_fonction(nom: str, lines: int = 100):
    """
    Récupère les logs (stdout) de la dernière exécution de la fonction.
    """
    command = ["microk8s", "kubectl", "logs", "-l", f"serving.knative.dev/service={nom}", "--tail", str(lines)]
    result = await execute_command(command)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["stderr"])
    return {"logs": result["stdout"]}

# ──────────────────────────────────────────────
# POINT D’ENTRÉE LOCAL
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
