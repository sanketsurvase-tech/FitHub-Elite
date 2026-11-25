# FitHub Elite

FitHub Elite is a gym operations platform with a Django REST Framework API and a
Next.js App Router dashboard. The API owns authentication, role permissions,
member records, memberships, attendance, payments, training plans, classes,
inventory, communications and Mistral-powered assistance.

## Requirements

- Python 3.11 or newer
- Node.js 20.9 or newer and npm
- PostgreSQL 15 or newer
- A Mistral API key for the optional AI assistant

## Local setup (Windows / VS Code)

1. Install PostgreSQL and create a database named `fithub_elite` (the default
   local connection is `postgres` on `localhost:5432`).
2. Open this folder in VS Code. In a terminal, create the backend environment:

   ```powershell
   cd backend
   py -3 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   Copy-Item .env.example .env
   ```

3. Edit `backend/.env`: set a long random `DJANGO_SECRET_KEY` and the
   PostgreSQL `DATABASE_URL` for your local database. Optionally set
   `MISTRAL_API_KEY`; AI endpoints return a clear service-unavailable response
   until configured, with no alternate paid provider.
4. Create the schema and an administrator:

   ```powershell
   python manage.py migrate
   python manage.py createsuperuser
   ```

   The API is at `http://127.0.0.1:8000/api/`; the browsable API and Django
   admin are available at `/api/` and `/admin/`.
   To load optional local sample records, run `python manage.py seed_sample_data`
   and enter a temporary password when prompted. The command creates sample
   trainer and member accounts; do not use sample accounts in production.
   Start the backend with `python manage.py runserver`.
5. In another terminal, configure and start the frontend:

   ```powershell
   cd frontend
   npm install
   Copy-Item .env.example .env.local
   npm run dev
   ```

   Open `http://localhost:3000`. Sign in with an API user. Create staff and
   member accounts in Django admin, or use the registration endpoint to create
   a member account. Never commit either `.env` file.

## Environment

- `backend/.env`: `DJANGO_SECRET_KEY`, `DATABASE_URL`; optionally
  `MISTRAL_API_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, and
  `CORS_ALLOWED_ORIGINS`
- `frontend/.env.local`: `NEXT_PUBLIC_API_BASE_URL`

Local PostgreSQL settings are provided as a `DATABASE_URL` in
`backend/.env.example`; change the username/password to match your local
PostgreSQL installation. Before deployment, never commit `.env` files.

## Deploy the backend to Render

1. Push this repository to GitHub and create a Render PostgreSQL database.
2. In Render, create a **Blueprint** from this repository (or create a Python
   web service with `backend` as its root directory). The [render.yaml](./render.yaml)
   configures Gunicorn, static assets and the API health check.
3. Copy the database's **Internal Database URL** into the web service's
   `DATABASE_URL` environment variable (the backend requires PostgreSQL in
   production). Keep the database and web service in the same Render region.
4. Set the web service environment variables:
   - `DJANGO_SECRET_KEY`: generate a new secret (Render can generate it).
   - `DJANGO_DEBUG`: `false`.
   - `DJANGO_ALLOWED_HOSTS`: your exact API hostname, such as
     `fithub-elite-api.onrender.com` (no scheme).
   - `CORS_ALLOWED_ORIGINS`: your exact Vercel production origin, such as
     `https://fithub-elite.vercel.app` (include the scheme, no trailing slash).
   - `MISTRAL_API_KEY`: optional; add it as a secret in Render if using AI.

   At runtime, the start command runs migrations and collects Django admin
   static assets against the deployed service configuration before starting
   Gunicorn. The web service starts only if both commands succeed. Migrations
   are safe to rerun: Django applies only unapplied migrations and does not
   reset or drop the database. The health endpoint
   `/api/health/` checks database readiness and returns HTTP 503 if the
   database or core schema is unavailable.
   If the web service was created manually rather than from the Blueprint,
   set its Start Command to
   `python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn fithub.wsgi:application --bind 0.0.0.0:$PORT`.

## Deploy the frontend to Vercel

1. Import the same GitHub repository into Vercel and set **Root Directory** to
   `frontend`.
2. Add this environment variable for Production (and Preview if desired):
   - `NEXT_PUBLIC_API_BASE_URL`: `https://<your-render-api-hostname>/api`
     (the frontend also accepts the Render origin without `/api`).
3. Deploy or redeploy. Add each Vercel origin that should call the API to the
   Render `CORS_ALLOWED_ORIGINS` value as a comma-separated list.

`NEXT_PUBLIC_API_BASE_URL` is embedded into the frontend at build time. After
changing it in Vercel, redeploy the frontend for the new value to take effect.

Do not put `DJANGO_SECRET_KEY`, `DATABASE_URL` or `MISTRAL_API_KEY` in Vercel.
Only the API base URL belongs in the frontend environment.

**Uploaded member files:** Render's default filesystem is ephemeral. Configure
a Render persistent disk and set `MEDIA_ROOT` to its mount path before relying
on uploaded profile photos and documents in production. Member photos,
documents and progress photos are served through authenticated API endpoints,
not public `/media/` URLs. An object-storage backend is not included.

## Features

- Role-aware JWT authentication (Admin, Trainer, Receptionist, Member).
- Member records, packages and memberships, payment and attendance records.
- Staff, workout plans and set/rep logs, meal plans and food diaries, fitness
  measurements, classes and bookings.
- Equipment and maintenance, feedback, announcements, notifications and audit
  records.
- Search, filtering, pagination, downloadable CSV/Excel/PDF exports, QR check-in, and a
  Mistral Codestral assistant for draft recommendations.
- Responsive dashboard with KPI summaries and a light/dark color theme.

## API and security notes

The API is rooted at `/api/`. Obtain JWTs from `POST /api/auth/login/` (or
`/api/auth/token/`) and send
the access token as `Authorization: Bearer <token>`. Member registration is
`POST /api/auth/register/`. JWTs are held in browser session storage; deploy
behind HTTPS and set an appropriate production secret before exposing the app.
The API validates uploads, restricts CORS to the local frontend by default,
and limits sensitive records by role. AI requests are sent only to Mistral
from the backend and are never given access to the API key by the browser.

## Development checks

```powershell
cd backend
python manage.py check
python manage.py test
python manage.py send_membership_reminders
cd ..\frontend
npm run lint
npm run build
```

Schedule `python manage.py send_membership_reminders` once per day in the
deployment scheduler to expire memberships, restore completed freezes and
create in-app expiry reminders.
