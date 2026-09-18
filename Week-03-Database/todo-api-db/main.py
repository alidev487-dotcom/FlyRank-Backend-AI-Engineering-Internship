from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from typing import Optional
import sqlite3

app = FastAPI(
    title="Task API",
    description="A CRUD API for managing a to-do list, backed by SQLite.",
    version="2.0"
)

DB_NAME = "tasks.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT 0
        )
    """)
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]

    if count == 0:
        cursor.executemany(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            [
                ("Buy milk", 0),
                ("Walk the dog", 1),
                ("Learn FastAPI", 0),
            ]
        )
        conn.commit()

    conn.close()

init_db()

class TaskCreate(BaseModel):
    title: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

@app.get("/")
def read_root():
    return {
        "name": "Task API",
        "version": "2.0",
        "endpoints": ["/tasks"]
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}