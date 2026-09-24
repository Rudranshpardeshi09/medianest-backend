# MediaNest backend

Django + DRF. Holds the site's editable content and serves it to the MediaNest
frontend.

The frontend is a **separate repository** (`Desktop/medianest`, deployed to
Vercel). This one deploys to PythonAnywhere. They are only joined by one HTTP
call, so either can be released without the other.

## How the two fit together

The frontend does **not** call this API in the browser. `scripts/fetch-content.mjs`
reads `/api/content/` once while Vite builds, downloads the images it references,
and bakes the whole payload into the bundle.

That means:

- a visitor never touches Django, so the site stays up and fast whatever this
  server is doing
- there is no loading state and no layout shift, which matters on a page built
  from scroll-triggered reveals
- **an edit in the admin is not live until the frontend is rebuilt.** On the
  PythonAnywhere free tier that rebuild has to be triggered by hand, because
  free accounts cannot make outbound calls to arbitrary hosts and so cannot
  call a Vercel deploy hook.

## What is built

`content` — one read endpoint, `GET /api/content/`, returning everything the
page renders:

| Key | Section it feeds |
| --- | --- |
| `settings` | figures several sections state (years, disciplines, hours, coverage) |
| `about` | About heading, copy, figure, and its three pillars |
| `services` / `service_strip` | the three cards and the strip beneath them |
| `disciplines` | the eight portfolio tiles and the films or stills behind each |
| `why_choose` | the heading and its reasons |
| `team` | the heading and the partners, with their lines and links |

`core` — `GET /api/health/`, which runs a real `SELECT 1` and answers 503 if the
database is unreachable.

**Not built:** `enquiries` (the contact form still discards what it receives).
Its `INSTALLED_APPS` and URL entries are marked with comments where they go.

## Run it locally

```bash
python -m venv .venv
.venv/Scripts/activate          # Windows;  source .venv/bin/activate elsewhere
pip install -r requirements.txt
cp .env.example .env

python manage.py migrate
python manage.py createsuperuser
python manage.py seed_content   # loads the content the site currently shows
python manage.py runserver
```

- Admin: http://127.0.0.1:8000/admin/
- Health: http://127.0.0.1:8000/api/health/

`manage.py` defaults to `config.settings.dev`.

### The database

SQLite, in development and in production both. A fresh clone boots with nothing
else installed, and PythonAnywhere keeps the file on a persistent disk.

That is not a compromise here. The browser never reads from this database — the
frontend bakes the content in at build time — so the only writes are a couple of
admin saves a day, which is the workload SQLite is best at. If that changes,
point `DATABASE_URL` at a Postgres and add `psycopg[binary]` to
`requirements.txt`; `base.py` parses the URL and nothing else needs touching.

### The seed

`seed_content` loads exactly what the site rendered before any of it was
editable, so the page must look identical after seeding. It never duplicates
rows and it leaves existing ones alone unless you pass `--force`, so running it
again after go-live cannot quietly undo someone's edit.

Images are copied from the frontend's `public/media`. `--media-from` defaults to
`../medianest/public/media`, which is correct when the two repositories sit side
by side.

## Deploying to PythonAnywhere

There is no config file for this — PythonAnywhere is set up through its own web
interface. Once:

1. **Clone both repositories**, side by side, so the seed can find the images:

   ```bash
   cd ~
   git clone https://github.com/Rudranshpardeshi09/medianest-backend.git
   git clone https://github.com/Rudranshpardeshi09/medianest.git
   ```

2. **Make a virtualenv** and install:

   ```bash
   mkvirtualenv --python=/usr/bin/python3.13 medianest
   pip install -r ~/medianest-backend/requirements.txt
   ```

3. **Add a web app** — "Manual configuration", the same Python version — then
   edit the WSGI file it creates (`/var/www/<user>_pythonanywhere_com_wsgi.py`):

   ```python
   import os, sys
   sys.path.insert(0, "/home/<user>/medianest-backend")
   os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.prod"
   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```

4. **Set the environment.** `prod.py` refuses to start without the first three.
   That is deliberate: a backend that silently boots with a dev secret is worse
   than one that fails.

   ```
   DJANGO_SECRET_KEY=<generate a new one — never the local value>
   DJANGO_ALLOWED_HOSTS=<user>.pythonanywhere.com
   CORS_ALLOWED_ORIGINS=https://<your-vercel-domain>
   CSRF_TRUSTED_ORIGINS=https://<user>.pythonanywhere.com
   DJANGO_ADMIN_PATH=<something other than "admin">
   ```

   PythonAnywhere has no environment panel, so these go in the WSGI file above
   the import, or in a `.env` beside `manage.py` (gitignored, so it will not be
   there after a clone).

5. **Migrate, seed and collect static:**

   ```bash
   cd ~/medianest-backend
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py seed_content
   python manage.py collectstatic --noinput
   ```

6. **Map static and media** in the web app's Static files table:

   | URL | Directory |
   | --- | --- |
   | `/static/` | `/home/<user>/medianest-backend/staticfiles` |
   | `/media/` | `/home/<user>/medianest-backend/media` |

7. Reload the web app, then check `https://<user>.pythonanywhere.com/api/health/`.

### Uploads and backups

PythonAnywhere's disk is persistent, so `media/` survives a reload and a
redeploy — unlike an ephemeral host, where uploads vanish on restart.

`media/` and `db.sqlite3` are both gitignored, which means **whatever the client
uploads exists only on that server**. Both are small; download them
occasionally. That is the whole backup.
