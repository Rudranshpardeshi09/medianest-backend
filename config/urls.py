"""
URL routing.

The admin path is configurable so production is not sitting on /admin/.
Media is served by Django only in development; in production the object
store or the web server serves it (see IMPLEMENTATION PLAN.md, Gate 3).
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from content.publish import publish

from .settings.base import env

urlpatterns = [
    # Before admin.site.urls, which would otherwise read "publish" as an app
    # label and answer 404. Under the admin path so it is as hard to find as
    # the admin itself, and the view requires a logged-in staff user anyway.
    path(f"{env('DJANGO_ADMIN_PATH', 'admin')}/publish/", publish, name="publish"),
    path(f"{env('DJANGO_ADMIN_PATH', 'admin')}/", admin.site.urls),
    path("api/", include("core.urls")),
    path("api/", include("content.urls")),
    # Phase 1 adds enquiries.urls
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
