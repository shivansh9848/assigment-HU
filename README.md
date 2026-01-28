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

## Environment

Copy `.env.example` to `.env` and adjust as needed.
