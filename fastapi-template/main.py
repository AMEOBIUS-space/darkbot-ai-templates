#!/usr/bin/env python3
"""FastAPI Backend Template — production-ready REST API with auth, SQLite, WebSocket."""
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
import sqlite3, jwt, hashlib, os, json

app = FastAPI(title="DarkBot API", version="1.0")
security = HTTPBearer()
SECRET = os.getenv("JWT_SECRET", "change-me")

DB = "app.db"
def get_db():
    conn = sqlite3.connect(DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT, created TEXT);
    CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, data TEXT, created TEXT);
    """)
    db.commit()

init_db()

class UserCreate(BaseModel):
    email: str
    password: str

class ItemCreate(BaseModel):
    name: str
    data: str = ""

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def make_token(user_id: int) -> str:
    return jwt.encode({"sub": str(user_id), "exp": datetime.utcnow() + timedelta(days=7)}, SECRET, algorithm="HS256")

def get_current_user(cred: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(cred.credentials, SECRET, algorithms=["HS256"])
        return int(payload["sub"])
    except Exception:
        raise HTTPException(401, "Invalid token")

@app.post("/register")
def register(user: UserCreate):
    db = get_db()
    try:
        db.execute("INSERT INTO users (email, password, created) VALUES (?, ?, ?)",
                   (user.email, hash_pw(user.password), datetime.now().isoformat()))
        db.commit()
        return {"token": make_token(db.execute("SELECT last_insert_rowid()").fetchone()[0])}
    except sqlite3.IntegrityError:
        raise HTTPException(400, "Email exists")

@app.post("/login")
def login(user: UserCreate):
    db = get_db()
    row = db.execute("SELECT id FROM users WHERE email=? AND password=?", (user.email, hash_pw(user.password))).fetchone()
    if not row: raise HTTPException(401, "Invalid credentials")
    return {"token": make_token(row["id"])}

@app.post("/items")
def create_item(item: ItemCreate, uid: int = Depends(get_current_user)):
    db = get_db()
    db.execute("INSERT INTO items (user_id, name, data, created) VALUES (?, ?, ?, ?)",
               (uid, item.name, item.data, datetime.now().isoformat()))
    db.commit()
    return {"id": db.execute("SELECT last_insert_rowid()").fetchone()[0]}

@app.get("/items")
def list_items(uid: int = Depends(get_current_user)):
    db = get_db()
    return [dict(r) for r in db.execute("SELECT * FROM items WHERE user_id=?", (uid,)).fetchall()]

@app.websocket("/ws/{token}")
async def ws_endpoint(ws: WebSocket, token: str):
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        uid = int(payload["sub"])
    except Exception:
        raise WebSocketDisconnect(code=4001)
    await ws.accept()
    while True:
        data = await ws.receive_text()
        await ws.send_text(json.dumps({"user": uid, "echo": data, "ts": datetime.now().isoformat()}))
