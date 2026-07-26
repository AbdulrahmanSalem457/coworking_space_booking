# Coworking Space Booking Platform

A full-stack coworking space booking demo: **Django + DRF + drf-yasg** on the
backend, **vanilla HTML/CSS/JS** (ES modules, no frameworks) on the frontend.

## Project architecture

```
coworking_space_booking/
├── backend/                   Django project (API only)
│   ├── config/                 settings, root urls, wsgi/asgi
│   ├── accounts/                CustomUser model, register/login/me
│   ├── spaces/                  Space model, SpaceViewSet
│   ├── bookings/                Booking model, BookingViewSet, overlap validation
│   ├── requirements.txt
│   └── manage.py
└── frontend/                  Static site (no build step, no framework)
    ├── index.html               space listing + search/filter
    ├── space.html                space detail + booking form
    ├── login.html / register.html
    ├── my-bookings.html          the logged-in user's bookings
    ├── css/style.css             design system (tokens + components)
    └── js/
        ├── api.js                 all fetch() calls + JWT handling
        ├── dom.js                 all DOM rendering/manipulation
        ├── auth.js                shared navbar auth state + route guard
        └── pages/                 one small entry script per HTML page
```

Each `pages/*.js` file only orchestrates: it calls `api.js` for data and
`dom.js` for rendering. No fetch calls live outside `api.js`, and no
`innerHTML`/DOM writes live outside `dom.js`.

## Quick start (Windows)

Double-click **`setup.bat`** in the project root (or run it from a terminal).
It will:

1. Create the backend virtual environment (first run only) and install dependencies
2. Copy `.env.example` → `.env` (first run only — you must fill in `ADMIN_USERNAME` /
   `ADMIN_EMAIL` / `ADMIN_PASSWORD` before this works)
3. Run migrations
4. Create your admin/superuser account from those `.env` values (idempotent — safe to re-run)
5. Start the frontend on port 5500 (minimized window) and the backend on port 8000 (this window)

When it's ready you'll see a banner with every link. Log into `/admin/`
with the account you set in `.env`. Press `Ctrl+C` in that window to stop
both servers.

## Backend setup

```bash
cd backend
python -m venv venv
source venv/Scripts/activate      # Windows Git Bash; use venv\Scripts\activate on cmd
pip install -r requirements.txt
cp .env.example .env               # then fill in SECRET_KEY / ADMIN_* below
python manage.py migrate
python manage.py ensure_admin      # creates the superuser from ADMIN_* in .env
python manage.py runserver 8000
```

- API root: `http://127.0.0.1:8000/api/`
- **Swagger UI**: `http://127.0.0.1:8000/swagger/`
- **Redoc**: `http://127.0.0.1:8000/redoc/`
- Django admin: `http://127.0.0.1:8000/admin/`

There is no seeded/demo data — `db.sqlite3` starts empty aside from the one
superuser created via `ensure_admin`. Add real spaces from `/admin/` (name,
capacity, price per hour, image) and they'll immediately show up on the
frontend and in Swagger.

`ADMIN_USERNAME` / `ADMIN_EMAIL` / `ADMIN_PASSWORD` live only in
`backend/.env`, which is git-ignored — they are never committed to source
control.

### Key endpoints

