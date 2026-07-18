# Portfolio Backend API

A backend API built with **Python + FastAPI + SQLite**, powering Muhammad
Abdul Kareem's portfolio (Hero, About, Skills, Experience, Projects,
Contact Info, and Contact Messages). Connected to the live portfolio
frontend (Project 4) and includes a full admin security layer: login
lockout, and email-based 2FA on every write action.

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
   after first login (via the Account panel or `change_admin.py`).

3. **(Optional but recommended) Configure Gmail for 2FA codes** — see
   the "Email / 2FA Setup" section below. If skipped, verification
   codes print to the server console instead of emailing (fine for
   local development, not for real use).

4. **Run the server**:
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Explore the API**:
   - Interactive docs (Swagger UI): http://127.0.0.1:8000/docs
   - Health check: http://127.0.0.1:8000/

⚠️ **If you already had a `portfolio.db` from before this security
update**, delete it and re-run `python seed.py` — SQLite doesn't
auto-migrate new columns onto existing tables.

---

## Email / 2FA Setup (Gmail)

Verification codes are sent via Gmail SMTP using an **App Password**
(not your normal Gmail password — Google blocks plain-password SMTP
login for security).

**1. Generate a Gmail App Password:**
   - Go to https://myaccount.google.com/security
   - Turn on 2-Step Verification, if not already on (required for App Passwords)
   - Go to https://myaccount.google.com/apppasswords
   - Create a new App Password (name it e.g. "Portfolio Admin")
   - Copy the 16-character password Google generates

**2. Set two environment variables before starting the server:**

   Windows (PowerShell):
   ```powershell
   $env:GMAIL_ADDRESS="youraddress@gmail.com"
   $env:GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"
   ```

   macOS / Linux:
   ```bash
   export GMAIL_ADDRESS="youraddress@gmail.com"
   export GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"
   ```

   These need to be set in the same terminal session each time before
   running `uvicorn`, or added to your system/profile environment
   variables so they persist.

**3. Set which email actually *receives* the codes** — this is your
   admin account's `email` field, set via `seed.py` (already set to
   your address) or changeable later via `change_admin.py` or the
   Account panel in the dashboard.

**Without these two variables set**, the server still works — but
instead of emailing the code, it prints it directly to the terminal
running uvicorn, prefixed with `[DEV MODE — EMAIL NOT CONFIGURED]`.
This is intentional, so local development and testing don't require
real Gmail credentials.

---

## Security Features

### 2FA on every write action
Every action that adds, edits, or deletes data (POST/PUT/PATCH/DELETE)
requires email verification:

1. The admin panel calls the endpoint normally.
2. The server responds `428 Precondition Required`, emails a 6-digit
   code, and returns a `pending_id`.
3. The admin panel shows a code-entry popup automatically.
4. The panel resubmits the exact same request with the code attached.
5. The server verifies it and only then makes the actual change.

Codes expire after 5 minutes, allow at most 5 wrong guesses before
being invalidated, and can't be reused once consumed.

Read-only `GET` endpoints are never affected — you can browse skills,
projects, messages, etc. without any code prompts.

### Login lockout
After 5 consecutive wrong passwords, the account locks for 15 minutes
— even the correct password is rejected while locked. The counter
resets on any successful login.

### Changing your username/password
Available in the admin panel's **Account** page, or via
`change_admin.py` as a recovery tool if you're ever locked out of the
panel itself. Changing credentials requires your current password
**and** a 2FA code — the two most sensitive fields in the whole
system are the most heavily guarded.

---

## Endpoints

| Method | Path                          | Auth | 2FA | Description                          |
|--------|-------------------------------|------|-----|---------------------------------------|
| POST   | `/api/auth/login`             | No   | No  | Log in, returns a JWT token          |
| PUT    | `/api/auth/credentials`       | Yes  | Yes | Change username/password             |
| GET    | `/api/hero`                   | No   | No  | Get hero section content             |
| PUT    | `/api/hero`                   | Yes  | Yes | Update hero section                  |
| GET    | `/api/about`                  | No   | No  | Get about section content            |
| PUT    | `/api/about`                  | Yes  | Yes | Update about section                 |
| POST   | `/api/about/photo`            | Yes  | Yes | Upload profile photo                 |
| GET    | `/api/skills`                 | No   | No  | List all skill categories            |
| POST   | `/api/skills`                 | Yes  | Yes | Create a skill category              |
| PUT    | `/api/skills/{id}`            | Yes  | Yes | Update a skill category              |
| DELETE | `/api/skills/{id}`            | Yes  | Yes | Delete a skill category              |
| GET    | `/api/experience`             | No   | No  | List all experience entries          |
| POST   | `/api/experience`             | Yes  | Yes | Create an experience entry           |
| PUT    | `/api/experience/{id}`        | Yes  | Yes | Update an experience entry           |
| DELETE | `/api/experience/{id}`        | Yes  | Yes | Delete an experience entry           |
| GET    | `/api/projects`               | No   | No  | List all projects                    |
| POST   | `/api/projects`               | Yes  | Yes | Create a project                     |
| PUT    | `/api/projects/{id}`          | Yes  | Yes | Update a project                     |
| DELETE | `/api/projects/{id}`          | Yes  | Yes | Delete a project                     |
| GET    | `/api/contact-info`           | No   | No  | Get contact info                     |
| PUT    | `/api/contact-info`           | Yes  | Yes | Update contact info                  |
| POST   | `/api/messages`               | No   | No  | Submit a contact message (public)    |
| GET    | `/api/messages`               | Yes  | No  | List all contact messages (read-only)|
| PATCH  | `/api/messages/{id}/read`     | Yes  | Yes | Mark a message as read               |
| DELETE | `/api/messages/{id}`          | Yes  | Yes | Delete a message                     |

---

## Design notes (Project 2/3 grading context, still applies)

- **GET / POST / PUT / DELETE** implemented across multiple resources.
- **Input validation** automatic via Pydantic.
- **Correct HTTP status codes**: `200`, `201`, `204`, `401`, `404`, `422`,
  `423` (locked), `428` (verification required).
- **Self-documenting**: FastAPI auto-generates docs at `/docs`.
- **Database integrity**: Primary Keys, UNIQUE, NOT NULL, and CHECK
  constraints, verified to fire at the schema level.
- **SQL injection protection**: parameterized queries throughout via
  SQLAlchemy's ORM — no raw string concatenation anywhere.

---

## Admin panel

A separate admin panel (`admin.html` / `admin_Style.css` /
`admin_Script.js`) manages this content through a UI. Open `admin.html`
in a browser while this server is running.

Default login (change immediately via the Account panel):
- Username: `abdulkareem`
- Password: `ChangeMe123!`
- 2FA codes sent to: whatever email is set in `seed.py` / `change_admin.py`
