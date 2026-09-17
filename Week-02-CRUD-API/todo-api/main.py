from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from typing import Optional

app = FastAPI(
    title="Task API",
    description="A simple in-memory CRUD API for managing a to-do list.",
    version="1.0"
)

tasks = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Walk the dog", "done": True},
    {"id": 3, "title": "Learn FastAPI", "done": False},
]

class TaskCreate(BaseModel):
    title: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

@app.get("/", summary="API info", description="Returns basic information about this API.")
def read_root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }

@app.get("/health", summary="Health check", description="Returns the server's health status.")
def health_check():
    return {"status": "ok"}

@app.get("/tasks", summary="List all tasks", description="Returns the full list of tasks.")
def get_tasks():
    return tasks

@app.get("/tasks/{task_id}", summary="Get one task", description="Returns a single task by its id. Returns 404 if not found.")
def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

@app.post("/tasks", status_code=201, summary="Create a task", description="Creates a new task. Title is required and cannot be empty.")
def create_task(task: TaskCreate):
    if not task.title or not task.title.strip():
        raise HTTPException(status_code=400, detail="Title is required and cannot be empty")

    new_id = max((t["id"] for t in tasks), default=0) + 1
    new_task = {"id": new_id, "title": task.title, "done": False}
    tasks.append(new_task)
    return new_task

@app.put("/tasks/{task_id}", summary="Update a task", description="Updates a task's title and/or done status. Returns 404 if not found.")
def update_task(task_id: int, task_update: TaskUpdate):
    for task in tasks:
        if task["id"] == task_id:
            if task_update.title is not None:
                if not task_update.title.strip():
                    raise HTTPException(status_code=400, detail="Title cannot be empty")
                task["title"] = task_update.title
            if task_update.done is not None:
                task["done"] = task_update.done
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task", description="Deletes a task by its id. Returns 404 if not found.")
def delete_task(task_id: int):
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            tasks.pop(i)
            return Response(status_code=204)
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")