"""
One endpoint, the whole published payload.

BACKEND-PLAN.md settles on two endpoints for the site, and this is the read
one. The page has no search, no filters, no pagination and no auth, and it
renders every section in a single paint, so splitting this into per-section
URLs would be extra round trips for data that is always wanted together.

It is also consumed at **build time**, not by the browser: the frontend fetches
this once while Vite builds and bakes the result into the bundle. That is why
there is no pagination and no partial response -- one caller, once per deploy,
wanting everything.
"""

from django.utils.http import http_date
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import AboutContent, AboutPillar, Service, SiteSettings
from .serializers import AboutContentSerializer, ServiceSerializer, SiteSettingsSerializer


def _last_modified():
    """The newest change across every content table, for ETag and caching."""
    stamps = []
    for model in (SiteSettings, AboutContent):
        obj = model.objects.first()
        if obj:
            stamps.append(obj.updated_at)
    for model in (AboutPillar, Service):
        obj = model.objects.order_by("-updated_at").first()
        if obj:
            stamps.append(obj.updated_at)
    return max(stamps) if stamps else None


@api_view(["GET"])
def content(request):
    settings_obj = SiteSettings.load()
    about = AboutContent.load()

    services = Service.objects.filter(is_published=True)
    ctx = {"request": request}

    payload = {
        "settings": SiteSettingsSerializer(settings_obj, context=ctx).data,
        "about": AboutContentSerializer(about, context=ctx).data,
        # Split here rather than in the frontend: which list a service belongs
        # to is a content decision, and the numbering below depends on it.
        "services": ServiceSerializer(
            services.filter(is_featured=True), many=True, context=ctx
        ).data,
        "service_strip": ServiceSerializer(
            services.filter(is_featured=False), many=True, context=ctx
        ).data,
    }

    response = Response(payload)
    stamp = _last_modified()
    if stamp:
        # ConditionalGetMiddleware turns these into a 304 on a repeat request.
        response["Last-Modified"] = http_date(stamp.timestamp())
    response["Cache-Control"] = "public, max-age=60"
    return response
