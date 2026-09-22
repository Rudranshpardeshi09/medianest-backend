"""Local development. Never used in production."""

from .base import *  # noqa: F401,F403
from .base import env_list

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# The Vite dev server, plus whatever else is set in .env
CORS_ALLOWED_ORIGINS = list(
    dict.fromkeys(
        ["http://localhost:5173", "http://127.0.0.1:5173"]
        + env_list("CORS_ALLOWED_ORIGINS")
    )
)