Full reference — every endpoint, parameter, error and business rule — is in
**[API_DOC.md](API_DOC.md)**.

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/auth/register/` | none | Create an account |
| POST | `/api/auth/login/` | none | Obtain JWT access + refresh |
| POST | `/api/auth/refresh/` | none | Refresh an access token |
| GET | `/api/auth/me/` | JWT | Current user profile |
| GET | `/api/spaces/` | none | List/search/filter spaces |
| GET | `/api/spaces/choices/` | none | `{slug, name}` list for pickers |
| GET | `/api/spaces/{slug}/` | none | Space detail |
| POST | `/api/spaces/` | staff/owner | Create a space |
| GET | `/api/bookings/` | JWT | Your own bookings (staff see all) |
| POST | `/api/bookings/` | JWT | Create a booking (overlap-checked) |
| DELETE | `/api/bookings/{id}/` | JWT (owner) | Delete a booking |
| PATCH | `/api/bookings/{id}/status/` | staff | Confirm or cancel |
| POST | `/api/bookings/{id}/check-in/` | JWT (owner) | Check in — gated on start time |
| POST | `/api/bookings/{id}/check-out/` | JWT (owner) | Check out + record payment |
| GET | `/api/payments/` | JWT | Your payment history (staff see all) |

Bookings reference a space by its **slug** (`"space": "space-1"`), which you can
look up from `/api/spaces/choices/`.

### Overbooking prevention

Implemented twice, for defense in depth:

1. **`BookingSerializer.validate()`** ([bookings/serializers.py](backend/bookings/serializers.py))
   — queries for any existing booking on the same space/date whose time
   range overlaps (`start_time__lt=end_time AND end_time__gt=start_time`),
   excluding cancelled bookings and the instance being updated. Returns a
   clean 400 with a readable message.
2. **`Booking.clean()` + `save()`** ([bookings/models.py](backend/bookings/models.py))
   — the same check runs again at the model layer via `full_clean()`, so
   direct ORM usage (admin, shell, management commands) can't bypass it.

Verified manually end-to-end: booking 10:00–12:00 succeeds, a second
booking 11:00–13:00 on the same space/date is rejected with
`"This space is already booked for an overlapping time slot on that date."`,
and a back-to-back 12:00–13:00 booking succeeds.

## Frontend setup

The frontend is static — no bundler, no npm install. Serve it with any
static file server so ES modules and `fetch()` work under `http://` (opening
the HTML files directly via `file://` will break module imports and CORS):

```bash
cd frontend
python -m http.server 5500
```

Then open `http://127.0.0.1:5500/index.html`.

The frontend picks its API automatically: served from localhost it calls the
local backend, served from anywhere else it calls the hosted one. To point it
at a specific API, set the global before the module loads:

```html
<script>window.API_BASE_URL = "https://username.pythonanywhere.com/api";</script>
```

## Hosting it online

