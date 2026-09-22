# MediaNest backend

Django + DRF. Serves CMS content to the MediaNest frontend and receives
contact enquiries.

The frontend is a **separate repository** (`Desktop/medianest`, deployed to
Vercel). This one deploys to Railway. They talk over HTTP only, so the two
can be developed and released independently.

See `IMPLEMENTATION PLAN.md` for the architecture, the phase order and the
open decision gates, and `BACKEND-PLAN.md` for what should be dynamic at all.
**Only Phase 0 (this skeleton) is built.**

## Run it

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate          # Windows;  source .venv/bin/activate elsewhere
pip install -r requirements.txt
cp .env.example .env

docker compose up -d db         # optional: Postgres. Without it, SQLite is used.

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

- Admin: http://127.0.0.1:8000/admin/
- Health: http://127.0.0.1:8000/api/health/

`manage.py` defaults to `config.settings.dev`. Production sets
`DJANGO_SETTINGS_MODULE=config.settings.prod`, which refuses to start without
`DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`.

## Deploying to Railway

Railway reads `railway.json`. Set these variables on the service:

```
DJANGO_SETTINGS_MODULE=config.settings.prod
DJANGO_SECRET_KEY=<generate>
DJANGO_ALLOWED_HOSTS=<your>.up.railway.app
CORS_ALLOWED_ORIGINS=https://<your-vercel-domain>
CSRF_TRUSTED_ORIGINS=https://<your>.up.railway.app
DJANGO_ADMIN_PATH=<something other than "admin">
```

Add the Postgres plugin and Railway injects `DATABASE_URL` itself; the
settings read it with no further configuration.

`prod.py` refuses to start without `DJANGO_SECRET_KEY`,
`DJANGO_ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`. That is deliberate: a
backend that silently boots with a dev secret is worse than one that fails.

**Uploaded media does not survive a redeploy on an ephemeral filesystem.**
Nothing uploads media yet (Phase 2), but attach a volume or object storage
before it does. See Decision Gate 3 in the plan.

## Not built yet

`enquiries` (Phase 1) and `content` (Phase 2). Their `INSTALLED_APPS` and URL
entries are marked with comments where they go.
