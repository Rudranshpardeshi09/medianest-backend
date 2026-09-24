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

from .models import (
    AboutContent,
    AboutPillar,
    Discipline,
    Person,
    Reason,
    Service,
    SiteSettings,
    number_word,
)


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


class ReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reason
        fields = ["label", "body"]


class WhyChooseSerializer(serializers.Serializer):
    """
    The heading and its reasons.

    `{count}` is resolved here rather than in the browser. The word list has
    to live somewhere, and a copy in the frontend beside a copy in the admin
    preview is two things to keep in step for no gain -- the page has the
    reasons either way, so it can be handed a finished sentence.
    """

    heading = serializers.SerializerMethodField()
    reasons = serializers.SerializerMethodField()

    def get_heading(self, obj):
        return obj["content"].heading.replace("{count}", number_word(len(obj["reasons"])))

    def get_reasons(self, obj):
        return ReasonSerializer(obj["reasons"], many=True).data


class PersonSerializer(serializers.ModelSerializer):
    """
    One partner, shaped as the section renders them.

    `platform` is sent as the stored key -- "instagram" -- not as an icon
    class. The class belongs beside the icon font that defines it, which is in
    the frontend; sending `fab fa-instagram` from Django would put a second
    copy of the frontend's icon library in the API.
    """

    photo = serializers.SerializerMethodField()
    lines = serializers.SerializerMethodField()
    social = serializers.SerializerMethodField()

    class Meta:
        model = Person
        fields = [
            "first_name", "last_name", "role",
            "photo", "focal_x", "focal_y",
            "lines", "social",
        ]

    def get_photo(self, obj):
        if not obj.photo:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.photo.url) if request else obj.photo.url

    def get_lines(self, obj):
        return [line.text for line in obj.lines.all()]

    def get_social(self, obj):
        return [{"platform": s.platform, "url": s.url} for s in obj.social.all()]


class TeamSerializer(serializers.Serializer):
    heading = serializers.SerializerMethodField()
    people = serializers.SerializerMethodField()

    def get_heading(self, obj):
        return obj["content"].heading.replace("{count}", number_word(len(obj["people"])))

    def get_people(self, obj):
        return PersonSerializer(obj["people"], many=True, context=self.context).data