**Live API:** <https://s3ody.pythonanywhere.com/api/> ·
[Swagger](https://s3ody.pythonanywhere.com/swagger/)

Two free pieces, deployed separately:

| Part | Host | Result |
|---|---|---|
| API (Django) | PythonAnywhere | `https://username.pythonanywhere.com` |
| Site (HTML/CSS/JS) | GitHub Pages | `https://username.github.io/coworking_space_booking/` |

Both serve HTTPS, which matters: a page loaded over HTTPS cannot call an API
over plain HTTP — browsers block it as mixed content.

### Part 1 — the API on PythonAnywhere

Sign up for a free "Beginner" account at
[pythonanywhere.com](https://www.pythonanywhere.com). No card required.

**Clone the repo.** Open a **Bash console** from the Consoles tab:

```bash
git clone https://github.com/AbdulrahmanSalem457/coworking_space_booking.git
cd coworking_space_booking/backend
```

**Create the virtualenv.** Let the shell resolve the interpreter rather than
hardcoding a path — PythonAnywhere's Pythons don't all live under `/usr/bin`,
and pointing a virtualenv at the wrong one produces a broken environment that
fails with `ModuleNotFoundError: No module named '_posixsubprocess'`:

```bash
mkvirtualenv --python=$(which python3.11) coworking
pip install -r requirements.txt
```

Note the path it prints — normally `/home/USERNAME/.virtualenvs/coworking`.
You'll paste it into the Web tab shortly.

> If you already made a broken one, delete it and start over:
> `deactivate; rmvirtualenv coworking`

**Write the environment file.** Still in `backend/`:

```bash
cp .env.example .env
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Open `.env` in the Files tab and set:

```
DEBUG=False
SECRET_KEY=<the key that was just printed>
ALLOWED_HOSTS=USERNAME.pythonanywhere.com
CORS_ALLOWED_ORIGINS=
TIME_ZONE=Africa/Cairo

ADMIN_USERNAME=<your admin username>
ADMIN_EMAIL=<your email>
ADMIN_PASSWORD=<a strong password>
```

Leaving `CORS_ALLOWED_ORIGINS` empty keeps the API callable from any site.

**Set up the database and static files:**

```bash
python manage.py migrate
python manage.py collectstatic --no-input
python manage.py ensure_admin
```

**Create the web app.** Web tab → **Add a new web app** → **Manual
configuration** (*not* the "Django" option — that scaffolds a fresh project) →
pick the same Python version. Then on that page set:

| Field | Value |
|---|---|
| Source code | `/home/USERNAME/coworking_space_booking/backend` |
| Virtualenv | `/home/USERNAME/.virtualenvs/coworking` |

Under **Static files**, add one mapping:

| URL | Directory |
|---|---|
| `/static/` | `/home/USERNAME/coworking_space_booking/backend/staticfiles` |

Click the **WSGI configuration file** link, delete everything in it, and paste
the contents of [`deploy/pythonanywhere_wsgi.py`](deploy/pythonanywhere_wsgi.py)
with `USERNAME` replaced. Save, then hit the green **Reload** button.

Your API is now live:

| | |
|---|---|
| API root | `https://USERNAME.pythonanywhere.com/api/` |
| Swagger UI | `https://USERNAME.pythonanywhere.com/swagger/` |
| Django admin | `https://USERNAME.pythonanywhere.com/admin/` |

**To deploy changes later:** in a Bash console, `git pull` inside the repo, then
press **Reload** on the Web tab. Run `migrate` too if models changed.

### Part 2 — the site on GitHub Pages

Point the frontend at your API first: open
[`frontend/js/api.js`](frontend/js/api.js) and set `HOSTED_API_URL` to
`https://USERNAME.pythonanywhere.com/api`, then commit and push.

In the repo on GitHub: **Settings → Pages → Source → GitHub Actions**. That's
the only click needed — [the workflow](.github/workflows/deploy-frontend.yml)
publishes `frontend/` on every push to `main`.

The site appears at `https://USERNAME.github.io/coworking_space_booking/`, works
on phones, and updates itself whenever you push.

### Keeping it alive

- **The free web app needs renewing monthly.** The Web tab shows a "best before"
  date and a **Run until 1 month from today** button; one click extends it, and
  they email a week beforehand. Miss it and the site is disabled until you click
  — your data is untouched either way.
- **Uploaded images do persist** here (unlike ephemeral hosts), so spaces keep
  their photos.
- **There's a daily CPU allowance.** A portfolio project won't come close.

### Deploying somewhere else instead

Nothing is host-specific except the WSGI file. The repo also carries a
[`render.yaml`](render.yaml) blueprint for Render, which trades PythonAnywhere's
manual setup for automatic deploys — at the cost of sleeping after ~15 minutes
idle and a free database that expires.

Any host works if you:

- install `requirements.txt`, then run `collectstatic` and `migrate`
- start with `gunicorn config.wsgi:application`
- set `DEBUG=False`, a long random `SECRET_KEY`, and `ALLOWED_HOSTS`
- set `DATABASE_URL` to a Postgres connection string if the host's filesystem
  is ephemeral — otherwise SQLite is fine and simpler

`DEBUG=False` also switches on HTTPS redirects, secure cookies and HSTS, and
trusts the `X-Forwarded-Proto` header that platform proxies send. If a host
doesn't forward that header you'll get a redirect loop — set
`SECURE_SSL_REDIRECT=False` in `.env` to break it.

## Design system

Defined as CSS custom properties at the top of
[frontend/css/style.css](frontend/css/style.css): warm off-white background,
muted sage green primary, soft terracotta accent, a serif display font
(Fraunces) paired with Inter for body text, and a consistent spacing/radius
scale used across every card, button, and form.
