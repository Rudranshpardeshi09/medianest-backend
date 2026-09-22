#!/usr/bin/env python
"""Defaults to dev settings; production sets DJANGO_SETTINGS_MODULE itself."""

import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django is not importable. Activate the virtualenv: "
            ".venv/Scripts/activate on Windows, .venv/bin/activate elsewhere."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
