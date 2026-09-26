\# Task API — with Dockerized PostgreSQL



A CRUD API for managing a to-do list, built with FastAPI (Python) and backed by PostgreSQL running in Docker. This is the third storage swap in the same project — memory (A1) → SQLite (A2) → containerized Postgres (this one). The API's routes and behavior have never changed.



\## Why Docker + Postgres?



Docker lets us run a real Postgres server without installing it directly on the machine — the exact same container works identically on any computer, killing "works on my machine" issues. Postgres is the same database engine used by a huge share of real-world backends.



\## Environment variables



This project uses a `.env` file for the database connection string (never hardcoded, never committed). Copy `.env.example` to `.env` and adjust if needed:



```

DATABASE\_URL=postgres://postgres:dev@db:5432/tasks

```



\## How to run this project (one command)



1\. Clone the repository and navigate to this folder:

```

cd Week-03-Database/todo-api-postgres

```



2\. Copy the example environment file:

```

copy .env.example .env

```



3\. Start the whole stack (app + database) with one command:

```

docker compose up

```



4\. The API will be running at `http://127.0.0.1:8000`. The database, table, and 3 example tasks are created automatically on first run.



\## Endpoints



| Method | Endpoint            | Description                        | Success Code | Error Codes |

|--------|----------------------|-------------------------------------|---------------|--------------|

| GET    | `/`                  | API info                            | 200           | -            |

| GET    | `/health`            | Health check                        | 200           | -            |

| GET    | `/tasks`             | List all tasks                      | 200           | -            |

| GET    | `/tasks/{task\_id}`   | Get a single task                   | 200           | 404          |

| POST   | `/tasks`             | Create a new task                   | 201           | 400          |

| PUT    | `/tasks/{task\_id}`   | Update a task's title/done status   | 200           | 400, 404     |

| DELETE | `/tasks/{task\_id}`   | Delete a task                       | 204           | 404          |



\## Example curl output



```

curl -i -X POST http://127.0.0.1:8000/tasks -H "Content-Type: application/json" -d "{\\"title\\":\\"Compose test\\"}"



HTTP/1.1 201 Created

content-type: application/json



{"id":4,"title":"Compose test","done":false}

```



\## Proving persistence



Created a task via POST, then ran `docker compose down` (which removes both containers) followed by `docker compose up`. Running `GET /tasks` again showed the task was still there — because the data lives in a named Docker volume (`taskdata`), not inside the container itself. This proves persistence survives a full stack restart, not just an app restart.



\## Database screenshots



\### Tables in the database

!\[Tables](screenshot-db.png)



\### Task rows

!\[Task rows](screenshot-db1.png)



\## What changed from Assignment 2 (SQLite)



Only the storage layer changed again — SQLite's file-based storage was replaced with a real PostgreSQL server running in a Docker container. The connection is now made via a `DATABASE\_URL` read from `.env`, using parameterized queries (`%s` placeholders) with the `psycopg` driver. The API's routes, request/response shapes, and status codes are all identical to Assignment 1 and 2 — proving that storage really is just an implementation detail.



\## One-command stack



`compose.yaml` defines two services:

\- \*\*api\*\* — built from the project's `Dockerfile`, runs the FastAPI app

\- \*\*db\*\* — the official `postgres` image, with a named volume for persistence



The `api` service waits for `db` to report healthy (via a `pg\_isready` healthcheck) before starting, avoiding race conditions on startup.

