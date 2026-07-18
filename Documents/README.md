# Portfolio Backend API

A standalone backend API built with **Python + FastAPI + SQLite**.

This was built as an extension of Project 2 (Backend API Development) —
it manages content for Muhammad Abdul Kareem's portfolio (Hero, About,
Skills, Experience, Projects, Contact Info, and Contact Messages) but
is **not currently connected to the live portfolio frontend** — it runs
entirely on its own.

---

## Setup

1. **Install dependencies** (Python 3.9+ required):
   ```bash
   pip install -r requirements.txt
   ```

2. **Seed the database** (creates `portfolio.db`, your admin account, and
   pre-fills it with your current portfolio content):
   ```bash
   python seed.py
   ```
   This prints your admin login credentials — **change the password**
   after first login if you ever deploy this publicly.

3. **Run the server**:
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Explore the API**:
   - Interactive docs (Swagger UI): http://127.0.0.1:8000/docs
   - Health check: http://127.0.0.1:8000/

---

## Endpoints

| Method | Path                          | Auth required | Description                          |
|--------|-------------------------------|----------------|---------------------------------------|
| POST   | `/api/auth/login`             | No             | Log in, returns a JWT token          |
| GET    | `/api/hero`                   | No             | Get hero section content             |
| PUT    | `/api/hero`                   | Yes            | Update hero section                  |
| GET    | `/api/about`                  | No             | Get about section content            |
| PUT    | `/api/about`                  | Yes            | Update about section                 |
| GET    | `/api/skills`                 | No             | List all skill categories            |
| GET    | `/api/skills/{id}`            | No             | Get one skill category               |
| POST   | `/api/skills`                 | Yes            | Create a skill category              |
| PUT    | `/api/skills/{id}`            | Yes            | Update a skill category              |
| DELETE | `/api/skills/{id}`            | Yes            | Delete a skill category              |
| GET    | `/api/experience`             | No             | List all experience entries          |
| GET    | `/api/experience/{id}`        | No             | Get one experience entry             |
| POST   | `/api/experience`             | Yes            | Create an experience entry           |
| PUT    | `/api/experience/{id}`        | Yes            | Update an experience entry           |
| DELETE | `/api/experience/{id}`        | Yes            | Delete an experience entry           |
| GET    | `/api/projects`               | No             | List all projects                    |
| GET    | `/api/projects/{id}`          | No             | Get one project                      |
| POST   | `/api/projects`               | Yes            | Create a project                     |
| PUT    | `/api/projects/{id}`          | Yes            | Update a project                     |
| DELETE | `/api/projects/{id}`          | Yes            | Delete a project                     |
| GET    | `/api/contact-info`           | No             | Get contact info                     |
| PUT    | `/api/contact-info`           | Yes            | Update contact info                  |
| POST   | `/api/messages`               | No             | Submit a contact message (public)    |
| GET    | `/api/messages`                | Yes            | List all contact messages            |
| PATCH  | `/api/messages/{id}/read`     | Yes            | Mark a message as read               |
| DELETE | `/api/messages/{id}`           | Yes            | Delete a message                     |

---

## How auth works

1. `POST /api/auth/login` with `{"username": "...", "password": "..."}`
   returns `{"access_token": "...", "token_type": "bearer"}`.
2. Send that token on every write request:
   `Authorization: Bearer <access_token>`
3. Tokens expire after 12 hours.

---

## Design notes (for Project 2 grading context)

- **GET / POST / PUT / DELETE** are all implemented across multiple resources.
- **Input validation** is automatic via Pydantic — required fields, string
  length limits, and email format (on contact messages) are all enforced
  before any code runs, satisfying "Never Trust the Client."
- **Correct HTTP status codes** are used throughout: `200` (OK), `201`
  (Created), `204` (No Content on delete), `401` (Unauthorized), `404`
  (Not Found), `422` (Validation Error).
- **Database-level integrity constraints** (not just application-level
  validation): `NOT NULL` on required fields, `UNIQUE` on the admin
  username, and `CHECK` constraints enforcing `sort_order >= 0` on
  Skills/Experience/Projects and a minimum message length on contact
  submissions. These fire even if a future bug in application code
  tried to insert bad data directly.
- **SQL injection protection**: every query goes through SQLAlchemy's
  query builder, which automatically parameterizes values — there is
  no raw string concatenation anywhere in this codebase.
- **Self-documenting**: FastAPI auto-generates interactive docs at `/docs`,
  directly addressing the brief's "if it isn't documented, it doesn't
  exist" principle with zero extra effort.
- **RESTful naming**: resources are nouns (`/projects`), methods are verbs
  (GET/POST/PUT/DELETE) — no `/getProjects` or `/createProject` anywhere.

---

## Admin panel

A separate admin panel (`admin.html` / `admin.css` / `admin.js`) is provided
to manage this content through a UI instead of raw API calls. Open
`admin.html` in a browser while this server is running.

Default login (change after first use):
- Username: `abdulkareem`
- Password: `ChangeMe123!`

This admin panel is **not connected to your live portfolio site** —
it only manages this backend's database. Wiring the live site to read
from this API is a separate step, by design, for now.
