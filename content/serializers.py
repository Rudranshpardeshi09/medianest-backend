"""
Serializers for the public content payload.

Read-only. Nothing here accepts input -- the only write endpoint on the site
is the contact form, which lives in its own app.

Shapes are chosen to match what the components already render, so the
frontend swap is a change of source and not a change of structure. Where the
page derives something from position (the 01/02/03 labels), it is derived
here too rather than stored, so the two can never disagree.
"""

from django.utils.text import slugify
from rest_framework import serializers

from .models import AboutContent, AboutPillar, Discipline, Service, SiteSettings


class SiteSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSettings
        fields = [
            "tagline",
            "years_of_practice",
            "discipline_count",
            "discipline_count_word",
            "hours_compact",
            "hours_spaced",
            "coverage",
        ]


class AboutPillarSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutPillar
        fields = ["title", "body", "is_wide"]


class AboutContentSerializer(serializers.ModelSerializer):
    figure = serializers.SerializerMethodField()
    pillars = serializers.SerializerMethodField()

    class Meta:
        model = AboutContent
        fields = ["heading", "description", "figure", "figure_alt", "focal_x", "focal_y", "pillars"]

    def get_figure(self, obj):
        if not obj.figure:
            return None
        request = self.context.get("request")
        url = obj.figure.url
        return request.build_absolute_uri(url) if request else url

    def get_pillars(self, obj):
        return AboutPillarSerializer(AboutPillar.objects.all(), many=True).data


class ServiceSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source="rail_label", read_only=True)
    tags = serializers.ListField(source="tag_list", read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = ["title", "label", "body", "tags", "image", "focal_x", "focal_y", "is_featured"]

    def get_image(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url


class DisciplineSerializer(serializers.ModelSerializer):
    """
    Shaped to match what the grid already renders, one tile at a time.

    `media` folds films and stills into a single list because that is what the
    lightbox steps through. A tile carries one kind or the other, so the two
    querysets never interleave and no ordering question arises between them.

    `span` is deliberately absent. It belongs to the grid position, not to the
    discipline -- see the model docstring -- so the frontend keeps the eight
    spans and applies them by position.
    """

    id = serializers.SerializerMethodField()
    meta = serializers.CharField(source="meta_label", read_only=True)
    img = serializers.SerializerMethodField()
    media = serializers.SerializerMethodField()

    class Meta:
        model = Discipline
        fields = ["id", "name", "meta", "img", "focal_x", "focal_y", "media"]

    def get_id(self, obj):
        """
        The anchor and React key. Derived from the name so it cannot drift
        from what is on the tile, and so a renamed discipline does not keep a
        stale slug pointing at it.
        """
        return slugify(obj.name)

    def _url(self, field):
        if not field:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(field.url) if request else field.url

    def get_img(self, obj):
        return self._url(obj.cover)

    def get_media(self, obj):
        items = [
            {"type": "video", "id": v.youtube_id, "title": v.title}
            for v in obj.videos.all()
        ]
        items += [
            {"type": "image", "src": self._url(i.image), "alt": i.alt}
            for i in obj.images.all()
        ]
        return items
