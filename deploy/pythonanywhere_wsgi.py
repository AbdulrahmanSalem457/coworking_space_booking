"""
WSGI file for PythonAnywhere.

Copy this into the Web tab's WSGI configuration file (the link is on the Web
page — it opens something like /var/www/USERNAME_pythonanywhere_com_wsgi.py),
delete everything already in there, paste this, replace USERNAME below, and
hit Save then Reload.

Settings such as SECRET_KEY, DEBUG and ALLOWED_HOSTS are read from
backend/.env — see the hosting section of the README.
"""
import sys

# ---------------------------------------------------------------------------
# Replace USERNAME with your PythonAnywhere username (both here and in the
# virtualenv path you enter on the Web tab).
# ---------------------------------------------------------------------------
PROJECT_PATH = "/home/USERNAME/coworking_space_booking/backend"

if PROJECT_PATH not in sys.path:
    sys.path.insert(0, PROJECT_PATH)

import os

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
