# Deploying the TPF Animal System

Local development needs no configuration (`DEBUG` on, dev secret key, any host). For a real server, configure it with
environment variables — nothing secret lives in the code.

## 1. Environment variables

| Variable | Required | Meaning |
|---|---|---|
| `TPF_DEBUG` | yes | Set `0` in production. Default is on (development). |
| `TPF_SECRET_KEY` | yes in production | Long random string. The app refuses to start without it when `TPF_DEBUG=0`. |
| `TPF_ALLOWED_HOSTS` | yes in production | Comma-separated host names, e.g. `animals.police.go.tz`. |
| `TPF_CSRF_TRUSTED_ORIGINS` | if behind a proxy/other domain | e.g. `https://animals.police.go.tz` |
| `TPF_BEHIND_PROXY` | if a reverse proxy terminates HTTPS | `1` makes Django trust `X-Forwarded-Proto`. |
| `TPF_SSL_REDIRECT` | optional | Defaults to on in production; set `0` only if the proxy already redirects. |
| `TPF_HSTS_SECONDS` | optional | Defaults to one year. |

Generate a key:

```bash
python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

## 2. First deployment

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt   # Windows: .venv\Scripts\...
python manage.py migrate
python manage.py collectstatic --noinput        # writes ./staticfiles
python manage.py createsuperuser                # or reuse existing accounts
TPF_DEBUG=0 python manage.py check --deploy     # should list only the two optional HSTS notes
```

Run the app with a production server (e.g. `gunicorn tpf_animal_system.wsgi` on Linux, `waitress-serve` on Windows)
behind a web server such as nginx or IIS that:

* serves HTTPS (the QR codes on ID cards must point at this public address);
* serves `/static/` from `staticfiles/` and `/media/` from `media/` (Django does not serve them when `DEBUG=0`).

## 3. Daily reminders (certificates, vaccinations/deworming/farrier, expected births, stock)

Schedule this once a day (e.g. 07:00):

```bash
python manage.py run_daily_reminders            # add --dry-run to preview
```

* Linux cron: `0 7 * * * cd /srv/tpf && TPF_DEBUG=0 ... .venv/bin/python manage.py run_daily_reminders`
* Windows Task Scheduler: action = `.venv\Scripts\python.exe`, arguments = `manage.py run_daily_reminders`,
  start in the project folder, with the environment variables set for the task.

Each reminder is sent only once per threshold, so running it more than once a day is harmless.

## 4. Data and backups

* The database is SQLite (`db.sqlite3`). Back it up (copy the file while the app is idle, or use `sqlite3 db.sqlite3 ".backup file"`)
  and back up `media/` (animal photos, certificate scans) with it.
* For many simultaneous users or multiple servers, move to PostgreSQL (change `DATABASES` in `settings.py`).
* `db.sqlite3` is currently tracked in git even though `.gitignore` lists it. Untrack it before pushing real data:
  `git rm --cached db.sqlite3`.

## 5. Before printing ID cards

Print them from the deployed site, not `localhost` — the QR code stores the address of the server that rendered the page.
Reissuing a card (animal profile → ID card → Reissue) invalidates previously printed ones.

## 6. Changing the default admin passwords

Change every default/test account password before go-live, and give each person their own account and branch.
