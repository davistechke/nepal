# Nepal Relief Funds

A small Flask app for applying to disaster-relief funds, reviewing
applications as an admin, and paying out approved applicants.

## Structure (Flask blueprints)

```
app/
  __init__.py     create_app() factory - builds the app, registers
                   blueprints, and creates its own database + admin
                   account automatically on startup
  extensions.py   shared db / login_manager instances
  models.py       User, Application
  auth/routes.py  blueprint 'auth'  -> /login /register /logout
  main/routes.py  blueprint 'main'  -> / /apply /account /account/payout/<ref>
  admin/routes.py blueprint 'admin' -> /admin /admin/status/<ref> /admin/recent
  templates/, static/
wsgi.py           entry point (python wsgi.py locally, gunicorn wsgi:app hosted)
Procfile          for Render/Heroku-style hosts
render.yaml        Render blueprint config for one-click deploy
```

Every route requires login except the homepage and login/register
themselves. `/admin/*` additionally requires `is_admin=True` on the
account.

## Running locally

```bash
pip install -r requirements.txt
python wsgi.py
```

On startup the app creates `relief.db` (SQLite) and its tables itself -
there's no separate migration step. It also reads `.env` in the project
root and, if `ADMIN_USERNAME`/`ADMIN_PASSWORD` are set there, creates or
promotes that account to admin every time it starts. A `.env` with a
working admin login is already included:

```
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeme123
ADMIN_FULL_NAME=Admin
SECRET_KEY=dev-secret-change-me
```

Log in at `/login` with those credentials, then visit `/admin`.
**Change `ADMIN_PASSWORD` and `SECRET_KEY` before this goes anywhere
public** - right now they're plaintext in `.env`.

Alternatively, create an admin without env vars:

```bash
flask --app wsgi create-admin someusername "Full Name" a-strong-password
```

## Deploying (e.g. on Render)

1. Push this folder to a Git repo, connect it to Render as a **Web
   Service** (or use the included `render.yaml` blueprint).
2. Build command: `pip install -r requirements.txt`
   Start command: `gunicorn wsgi:app`
3. Set environment variables in Render's dashboard: `SECRET_KEY`,
   `ADMIN_USERNAME`, `ADMIN_PASSWORD` (and `ADMIN_FULL_NAME`
   optionally). The app seeds/promotes that admin account the moment
   it boots - no shell access or manual command needed.
4. SQLite works immediately but Render's free-tier filesystem is not
   persistent (data resets on redeploy). For real use, attach a Render
   Postgres database - the app reads `DATABASE_URL` automatically if
   it's set and will use that instead of SQLite, no code changes
   needed.

## Notes / limitations

This is a prototype: don't submit real ID/passport numbers or bank
details into it as-is. A production version would need proper
identity verification, encryption for sensitive fields, and a real
payments backend rather than a plain stored account number.
