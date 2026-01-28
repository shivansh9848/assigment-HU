# Simple Todo List — Requirements Pack (Sample)

## 1) Overview
A minimal API to manage personal todo items.

## 2) Core Features (MVP)
### 2.1 Authentication
- Users can sign up and log in.
- All todo endpoints require authentication.

### 2.2 Todo CRUD
A todo has:
- `title` (required, 1–120 chars)
- `description` (optional, up to 1000 chars)
- `is_done` (boolean)
- `created_at`, `updated_at`

Endpoints (high level):
- Create todo
- List todos
- Get todo by id
- Update todo
- Delete todo

### 2.3 Complete / Uncomplete
- User can mark a todo as done.
- User can mark a todo as not done.

### 2.4 Filtering
- List todos filtered by:
  - `status=done`
  - `status=todo`

## 3) Validation & Error Handling
- Reject empty title.
- Reject overly long title/description.
- Return clear 400 errors for validation.
- Return 404 if todo not found.

## 4) Security
- JWT auth.
- A user can only access their own todos.

## 5) Edge Cases
- Updating a todo that doesn’t exist.
- Attempting to access another user’s todo.
- Invalid filter value.

## 6) Success Criteria
- A user can create a todo, mark it done, filter, and delete it.
