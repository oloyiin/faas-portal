import os
from dotenv import load_dotenv
import logging
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import urllib3

# Désactiver les warnings SSL (à utiliser avec précaution)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Charger les variables d'environnement depuis .env
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration des chemins pour les certificats
BASE_DIR = Path(__file__).parent
CERTS_DIR = BASE_DIR / "certs"

# Charger la variable d'environnement API_SERVER
#API_SERVER = os.getenv("API_SERVER", "https://172.16.50.100:16443")
API_SERVER = "https://134.214.202.225:16443"

# Chemins des certificats client et CA
CERT = (str(CERTS_DIR / "client.crt"), str(CERTS_DIR / "client.key"))
CACERT = str(CERTS_DIR / "cert.crt")

HEADERS = {"Content-Type": "application/json"}

def verify_certificates():
    """Vérifie que tous les certificats nécessaires sont présents"""
    required_certs = ["client.crt", "client.key", "cert.crt"]
    missing_certs = []

    for cert in required_certs:
        cert_path = CERTS_DIR / cert
        if not cert_path.exists():
            missing_certs.append(str(cert_path))

    if missing_certs:
        logger.error(f"Certificats manquants : {missing_certs}")
        raise FileNotFoundError(f"Certificats manquants : {missing_certs}")

    logger.info("Tous les certificats sont présents")

# Création de l'application FastAPI
app = FastAPI()

# Middleware CORS (autorise toutes les origines, à restreindre en prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Vérifications au démarrage de l'application"""
    try:
        verify_certificates()
    except FileNotFoundError as e:
        logger.error(f"Erreur de configuration : {e}")

@app.get("/")
def read_root():
    return {"message": "API FaaS Portal en ligne"}

# Modèle Pydantic pour une fonction (utile si tu ajoutes des endpoints POST/PUT)
class Fonction(BaseModel):
    nom: str
    langage: str
    version: str
    commande: Optional[List[str]] = []
    dependances: Optional[List[str]] = []

# Récupérer toutes les fonctions Knative
@app.get("/fonctions")
def get_fonctions():
    try:
        resp = requests.get(
            f"{API_SERVER}/apis/serving.knative.dev/v1/namespaces/default/services",
            cert=CERT,
            verify=CACERT,  # Désactive la vérification SSL (à sécuriser en prod)
            headers=HEADERS,
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        return [item["metadata"]["name"] for item in data.get("items", [])]

    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur de connexion : {e}")
        raise HTTPException(status_code=503, detail="Erreur de connexion au serveur Kubernetes")
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des fonctions : {e}")
        return {"message": "Erreur lors de l'appel à l'API", "erreur": str(e), "fonctions": []}

# Récupérer une fonction spécifique
@app.get("/fonctions/{nom}")
def get_fonction(nom: str):
    try:
        resp = requests.get(
            f"{API_SERVER}/apis/serving.knative.dev/v1/namespaces/default/services/{nom}",
            cert=CERT,
            verify=CACERT,
            headers=HEADERS,
            timeout=30
        )
        if resp.status_code == 404:
            return {"message": "Fonction non trouvée", "nom": nom}
        resp.raise_for_status()

        service = resp.json()
        url = service["status"].get("url")
        return {"nom": nom, "url": url}

    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur de connexion : {e}")
        raise HTTPException(status_code=503, detail="Erreur de connexion au serveur Kubernetes")
    except Exception as e:
        logger.error(f"Erreur : {e}")
        return {"message": "Erreur API", "erreur": str(e), "nom": nom}

# Récupérer l'état d'une fonction
@app.get("/fonctions/{nom}/etat")
def get_etat_fonction(nom: str):
    try:
        resp = requests.get(
            f"{API_SERVER}/apis/serving.knative.dev/v1/namespaces/default/services/{nom}",
            cert=CERT,
            verify=CACERT,
            headers=HEADERS,
            timeout=30
        )
        if resp.status_code == 404:
            return {"etat": "Inconnue", "message": "Fonction non trouvée"}
        resp.raise_for_status()

        service = resp.json()
        conditions = service["status"].get("conditions", [])
        for cond in conditions:
            if cond.get("type") == "Ready":
                return {"etat": cond.get("status")}
        return {"etat": "Inconnu"}

    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur de connexion : {e}")
        raise HTTPException(status_code=503, detail="Erreur de connexion au serveur Kubernetes")
    except Exception as e:
        logger.error(f"Erreur : {e}")
        return {"etat": "Erreur", "message": str(e)}

# Patch d'une fonction (mise à jour via JSON)
@app.patch("/fonctions/{nom}")
def patch_fonction(nom: str, patch_data: dict = Body(...)):
    try:
        resp = requests.patch(
            f"{API_SERVER}/apis/serving.knative.dev/v1/namespaces/default/services/{nom}",
            cert=CERT,
            verify=CACERT,
            headers={"Content-Type": "application/merge-patch+json"},
            json=patch_data,
            timeout=30
        )
        if resp.status_code == 404:
            return {"message": "Fonction non trouvée", "nom": nom}
        if resp.status_code >= 400:
            return {"message": "Échec du patch", "code": resp.status_code, "erreur": resp.text}

        return {"message": "Patch appliqué", "resultat": resp.json()}

    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur de connexion : {e}")
        raise HTTPException(status_code=503, detail="Erreur de connexion au serveur Kubernetes")
    except Exception as e:
        logger.error(f"Erreur lors du patch : {e}")
        return {"message": "Erreur interne", "erreur": str(e)}

# Supprimer une fonction Knative
@app.delete("/fonctions/{nom}")
def delete_fonction(nom: str):
    try:
        resp = requests.delete(
            f"{API_SERVER}/apis/serving.knative.dev/v1/namespaces/default/services/{nom}",
            cert=CERT,
            verify=CACERT,
            headers=HEADERS,
            timeout=30
        )
        if resp.status_code == 404:
            return {"message": "Fonction non trouvée", "nom": nom}
        if resp.status_code >= 400:
            return {"message": "Échec de la suppression", "code": resp.status_code, "erreur": resp.text}

        return {"message": f"Fonction '{nom}' supprimée"}

    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur de connexion : {e}")
        raise HTTPException(status_code=503, detail="Erreur de connexion au serveur Kubernetes")
    except Exception as e:
        logger.error(f"Erreur lors de la suppression : {e}")
        return {"message": "Erreur interne", "erreur": str(e)}

# Point d'entrée local
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)