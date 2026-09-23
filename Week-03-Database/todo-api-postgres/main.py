import os
import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI(
    title="Task API",
    description="A CRUD API for managing a to-do list, backed by PostgreSQL.",
    version="3.0"
)

def get_connection():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT FALSE
        )
    """)
    conn.commit()

    cur.execute("SELECT COUNT(*) AS count FROM tasks")
    count = cur.fetchone()["count"]

    if count == 0:
        cur.executemany(
            "INSERT INTO tasks (title, done) VALUES (%s, %s)",
            [
                ("Buy milk", False),
                ("Walk the dog", True),
                ("Learn FastAPI", False),
            ]
        )
        conn.commit()

    cur.close()
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
        "version": "3.0",
        "endpoints": ["/tasks"]
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/tasks")
def get_tasks():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return row

@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate):
    if not task.title or not task.title.strip():
        raise HTTPException(status_code=400, detail="Title is required and cannot be empty")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING *",
        (task.title, False)
    )
    new_task = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return new_task

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task_update: TaskUpdate):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    row = cur.fetchone()

    if row is None:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    new_title = row["title"]
    new_done = row["done"]

    if task_update.title is not None:
        if not task_update.title.strip():
            cur.close()
            conn.close()
            raise HTTPException(status_code=400, detail="Title cannot be empty")
        new_title = task_update.title

    if task_update.done is not None:
        new_done = task_update.done

    cur.execute(
        "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING *",
        (new_title, new_done, task_id)
    )
    updated_task = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return updated_task

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    row = cur.fetchone()

    if row is None:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    conn.commit()
    cur.close()
    conn.close()

    return Response(status_code=204)