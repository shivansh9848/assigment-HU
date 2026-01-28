# Milestone 1 (Foundation)

FastAPI backend with:
- JWT authentication (User/Admin)
- Project creation + tracking (SQLite)
- PDF upload stored on filesystem (artifacts)
- Backlog generation "run" stub

## Setup

```powershell
C:/Users/raish/Desktop/assigment-HU/.venv/Scripts/python.exe -m pip install -r requirements.txt
```

## Run API

```powershell
C:/Users/raish/Desktop/assigment-HU/.venv/Scripts/python.exe -m uvicorn app.main:app --reload
```

Open Swagger UI:
- http://127.0.0.1:8000/docs

## Milestone 2 (Research)

Set `TAVILY_API_KEY` in `.env`.

Backlog run now triggers research in the background:
- `POST /projects/{project_id}/runs/backlog`

Poll progress events:
- `GET /runs/{run_id}/events`

View the persisted Research Appendix artifact:
- `GET /runs/{run_id}/research`

## Environment

Copy `.env.example` to `.env` and adjust as needed.
