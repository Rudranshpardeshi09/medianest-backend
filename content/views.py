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

from .models import (
    AboutContent,
    AboutPillar,
    Client,
    ClientsContent,
    ContactContent,
    FooterContent,
    Discipline,
    Person,
    Reason,
    Service,
    SiteSettings,
    SocialLink,
    TeamContent,
    Testimonial,
    WhyChooseContent,
)
from .serializers import (
    AboutContentSerializer,
    ClientsSerializer,
    ContactSerializer,
    FooterSerializer,
    SocialLinkSerializer,
    DisciplineSerializer,
    ServiceSerializer,
    SiteSettingsSerializer,
    TeamSerializer,
    TestimonialSerializer,
    WhyChooseSerializer,
)


def _last_modified():
    """The newest change across every content table, for ETag and caching."""
    stamps = []
    for model in (SiteSettings, AboutContent, WhyChooseContent, TeamContent, ClientsContent, ContactContent, FooterContent):
        obj = model.objects.first()
        if obj:
            stamps.append(obj.updated_at)
    for model in (AboutPillar, Service, Discipline, Reason, Person, Testimonial, Client, SocialLink):
        obj = model.objects.order_by("-updated_at").first()
        if obj:
            stamps.append(obj.updated_at)
    return max(stamps) if stamps else None


@api_view(["GET"])
def content(request):
    settings_obj = SiteSettings.load()
    about = AboutContent.load()

    services = Service.objects.filter(is_published=True)
    disciplines = Discipline.objects.filter(is_published=True).prefetch_related(
        "videos", "images"
    )
    # Listed, not sliced: the reasons stack rather than tile, so there is no
    # count the layout cannot take. The section's height follows instead.
    reasons = list(Reason.objects.filter(is_published=True))
    people = list(
        Person.objects.filter(is_published=True).prefetch_related("lines", "social")
    )
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
        # Only the first eight published tiles. A ninth would start a fifth
        # grid row with eight empty columns beside it, so the cut happens here
        # rather than leaving the frontend to slice a list it did not size.
        "disciplines": DisciplineSerializer(
            disciplines[: Discipline.VISIBLE_TILES], many=True, context=ctx
        ).data,
        "why_choose": WhyChooseSerializer(
            {"content": WhyChooseContent.load(), "reasons": reasons}, context=ctx
        ).data,
        "team": TeamSerializer(
            {"content": TeamContent.load(), "people": people}, context=ctx
        ).data,
        "testimonials": TestimonialSerializer(
            Testimonial.objects.filter(is_published=True), many=True, context=ctx
        ).data,
        "clients": ClientsSerializer(
            {
                "content": ClientsContent.load(),
                "items": Client.objects.filter(is_published=True),
            },
            context=ctx,
        ).data,
        "contact": ContactSerializer(
            {"content": ContactContent.load(), "settings": settings_obj}, context=ctx
        ).data,
        "footer": FooterSerializer(FooterContent.load(), context=ctx).data,
        # Top level, not under `footer`: the header's mobile menu shows these
        # too, so they belong to the firm rather than to a section.
        "social": SocialLinkSerializer(
            SocialLink.objects.filter(is_published=True), many=True, context=ctx
        ).data,
    }

    response = Response(payload)
    stamp = _last_modified()
    if stamp:
        # ConditionalGetMiddleware turns these into a 304 on a repeat request.
        response["Last-Modified"] = http_date(stamp.timestamp())
    response["Cache-Control"] = "public, max-age=60"
    return response
