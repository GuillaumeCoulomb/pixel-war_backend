import time
from copy import deepcopy
from uuid import uuid4
from fastapi import Cookie, FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# configuration de l'API

app = FastAPI()

app.add_middleware(CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# classe userinfo qui permet d'implémenter le temps minimum entre deux nouveaux pixels d'un même utilisateur

class UserInfo:
    def __init__(self, carte):
        self.last_seen_map = deepcopy(carte)
        self.last_edited_time_nanos = 0


# classe carte qui contient les dimensions, les clés et id d'authentification des utilisateurs

class Carte:
    def __init__(self, nx: int, ny: int, timeout_nanos: int = int(1e9)):
        self.keys = set()
        self.user_ids = set()
        self.users = {}
        self.nx = nx
        self.ny = ny
        self.data = [[(0, 0, 0) for _ in range(ny)] for _ in range(nx)]
        self.timeout_nanos = timeout_nanos

    def create_new_key(self):
        key = str(uuid4())
        self.keys.add(key)
        return key

    def is_valid_key(self, key: str):
        return key in self.keys

    def create_new_user_id(self):
        user_id = str(uuid4())
        self.user_ids.add(user_id)
        return user_id

    def is_valid_user_id(self, user_id: str):
        return user_id in self.user_ids

cartes: dict[str, Carte] = {
    "0000": Carte(nx=10, ny=10),
}


# génération de la clé et stockage dans un cookie

@app.get("/api/v1/{nom_carte}/preinit")
async def preinit(nom_carte: str):
    carte = cartes.get(nom_carte)
    if not carte:
        return {"error": "Carte introuvable"}
    
    key = carte.create_new_key()
    res = JSONResponse({"key": key})
    res.set_cookie("key", key, max_age=360, samesite="lax")
    return res
   

# génération d'un identifiant

@app.get("/api/v1/{nom_carte}/init")
async def init(nom_carte: str,
               query_key: str = Query(alias="key"),
               cookie_key: str = Cookie(alias="key")):
    carte = cartes.get(nom_carte)
    if not carte:
        return {"error": "Carte introuvable"}
    if query_key != cookie_key:
        return {"error": "Clés non concordantes"}
    if not carte.is_valid_key(cookie_key):
        return {"error": "Clé invalide"}

    user_id = carte.create_new_user_id()
    carte.users[user_id] = UserInfo(carte.data)
    res = JSONResponse({
        "id": user_id,
        "nx": carte.nx,
        "ny": carte.ny,
        "data": carte.data
    })
    res.set_cookie("id", user_id, max_age=3600, samesite="lax")
    return res


# mise à jour de la carte en rafraichissant uniquement les pixels changés

@app.get("/api/v1/{nom_carte}/deltas")
async def deltas(nom_carte: str,
                 query_user_id: str = Query(alias="id"),
                 cookie_key: str = Cookie(alias="key"),
                 cookie_user_id: str = Cookie(alias="id")):
    carte = cartes.get(nom_carte)
    if not carte:
        return {"error": "Carte introuvable"}
    if not carte.is_valid_key(cookie_key):
        return {"error": "Clé invalide"}
    if query_user_id != cookie_user_id:
        return {"error": "ID utilisateur non concordant"}
    if not carte.is_valid_user_id(query_user_id):
        return {"error": "ID utilisateur invalide"}

    user_info = carte.users[query_user_id]
    user_carte = user_info.last_seen_map

    deltas = []
    for y in range(carte.ny):
        for x in range(carte.nx):
            if carte.data[x][y] != user_carte[x][y]:
                deltas.append((x, y, *carte.data[x][y]))
                user_carte[x][y] = carte.data[x][y]

    return {
        "deltas": deltas
    }

# placement pixels et vérification temps minimum

@app.post("/api/v1/{nom_carte}/edit")
async def edit_pixel(nom_carte: str,
                     x: int = Query(...),
                     y: int = Query(...),
                     r: int = Query(...),
                     g: int = Query(...),
                     b: int = Query(...),
                     cookie_user_id: str = Cookie(alias="id"),
                     cookie_key: str = Cookie(alias="key")):
    carte = cartes.get(nom_carte)
    if not carte:
        return {"status": "ignored"}
    if not carte.is_valid_key(cookie_key):
        return {"status": "ignored"}
    if not carte.is_valid_user_id(cookie_user_id):
        return {"status": "ignored"}

    now = round(time.time() * 1e9)
    user_info = carte.users[cookie_user_id]
    if now - user_info.last_edited_time_nanos < carte.timeout_nanos:
        return {"status": "ignored"}  # Silencieux

    if 0 <= x < carte.nx and 0 <= y < carte.ny:
        carte.data[x][y] = (r, g, b)
        user_info.last_edited_time_nanos = now
        return {"status": "ok"}
    return {"status": "ignored"}

# connexion avec html

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

@app.get("/")
async def root():
    return FileResponse("frontend/index.html")
