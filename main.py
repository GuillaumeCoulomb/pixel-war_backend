import time
from copy import deepcopy
from uuid import uuid4
from fastapi import Cookie, FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI()

app.add_middleware(CORSMiddleware,
    allow_origins=["*", "http://localhost:8000"],
    allow_credentials=True
    )

class UserInfo:
    last_edited_time_nanos : int
    last_seen_map: list[list[tuple[int, int, int]]]

    def __init__(self, carte):
        self.last_seen_map = deepcopy(carte)
        self.last_edited_time_nanos = round(time.time()) * 1000000000



class Carte:

    def __init__(self, nx: int, ny: int, timeout_nanos: int = int(1e9)):
        self.keys = set()
        self.user_ids = set()
        self.users = {}
        self.nx = nx
        self.ny = ny
        self.data = [[(255, 255, 255) for _ in range(ny)] for _ in range(nx)]
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

cartes = {
    "0000": Carte(nx=10, ny=10),
}

@app.get("/api/v1/{nom_carte}/preinit")
async def preinit(nom_carte: str):
    carte = cartes.get(nom_carte)
    if carte is None:
        return {"error": "Je n'ai pas trouvé la carte."}

    key = carte.create_new_key()
    res = JSONResponse({"key": key})
    res.set_cookie("key", key, secure=False, max_age=3600, samesite="lax")
    return res
   

@app.get("/api/v1/{nom_carte}/init")
async def init(
    nom_carte: str,
    query_key: str = Query(alias="key"),
    cookie_key: str = Cookie(alias="key")
):
    carte = cartes.get(nom_carte)
    if carte is None:
        return {"error": "Je n'ai pas trouvé la carte."}
    if query_key != cookie_key or not carte.is_valid_key(cookie_key):
        return {"error": "Clé invalide ou non correspondante"}

    user_id = carte.create_new_user_id()
    carte.users[user_id] = UserInfo(carte.data)

    res = JSONResponse({
        "id": user_id,
        "nx": carte.nx,
        "ny": carte.ny,
        "data": carte.data,
    })
    res.set_cookie("id", user_id, secure=False, samesite="lax", max_age=3600)
    return res




@app.get("/api/v1/{nom_carte}/deltas")
async def get_deltas(
    nom_carte: str,
    query_user_id: str = Query(alias="id"),
    cookie_key: str = Cookie(alias="key"),
    cookie_user_id: str = Cookie(alias="id")
):
    carte = cartes.get(nom_carte)
    if carte is None:
        return {"error": "Carte non trouvée"}
    if not carte.is_valid_key(cookie_key):
        return {"error": "Clé invalide"}
    if query_user_id != cookie_user_id or not carte.is_valid_user_id(cookie_user_id):
        return {"error": "ID utilisateur invalide"}

    user_info = carte.users[cookie_user_id]
    deltas = []

    for x in range(carte.nx):
        for y in range(carte.ny):
            if carte.data[x][y] != user_info.last_seen_map[x][y]:
                deltas.append((x, y, *carte.data[x][y]))
                user_info.last_seen_map[x][y] = carte.data[x][y]

    return {
        "deltas": deltas
    }

