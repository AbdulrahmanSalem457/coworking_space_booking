#!/usr/bin/env bash
# Render runs this on every deploy, before starting the web process.
set -o errexit

pip install -r requirements.txt

# Collect Swagger's CSS/JS (and the admin's) so WhiteNoise can serve them.
python manage.py collectstatic --no-input

python manage.py migrate

# Creates the superuser from ADMIN_USERNAME/ADMIN_EMAIL/ADMIN_PASSWORD.
# Skips silently if the account already exists or the vars aren't set.
python manage.py ensure_admin || echo "Skipping admin creation — ADMIN_* env vars not set."
