# MediMate Backend (FastAPI)

Backend API for a health chatbot: users can chat about health questions, upload
medical reports for AI summarization, log BP/glucose/weight vitals, and get
AI-generated diet plans + daily schedules (medication/meal/exercise reminders).

**⚠️ Not a medical device.** This app gives general information only and is not a
substitute for professional medical advice, diagnosis, or treatment. Make sure your
frontend surfaces that disclaimer to users too.

## Tech stack
- **FastAPI** + **SQLAlchemy** (PostgreSQL)
- **Groq** (LLM API) for chat, report summaries, diet plan generation
- **JWT** auth (python-jose + passlib/bcrypt)
- **pdfplumber** for PDF report text extraction (+ optional Tesseract OCR for photos/scans)

## 1. Local setup

```bash
cd medimate-backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:
- `DATABASE_URL` — point at your Postgres instance
- `GROQ_API_KEY` — get a free key at https://console.groq.com
- `SECRET_KEY` — generate with `openssl rand -hex 32`
- `FRONTEND_ORIGINS` — your React app's URL(s)

### Run Postgres + API with Docker (recommended, easiest)

```bash
docker compose up --build
```

This starts Postgres and the API together. API will be at `http://localhost:8000`.

### Or run manually (Postgres installed separately)

```bash
uvicorn app.main:app --reload --port 8000
```

Tables are auto-created on startup for this MVP. Before you have real user data in
production, switch to Alembic migrations (`pip install alembic`) so schema changes
don't require dropping tables.

Interactive API docs: `http://localhost:8000/docs`

## 2. API overview

All endpoints except `/auth/register` and `/auth/login` require:
`Authorization: Bearer <token>`

| Area | Endpoint | Purpose |
|---|---|---|
| Auth | `POST /auth/register` | Create account, returns JWT |
| Auth | `POST /auth/login` | Login (OAuth2 form: `username`=email, `password`) |
| Auth | `GET /auth/me` | Get profile |
| Auth | `PUT /auth/me` | Update profile (age, diabetes/BP flags, etc.) |
| Chat | `POST /chat/message` | Send a message, get AI reply + full history |
| Chat | `GET /chat/history` | Get chat history |
| Reports | `POST /reports/upload` | Upload PDF/image report, get AI summary |
| Reports | `GET /reports` | List reports |
| Reports | `GET /reports/{id}` | Report detail incl. extracted text |
| Reports | `DELETE /reports/{id}` | Delete a report |
| Vitals | `POST /vitals` | Log a BP / glucose / weight / heart-rate reading |
| Vitals | `GET /vitals?type=blood_pressure` | List readings, optional filter |
| Vitals | `GET /vitals/summary` | Latest glucose + BP snapshot |
| Diet | `POST /diet/generate` | Generate a new AI diet plan (uses profile + goal) |
| Diet | `GET /diet/current` | Get active diet plan |
| Diet | `GET /diet/history` | Past diet plans |
| Schedule | `POST /schedule` | Add a reminder (medication/meal/exercise/vitals check) |
| Schedule | `GET /schedule` | List active reminders |
| Schedule | `DELETE /schedule/{id}` | Remove a reminder |

Full request/response schemas are in `/docs` (Swagger UI) once the server is running.

## 3. Connecting your React frontend

1. Set `FRONTEND_ORIGINS` in `.env` to your React dev/prod URL(s), comma-separated.
2. On login/register, store the returned `access_token` (e.g. in memory + httpOnly
   cookie, or localStorage if you accept the XSS tradeoff) and attach it as
   `Authorization: Bearer <token>` on every subsequent request.
3. For `/reports/upload`, send `multipart/form-data` with a `file` field:
   ```js
   const formData = new FormData();
   formData.append("file", fileInput.files[0]);
   await fetch(`${API_URL}/reports/upload`, {
     method: "POST",
     headers: { Authorization: `Bearer ${token}` },
     body: formData,
   });
   ```
4. `/auth/login` expects `application/x-www-form-urlencoded` (OAuth2 password flow),
   not JSON:
   ```js
   const body = new URLSearchParams({ username: email, password });
   await fetch(`${API_URL}/auth/login`, {
     method: "POST",
     headers: { "Content-Type": "application/x-www-form-urlencoded" },
     body,
   });
   ```

## 4. OCR for scanned/photographed reports (optional)

PDF text extraction works out of the box. If you also want OCR for photos of
reports, install the system package:
- Docker: already included in the provided `Dockerfile`
- Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
- Mac: `brew install tesseract`

Without it, image uploads still work but text extraction returns empty and the
summary will say OCR isn't configured.

## 5. Deployment

You haven't picked a platform yet — here are the three easiest paths:

### Option A: Render or Railway (fastest, recommended to start)
1. Push this repo to GitHub.
2. Create a new **Web Service** from the repo (both platforms auto-detect the
   `Dockerfile`).
3. Add a managed **PostgreSQL** add-on (both offer one-click Postgres) and copy its
   connection string into `DATABASE_URL`.
4. Set the other env vars (`GROQ_API_KEY`, `SECRET_KEY`, `FRONTEND_ORIGINS`) in the
   platform's dashboard.
5. Deploy. You'll get a public HTTPS URL — put that in your React app's API base URL.

### Option B: A VPS (DigitalOcean/Linode/etc.)
1. `git clone` your repo onto the server.
2. `cp .env.example .env` and fill in production values.
3. `docker compose up -d --build` — this runs Postgres + API together.
4. Put Nginx or Caddy in front for HTTPS (Caddy auto-issues Let's Encrypt certs with
   almost no config) and reverse-proxy to `localhost:8000`.

### Option C: AWS/GCP/Azure
Same Docker image works on ECS/Cloud Run/App Service. Use a managed Postgres
(RDS/Cloud SQL/Azure Database for PostgreSQL) instead of running Postgres yourself.
Cloud Run or App Service are the least setup if you want to stay serverless-ish.

**Before going to production on any option:**
- Rotate `SECRET_KEY` to a real random value and keep it out of git.
- Switch schema management from `create_all` to Alembic migrations.
- Put uploaded report files in object storage (S3/GCS) instead of local disk,
  since containers on most PaaS platforms don't persist disk across deploys.
- Add rate limiting on `/chat/message` and `/reports/upload` to control Groq usage costs.

## 6. Project structure

```
app/
  core/        # config, db session, security/JWT
  models/      # SQLAlchemy models
  schemas/     # Pydantic request/response schemas
  services/    # Groq LLM calls, report text extraction
  api/routes/  # auth, chat, reports, vitals, diet/schedule
  main.py      # FastAPI app + router wiring
```
