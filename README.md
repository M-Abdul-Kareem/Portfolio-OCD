<div align="center">

# Portfolio — Backend & Frontend

A full-stack personal portfolio site: a static frontend paired with a self-hosted **FastAPI** backend, deployed on an **Oracle Cloud** VM behind **nginx** with a free auto-renewing TLS certificate.

[![Live Site](https://img.shields.io/badge/Live%20Site-visit-00d4ff?style=flat-square)](https://m-abdul-kareem.github.io/Portfolio-OCD/)
[![API Docs](https://img.shields.io/badge/API%20Docs-Swagger-009688?style=flat-square&logo=fastapi&logoColor=white)](https://abdulkareem-portfolio.duckdns.org/docs)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.138-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](#license)

**[Live Site](https://m-abdul-kareem.github.io/Portfolio-OCD/) · [Admin Panel](https://m-abdul-kareem.github.io/Portfolio-OCD/admin.html) · [API Docs](https://abdulkareem-portfolio.duckdns.org/docs)**

</div>

---

## Overview

This repository powers my personal portfolio site end-to-end:

- A **static frontend** (vanilla HTML/CSS/JS) presenting my background, skills, experience, and projects — auto-deployed to **GitHub Pages** on every push.
- A **dynamic FastAPI backend** that serves all site content from a SQLite database, and powers a full admin panel for editing that content — no redeploy needed to update the site.
- The backend runs on a **self-managed Oracle Cloud VM**, behind an **nginx** reverse proxy with a free **Let's Encrypt** TLS certificate, as a persistent **systemd** service.

Originally built on a serverless stack (Vercel + Neon Postgres + Cloudinary), it was later migrated to this self-hosted setup to eliminate serverless cold-start latency by running on an always-on server.

---

## ✨ Features

- **Fully dynamic content** — hero section, about, skills, experience, and projects are all editable through an admin panel and stored in SQLite, not hardcoded.
- **Secure admin authentication** — JWT-based sessions, bcrypt-hashed passwords, and **email-based two-factor authentication** for sensitive account changes.
- **Photo uploads** — profile photo managed through the admin panel and served directly by the API.
- **Zero cold starts** — backend runs persistently on a real VM, not a serverless function.
- **HTTPS everywhere** — free, auto-renewing TLS certificate via Certbot.
- **CI/CD for the frontend** — GitHub Actions automatically redeploys the `Frontend/` folder to GitHub Pages on every push to `main`.
- **Automated backups** — daily SQLite snapshots via a scheduled cron job, with rotation.

---

## 🏗️ Architecture

```
┌─────────────────┐        HTTPS        ┌──────────────────────────────────────┐
│  GitHub Pages     │  ───────────────▶  │  Oracle Cloud VM (Ubuntu 24.04)       │
│  (Frontend)        │                    │                                        │
│  index.html         │                    │  nginx  ── reverse proxy, TLS         │
│  admin.html          │                   │    │                                    │
└──────────┬───────┘                    │    ▼                                    │
           │                              │  systemd ── FastAPI / Uvicorn (127.0.0.1:8000)│
   GitHub Actions                        │    │                                    │
   auto-deploy on push                   │    ▼                                    │
                                          │  SQLite (portfolio.db)                 │
                                          └──────────────────────────────────────┘
```

| Layer | Technology |
|---|---|
| Frontend hosting | GitHub Pages (deployed via GitHub Actions) |
| Backend framework | FastAPI + SQLAlchemy |
| Database | SQLite |
| Auth | JWT (python-jose) + bcrypt + email-based 2FA |
| Process manager | systemd |
| Reverse proxy | nginx |
| TLS | Let's Encrypt / Certbot (auto-renewing) |
| DNS | DuckDNS (dynamic DNS subdomain) |
| Hosting | Oracle Cloud Infrastructure — Always Free tier VM |
| Firewall | ufw + OCI Security Lists |
| Intrusion protection | fail2ban |

---

## 📁 Project Structure

```
Portfolio-OCD/
├── Backend/
│   ├── app/
│   │   ├── routers/          # auth, hero, about, skills, experience, projects, contact-info
│   │   ├── main.py            # FastAPI app, CORS, middleware, static file serving
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── schemas.py         # Pydantic schemas
│   │   ├── database.py        # DB engine/session setup
│   │   ├── auth.py             # Password hashing, JWT handling
│   │   └── two_factor.py      # Email-based 2FA logic
│   ├── seed.py                 # Seeds the database with initial content + admin account
│   ├── change_admin.py         # CLI recovery tool to reset admin credentials
│   └── requirements.txt
├── Frontend/
│   ├── index.html / index_Script.js / index_Style.css
│   └── admin.html / admin_Script.js / admin_Style.css
├── Documents/                  # Project planning docs
└── .github/workflows/
    └── deploy-pages.yml        # Auto-deploys Frontend/ to GitHub Pages
```

---

## 🚀 Local Development

### Prerequisites
- Python 3.12+
- Git

### Backend Setup

```bash
git clone https://github.com/M-Abdul-Kareem/Portfolio-OCD.git
cd Portfolio-OCD/Backend

python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Set the required environment variables (see table below), then seed the database:

```bash
python seed.py
```

Run the development server:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`, with interactive docs at `http://127.0.0.1:8000/docs`.

### Frontend Setup

The frontend is plain static HTML/CSS/JS — no build step required. Open `Frontend/index.html` directly, or serve the folder with any static file server (e.g. VS Code's Live Server extension). Update `API_BASE` in `index_Script.js` and `admin_Script.js` to point at your local backend if testing against it.

---

## 🔐 Environment Variables

| Variable | Purpose |
|---|---|
| `PORTFOLIO_API_SECRET` | Secret key used to sign JWT session tokens |
| `ADMIN_USERNAME` | Initial admin username (used only by `seed.py`) |
| `ADMIN_PASSWORD` | Initial admin password (used only by `seed.py`) |
| `ADMIN_EMAIL` | Email address for 2FA codes and account notifications |
| `GMAIL_ADDRESS` | Gmail account used to send 2FA emails |
| `GMAIL_APP_PASSWORD` | Gmail App Password (not your regular password) for SMTP |

> Never commit real values for these — set them via your shell environment, a `.env` file (excluded via `.gitignore`), or your process manager's environment configuration.

---

## ☁️ Deployment

The backend is deployed on an Oracle Cloud Infrastructure Always Free tier VM:

1. Backend runs via **Uvicorn**, managed as a **systemd** service for auto-restart and boot persistence.
2. **nginx** reverse-proxies HTTPS traffic on ports 80/443 to Uvicorn on `127.0.0.1:8000`.
3. **Certbot** issues and auto-renews a free Let's Encrypt TLS certificate.
4. A **DuckDNS** subdomain provides a stable hostname pointing at the VM's public IP.
5. The frontend is deployed independently via a **GitHub Actions** workflow that publishes `Frontend/` to GitHub Pages on every push to `main`.
6. The database is backed up daily via a scheduled **cron** job with local rotation.

---

## 🛡️ Security Notes

- Admin passwords are hashed with **bcrypt** — never stored in plaintext.
- Sensitive account changes require **email-verified two-factor authentication**.
- CORS is restricted to the production frontend origin only.
- SSH access to the host server is **key-only** (password authentication disabled).
- **fail2ban** is active to mitigate brute-force login attempts at the network level.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

**Muhammad Abdul Kareem**
Software Engineering Student · [LinkedIn](https://www.linkedin.com/in/m-abdul-kareem5122006) · [Portfolio](https://m-abdul-kareem.github.io/Portfolio-OCD/)

</div>
