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

## Milestone 3 (Epic Generation)

Pre-req: Run Milestone 2 once so a Research Appendix exists for the project.

Generate epics (defaults to 6) with optional constraints:
- `POST /projects/{project_id}/epics/generate`
	- body example: `{ "constraints": "must support SSO" }`

Get latest epic batch:
- `GET /projects/{project_id}/epics`

Approve a generated epic batch (demo scenario):
- `POST /projects/{project_id}/epics/{batch_id}/approve`

Mermaid dependency graph is returned in the response as `mermaid` and also saved under the project run folder.

## Environment

Copy `.env.example` to `.env` and adjust as needed.
