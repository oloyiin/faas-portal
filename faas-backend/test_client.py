import requests

API_URL = "http://localhost:8000"

code_python = b"""
def main(args):
    return {"message": "Hello from function!"}
"""

def deploy_function():
    files = {
        "code": ("func.py", code_python, "text/plain"),
    }
    data = {
        "nom": "test-fonction",
        "langage": "python",
        "version": "1.0"
    }
    resp = requests.post(f"{API_URL}/fonctions", files=files, data=data)
    print("Deploy:", resp.status_code, resp.json())

def list_functions():
    resp = requests.get(f"{API_URL}/fonctions")
    print("Fonctions:", resp.status_code, resp.json())

def get_function(name):
    resp = requests.get(f"{API_URL}/fonctions/{name}")
    print(f"Get {name}:", resp.status_code, resp.json())

def delete_function(name):
    resp = requests.delete(f"{API_URL}/fonctions/{name}")
    print(f"Delete {name}:", resp.status_code, resp.json())

if __name__ == "__main__":
    deploy_function()
    list_functions()
    get_function("test-fonction")
    delete_function("test-fonction")
