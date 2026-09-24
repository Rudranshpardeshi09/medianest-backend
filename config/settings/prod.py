"""
Production. Everything secret comes from the environment and the process
refuses to start without it, rather than falling back to a dev default.
"""

from .base import *  # noqa: F401,F403
from .base import env, env_list

DEBUG = False
SECRET_KEY = env("DJANGO_SECRET_KEY", required=True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS")

if not ALLOWED_HOSTS:
    raise RuntimeError("DJANGO_ALLOWED_HOSTS must be set in production")
if not CORS_ALLOWED_ORIGINS:
    raise RuntimeError("CORS_ALLOWED_ORIGINS must be set in production")

# Behind a TLS-terminating proxy. PythonAnywhere terminates HTTPS at its own
# front end and passes X-Forwarded-Proto through, so without this Django sees
# every request as plain HTTP and the redirect below would loop.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")
